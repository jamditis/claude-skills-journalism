#!/usr/bin/env bash
set -euo pipefail

SCANNER="$(cd "$(dirname "$0")/.." && pwd)/scripts/transcript-scanner.py"
TMPDIR_BASE="/tmp/test-transcript-scanner-$$"
mkdir -p "$TMPDIR_BASE"
trap "rm -rf '$TMPDIR_BASE'" EXIT

PASS=0
FAIL=0

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

# Helper: build a minimal JSONL entry
make_entry() {
    local tool_name="$1"
    local input_json="$2"
    local ts="${3:-}"
    if [[ -n "$ts" ]]; then
        printf '{"type":"assistant","timestamp":"%s","message":{"content":[{"type":"tool_use","name":"%s","input":%s}]}}\n' \
            "$ts" "$tool_name" "$input_json"
    else
        printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"%s","input":%s}]}}\n' \
            "$tool_name" "$input_json"
    fi
}

# ── Test 1: Write/Edit = high ─────────────────────────────────────────────────
T="$TMPDIR_BASE/t1.jsonl"
make_entry "Write" '{"file_path":"/tmp/foo.py"}' > "$T"
result=$(python3 "$SCANNER" --transcript "$T")
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
level=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
assert_eq "Write is meaningful" "True" "$meaningful"
assert_eq "Write level is high" "high" "$level"

# ── Test 2: Read/Grep/Glob only = not meaningful ──────────────────────────────
T="$TMPDIR_BASE/t2.jsonl"
make_entry "Read" '{"file_path":"/tmp/foo.py"}' > "$T"
make_entry "Grep" '{"pattern":"foo"}' >> "$T"
make_entry "Glob" '{"pattern":"*.py"}' >> "$T"
result=$(python3 "$SCANNER" --transcript "$T")
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "Read/Grep/Glob only = not meaningful" "False" "$meaningful"

# ── Test 3: git commit Bash = high ────────────────────────────────────────────
T="$TMPDIR_BASE/t3.jsonl"
make_entry "Bash" '{"command":"git commit -m \"fix thing\""}' > "$T"
result=$(python3 "$SCANNER" --transcript "$T")
level=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
assert_eq "git commit Bash = high" "high" "$level"

# ── Test 4: Agent = medium ────────────────────────────────────────────────────
T="$TMPDIR_BASE/t4.jsonl"
make_entry "Agent" '{"description":"do some research"}' > "$T"
result=$(python3 "$SCANNER" --transcript "$T")
level=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
assert_eq "Agent = medium" "medium" "$level"

# ── Test 5: --since filters old entries ──────────────────────────────────────
T="$TMPDIR_BASE/t5.jsonl"
# Timestamp in milliseconds (old: 2020-01-01)
make_entry "Write" '{"file_path":"/tmp/old.py"}' "2020-01-01T00:00:00.000Z" > "$T"
result=$(python3 "$SCANNER" --transcript "$T" --since 9999999999)
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "--since filters old entries" "False" "$meaningful"

# ── Test 6: Missing file = not meaningful ────────────────────────────────────
result=$(python3 "$SCANNER" --transcript "/tmp/this-file-does-not-exist-$$")
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "Missing file = not meaningful" "False" "$meaningful"

# ── Test 7: No args = not meaningful ─────────────────────────────────────────
result=$(python3 "$SCANNER")
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "No args = not meaningful" "False" "$meaningful"

# ── Test 8: Custom config overrides ──────────────────────────────────────────
T="$TMPDIR_BASE/t8.jsonl"
CFG="$TMPDIR_BASE/config8.json"
# Mark "Read" as a high tool via config
printf '{"activity_signals":{"high_tool_names":["Read"]}}\n' > "$CFG"
make_entry "Read" '{"file_path":"/tmp/foo.py"}' > "$T"
result=$(python3 "$SCANNER" --transcript "$T" --config "$CFG")
level=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['level'])")
assert_eq "Custom config overrides high_tool_names" "high" "$level"

# ── Test 9: Non-dict activity_signals in config is handled safely ─────────────
T="$TMPDIR_BASE/t9.jsonl"
CFG="$TMPDIR_BASE/config9.json"
printf '{"activity_signals":null}\n' > "$CFG"
make_entry "Write" '{"file_path":"/tmp/foo.py"}' > "$T"
result=$(python3 "$SCANNER" --transcript "$T" --config "$CFG" 2>&1)
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "null activity_signals handled safely" "True" "$meaningful"

# ── Test 10: ISO 8601 timestamps ─────────────────────────────────────────────
T="$TMPDIR_BASE/t10.jsonl"
# Recent ISO 8601 timestamp
make_entry "Write" '{"file_path":"/tmp/iso.py"}' "2026-04-03T16:17:28.078Z" > "$T"
result=$(python3 "$SCANNER" --transcript "$T" --since 1000000000)
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
ts=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['signals'][0]['ts'] if d['signals'] else 0)")
assert_eq "ISO 8601 entry is meaningful" "True" "$meaningful"
# ts should be a positive float, not null/0
if python3 -c "import sys; sys.exit(0 if float('$ts') > 0 else 1)"; then
    echo "PASS: ISO 8601 ts resolved to positive float ($ts)"
    PASS=$((PASS + 1))
else
    echo "FAIL: ISO 8601 ts not resolved ($ts)"
    FAIL=$((FAIL + 1))
fi

# ── Test 11: Entries without timestamp included when --since set ──────────────
T="$TMPDIR_BASE/t11.jsonl"
# Entry with no timestamp field at all
printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Write","input":{"file_path":"/tmp/notimestamp.py"}}]}}\n' > "$T"
result=$(python3 "$SCANNER" --transcript "$T" --since 9999999999)
meaningful=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin)['meaningful'])")
assert_eq "No-timestamp entry included even with --since" "True" "$meaningful"

# ── ts fallback = 0 when timestamp missing ────────────────────────────────────
ts=$(echo "$result" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['signals'][0]['ts'] if d['signals'] else 'missing')")
assert_eq "Missing timestamp signal ts = 0" "0" "$ts"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "Results: $PASS passed, $FAIL failed"
if [[ "$FAIL" -gt 0 ]]; then
    exit 1
fi
