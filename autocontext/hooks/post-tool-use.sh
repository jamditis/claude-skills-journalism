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

    local file=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') if isinstance(d.get('tool_input'),dict) else '')" 2>/dev/null || echo "")

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
    local test_methods=$(echo "$content" | grep -oE 'def (test_[a-zA-Z_0-9]+|it\(['\''"][^'\''\"]*' | sed "s/def test_\|it('//" | sed "s/['\''\"]//" | grep -v '^$')

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

# Check performance baseline
check_performance_baseline() {
    local cmd="$1"
    local output="$2"
    local config_file="$CWD/.autocontext/config.json"

    if [[ ! -f "$config_file" ]]; then
        return 1
    fi

    # Check if config has performance_baselines enabled
    local perf_enabled=$(python3 -c "import json; c=json.load(open('$config_file')); print(c.get('performance_baselines', False))" 2>/dev/null || echo "false")

    if [[ "$perf_enabled" != "True" ]]; then
        return 1
    fi

    # Check if command matches a baseline command
    local baseline_commands=$(python3 -c "import json; c=json.load(open('$config_file')); print(' '.join(c.get('baseline_commands', [])))" 2>/dev/null || echo "")

    local matched=0
    for baseline_cmd in $baseline_commands; do
        if [[ "$cmd" == *"$baseline_cmd"* ]]; then
            matched=1
            break
        fi
    done

    if [[ $matched -eq 0 ]]; then
        return 1
    fi

    # Extract timing from output (look for seconds)
    local timing=$(echo "$output" | grep -oE '[0-9]+\.[0-9]+s' | head -1 | sed 's/s$//')

    if [[ -z "$timing" ]]; then
        return 1
    fi

    # Compare against baseline
    local baseline=$(python3 -c "import json; c=json.load(open('$config_file')); b=c.get('baselines',{}); print(b.get('$cmd', 0))" 2>/dev/null || echo "0")

    if [[ -z "$baseline" || "$baseline" == "0" ]]; then
        # First time, store baseline
        python3 << EOF
import json
with open('$config_file', 'r') as f:
    config = json.load(f)
if 'baselines' not in config:
    config['baselines'] = {}
config['baselines']['$cmd'] = $timing
with open('$config_file', 'w') as f:
    json.dump(config, f, indent=2)
EOF
        return 1
    fi

    # Check for regression
    local threshold=$(python3 -c "print($baseline * 1.1)")

    if (( $(echo "$timing > $threshold" | bc -l) )); then
        echo "perf_baseline: command '$cmd' took ${timing}s (${threshold}s baseline, 10% regression)"
        return 0
    fi

    return 1
}

# Main
warnings=()

if is_test_file_edit "$TOOL_NAME" "$INPUT"; then
    local file=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path','') if isinstance(d.get('tool_input'),dict) else '')" 2>/dev/null || echo "")
    local result=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_result',''))" 2>/dev/null || echo "")

    if [[ -n "$file" && -n "$result" ]]; then
        local test_warnings=$(check_test_quality "$file" "$result" || true)
        if [[ -n "$test_warnings" ]]; then
            warnings+=("$test_warnings")
        fi
    fi
fi

# Check performance baseline for Bash commands
if [[ "$TOOL_NAME" == "Bash" ]]; then
    local cmd=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command','') if isinstance(d.get('tool_input'),dict) else '')" 2>/dev/null || echo "")
    local output=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_result',''))" 2>/dev/null || echo "")

    if [[ -n "$cmd" && -n "$output" ]]; then
        local perf_warning=$(check_performance_baseline "$cmd" "$output" || true)
        if [[ -n "$perf_warning" ]]; then
            warnings+=("$perf_warning")
        fi
    fi
fi

# Cap at 3 warnings
if [[ ${#warnings[@]} -gt 3 ]]; then
    warnings=("${warnings[@]:0:3}")
fi

# Output response
if [[ ${#warnings[@]} -gt 0 ]]; then
    python3 << EOF
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
EOF
else
    echo "{}"
fi
