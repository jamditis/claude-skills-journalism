#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
AUTOCONTEXT_DIR=".autocontext"
LESSONS_FILE="$AUTOCONTEXT_DIR/lessons.json"
CACHE_DIR="$AUTOCONTEXT_DIR/cache"
SESSION_LESSONS_FILE="$CACHE_DIR/session-lessons.json"
PENDING_FILE="$CACHE_DIR/pending-lessons.json"
PLAYBOOK_FILE="$AUTOCONTEXT_DIR/playbook.md"
GENERATE_PLAYBOOK="$PLUGIN_ROOT/scripts/generate-playbook.py"

# Read stdin (ignored, no LLM calls)
INPUT=$(cat)

if [[ ! -f "$SESSION_LESSONS_FILE" ]]; then
  echo '{}'
  exit 0
fi

if [[ ! -f "$LESSONS_FILE" ]]; then
  echo '{}'
  exit 0
fi

python3 - <<'PYEOF'
import json
import sys
from datetime import datetime, timezone

session_path = ".autocontext/cache/session-lessons.json"
pending_path = ".autocontext/cache/pending-lessons.json"
lessons_path = ".autocontext/lessons.json"

# Load session lessons (the ones that were loaded at session start)
try:
    with open(session_path) as f:
        session_lessons = json.load(f)
    if not isinstance(session_lessons, list):
        session_lessons = []
except Exception as e:
    sys.stderr.write(f"[autocontext] warning: could not read session-lessons.json: {e}\n")
    session_lessons = []

if not session_lessons:
    print("{}")
    sys.exit(0)

# Load pending corrections (if any)
correction_text = ""
try:
    with open(pending_path) as f:
        pending = json.load(f)
    if isinstance(pending, list) and pending:
        correction_text = " ".join(
            p.get("user_message", "") for p in pending
        ).lower()
except Exception:
    pass

# Build set of session lesson IDs (by text) for fast lookup
session_texts = {l.get("text", "").strip() for l in session_lessons}

# Load full lessons.json to update
try:
    with open(lessons_path) as f:
        all_lessons = json.load(f)
    if not isinstance(all_lessons, list):
        raise ValueError("lessons.json must be a list")
except Exception as e:
    sys.stderr.write(f"[autocontext] warning: could not read lessons.json: {e}\n")
    sys.exit(0)

now = datetime.now(timezone.utc).isoformat()
updated_count = 0

for lesson in all_lessons:
    if lesson.get("deleted"):
        continue

    text = lesson.get("text", "").strip()
    if text not in session_texts:
        continue

    # Check if any of this lesson's tags appear in correction text
    tags = lesson.get("tags", [])
    was_contradicted = False
    if correction_text and tags:
        was_contradicted = any(
            tag.lower() in correction_text for tag in tags
        )

    if was_contradicted:
        continue

    # Bump validated_count, confidence (cap 1.0), update last_validated
    lesson["validated_count"] = lesson.get("validated_count", 0) + 1
    lesson["confidence"] = min(1.0, lesson.get("confidence", 0.5) + 0.1)
    lesson["last_validated"] = now
    updated_count += 1

# Write updated lessons.json
try:
    with open(lessons_path, "w") as f:
        json.dump(all_lessons, f, indent=2)
except Exception as e:
    sys.stderr.write(f"[autocontext] warning: could not write lessons.json: {e}\n")
    sys.exit(0)

sys.stderr.write(f"[autocontext] session end: validated {updated_count} lessons\n")
PYEOF

# Regenerate playbook (no LLM, pure file I/O)
if [[ -f "$LESSONS_FILE" ]] && [[ -f "$GENERATE_PLAYBOOK" ]]; then
  python3 "$GENERATE_PLAYBOOK" "$LESSONS_FILE" "$PLAYBOOK_FILE" 2>/dev/null || true
fi

echo '{}'
