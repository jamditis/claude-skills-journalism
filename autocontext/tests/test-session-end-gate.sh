#!/usr/bin/env bash
set -euo pipefail

AUTOCONTEXT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION_END="$AUTOCONTEXT_DIR/hooks/session-end.sh"
TEST_DIR="/tmp/test-session-end-gate-$$"

PASS=0
FAIL=0

trap "rm -rf '$TEST_DIR'" EXIT

assert_eq() {
    local label="$1"
    local expected="$2"
    local actual="$3"
    if [[ "$actual" == "$expected" ]]; then
        echo "PASS: $label"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $label (expected '$expected', got '$actual')"
        FAIL=$((FAIL + 1))
    fi
}

# Set up minimal autocontext project structure
mkdir -p "$TEST_DIR/.autocontext/cache"

# Minimal lessons.json with one lesson at confidence 0.5
cat > "$TEST_DIR/.autocontext/lessons.json" <<'JSON'
[{"id":"test-lesson-1","text":"Always write tests first.","tags":["testing"],"confidence":0.5,"validated_count":0}]
JSON

# session-lessons.json with the same lesson (so session-end has something to validate)
cat > "$TEST_DIR/.autocontext/cache/session-lessons.json" <<'JSON'
[{"id":"test-lesson-1","text":"Always write tests first.","tags":["testing"],"confidence":0.5,"validated_count":0}]
JSON

# Create a research-only transcript (only Read/Grep/Glob — not meaningful)
TRANSCRIPT="$TEST_DIR/research-only.jsonl"
cat > "$TRANSCRIPT" <<'JSONL'
{"type":"assistant","timestamp":"2026-04-03T10:00:00.000Z","message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/tmp/foo.py"}}]}}
{"type":"assistant","timestamp":"2026-04-03T10:01:00.000Z","message":{"content":[{"type":"tool_use","name":"Grep","input":{"pattern":"foo"}}]}}
{"type":"assistant","timestamp":"2026-04-03T10:02:00.000Z","message":{"content":[{"type":"tool_use","name":"Glob","input":{"pattern":"*.py"}}]}}
JSONL

# Touch session-lessons.json to be recent (< 10 min old) so time fallback doesn't fire
touch "$TEST_DIR/.autocontext/cache/session-lessons.json"

# Run session-end.sh from the test project dir
OUTPUT=$(
    cd "$TEST_DIR"
    printf '{"session_id":"gate-test-session","transcript_path":"%s"}\n' "$TRANSCRIPT" \
        | CLAUDE_PLUGIN_ROOT="$AUTOCONTEXT_DIR" bash "$SESSION_END" 2>/dev/null
)

assert_eq "session-end outputs {} for research-only + fresh session" "{}" "$OUTPUT"

# Confidence should be unchanged (session was skipped, no validation bump)
CONF_AFTER=$(python3 -c "
import json
with open('$TEST_DIR/.autocontext/lessons.json') as f:
    lessons = json.load(f)
print(lessons[0]['confidence'])
")
assert_eq "Confidence unchanged after skip" "0.5" "$CONF_AFTER"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
