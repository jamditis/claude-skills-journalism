#!/usr/bin/env bash
set -euo pipefail

# Test: post-tool-use.sh writes skill name to /tmp/claude-skills-{session_id}
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SESSION_ID="test-session-$(date +%s)"
SKILL_FILE="/tmp/claude-skills-${SESSION_ID}"

# Clean up
trap "rm -f '$SKILL_FILE'" EXIT

# Simulate Skill tool PostToolUse event
echo '{"tool_name":"Skill","tool_input":{"skill":"web-scraping"},"session_id":"'"$SESSION_ID"'","cwd":"/tmp"}' | \
    bash "$SCRIPT_DIR/hooks/post-tool-use.sh" > /dev/null 2>&1

# Verify
if [[ -f "$SKILL_FILE" ]] && grep -qxF "web-scraping" "$SKILL_FILE"; then
    echo "PASS: skill name written to $SKILL_FILE"
else
    echo "FAIL: skill name not found in $SKILL_FILE"
    exit 1
fi

# Test dedup: same skill shouldn't be written twice
echo '{"tool_name":"Skill","tool_input":{"skill":"web-scraping"},"session_id":"'"$SESSION_ID"'","cwd":"/tmp"}' | \
    bash "$SCRIPT_DIR/hooks/post-tool-use.sh" > /dev/null 2>&1

COUNT=$(wc -l < "$SKILL_FILE")
if [[ "$COUNT" -eq 1 ]]; then
    echo "PASS: dedup works (1 line after 2 invocations)"
else
    echo "FAIL: dedup broken ($COUNT lines)"
    exit 1
fi

# Test: non-Skill tool should not create the file
rm -f "$SKILL_FILE"
echo '{"tool_name":"Edit","tool_input":{"file_path":"/tmp/foo.py"},"session_id":"'"$SESSION_ID"'","cwd":"/tmp"}' | \
    bash "$SCRIPT_DIR/hooks/post-tool-use.sh" > /dev/null 2>&1

if [[ ! -f "$SKILL_FILE" ]]; then
    echo "PASS: Edit tool did not create skill file"
else
    echo "FAIL: Edit tool created skill file"
    exit 1
fi

echo "All skill tracking tests passed"
