---
name: prose-question-guard
event: Stop
description: Nudge Claude to use AskUserQuestion when its final reply asks the user a question in prose.
---

# Prose question guard

If Claude ends a turn with “Should I publish this?” or “Let me know which version
you prefer,” this hook blocks that stop once. It tells Claude to ask through
`AskUserQuestion`, where the user can answer in the question interface.

Use it for interactive Claude Code sessions when you want decisions and questions
in that interface. It does not send notifications. Phone delivery depends on your
client and notification setup.

## Hook behavior

- **Event:** `Stop`, for the main agent.
- **Runtime:** Python 3, standard library only. No model calls or network access.
- **Decision:** Prints `{"decision": "block", "reason": "..."}` on stdout and
  exits zero when it finds a possible question. Otherwise it exits zero silently.
- **Loop guard:** Always allows a stop with `stop_hook_active: true`. A false
  positive can pass on the next stop without rewriting the reply.
- **Non-interactive runs:** Skips when `CLAUDE_CODE_ENTRYPOINT` starts with `sdk`.
  Other unattended entrypoints should omit this hook from their settings.

The executable is [prose-question-guard.py](prose-question-guard.py). It checks
question marks and phrases such as “would you like,” “your call,” “let me know,”
and “needs your approval.” It ignores fenced code, inline code, URLs, double-quoted
phrases, and lines that start with a Markdown blockquote marker.

The hook reads the supplied `last_assistant_message` when available. It also reads
the local JSONL transcript to identify the current turn and the last tool call.
On older clients without that message field, it checks assistant text after the
last tool call. User entries containing tool results do not start a new turn.

When the last tool call in the current turn is `AskUserQuestion`, the reply passes.
An earlier question-tool call does not exempt text after a later tool call.
Malformed JSON records are skipped. Missing or unreadable transcripts and invalid
payloads allow the stop unless a usable final message is supplied directly.

## Install

From a clone of this repository, copy the executable:

```sh
mkdir -p ~/.claude/hooks
cp hooks/prose-question-guard.py ~/.claude/hooks/
```

Merge this entry into the existing `hooks.Stop` array in
`~/.claude/settings.json`. Keep any existing hooks and settings. Replace the
example path with the absolute path to the copied file on your machine:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /absolute/path/to/.claude/hooks/prose-question-guard.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

On Windows, use `python` if that is your Python 3 command. Use forward slashes in
the absolute path. Quote the script path inside the JSON command if it contains
spaces: `"command": "python \"C:/Users/Your Name/.claude/hooks/prose-question-guard.py\""`.

These top-level hooks are installed manually. Installing a marketplace skill
package does not enable this hook. It uses Claude Code's Stop event and
`AskUserQuestion`; it is not a Codex hook.

## Examples and limits

| Final reply or state | Result |
| --- | --- |
| `Should I publish this?` | Blocks once; asks Claude to use `AskUserQuestion` |
| `Let me know which draft you prefer.` | Blocks once, even without a question mark |
| `The build passed.` | Allows |
| A question inside a code block or Markdown blockquote | Allows |
| `AskUserQuestion` is the last tool call | Allows |
| `stop_hook_active` is true | Allows |
| SDK entrypoint | Allows |

This is a wording heuristic. Rhetorical questions can trigger it, and questions
inside quotes can escape it. It does not prove that a question was answered or
that a user approved an action. It does not grant permission to act.

## Verify

Run the behavior tests from the repository root:

```sh
python3 -m pytest hooks/tests/test_prose_question_guard.py -q
```

In a fresh interactive Claude Code session with the hook loaded, ask for a reply
that ends with a plain-text question. Confirm that Claude receives the hook reason
and moves the question into `AskUserQuestion`. A second stop must be allowed if
Claude determines that the match was not a question for the user.

See the [public guide](https://skills.amditis.tech/prose-question-guard/) and
Claude Code's [Stop hook reference](https://code.claude.com/docs/en/hooks#stop)
for the event contract.
