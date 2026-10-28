"""Characterize the existing Stop hook and its public Claude Code input contract."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


HOOK = Path(__file__).resolve().parents[1] / "prose-question-guard.py"


def assistant(*blocks):
    return {"type": "assistant", "message": {"content": list(blocks)}}


def text(value):
    return {"type": "text", "text": value}


def tool(name):
    return {"type": "tool_use", "id": "example-call", "name": name, "input": {}}


def user(content="Please help with this draft."):
    return {"type": "user", "message": {"content": content}}


def run_hook(tmp_path, entries=(), *, payload=None, entrypoint="cli", raw=None):
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
    if payload is None:
        payload = {"transcript_path": str(transcript), "stop_hook_active": False}
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        env={**os.environ, "CLAUDE_CODE_ENTRYPOINT": entrypoint},
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return json.loads(result.stdout) if result.stdout else None


@pytest.mark.parametrize("reply", [
    "Should I publish this?", "Let me know which draft you prefer.",
    "Your call.", "This needs your approval.", "Would you like a shorter draft",
])
def test_prose_questions_block_once(tmp_path, reply):
    decision = run_hook(tmp_path, [user(), assistant(text(reply))])
    assert decision["decision"] == "block"
    assert "AskUserQuestion" in decision["reason"]


@pytest.mark.parametrize("reply", [
    "The build passed.", "```text\nShould I publish?\n```\nDone.",
    "~~~text\nShould I publish?\n~~~\nDone.", "Run `query?` to test.",
    "See https://example.test/search?q=story", '> Should I publish this?',
    'The headline is "What next?".', 'The headline is “What next?”.',
])
def test_completion_and_quoted_examples_pass(tmp_path, reply):
    assert run_hook(tmp_path, [user(), assistant(text(reply))]) is None


def test_tool_result_does_not_hide_the_last_question_tool(tmp_path):
    entries = [user(), assistant(tool("AskUserQuestion")),
               user([{"type": "tool_result", "tool_use_id": "example-call", "content": "Draft A"}]),
               assistant(text("Your call."))]
    assert run_hook(tmp_path, entries) is None


def test_a_later_tool_call_removes_the_exemption(tmp_path):
    entries = [user(), assistant(tool("AskUserQuestion")),
               assistant(tool("Read")), assistant(text("Should I publish?"))]
    assert run_hook(tmp_path, entries)["decision"] == "block"


def test_earlier_turn_does_not_exempt_a_new_question(tmp_path):
    entries = [user(), assistant(tool("AskUserQuestion")),
               user("New task."), assistant(text("Should I publish?"))]
    assert run_hook(tmp_path, entries)["decision"] == "block"


def test_only_text_after_the_last_tool_is_checked(tmp_path):
    entries = [user(), assistant(text("Should I publish?"), tool("Read")),
               assistant(text("The build passed."))]
    assert run_hook(tmp_path, entries) is None


def test_stop_hook_active_prevents_a_loop(tmp_path):
    payload = {"stop_hook_active": True, "last_assistant_message": "Should I publish?"}
    assert run_hook(tmp_path, payload=payload) is None


@pytest.mark.parametrize("entrypoint", ["sdk-cli", "sdk-py"])
def test_sdk_entrypoints_are_exempt(tmp_path, entrypoint):
    assert run_hook(tmp_path, [user(), assistant(text("Should I publish?"))],
                    entrypoint=entrypoint) is None


def test_direct_final_message_handles_a_lagging_transcript(tmp_path):
    payload = {"transcript_path": str(tmp_path / "session.jsonl"),
               "last_assistant_message": "Should I publish?"}
    assert run_hook(tmp_path, [user(), assistant(text("Old text."))],
                    payload=payload)["decision"] == "block"


def test_direct_completion_overrides_old_transcript_question(tmp_path):
    payload = {"transcript_path": str(tmp_path / "session.jsonl"),
               "last_assistant_message": "The build passed."}
    assert run_hook(tmp_path, [user(), assistant(text("Should I publish?"))],
                    payload=payload) is None


@pytest.mark.parametrize("payload", [{}, {"transcript_path": "/missing/session.jsonl"},
                                     {"transcript_path": 42}])
def test_missing_transcript_allows_the_stop(tmp_path, payload):
    assert run_hook(tmp_path, payload=payload) is None


@pytest.mark.parametrize("raw", ["", "not json", "[]", "null"])
def test_malformed_input_allows_the_stop(tmp_path, raw):
    assert run_hook(tmp_path, raw=raw) is None


def test_malformed_transcript_records_are_skipped(tmp_path):
    transcript = tmp_path / "malformed.jsonl"
    transcript.write_text('broken\nnull\n' + json.dumps(assistant(text("Should I publish?"))))
    assert run_hook(tmp_path, payload={"transcript_path": str(transcript)})["decision"] == "block"
