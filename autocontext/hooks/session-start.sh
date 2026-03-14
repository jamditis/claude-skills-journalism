#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$0")")}"
AUTOCONTEXT_DIR=".autocontext"
LESSONS_FILE="$AUTOCONTEXT_DIR/lessons.json"
CONFIG_FILE="$AUTOCONTEXT_DIR/config.json"
CACHE_DIR="$AUTOCONTEXT_DIR/cache"
PENDING_FILE="$CACHE_DIR/pending-lessons.json"
SESSION_LESSONS_FILE="$CACHE_DIR/session-lessons.json"
CURATED_PENDING_FILE="$CACHE_DIR/curated-pending.json"
PLAYBOOK_FILE="$AUTOCONTEXT_DIR/playbook.md"
GENERATE_PLAYBOOK="$PLUGIN_ROOT/scripts/generate-playbook.py"

# Read stdin (may contain cwd, but we rely on shell cwd)
INPUT=$(cat)

# Ensure cache dir exists
mkdir -p "$CACHE_DIR"

# ── Phase 1: Curate pending lessons from previous session ─────────────────────

if [[ -f "$PENDING_FILE" ]]; then
  PENDING_COUNT=$(python3 - <<'PYEOF'
import json, sys
try:
    with open(".autocontext/cache/pending-lessons.json") as f:
        data = json.load(f)
    print(len(data) if isinstance(data, list) else 0)
except Exception:
    print(0)
PYEOF
)

  if [[ "$PENDING_COUNT" -gt 0 ]]; then
    # Build curator prompt
    PENDING_JSON=$(cat "$PENDING_FILE")
    CURATOR_PROMPT="You are curating lessons for a project knowledge base. Below are candidate lessons extracted from user corrections during a previous session. For each candidate, decide if it contains a clear, actionable, project-specific lesson worth persisting.

NEVER include secrets, API keys, tokens, passwords, or PII in lesson text. Describe patterns without actual credential values.

Output a JSON array of lesson objects to keep. Each object must have:
- text (string): concise lesson statement
- category (string): one of: efficiency, codebase, optimization
- tags (array of strings): relevant file paths, tools, or concepts
- confidence (number): 0.6 to 0.8 for new lessons

If a candidate includes an 'active_skills' field with skill names, also include:
- skill (string or null): the skill name most relevant to this lesson (pick one if multiple), or null if no skills were active
- scope (string): 'project' if the lesson is specific to this codebase, 'skill' if it would help anyone using this skill

Candidates:
$PENDING_JSON

Respond with ONLY the JSON array, no explanation."

    CURATED=$(echo "$CURATOR_PROMPT" | timeout --foreground 45 claude -p 2>/dev/null || echo "[]")

    # Validate curated output is a JSON array
    IS_VALID=$(echo "$CURATED" | python3 - <<'PYEOF'
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print("yes" if isinstance(data, list) else "no")
except Exception:
    print("no")
PYEOF
)

    if [[ "$IS_VALID" == "yes" ]]; then
      # Check persistence_mode
      PERSISTENCE_MODE=$(python3 - <<'PYEOF'
import json
try:
    with open(".autocontext/config.json") as f:
        cfg = json.load(f)
    print(cfg.get("persistence_mode", "auto_curated"))
except Exception:
    print("auto_curated")
PYEOF
)

      if [[ "$PERSISTENCE_MODE" == "ask_before_persist" ]]; then
        echo "$CURATED" > "$CURATED_PENDING_FILE"
      else
        # Merge curated lessons into lessons.json (skip duplicates by text)
        EXISTING_LESSONS="[]"
        if [[ -f "$LESSONS_FILE" ]]; then
          EXISTING_LESSONS=$(cat "$LESSONS_FILE")
        fi

        CURATED_JSON="$CURATED" EXISTING_JSON="$EXISTING_LESSONS" python3 - <<'PYEOF'
import json, os, uuid
from datetime import datetime, timezone

curated_raw = os.environ.get("CURATED_JSON", "[]")
existing_raw = os.environ.get("EXISTING_JSON", "[]")

try:
    curated = json.loads(curated_raw)
except Exception:
    curated = []

try:
    existing = json.loads(existing_raw)
except Exception:
    existing = []

existing_texts = {l.get("text", "").strip().lower() for l in existing}
now = datetime.now(timezone.utc).isoformat()

import sys
added = 0
for lesson in curated:
    text = lesson.get("text", "").strip()
    if text.lower() not in existing_texts:
        lesson.setdefault("id", "lesson_" + uuid.uuid4().hex[:8])
        lesson.setdefault("schema_version", 1)
        lesson.setdefault("confidence", 0.7)
        lesson.setdefault("created", now)
        lesson.setdefault("last_validated", now)
        lesson.setdefault("validated_count", 0)
        lesson.setdefault("deleted", False)
        lesson.setdefault("tags", [])
        lesson.setdefault("category", "workflow")
        lesson.setdefault("context", "")
        lesson.setdefault("created_by", "curator")
        lesson.setdefault("supersedes", None)
        lesson.setdefault("skill", None)
        lesson.setdefault("scope", "project")
        existing.append(lesson)
        existing_texts.add(text.lower())
        added += 1

