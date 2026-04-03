# Transcript scanner implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shared transcript scanner utility to the autocontext plugin and wire it into session-end.sh so lesson validation only runs when meaningful work happened.

**Architecture:** Standalone Python script (`transcript-scanner.py`) reads Claude Code session JSONL transcripts and returns structured activity signals as JSON. The existing `session-end.sh` Stop hook calls this script before doing any lesson validation work and exits early if no meaningful activity is detected (with a 10-minute time fallback).

**Tech Stack:** Python 3 (stdlib only — json, argparse, os, sys, time), bash

---

### Task 1: Create transcript scanner script

**Files:**
- Create: `autocontext/scripts/transcript-scanner.py`

- [ ] **Step 1: Write the failing test**

Create a test script that exercises the scanner against synthetic JSONL input:

```bash
cat > /tmp/test-transcript-scanner.sh << 'TESTEOF'
#!/bin/bash
set -euo pipefail

SCANNER="$(pwd)/autocontext/scripts/transcript-scanner.py"
PASS=0
FAIL=0

assert_eq() {
    local label="$1" expected="$2" actual="$3"
    if [[ "$expected" == "$actual" ]]; then
        echo "PASS: $label"
        ((PASS++))
    else
        echo "FAIL: $label"
        echo "  expected: $expected"
        echo "  actual:   $actual"
        ((FAIL++))
    fi
}

# --- Test 1: Write/Edit signals detected ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"src/app.py"}}]}}
{"type":"assistant","timestamp":2000000,"message":{"content":[{"type":"tool_use","name":"Write","input":{"file_path":"src/new-file.py"}}]}}
{"type":"assistant","timestamp":3000000,"message":{"content":[{"type":"tool_use","name":"Edit","input":{"file_path":"src/app.py","old_string":"x","new_string":"y"}}]}}
JSONL
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE")
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
LEVEL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
SIGNAL_COUNT=$(echo "$RESULT" | python3 -c "import json,sys; print(len(json.load(sys.stdin)['signals']))")
assert_eq "write/edit detected as meaningful" "True" "$MEANINGFUL"
assert_eq "write/edit level is high" "high" "$LEVEL"
assert_eq "write/edit signal count" "2" "$SIGNAL_COUNT"
rm -f "$TMPFILE"

# --- Test 2: Read/Grep only = not meaningful ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"src/app.py"}}]}}
{"type":"assistant","timestamp":2000000,"message":{"content":[{"type":"tool_use","name":"Grep","input":{"pattern":"foo"}}]}}
{"type":"assistant","timestamp":3000000,"message":{"content":[{"type":"tool_use","name":"Glob","input":{"pattern":"**/*.py"}}]}}
JSONL
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE")
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "read-only not meaningful" "False" "$MEANINGFUL"
rm -f "$TMPFILE"

# --- Test 3: git commit in Bash = high signal ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"git commit -m 'fix bug'"}}]}}
JSONL
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE")
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
LEVEL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
assert_eq "git commit is meaningful" "True" "$MEANINGFUL"
assert_eq "git commit level is high" "high" "$LEVEL"
rm -f "$TMPFILE"

# --- Test 4: Agent tool = medium signal ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Agent","input":{"description":"research","prompt":"find files"}}]}}
JSONL
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE")
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
LEVEL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
assert_eq "agent is meaningful" "True" "$MEANINGFUL"
assert_eq "agent level is medium" "medium" "$LEVEL"
rm -f "$TMPFILE"

# --- Test 5: --since filters old entries ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Write","input":{"file_path":"old.py"}}]}}
{"type":"assistant","timestamp":5000000,"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"new.py"}}]}}
JSONL
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE" --since 2000)
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "since filters old Write" "False" "$MEANINGFUL"
rm -f "$TMPFILE"

# --- Test 6: Missing transcript file = not meaningful ---
RESULT=$(python3 "$SCANNER" --transcript "/tmp/nonexistent-transcript.jsonl")
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "missing file not meaningful" "False" "$MEANINGFUL"

# --- Test 7: No --transcript arg = not meaningful ---
RESULT=$(python3 "$SCANNER")
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "no args not meaningful" "False" "$MEANINGFUL"

# --- Test 8: tool_counts populated ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"a.py"}}]}}
{"type":"assistant","timestamp":2000000,"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"b.py"}}]}}
{"type":"assistant","timestamp":3000000,"message":{"content":[{"type":"tool_use","name":"Write","input":{"file_path":"c.py"}}]}}
JSONL
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE")
READ_COUNT=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['tool_counts'].get('Read',0))")
WRITE_COUNT=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['tool_counts'].get('Write',0))")
assert_eq "tool_counts Read=2" "2" "$READ_COUNT"
assert_eq "tool_counts Write=1" "1" "$WRITE_COUNT"
rm -f "$TMPFILE"

# --- Test 9: Custom config overrides defaults ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
CFGFILE=$(mktemp /tmp/config-XXXX.json)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Write","input":{"file_path":"a.py"}}]}}
JSONL
cat > "$CFGFILE" << 'JSON'
{"activity_signals":{"high_tool_names":["Bash"],"medium_tool_names":[],"high_bash_patterns":[],"medium_bash_patterns":[]}}
JSON
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE" --config "$CFGFILE")
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "config override: Write not high when overridden" "False" "$MEANINGFUL"
rm -f "$TMPFILE" "$CFGFILE"

# --- Test 10: Entries without timestamp included when --since set ---
TMPFILE=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TMPFILE" << 'JSONL'
{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"file_path":"no-ts.py"}}]}}
JSONL
RESULT=$(python3 "$SCANNER" --transcript "$TMPFILE" --since 9999999)
MEANINGFUL=$(echo "$RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "no-timestamp entry included" "True" "$MEANINGFUL"
rm -f "$TMPFILE"

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
TESTEOF
chmod +x /tmp/test-transcript-scanner.sh
```

