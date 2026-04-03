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

# Read stdin — extract session_id for skill tracking cleanup
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")

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

# Build set of session lesson IDs for fast lookup (match by id, not text)
session_ids = {l.get("id") for l in session_lessons if l.get("id")}

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

    if lesson.get("id") not in session_ids:
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

# Regenerate playbook (respect playbook_generation setting, no LLM, pure file I/O)
PLAYBOOK_MODE=$(python3 -c "
import json
try:
    with open('.autocontext/config.json') as f:
        cfg = json.load(f)
    print(cfg.get('playbook_generation', 'auto'))
except Exception:
    print('auto')
")
if [[ "$PLAYBOOK_MODE" == "auto" ]] && [[ -f "$LESSONS_FILE" ]] && [[ -f "$GENERATE_PLAYBOOK" ]]; then
  python3 "$GENERATE_PLAYBOOK" "$LESSONS_FILE" "$PLAYBOOK_FILE" 2>/dev/null || true
fi

# Clean up skill tracking temp file
if [[ -n "$SESSION_ID" ]]; then
    rm -f "/tmp/claude-skills-${SESSION_ID}"
fi

echo '{}'