with open(".autocontext/lessons.json", "w") as f:
    json.dump(existing, f, indent=2)

sys.stderr.write(f"[autocontext] merged {added} new lessons\n")
PYEOF

        # Regenerate playbook (respect playbook_generation setting)
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
      fi
    fi

    # Delete pending-lessons.json regardless
    rm -f "$PENDING_FILE"
  fi
fi

# ── Phase 2 + 3: Decay confidence, load and cache lessons ────────────────────

if [[ ! -f "$LESSONS_FILE" ]]; then
  echo '{}'
  exit 0
fi

python3 - <<'PYEOF'
import json
import sys
import subprocess
import socket
import os
from datetime import datetime, timezone

lessons_path = ".autocontext/lessons.json"
config_path = ".autocontext/config.json"
cache_path = ".autocontext/cache/session-lessons.json"
gitattributes_path = ".gitattributes"

# Load config
try:
    with open(config_path) as f:
        config = json.load(f)
except Exception as e:
    sys.stderr.write(f"[autocontext] warning: could not read config.json: {e}\n")
    config = {}

# Load lessons
try:
    with open(lessons_path) as f:
        lessons = json.load(f)
    if not isinstance(lessons, list):
        raise ValueError("lessons.json must be a JSON array")
except json.JSONDecodeError as e:
    sys.stderr.write(f"[autocontext] warning: malformed lessons.json, skipping: {e}\n")
    print("{}")
    sys.exit(0)
except Exception as e:
    sys.stderr.write(f"[autocontext] warning: could not read lessons.json: {e}\n")
    print("{}")
    sys.exit(0)

# Phase 2: Apply confidence decay on stale lessons
now = datetime.now(timezone.utc)
staleness_days = config.get("staleness_days", 60)
for l in lessons:
    if l.get("deleted"):
        continue
    last_val = l.get("last_validated", l.get("created", ""))
    if not last_val:
        continue
    try:
        last_dt = datetime.fromisoformat(last_val.replace("Z", "+00:00"))
        days_stale = (now - last_dt).days
        if days_stale > staleness_days:
            decay_periods = (days_stale - staleness_days) // 30
            l["confidence"] = max(0.0, l.get("confidence", 0.5) - (0.1 * decay_periods))
    except Exception:
        pass

# Save decayed lessons back
try:
    with open(lessons_path, "w") as f:
        json.dump(lessons, f, indent=2)
except Exception as e:
    sys.stderr.write(f"[autocontext] warning: could not write decayed lessons: {e}\n")

# Phase 3: Filter lessons
threshold = config.get("confidence_threshold", 0.3)
max_lessons = config.get("max_session_lessons", 15)
hostname = socket.gethostname()

def machine_matches(lesson):
    tags = lesson.get("tags", [])
    machine_tags = [t for t in tags if t.startswith("machine:")]
    if not machine_tags:
        return True
    return f"machine:{hostname}" in machine_tags

filtered = [
    l for l in lessons
    if not l.get("deleted", False)
    and l.get("confidence", 0) >= threshold
    and machine_matches(l)
]

# Rank by relevance: match tags against recent changed files
changed_files = []
for cmd in [
    ["git", "diff", "--name-only", "HEAD~5..HEAD"],
    ["git", "diff", "--name-only", "HEAD~1..HEAD"],
    ["git", "diff", "--name-only"],
]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            changed_files = result.stdout.strip().splitlines()
            break
    except Exception:
        continue

changed_set = set(changed_files)

def relevance_score(lesson):
    tags = lesson.get("tags", [])
    matches = sum(1 for t in tags if any(t in f or f in t for f in changed_set))
    return (matches, lesson.get("confidence", 0))

filtered.sort(key=relevance_score, reverse=True)
top_lessons = filtered[:max_lessons]

# Write session cache
try:
    with open(cache_path, "w") as f:
        json.dump(top_lessons, f, indent=2)
except Exception as e:
    sys.stderr.write(f"[autocontext] warning: could not write session cache: {e}\n")

# Check merge driver configured
merge_driver_ok = False
if os.path.exists(gitattributes_path):
    try:
        with open(gitattributes_path) as f:
            content = f.read()
        merge_driver_ok = "autocontext-union" in content or "lessons.json" in content
    except Exception:
        pass

if not merge_driver_ok:
    sys.stderr.write("[autocontext] warning: merge driver not configured. Run: git config merge.autocontext-union.driver '...'\n")

# Build hookResponse message
count = len(top_lessons)
if count == 0:
    msg = "No lessons loaded for this session."
else:
    categories = {}
    for l in top_lessons:
        cat = l.get("category", "uncategorized")
        categories[cat] = categories.get(cat, 0) + 1
    cat_summary = ", ".join(f"{v} {k}" for k, v in sorted(categories.items()))
    msg = f"Loaded {count} lessons ({cat_summary}). Playbook: .autocontext/playbook.md"

print(json.dumps({"hookResponse": {"message": msg}}))
PYEOF
