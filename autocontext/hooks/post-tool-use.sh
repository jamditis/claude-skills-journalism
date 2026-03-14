#!/usr/bin/env bash
set -euo pipefail

# Post-tool-use hook for autocontext plugin
# Responsibilities:
# 1. Deterministic test quality checks (on Edit/Write of test files)
# 2. Performance baselines (on Bash matching test/build commands)

INPUT=$(cat)
CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd','.'))")
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))")

# Determine if this is a test file write/edit
is_test_file_edit() {
    local tool="$1"
    local input="$2"

    if [[ "$tool" != "Edit" && "$tool" != "Write" ]]; then
        return 1
    fi

    local file
    file=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') if isinstance(d.get('tool_input'),dict) else '')" 2>/dev/null || echo "")

    if [[ -z "$file" ]]; then
        return 1
    fi

    # Check if it's a test file
    if [[ "$file" =~ /tests/ || "$file" =~ /__tests__/ || "$file" =~ _test\.py$ || "$file" =~ \.test\.ts$ || "$file" =~ \.test\.js$ || "$file" =~ \.spec\.ts$ || "$file" =~ \.spec\.js$ || "$file" =~ ^test_ ]]; then
        return 0
    fi

    return 1
}

# Check test file for quality issues
check_test_quality() {
    local file="$1"
    local content="$2"

    local warnings=()

    # Check: no_assert_true
    if echo "$content" | grep -qE '(assert True|assert result is not None|assert len\(result\) > 0|self\.assertTrue\(True\))'; then
        warnings+=("no_assert_true: found tautological assertion (assert True, assert is not None, etc)")
    fi

    # Check: no_happy_path_only
    # Extract all test method names
    local test_methods
    test_methods=$(echo "$content" | grep -oE 'def (test_[a-zA-Z_0-9]+|it\(['\''"][^'\''\"]*' | sed "s/def test_\|it('//" | sed "s/['\''\"]//" | grep -v '^$')

    if [[ -n "$test_methods" ]]; then
        local happy_count=0
        local error_count=0
        local total=0

        while IFS= read -r method; do
            ((total++))
            if [[ "$method" =~ (success|valid|happy|can_|should_) ]]; then
                ((happy_count++))
            fi
            if [[ "$method" =~ (error|fail|invalid|edge|missing|empty|bad|reject) ]]; then
                ((error_count++))
            fi
        done <<< "$test_methods"

        # If all tests are happy path and none test errors
        if [[ $total -gt 0 && $happy_count -eq $total && $error_count -eq 0 ]]; then
            warnings+=("no_happy_path_only: all test names match happy-path patterns, no error/edge case tests found")
        fi
    fi

    if [[ ${#warnings[@]} -gt 0 ]]; then
        printf '%s\n' "${warnings[@]}"
        return 0
    fi

    return 1
}

# Check performance baseline — all matching, timing, and comparison done in Python
check_performance_baseline() {
    local input="$1"
    local config_file="$CWD/.autocontext/config.json"

    if [[ ! -f "$config_file" ]]; then
        return 1
    fi

    export AUTOCONTEXT_CONFIG_FILE="$config_file"
    echo "$input" | python3 - <<'PYEOF'
import json
import os
import sys

config_file = os.environ.get("AUTOCONTEXT_CONFIG_FILE", "")

try:
    with open(config_file) as f:
        config = json.load(f)
except Exception:
    sys.exit(0)

if not config.get("performance_baselines", False):
    sys.exit(0)

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input", {})
if not isinstance(tool_input, dict):
    sys.exit(0)

cmd = tool_input.get("command", "")
output = data.get("tool_result", "")

if not cmd or not output:
    sys.exit(0)

baseline_commands = config.get("baseline_commands", [])

# Match cmd against each baseline command (exact substring, no shell word-splitting)
matched_baseline_cmd = None
for baseline_cmd in baseline_commands:
    if baseline_cmd in cmd:
        matched_baseline_cmd = baseline_cmd
        break

if matched_baseline_cmd is None:
    sys.exit(0)

# Extract timing from output
import re
m = re.search(r'([0-9]+\.[0-9]+)s', output)
if not m:
    sys.exit(0)

timing = float(m.group(1))

baselines = config.get("baselines", {})
baseline_val = baselines.get(cmd, None)

if baseline_val is None or baseline_val == 0:
    # First time: store baseline
    if "baselines" not in config:
        config["baselines"] = {}
    config["baselines"][cmd] = timing
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass
    sys.exit(0)

threshold = float(baseline_val) * 1.1

if timing > threshold:
    print(f"perf_baseline: command '{cmd}' took {timing}s ({threshold:.4f}s baseline, 10% regression)")
PYEOF
}

# Main
warnings=()

if is_test_file_edit "$TOOL_NAME" "$INPUT"; then
    file=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') if isinstance(d.get('tool_input'),dict) else '')" 2>/dev/null || echo "")
    result=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_result',''))" 2>/dev/null || echo "")

    if [[ -n "$file" && -n "$result" ]]; then
        test_warnings=$(check_test_quality "$file" "$result" || true)
        if [[ -n "$test_warnings" ]]; then
            warnings+=("$test_warnings")
        fi
    fi
fi

# Check performance baseline for Bash commands
if [[ "$TOOL_NAME" == "Bash" ]]; then
    perf_warning=$(check_performance_baseline "$INPUT" || true)
    if [[ -n "$perf_warning" ]]; then
        warnings+=("$perf_warning")
    fi
fi

# Cap at 3 warnings
if [[ ${#warnings[@]} -gt 3 ]]; then
    warnings=("${warnings[@]:0:3}")
fi

# Output response
if [[ ${#warnings[@]} -gt 0 ]]; then
    python3 - <<PYEOF
import json
warnings = [
    $(printf '%s\n' "${warnings[@]}" | sed 's/.*/"&"/' | paste -sd, -)
]
response = {
    "hookResponse": {
        "message": "Quality check warnings:\n" + "\n".join("- " + w for w in warnings)
    }
}
print(json.dumps(response))
PYEOF
else
    echo "{}"
fi
