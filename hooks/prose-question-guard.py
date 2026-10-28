#!/usr/bin/env python3
"""Stop hook: nudge Claude to use AskUserQuestion instead of prose questions.

Use this for interactive sessions where questions belong in AskUserQuestion.
When the final reply of a turn asks the user something in prose, block the stop
once and tell Claude to put the question in the tool. A second stop in the
same chain (stop_hook_active) always passes, so this cannot loop.
"""
import json
import os
import re
import sys

ASK_PATTERNS = [
    r"\?(?=[\s*_)\]\"']|$)",
    r"\b(let me know|tell me (if|whether|which|when)|your call|up to you)\b",
    r"\b(would you like|do you want|want me to|should i|shall i|can you confirm|ok to|okay to)\b",
    r"\bneeds? your (approval|decision|ok|go-ahead|input|answer)\b",
    r"\b(if you('d| would) (like|prefer|rather))\b",
]
ASK_RE = re.compile("|".join(ASK_PATTERNS), re.IGNORECASE)


def strip_code(text):
    text = re.sub(r"(```|~~~).*?\1", "", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return re.sub(r"[\"\u201c][^\"\u201d\n]*[\"\u201d]", "", text)  # quoted phrases


def is_genuine_user(entry):
    if entry.get("type") != "user":
        return False
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)
    return False


def final_reply(entries):
    """Return (final text, used AskUserQuestion this turn)."""
    turn = []
    for entry in reversed(entries):
        if is_genuine_user(entry):
            break
        turn.append(entry)
    turn.reverse()
    used_auq = False
    texts = []
    for entry in turn:
        if entry.get("type") != "assistant":
            continue
        message = entry.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                # Only the reply after the last tool call counts; it is exempt
                # only when that last call was the question tool itself.
                used_auq = block.get("name") == "AskUserQuestion"
                texts = []
            elif block.get("type") == "text":
                texts.append(block.get("text", ""))
    return "\n".join(texts), used_auq


def find_question(text):
    for line in strip_code(text).splitlines():
        stripped = line.strip()
        if stripped.startswith(">"):
            continue  # quoted text, not our own question
        if stripped and ASK_RE.search(stripped):
            return stripped[:160]
    return None


def main():
    try:
        data = json.load(sys.stdin.buffer)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    if data.get("stop_hook_active"):
        return
    # SDK entrypoints are non-interactive and have no one to ask.
    if os.environ.get("CLAUDE_CODE_ENTRYPOINT", "cli").startswith("sdk"):
        return
    path = data.get("transcript_path")
    entries = []
    if isinstance(path, str) and path:
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    try:
                        entry = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(entry, dict):
                        entries.append(entry)
        except OSError:
            pass
    text, used_auq = final_reply(entries)
    # Current clients include the final text directly; their transcript can lag.
    if isinstance(data.get("last_assistant_message"), str):
        text = data["last_assistant_message"]
    if used_auq or not text:
        return
    hit = find_question(text)
    if not hit:
        return
    print(json.dumps({
        "decision": "block",
        "reason": (
            "Your final reply seems to ask the user something in prose: \"" + hit + "\". "
            "Use AskUserQuestion for questions that need the user's answer. "
            "If it is a question or a decision for the user, ask it with AskUserQuestion now. "
            "If it is not a question, end the turn again without change."
        ),
    }))


if __name__ == "__main__":
    main()
