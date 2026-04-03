# Transcript scanner and activity-aware session-end hook

**Date:** 2026-04-03
**Status:** Approved
**Scope:** autocontext plugin (`claude-skills-journalism`)

## Problem

The autocontext `session-end.sh` Stop hook runs after every Claude response. It validates lessons (bumping confidence, checking for contradictions) and regenerates the playbook each time. While it's a lightweight command hook (not an agent spawn), it does unnecessary disk I/O on sessions where nothing meaningful happened — pure Q&A, research, or reading.

Separately, users who build custom Stop hooks (like session handoff writers) lack a reusable way to detect whether a session produced meaningful work. Each hook ends up reimplementing transcript parsing logic independently.

## Solution

Two changes:

1. **Shared transcript scanner** (`scripts/transcript-scanner.py`) — a standalone utility that reads a Claude Code session transcript (JSONL) and returns structured activity signals.
2. **Activity gate in `session-end.sh`** — calls the scanner before doing lesson validation. Skips work when no meaningful activity happened, with a 10-minute time fallback.

## Design

### Transcript scanner

**Location:** `autocontext/scripts/transcript-scanner.py`

**Interface:**
```bash
python3 "$PLUGIN_ROOT/scripts/transcript-scanner.py" \
    --transcript "/path/to/session.jsonl" \
    --since 1743700000 \
    --config ".autocontext/config.json"
```

All arguments are optional:
- `--transcript` — path to the session JSONL file. If missing, empty, or file doesn't exist, returns `{"meaningful": false}` (no data to scan, so no signals found). Callers that want fail-open behavior should handle this themselves.
- `--since` — Unix timestamp (seconds). Only consider tool calls after this time. Entries without a timestamp field are included regardless. Default: 0 (scan all).
- `--config` — path to config file for custom signal definitions. Falls back to hardcoded defaults if missing or unreadable.

**Output (JSON to stdout):**
```json
{
  "meaningful": true,
  "level": "high",
  "signals": [
    {"type": "Write", "detail": "src/hooks/session-end.sh", "ts": 1743700500},
    {"type": "Bash", "detail": "git commit -m 'Fix hook'", "ts": 1743700600}
  ],
  "tool_counts": {"Write": 1, "Edit": 3, "Read": 12, "Bash": 7, "Grep": 4}
}
```

When no meaningful activity:
```json
{
  "meaningful": false,
  "level": "none",
  "signals": [],
  "tool_counts": {"Read": 5, "Grep": 2}
}
```

**Signal classification (defaults):**

| Level | Trigger |
|-------|---------|
| High | Write tool, Edit tool, Bash containing: `git commit`, `gh pr create`, `gh pr merge`, `firebase deploy`, `systemctl restart`, `systemctl stop`, `systemctl start`. Any MCP tool with "email" or "compose" in the name. |
| Medium | Agent tool, Bash containing: `git push`, `npm run build`, `cargo build`, `pip install`, `npm install`. |
| Low (no trigger) | Read, Grep, Glob, Bash not matching any pattern above. |

Result is `meaningful: true` when any high or medium signal is found.

**Config override** (optional key in `.autocontext/config.json`):
```json
{
  "activity_signals": {
    "high_bash_patterns": ["git commit", "gh pr create", "deploy"],
    "medium_bash_patterns": ["git push", "npm run build"],
    "high_tool_names": ["Write", "Edit"],
    "medium_tool_names": ["Agent"]
  }
}
```

If the `activity_signals` key is absent, defaults apply. If present, each sub-key fully replaces that signal tier (not merged with defaults). This lets projects narrow or widen what counts as meaningful.

**Transcript JSONL parsing:**

The scanner reads lines from the JSONL file. For each line:
1. Parse as JSON. Skip invalid lines.
2. Skip entries where `type` is not `"assistant"`.
3. If `--since` is set and the entry has a `timestamp` field (milliseconds), skip entries before that time. Entries without a timestamp field are always included (fail-open at entry level).
4. Walk `message.content` array looking for blocks where `type == "tool_use"`.
5. For each tool use, check `name` and `input` against the signal classification.
6. Collect matching signals and aggregate tool counts.

**Error handling:** The scanner itself returns `{"meaningful": false}` when there's no data to scan (missing file, empty path). Unexpected errors (malformed JSON mid-file, permission issues) are logged to stderr and the scanner continues scanning remaining lines. The fail-open behavior lives in `session-end.sh`, which defaults to `{"meaningful": true}` if the scanner subprocess fails entirely — so validation proceeds as before.

### Changes to session-end.sh

Add an activity gate at the top of the script, after reading stdin and before the lesson validation logic.

**Gate logic:**
1. Extract `transcript_path` from stdin JSON (already available in Stop hook input).
2. Call `transcript-scanner.py` with `--transcript` and `--since` (mtime of `session-lessons.json`, which marks session start).
3. If scanner returns `meaningful: false`:
   - Check session age (now - mtime of session-lessons.json).
   - If under 10 minutes (600 seconds), return `{}` and exit — skip validation.
   - If 10+ minutes, fall through to normal validation (time fallback).
4. If scanner returns `meaningful: true` or errors, proceed with existing validation.

**Fail-open guarantees:**
- If `transcript-scanner.py` doesn't exist → fall through to existing behavior.
- If Python call errors → default to `{"meaningful": true}` → fall through.
- If stdin doesn't contain `transcript_path` → fall through.

The existing lesson validation, playbook regeneration, and skill tracking cleanup code is unchanged.

### What this does NOT change

- `session-start.sh` — runs once per session, already efficient.
- `post-tool-use.sh` — already scoped to specific tool types.
- `user-prompt-submit.sh` — fires on user messages, correct trigger for correction detection.
- `generate-playbook.py` — called by session-end.sh only when validation runs.
- Plugin config schema — `activity_signals` is optional, all existing configs work unchanged.

## Backward compatibility

- No new required config keys.
- No changes to lesson.json schema.
- If the scanner script is missing (e.g., older plugin version), session-end.sh falls through to current behavior.
- The scanner reads the transcript JSONL format that Claude Code produces. No version-specific coupling — it only looks for `type: "assistant"` entries with `content` arrays containing `tool_use` blocks.

## Files changed

| File | Change |
|------|--------|
| `autocontext/scripts/transcript-scanner.py` | New file |
| `autocontext/hooks/session-end.sh` | Add activity gate before lesson validation |
| `autocontext/README.md` | Document scanner utility and `activity_signals` config |

## Testing

- **Scanner with active session transcript:** Feed a real JSONL with Write/Edit calls, verify `meaningful: true` and correct signals list.
- **Scanner with research-only transcript:** Feed JSONL with only Read/Grep/Glob, verify `meaningful: false`.
- **Scanner with empty/missing transcript:** Verify fail-open (`meaningful: true`).
- **Scanner with `--since` filtering:** Verify only tool calls after the timestamp are considered.
- **Scanner with custom config:** Verify config overrides replace defaults.
- **session-end.sh gate:** Verify lesson validation is skipped for non-meaningful sessions under 10 min.
- **session-end.sh time fallback:** Verify validation runs for non-meaningful sessions over 10 min.
- **session-end.sh without scanner:** Remove scanner script, verify existing behavior unchanged.
