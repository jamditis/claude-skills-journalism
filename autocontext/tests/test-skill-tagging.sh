#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION_ID="test-tag-$(date +%s)"
SKILL_FILE="/tmp/claude-skills-${SESSION_ID}"
TEST_DIR="/tmp/test-skill-tagging-$$"

trap "rm -f '$SKILL_FILE'; rm -rf '$TEST_DIR'" EXIT

# Set up fake project with autocontext
mkdir -p "$TEST_DIR/.autocontext/cache"
echo '{}' > "$TEST_DIR/.autocontext/config.json"

# Pre-populate skill tracking file (simulates previous Skill tool use)
echo "web-scraping" > "$SKILL_FILE"

# Run user-prompt-submit with a correction message
cd "$TEST_DIR"
echo '{"user_message":"no, use Selenium instead of requests","session_id":"'"$SESSION_ID"'"}' | \
    bash "$SCRIPT_DIR/hooks/user-prompt-submit.sh" > /dev/null 2>&1

# Check pending-lessons.json for active_skills field
if [[ -f ".autocontext/cache/pending-lessons.json" ]]; then
    HAS_SKILLS=$(python3 -c "
import json
with open('.autocontext/cache/pending-lessons.json') as f:
    data = json.load(f)
if data and 'active_skills' in data[-1] and 'web-scraping' in data[-1]['active_skills']:
    print('yes')
else:
    print('no')
")
    if [[ "$HAS_SKILLS" == "yes" ]]; then
        echo "PASS: active_skills includes web-scraping"
    else
        echo "FAIL: active_skills missing or wrong"
        cat ".autocontext/cache/pending-lessons.json"
        exit 1
    fi
else
    echo "FAIL: pending-lessons.json not created"
    exit 1
fi

# Test: no skills active -> empty array
rm -f "$SKILL_FILE"
rm -f ".autocontext/cache/pending-lessons.json"
echo '{"user_message":"no, use Selenium instead of requests","session_id":"no-skills-session"}' | \
    bash "$SCRIPT_DIR/hooks/user-prompt-submit.sh" > /dev/null 2>&1

EMPTY_SKILLS=$(python3 -c "
import json
with open('.autocontext/cache/pending-lessons.json') as f:
    data = json.load(f)
print('yes' if data and data[-1].get('active_skills') == [] else 'no')
")
if [[ "$EMPTY_SKILLS" == "yes" ]]; then
    echo "PASS: empty active_skills when no skills tracked"
else
    echo "FAIL: active_skills not empty array"
    exit 1
fi

echo "All skill tagging tests passed"