Note: the test script does not `exit 1` on failure here — it uses the exit code from `[[ "$FAIL" -eq 0 ]]` so the script can be appended to in Task 2.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jamditis/projects/claude-skills-journalism && bash /tmp/test-transcript-scanner.sh`
Expected: FAIL — `transcript-scanner.py` doesn't exist yet.

- [ ] **Step 3: Write the scanner implementation**

Create `autocontext/scripts/transcript-scanner.py`:

```python
#!/usr/bin/env python3
"""Scan a Claude Code session transcript for meaningful activity signals.

Reads a JSONL transcript file and classifies tool usage into high/medium/low
signal levels. Returns structured JSON to stdout.

Usage:
    python3 transcript-scanner.py --transcript /path/to/session.jsonl [--since UNIX_TS] [--config path/to/config.json]
"""

import argparse
import json
import os
import sys

DEFAULT_HIGH_TOOL_NAMES = ["Write", "Edit"]
DEFAULT_MEDIUM_TOOL_NAMES = ["Agent"]
DEFAULT_HIGH_BASH_PATTERNS = [
    "git commit",
    "gh pr create",
    "gh pr merge",
    "firebase deploy",
    "systemctl restart",
    "systemctl stop",
    "systemctl start",
]
DEFAULT_MEDIUM_BASH_PATTERNS = [
    "git push",
    "npm run build",
    "cargo build",
    "pip install",
    "npm install",
]


def load_config(config_path):
    """Load signal config from file, returning None if unavailable."""
    if not config_path or not os.path.isfile(config_path):
        return None
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        return cfg.get("activity_signals")
    except Exception:
        return None


def get_signals_config(config_path):
    """Return signal classification config, using defaults where needed."""
    overrides = load_config(config_path)
    if overrides and isinstance(overrides, dict):
        return {
            "high_tool_names": overrides.get("high_tool_names", DEFAULT_HIGH_TOOL_NAMES),
            "medium_tool_names": overrides.get("medium_tool_names", DEFAULT_MEDIUM_TOOL_NAMES),
            "high_bash_patterns": overrides.get("high_bash_patterns", DEFAULT_HIGH_BASH_PATTERNS),
            "medium_bash_patterns": overrides.get("medium_bash_patterns", DEFAULT_MEDIUM_BASH_PATTERNS),
        }
    return {
        "high_tool_names": DEFAULT_HIGH_TOOL_NAMES,
        "medium_tool_names": DEFAULT_MEDIUM_TOOL_NAMES,
        "high_bash_patterns": DEFAULT_HIGH_BASH_PATTERNS,
        "medium_bash_patterns": DEFAULT_MEDIUM_BASH_PATTERNS,
    }


