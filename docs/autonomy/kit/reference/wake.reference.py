#!/usr/bin/env python3
"""REFERENCE IMPLEMENTATION — read it, adapt it, do NOT run it as-is.

The wake loop: one scheduled run. It picks one issue, assembles the prompt,
spawns the agent CLI under a hard timeout, watches for a stuck session, then
summarizes and notifies. Your agent should rewrite this for your OS (see the
"Five primitives" table in BUILD-WITH-YOUR-AGENT.md) and your real config loader.

This version uses the GNU/Linux primitives. On macOS swap `timeout` for
`gtimeout`; on Windows run the loop inside WSL or replace the spawn with a
PowerShell job. Standard library + the agent CLI only.
"""
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pick_one  # the sibling reference picker


def receipt_token():
    """A unique, sortable, non-secret session marker. Goes in commit/PR/comment
    text so a verifier can attribute the work — never inside a committed file."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M")
    return f"wake-{stamp}-{uuid.uuid4().hex[:6]}"


def assemble_prompt(pick, cfg, token):
    """Concatenate the chosen issue, the scope constraints, and the standing
    nudges whose flags are on. Block text lives in prompts.md; load it from there
    so you edit wording in one place. Order matters — keep it as written."""
    issue = pick["chosen"]
    scope = cfg["scope"]
    parts = [
        render_block("task", token=token, issue=issue, scope=scope),  # always first
    ]
    order = ["quality_bar", "verify_from_code", "review", "wrap_up",
             "final_reflection", "capture_followups_as_issues", "out_of_scope_as_issue"]
    for name in order:
        if cfg["nudges"].get(name):
            parts.append(render_block(name, token=token, cfg=cfg))
    return "\n\n".join(parts)


def render_block(name, **kw):
    """Stub: in the real build this reads the matching block from prompts.md and
    substitutes <TOKEN>, the issue, and the scope text. Kept abstract here so the
    loop's shape stays visible."""
    return f"[block:{name}]"  # replace with the real prompts.md loader


def spawn_session(cfg, prompt, log_path):
    """Run the agent CLI non-interactively on the prompt, under a hard timeout
    that flushes output before it kills (the --foreground flag is the difference
    between a real log and a zero-byte lie). Returns the subprocess.Popen."""
    hard = cfg["schedule"]["timeouts"]["hard_minutes"] * 60
    cmd = [
        "timeout", "--foreground", "--kill-after=30", str(hard),
        cfg["machine"]["agent_cli"],
        "--dangerously-skip-permissions",   # unattended: no interactive approvals
        "-p",                                # prompt mode; the prompt arrives on stdin
    ]
    log = open(log_path, "wb")
    # Long prompts overflow argv on some kernels; feed it on stdin instead.
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=log, stderr=log,
                            cwd=cfg["machine"]["work_dir"], text=False), log, prompt


def monitor(proc, log_path, cfg):
    """Watch the session. Kill it if the log stops growing for idle_minutes
    (likely stuck); the timeout wrapper enforces the hard ceiling on its own."""
    idle = cfg["schedule"]["timeouts"]["idle_minutes"] * 60
    last_size, last_change = -1, time.monotonic()
    while proc.poll() is None:
        time.sleep(30)
        size = Path(log_path).stat().st_size if Path(log_path).exists() else 0
        if size != last_size:
            last_size, last_change = size, time.monotonic()
        elif time.monotonic() - last_change > idle:
            proc.kill()                      # stuck: no output for idle_minutes
            return "killed-idle"
    return "ok" if proc.returncode == 0 else f"exit-{proc.returncode}"


def summarize_and_notify(cfg, token, status, summary_path):
    """The session writes a short summary to summary_path; deliver it. stdout is
    the zero-setup default; telegram (an HTTPS call) is the same on every OS."""
    summary = Path(summary_path).read_text() if Path(summary_path).exists() else "(no summary)"
    line = f"[{token}] {status}\n{summary}"
    if cfg["notify"]["channel"] == "telegram":
        send_telegram(cfg, line)             # resolve the token refs, POST to the bot API
    else:
        print(line)


def send_telegram(cfg, text):
    """Stub: resolve notify.telegram.*_ref via your secret backend, then POST to
    https://api.telegram.org/bot<token>/sendMessage. Omitted for brevity."""
    print("[telegram]", text)


def run_wake(cfg):
    token = receipt_token()
    pick = pick_one.pick_one(cfg["github"])
    if pick is None:
        print(f"[{token}] no eligible issues — nothing to do")  # invariant 8: fail safe
        return
    prompt = assemble_prompt(pick, cfg, token)
    log_path = f"/tmp/wake-{token}.log"
    summary_path = f"/tmp/wake-{token}.summary"
    proc, log, payload = spawn_session(cfg, prompt, log_path)
    proc.stdin.write(payload.encode())
    proc.stdin.close()
    status = monitor(proc, log_path, cfg)
    log.close()
    # NOTE: scope enforcement (deny-path / size-cap check before the PR opens)
    # lives in the harness too, not only the prompt — see BUILD step 7.
    summarize_and_notify(cfg, token, status, summary_path)


if __name__ == "__main__":
    raise SystemExit("Reference only. Load config.yaml and call run_wake(cfg).")
