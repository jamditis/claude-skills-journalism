#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION_ID="test-cleanup-$(date +%s)"
SKILL_FILE="/tmp/claude-skills-${SESSION_ID}"
TEST_DIR="/tmp/test-session-end-$$"

trap "rm -f '$SKILL_FILE'; rm -rf '$TEST_DIR'" EXIT

# Set up minimal autocontext project
mkdir -p "$TEST_DIR/.autocontext/cache"
echo '[]' > "$TEST_DIR/.autocontext/lessons.json"
echo '[]' > "$TEST_DIR/.autocontext/cache/session-lessons.json"

# Create skill tracking file
echo "web-scraping" > "$SKILL_FILE"

cd "$TEST_DIR"
echo '{"session_id":"'"$SESSION_ID"'"}' | \
    bash "$SCRIPT_DIR/hooks/session-end.sh" > /dev/null 2>&1

if [[ ! -f "$SKILL_FILE" ]]; then
    echo "PASS: skill tracking file cleaned up"
else
    echo "FAIL: skill tracking file still exists"
    exit 1
fi

echo "All session-end cleanup tests passed"