def classify_tool_use(name, inp, cfg):
    """Classify a tool use block. Returns ('high'|'medium'|None, detail_string)."""
    # High-signal tool names
    if name in cfg["high_tool_names"]:
        detail = inp.get("file_path", name)
        return "high", detail

    # Medium-signal tool names
    if name in cfg["medium_tool_names"]:
        detail = inp.get("description", inp.get("prompt", name))
        if isinstance(detail, str):
            detail = detail[:120]
        return "medium", detail

    # Bash command pattern matching
    if name == "Bash":
        cmd = inp.get("command", "")
        for pattern in cfg["high_bash_patterns"]:
            if pattern in cmd:
                return "high", cmd[:120]
        for pattern in cfg["medium_bash_patterns"]:
            if pattern in cmd:
                return "medium", cmd[:120]

    # MCP tools with email/compose in name
    if "email" in name.lower() or "compose" in name.lower():
        return "high", name

    return None, None


def scan_transcript(transcript_path, since_ts, cfg):
    """Scan the transcript JSONL and return activity results."""
    signals = []
    tool_counts = {}
    max_level = "none"

    if not transcript_path or not os.path.isfile(transcript_path):
        return {
            "meaningful": False,
            "level": "none",
            "signals": [],
            "tool_counts": {},
        }

    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                if entry.get("type") != "assistant":
                    continue

                # Timestamp filtering (milliseconds in JSONL)
                ts = entry.get("timestamp")
                if since_ts > 0 and ts is not None:
                    if isinstance(ts, (int, float)) and ts / 1000 < since_ts:
                        continue

                msg = entry.get("message", {})
                content = msg.get("content", [])
                if not isinstance(content, list):
                    continue

                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue

                    name = block.get("name", "")
                    inp = block.get("input", {})

                    # Count all tool uses
                    tool_counts[name] = tool_counts.get(name, 0) + 1

                    # Classify
                    level, detail = classify_tool_use(name, inp, cfg)
                    if level:
                        entry_ts = entry.get("timestamp")
                        if isinstance(entry_ts, (int, float)):
                            entry_ts = int(entry_ts / 1000)
                        else:
                            entry_ts = 0
                        signals.append({
                            "type": name,
                            "detail": detail or name,
                            "ts": entry_ts,
                        })
                        if level == "high":
                            max_level = "high"
                        elif level == "medium" and max_level != "high":
                            max_level = "medium"

    except (IOError, OSError) as e:
        print(f"[transcript-scanner] warning: {e}", file=sys.stderr)

    return {
        "meaningful": max_level in ("high", "medium"),
        "level": max_level,
        "signals": signals,
        "tool_counts": tool_counts,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan session transcript for activity signals")
    parser.add_argument("--transcript", default="", help="Path to session JSONL file")
    parser.add_argument("--since", type=float, default=0, help="Unix timestamp — ignore entries before this")
    parser.add_argument("--config", default="", help="Path to config JSON with activity_signals key")
    args = parser.parse_args()

    cfg = get_signals_config(args.config)
    result = scan_transcript(args.transcript, args.since, cfg)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/jamditis/projects/claude-skills-journalism && bash /tmp/test-transcript-scanner.sh`
Expected: All 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add autocontext/scripts/transcript-scanner.py
git commit -m "Add transcript scanner utility for activity-based hook gating"
```

---

### Task 2: Add activity gate to session-end.sh

**Files:**
- Modify: `autocontext/hooks/session-end.sh:13-15` (after stdin read, before lesson file checks)

- [ ] **Step 1: Write the failing test**

Append integration tests to the existing test script. The append replaces the final summary block with additional tests and a new summary:

```bash
# Remove the old summary lines (last 4 lines) and append new tests
head -n -4 /tmp/test-transcript-scanner.sh > /tmp/test-transcript-scanner.tmp
mv /tmp/test-transcript-scanner.tmp /tmp/test-transcript-scanner.sh
chmod +x /tmp/test-transcript-scanner.sh

cat >> /tmp/test-transcript-scanner.sh << 'TESTEOF'

# --- session-end.sh integration tests ---

# Test 11: session-end exits early for non-meaningful session under 10 min
# We test this by checking that session-end.sh outputs '{}' when the
# transcript has no meaningful activity and session-lessons.json is fresh.

TMPDIR=$(mktemp -d /tmp/session-end-test-XXXX)
cd "$TMPDIR"
mkdir -p .autocontext/cache

# Create a minimal lessons.json and session-lessons.json
echo '[{"id":"test1","text":"test lesson","confidence":0.7,"validated_count":0,"last_validated":"2026-04-03T00:00:00+00:00","deleted":false,"tags":[],"category":"test"}]' > .autocontext/lessons.json
echo '[{"id":"test1","text":"test lesson","confidence":0.7,"validated_count":0,"last_validated":"2026-04-03T00:00:00+00:00","deleted":false,"tags":[],"category":"test"}]' > .autocontext/cache/session-lessons.json

# Touch session-lessons.json to NOW (session just started)
touch .autocontext/cache/session-lessons.json

# Create a research-only transcript
TRANSCRIPT=$(mktemp /tmp/transcript-XXXX.jsonl)
cat > "$TRANSCRIPT" << 'JSONL'
{"type":"assistant","timestamp":1000000,"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"a.py"}}]}}
JSONL

# Feed session-end.sh with the transcript path
PLUGIN_ROOT="$(cd /home/jamditis/projects/claude-skills-journalism/autocontext && pwd)"
RESULT=$(echo "{\"session_id\":\"test\",\"transcript_path\":\"$TRANSCRIPT\"}" | \
    CLAUDE_PLUGIN_ROOT="$PLUGIN_ROOT" bash "$PLUGIN_ROOT/hooks/session-end.sh" 2>/dev/null)

assert_eq "session-end skips for non-meaningful + fresh session" "{}" "$RESULT"

# Verify lessons.json was NOT modified (confidence should be unchanged)
CONFIDENCE=$(python3 -c "import json; print(json.load(open('.autocontext/lessons.json'))[0]['confidence'])")
assert_eq "confidence unchanged after skip" "0.7" "$CONFIDENCE"

rm -rf "$TMPDIR" "$TRANSCRIPT"
cd /home/jamditis/projects/claude-skills-journalism

echo ""
echo "Final results: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
TESTEOF
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jamditis/projects/claude-skills-journalism && bash /tmp/test-transcript-scanner.sh`
Expected: Tests 1-10 pass, test 11 FAILS — session-end.sh doesn't have the gate yet.

- [ ] **Step 3: Add the activity gate to session-end.sh**

Insert the gate after line 15 (after `INPUT=$(cat)` and `SESSION_ID=...`), before line 17 (`if [[ ! -f "$SESSION_LESSONS_FILE" ]]`).

The new block to insert between the `SESSION_ID` line and the `SESSION_LESSONS_FILE` check:

```bash
# ── Activity gate: skip validation if no meaningful work happened ──────────
TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('transcript_path',''))" 2>/dev/null || echo "")
SCANNER_SCRIPT="$PLUGIN_ROOT/scripts/transcript-scanner.py"

if [[ -n "$TRANSCRIPT_PATH" ]] && [[ -f "$SCANNER_SCRIPT" ]]; then
    SINCE_TS=0
    if [[ -f "$SESSION_LESSONS_FILE" ]]; then
        SINCE_TS=$(stat -c %Y "$SESSION_LESSONS_FILE" 2>/dev/null || echo 0)
    fi

    SCAN_RESULT=$(python3 "$SCANNER_SCRIPT" \
        --transcript "$TRANSCRIPT_PATH" \
        --since "$SINCE_TS" \
        --config "$AUTOCONTEXT_DIR/config.json" 2>/dev/null || echo '{"meaningful":true}')

    IS_MEANINGFUL=$(echo "$SCAN_RESULT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('meaningful',True))" 2>/dev/null || echo "True")

    if [[ "$IS_MEANINGFUL" == "False" ]]; then
        # Time fallback: validate anyway if session is 10+ minutes old
        NOW=$(date +%s)
        SESSION_START=$(stat -c %Y "$SESSION_LESSONS_FILE" 2>/dev/null || echo "$NOW")
        SESSION_AGE=$((NOW - SESSION_START))
        if [[ "$SESSION_AGE" -lt 600 ]]; then
            echo '{}'
            exit 0
        fi
    fi
fi
# ── End activity gate ──────────────────────────────────────────────────────
```

The rest of session-end.sh remains unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/jamditis/projects/claude-skills-journalism && bash /tmp/test-transcript-scanner.sh`
Expected: All 11 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add autocontext/hooks/session-end.sh
git commit -m "Add activity gate to session-end.sh to skip validation for research-only sessions"
```

---

### Task 3: Update README with scanner docs and activity_signals config

**Files:**
- Modify: `autocontext/README.md`

- [ ] **Step 1: Add transcript scanner section to README**

Add after the "Configuration" section (after line 107), before "Inspiration and attribution":

```markdown
## Transcript scanner

The plugin includes a shared transcript scanner utility that detects meaningful activity in Claude Code session transcripts. It powers the activity gate in `session-end.sh` and can be used by custom hooks.

**Usage from a hook script:**

```bash
RESULT=$(python3 "$PLUGIN_ROOT/scripts/transcript-scanner.py" \
    --transcript "$TRANSCRIPT_PATH" \
    --since "$LAST_HANDOFF_MTIME" \
    --config ".autocontext/config.json")

# Returns JSON:
# {"meaningful": true, "level": "high", "signals": [...], "tool_counts": {...}}
```

**Arguments:**
- `--transcript` — path to the session JSONL file
- `--since` — Unix timestamp (seconds). Only scan entries after this time. Default: 0 (scan all).
- `--config` — path to config file. Reads `activity_signals` key if present.

**Signal levels:**

| Level | Triggers |
|-------|----------|
| High | Write, Edit, Bash with `git commit` / `gh pr create` / `firebase deploy` / `systemctl restart` |
| Medium | Agent, Bash with `git push` / `npm run build` / `cargo build` |
| Low | Read, Grep, Glob, unmatched Bash (does not trigger `meaningful: true`) |
```

- [ ] **Step 2: Add activity_signals to the config table**

Add a new row to the `config.json` table in the Configuration section (after the `builtin_rules` row):

```markdown
| `activity_signals` | (see below) | Override which tools/patterns count as meaningful activity (see Transcript scanner section) |
```

- [ ] **Step 3: Commit**

```bash
git add autocontext/README.md
git commit -m "Document transcript scanner utility and activity_signals config"
```

---

### Task 4: Clean up test file and verify full integration

**Files:**
- No files created or modified. Verification only.

- [ ] **Step 1: Run the full test suite one final time**

Run: `cd /home/jamditis/projects/claude-skills-journalism && bash /tmp/test-transcript-scanner.sh`
Expected: All 11 tests PASS.

- [ ] **Step 2: Test scanner against the real current session transcript**

Run:
```bash
python3 autocontext/scripts/transcript-scanner.py \
    --transcript "$(ls -t ~/.claude/projects/-home-jamditis/*.jsonl | head -1)"
```

Expected: `meaningful: true` with Write/Edit signals from this session's work.

- [ ] **Step 3: Test scanner with --since filtering against real transcript**

Run:
```bash
python3 autocontext/scripts/transcript-scanner.py \
    --transcript "$(ls -t ~/.claude/projects/-home-jamditis/*.jsonl | head -1)" \
    --since 9999999999
```

Expected: `meaningful: false` — all entries are before that far-future timestamp.

- [ ] **Step 4: Clean up test script**

```bash
rm -f /tmp/test-transcript-scanner.sh
```

- [ ] **Step 5: Create branch and push for PR**

```bash
cd /home/jamditis/projects/claude-skills-journalism
git checkout -b feat/transcript-scanner
git push -u origin feat/transcript-scanner
```
