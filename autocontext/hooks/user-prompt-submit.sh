#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
AUTOCONTEXT_DIR=".autocontext"
CACHE_DIR="$AUTOCONTEXT_DIR/cache"
PENDING_FILE="$CACHE_DIR/pending-lessons.json"

# Read stdin
INPUT=$(cat)

# Extract user message from JSON input
USER_MESSAGE=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    msg = data.get('user_message', data.get('message', ''))
    print(msg[:2000])
except Exception:
    print('')
" <<< "$INPUT")

if [[ -z "$USER_MESSAGE" ]]; then
  echo '{}'
  exit 0
fi

# Pattern match for correction phrases (case-insensitive)
IS_CORRECTION=$(python3 -c "
import re, sys

msg = sys.stdin.read()
patterns = [
    r'no,?\s+use\s+\S+\s+instead',
    r\"that'?s?\s+wrong\",
    r\"don'?t\s+do\s+that\",
    r'\bactually\b',
    r'remember\s+that\b',
    r'remember\s+this\b',
    r'keep\s+in\s+mind\b',
    r'the\s+correct\s+way\b',
    r'you\s+forgot\b',
    r'stop\s+doing\b',
    r'instead,?\s+use\b',
    r'instead,?\s+do\b',
    r'instead,?\s+try\b',
]
for p in patterns:
    if re.search(p, msg, re.IGNORECASE):
        print('yes')
        sys.exit(0)
print('no')
" <<< "$USER_MESSAGE")

if [[ "$IS_CORRECTION" != "yes" ]]; then
  echo '{}'
  exit 0
fi

# Ensure cache dir exists
mkdir -p "$CACHE_DIR"

# Append candidate to pending-lessons.json
TIMESTAMP=$(python3 -c "from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat())")

python3 - <<PYEOF
import json
from datetime import datetime, timezone

pending_path = "$PENDING_FILE"
user_message = """$USER_MESSAGE"""
timestamp = "$TIMESTAMP"

# Load existing pending list
try:
    with open(pending_path) as f:
        pending = json.load(f)
    if not isinstance(pending, list):
        pending = []
except Exception:
    pending = []

# Append new candidate
pending.append({
    "user_message": user_message[:2000],
    "timestamp": timestamp,
})

with open(pending_path, "w") as f:
    json.dump(pending, f, indent=2)
PYEOF

echo '{}'
