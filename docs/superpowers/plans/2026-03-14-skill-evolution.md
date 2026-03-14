# Skill evolution implementation plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make skills self-improving by extending autocontext to tag lessons with active skill names, store them globally, and fold validated lessons back into skill files via `/autocontext-evolve`.

**Architecture:** Extend existing autocontext hooks with skill-awareness (post-tool-use.sh tracks skills, user-prompt-submit.sh tags corrections). Global store at `~/.claude/skill-lessons/`. New `/autocontext-evolve` command uses `claude -p` to rewrite skill files, with diff review and rollback.

**Tech Stack:** Bash hooks, Python scripts, JSON data stores, `claude -p` subprocess for evolution prompts.

**Spec:** `docs/superpowers/specs/2026-03-14-skill-evolution-design.md`

**Plugin root:** All paths relative to `autocontext/` within the plugin directory at `~/.claude/plugins/marketplaces/claude-skills-journalism/autocontext/`

---

## Chunk 1: Foundation — config utils and skill tracking

### Task 1: Create shared config resolution helper

**Files:**
- Create: `scripts/config-utils.sh`

- [ ] **Step 1: Write config-utils.sh**

```bash
#!/usr/bin/env bash
# Shared config resolution: project .autocontext/config.json -> global ~/.claude/autocontext.json -> default
# Usage: source this file, then call read_config "key.path" "default_value"

read_config() {
    local key="$1"
    local default="$2"
    python3 -c "
import json, os
key_parts = '${key}'.split('.')
for path in ['.autocontext/config.json', os.path.expanduser('~/.claude/autocontext.json')]:
    try:
        with open(path) as f:
            cfg = json.load(f)
        val = cfg
        for k in key_parts:
            val = val[k]
        if isinstance(val, bool):
            print(str(val).lower())
        elif isinstance(val, list):
            import json as j
            print(j.dumps(val))
        else:
            print(val)
        exit(0)
    except Exception:
        continue
print('${default}')
"
}
```

- [ ] **Step 2: Make it executable**

Run: `chmod +x scripts/config-utils.sh`

- [ ] **Step 3: Test config resolution manually**

Create a temp config and verify fallback:

```bash
cd /tmp && mkdir -p .autocontext
echo '{"skill_learning": {"enabled": true}}' > .autocontext/config.json
source /path/to/scripts/config-utils.sh
result=$(read_config "skill_learning.enabled" "false")
echo "$result"  # Should print: true
rm -rf .autocontext
```

Expected: `true`

- [ ] **Step 4: Commit**

```bash
git add scripts/config-utils.sh
git commit -m "feat(skill-evolution): add shared config resolution helper"
```

### Task 2: Add skill tracking to post-tool-use.sh

**Files:**
- Modify: `hooks/post-tool-use.sh:11-12` (add after TOOL_NAME extraction)

- [ ] **Step 1: Write a test script for skill tracking**

Create `tests/test-skill-tracking.sh`:

```bash
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash tests/test-skill-tracking.sh`
Expected: FAIL (skill tracking not implemented yet)

- [ ] **Step 3: Add skill tracking branch to post-tool-use.sh**

Insert after line 11 (`TOOL_NAME=...`) and before line 13 (`# Determine if this is a test file write/edit`):

```bash
# Track active skills for skill-aware lesson tagging
if [[ "$TOOL_NAME" == "Skill" ]]; then
    SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")
    SKILL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('skill',''))" 2>/dev/null || echo "")
    if [[ -n "$SESSION_ID" && -n "$SKILL_NAME" ]]; then
        SKILL_FILE="/tmp/claude-skills-${SESSION_ID}"
        grep -qxF "$SKILL_NAME" "$SKILL_FILE" 2>/dev/null || echo "$SKILL_NAME" >> "$SKILL_FILE"
    fi
fi
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `bash tests/test-skill-tracking.sh`
Expected: All 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add hooks/post-tool-use.sh tests/test-skill-tracking.sh
git commit -m "feat(skill-evolution): track active skills in post-tool-use.sh"
```

### Task 3: Add skill tagging to user-prompt-submit.sh

**Files:**
- Modify: `hooks/user-prompt-submit.sh:9-21` (add session_id extraction), `:94-123` (add active_skills to pending lesson)

- [ ] **Step 1: Write test for skill-tagged corrections**

Create `tests/test-skill-tagging.sh`:

```bash
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `bash tests/test-skill-tagging.sh`
Expected: FAIL

- [ ] **Step 3: Modify user-prompt-submit.sh**

After line 10 (`INPUT=$(cat)`), add session_id extraction:

```bash
# Extract session_id for skill tracking
SESSION_ID=$(python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    print(data.get('session_id', ''))
except Exception:
    print('')
" <<< "$INPUT")
```

In the pending lesson append block (line 116, inside the `pending.append({` dict), add active_skills:

```python
# Read active skills from /tmp/claude-skills-{session_id}
active_skills = []
session_id = os.environ.get("AUTOCONTEXT_SESSION_ID", "")
if session_id:
    skill_file = f"/tmp/claude-skills-{session_id}"
    try:
        with open(skill_file) as f:
            active_skills = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pass

# Append new candidate
pending.append({
    "user_message": user_message[:2000],
    "timestamp": timestamp,
    "active_skills": active_skills,
    "session_id": session_id,
})
```

Also add `AUTOCONTEXT_SESSION_ID="$SESSION_ID"` to the environment variables passed to the Python block (alongside AUTOCONTEXT_PENDING_FILE, etc.).

- [ ] **Step 4: Run the test to verify it passes**

Run: `bash tests/test-skill-tagging.sh`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add hooks/user-prompt-submit.sh tests/test-skill-tagging.sh
git commit -m "feat(skill-evolution): tag corrections with active skill names"
```

### Task 4: Add session_id parsing and cleanup to session-end.sh

**Files:**
- Modify: `hooks/session-end.sh:13-14` (parse session_id), `:126` (add cleanup before final echo)

- [ ] **Step 1: Write test for session-end cleanup**

Create `tests/test-session-end-cleanup.sh`:

```bash
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash tests/test-session-end-cleanup.sh`
Expected: FAIL (cleanup not implemented)

- [ ] **Step 3: Modify session-end.sh**

Replace line 13-14:
```bash
# Read stdin (ignored, no LLM calls)
INPUT=$(cat)
```

With:
```bash
# Read stdin — extract session_id for skill tracking cleanup
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null || echo "")
```

Before the final `echo '{}'` (line 126), add:
```bash
# Clean up skill tracking temp file
if [[ -n "$SESSION_ID" ]]; then
    rm -f "/tmp/claude-skills-${SESSION_ID}"
fi
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash tests/test-session-end-cleanup.sh`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add hooks/session-end.sh tests/test-session-end-cleanup.sh
git commit -m "feat(skill-evolution): parse session_id and clean up skill tracking in session-end"
```

### Task 5: Update curator prompt in session-start.sh

**Files:**
- Modify: `hooks/session-start.sh:38-51` (curator prompt), `:110-127` (lesson defaults)

- [ ] **Step 1: Update curator prompt to include skill awareness**

In session-start.sh, modify the CURATOR_PROMPT (around line 38) to add skill awareness. After the existing rules about secrets/PII, add:

```
If a candidate includes an 'active_skills' field with skill names, include these fields in the output lesson object:
- skill (string): the skill name most relevant to this lesson (pick one if multiple)
- scope (string): 'project' if the lesson is specific to this codebase, 'skill' if it would help anyone using this skill
```

- [ ] **Step 2: Update lesson defaults to include new fields**

In the merge block (around line 113-124), add defaults for the new fields after the existing `lesson.setdefault` calls:

```python
        lesson.setdefault("skill", None)
        lesson.setdefault("scope", "project")
```

- [ ] **Step 3: Verify backward compatibility**

Run existing autocontext tests or manually test that session-start still works with lessons that have no `active_skills` field:

```bash
echo '{"user_message": "no, use pytest -x", "timestamp": "2026-03-14T10:00:00Z"}' > /tmp/test-pending.json
# The curator should handle this gracefully (no active_skills = no skill/scope in output)
```

- [ ] **Step 4: Commit**

```bash
git add hooks/session-start.sh
git commit -m "feat(skill-evolution): update curator to output skill and scope fields"
```

---

## Chunk 2: Global store and lesson injection

### Task 6: Create global skill lesson store structure

**Files:**
- Create: `scripts/skill-evolution/store.py`

- [ ] **Step 1: Write store.py — the global lesson store manager**

```python
#!/usr/bin/env python3
"""Global skill lesson store manager.

Handles reading, writing, promoting, and querying lessons
in ~/.claude/skill-lessons/.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_STORE = os.path.expanduser("~/.claude/skill-lessons")


def get_store_path(config_store=None):
    """Resolve the global store path from config or default."""
    path = config_store or DEFAULT_STORE
    path = os.path.expanduser(path)
    return path


def ensure_store(store_path=None):
    """Create store directory structure if it doesn't exist."""
    store = get_store_path(store_path)
    os.makedirs(store, exist_ok=True)
    os.makedirs(os.path.join(store, "backups"), exist_ok=True)
    os.makedirs(os.path.join(store, "exports"), exist_ok=True)

    index_path = os.path.join(store, "index.json")
    if not os.path.exists(index_path):
        with open(index_path, "w") as f:
            json.dump({
                "skills": {},
                "created": datetime.now(timezone.utc).isoformat(),
                "schema_version": 1,
            }, f, indent=2)

    return store


def load_index(store_path=None):
    """Load the index.json registry."""
    store = get_store_path(store_path)
    index_path = os.path.join(store, "index.json")
    try:
        with open(index_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"skills": {}, "schema_version": 1}


def save_index(index, store_path=None):
    """Write the index.json registry."""
    store = get_store_path(store_path)
    with open(os.path.join(store, "index.json"), "w") as f:
        json.dump(index, f, indent=2)


def load_skill_lessons(skill_name, store_path=None):
    """Load lessons for a specific skill."""
    store = get_store_path(store_path)
    skill_file = os.path.join(store, f"{skill_name}.json")
    try:
        with open(skill_file) as f:
            data = json.load(f)
        return data.get("lessons", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_skill_lessons(skill_name, lessons, store_path=None):
    """Write lessons for a specific skill."""
    store = get_store_path(store_path)
    skill_file = os.path.join(store, f"{skill_name}.json")
    data = {
        "skill": skill_name,
        "lessons": lessons,
        "schema_version": 1,
    }
    with open(skill_file, "w") as f:
        json.dump(data, f, indent=2)

    # Update index
    index = load_index(store_path)
    active = [l for l in lessons if not l.get("folded", False)]
    index["skills"][skill_name] = {
        "lesson_count": len(active),
        "last_evolved": index.get("skills", {}).get(skill_name, {}).get("last_evolved"),
        "skill_path": index.get("skills", {}).get(skill_name, {}).get("skill_path"),
        "evolution_count": index.get("skills", {}).get(skill_name, {}).get("evolution_count", 0),
    }
    save_index(index, store_path)


def promote_lesson(lesson, skill_name, project_name=None, store_path=None):
    """Promote a project lesson to the global skill store.

    Args:
        lesson: The lesson dict from .autocontext/lessons.json
        skill_name: The skill to associate it with
        project_name: Optional project name for source tracking
        store_path: Override store path
    """
    store = ensure_store(store_path)
    existing = load_skill_lessons(skill_name, store_path)

    # Check for duplicates by text
    existing_texts = {l["text"].strip().lower() for l in existing}
    if lesson.get("text", "").strip().lower() in existing_texts:
        return False  # Already exists

    now = datetime.now(timezone.utc).isoformat()
    global_lesson = {
        "id": "skill_lesson_" + uuid.uuid4().hex[:8],
        "text": lesson["text"],
        "confidence": lesson.get("confidence", 0.7),
        "validated_count": lesson.get("validated_count", 0),
        "source_projects": [project_name] if project_name else [],
        "promoted_from": lesson.get("id"),
        "created": lesson.get("created", now),
        "last_validated": lesson.get("last_validated", now),
        "folded": False,
    }

    existing.append(global_lesson)
    save_skill_lessons(skill_name, existing, store_path)
    return True


def get_eligible_lessons(skill_name, min_confidence=0.85, min_validations=3, store_path=None):
    """Get lessons eligible for evolution (high confidence, not yet folded)."""
    lessons = load_skill_lessons(skill_name, store_path)
    return [
        l for l in lessons
        if not l.get("folded", False)
        and l.get("confidence", 0) >= min_confidence
        and l.get("validated_count", 0) >= min_validations
    ]


def mark_folded(skill_name, lesson_ids, store_path=None):
    """Mark lessons as folded (integrated into skill file)."""
    lessons = load_skill_lessons(skill_name, store_path)
    for lesson in lessons:
        if lesson.get("id") in lesson_ids:
            lesson["folded"] = True
    save_skill_lessons(skill_name, lessons, store_path)

    # Update evolution count and timestamp in index
    index = load_index(store_path)
    if skill_name in index.get("skills", {}):
        entry = index["skills"][skill_name]
        entry["last_evolved"] = datetime.now(timezone.utc).isoformat()
        entry["evolution_count"] = entry.get("evolution_count", 0) + 1
        save_index(index, store_path)
```

- [ ] **Step 2: Write tests for store.py**

Create `tests/test_store.py`:

```python
#!/usr/bin/env python3
"""Tests for the global skill lesson store."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "skill-evolution"))
from store import (
    ensure_store, load_index, load_skill_lessons, save_skill_lessons,
    promote_lesson, get_eligible_lessons, mark_folded,
)


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = os.path.join(self.tmpdir, "skill-lessons")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_ensure_store_creates_structure(self):
        path = ensure_store(self.store)
        self.assertTrue(os.path.isdir(path))
        self.assertTrue(os.path.isdir(os.path.join(path, "backups")))
        self.assertTrue(os.path.isdir(os.path.join(path, "exports")))
        self.assertTrue(os.path.isfile(os.path.join(path, "index.json")))

    def test_promote_lesson(self):
        ensure_store(self.store)
        lesson = {
            "id": "lesson_abc123",
            "text": "Use Selenium for JS-heavy sites",
            "confidence": 0.9,
            "validated_count": 5,
        }
        result = promote_lesson(lesson, "web-scraping", "rosen-frontend", self.store)
        self.assertTrue(result)

        # Verify stored
        lessons = load_skill_lessons("web-scraping", self.store)
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["text"], "Use Selenium for JS-heavy sites")
        self.assertEqual(lessons[0]["source_projects"], ["rosen-frontend"])

        # Verify dedup
        result2 = promote_lesson(lesson, "web-scraping", "rosen-frontend", self.store)
        self.assertFalse(result2)
        self.assertEqual(len(load_skill_lessons("web-scraping", self.store)), 1)

    def test_get_eligible_lessons(self):
        ensure_store(self.store)
        lessons = [
            {"id": "sl_1", "text": "High conf", "confidence": 0.92, "validated_count": 5, "folded": False},
            {"id": "sl_2", "text": "Low conf", "confidence": 0.5, "validated_count": 1, "folded": False},
            {"id": "sl_3", "text": "Already folded", "confidence": 0.95, "validated_count": 10, "folded": True},
        ]
        save_skill_lessons("test-skill", lessons, self.store)

        eligible = get_eligible_lessons("test-skill", 0.85, 3, self.store)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0]["id"], "sl_1")

    def test_mark_folded(self):
        ensure_store(self.store)
        lessons = [
            {"id": "sl_1", "text": "Fold me", "confidence": 0.9, "validated_count": 5, "folded": False},
            {"id": "sl_2", "text": "Keep me", "confidence": 0.9, "validated_count": 5, "folded": False},
        ]
        save_skill_lessons("test-skill", lessons, self.store)

        mark_folded("test-skill", ["sl_1"], self.store)
        updated = load_skill_lessons("test-skill", self.store)
        self.assertTrue(updated[0]["folded"])
        self.assertFalse(updated[1]["folded"])

    def test_index_updated_on_save(self):
        ensure_store(self.store)
        lessons = [{"id": "sl_1", "text": "Test", "confidence": 0.9, "validated_count": 5, "folded": False}]
        save_skill_lessons("web-scraping", lessons, self.store)

        index = load_index(self.store)
        self.assertIn("web-scraping", index["skills"])
        self.assertEqual(index["skills"]["web-scraping"]["lesson_count"], 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `cd autocontext && python3 -m pytest tests/test_store.py -v`
Expected: All 5 tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/skill-evolution/store.py tests/test_store.py
git commit -m "feat(skill-evolution): add global skill lesson store manager"
```

### Task 7: Create skill-lesson-injector.md hook

**Files:**
- Create: `hooks/skill-lesson-injector.md`

- [ ] **Step 1: Write the PreToolUse prompt hook**

```markdown
---
name: autocontext-skill-lesson-injector
description: Inject global skill lessons when a skill is loaded
hooks:
  - event: PreToolUse
    type: prompt
    matcher: "Skill"
---

Check if skill learning is enabled. Read the config with this fallback chain:
1. `.autocontext/config.json` -> `skill_learning.enabled`
2. `~/.claude/autocontext.json` -> `skill_learning.enabled`
3. Default: `false`

If disabled, do nothing.

If enabled, extract the skill name from `tool_input.skill`. Then check if `~/.claude/skill-lessons/<skill-name>.json` exists.

If the file exists, read it and find lessons where `folded` is `false`. If there are un-folded lessons, inject them as a brief note:

```
Note: The following patterns have been learned from real usage of this skill:
- [lesson text] (confidence: [score], from: [comma-separated source_projects])
```

Cap at 5 lessons, sorted by confidence descending. If no un-folded lessons exist, do nothing.

The global store path defaults to `~/.claude/skill-lessons/` but can be overridden by `skill_learning.global_store` in config.
```

- [ ] **Step 2: Commit**

```bash
git add hooks/skill-lesson-injector.md
git commit -m "feat(skill-evolution): add PreToolUse hook to inject global skill lessons"
```

### Task 8: Add "Promote to global" action to review.md

**Files:**
- Modify: `commands/review.md`

- [ ] **Step 1: Read the full review.md**

Read `commands/review.md` to understand the current action options.

- [ ] **Step 2: Add the promote action**

After the existing actions (Approve, Edit, Delete, Supersede, Skip), add:

```markdown
### Promote to global (skill-tagged lessons only)

When a lesson has a `skill` field (non-null), add a sixth action:

- **Promote to global** — Copy this lesson to `~/.claude/skill-lessons/<skill>.json` using the promote function. Update the original lesson's `scope` to `"skill"` in `lessons.json`. Report: "Promoted to global store for [skill name]."

The global store path comes from config: `skill_learning.global_store` (default `~/.claude/skill-lessons/`).

To perform the promotion, run:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from store import promote_lesson, ensure_store
import json

ensure_store()
lesson = json.loads('''LESSON_JSON_HERE''')
result = promote_lesson(lesson, 'SKILL_NAME_HERE', 'PROJECT_NAME_HERE')
print('promoted' if result else 'already_exists')
"
```

Only show this action when `skill_learning.enabled` is true in config.
```

- [ ] **Step 3: Commit**

```bash
git add commands/review.md
git commit -m "feat(skill-evolution): add 'Promote to global' action to /autocontext-review"
```

---

## Chunk 3: Evolution engine

### Task 9: Create the evolution engine scripts

**Files:**
- Create: `scripts/skill-evolution/evolve.sh`
- Create: `scripts/skill-evolution/generate-diff.py`
- Create: `scripts/skill-evolution/apply-edit.py`

- [ ] **Step 1: Write generate-diff.py**

```python
#!/usr/bin/env python3
"""Generate an improved skill file by integrating validated lessons.

Uses claude -p to rewrite the skill content with lessons woven in.
Falls back to appending a '## Learned patterns' section if the user rejects.
"""

import json
import subprocess
import sys
import os


def generate_evolved_skill(skill_content, lessons, model_cmd="claude -p"):
    """Call claude -p to generate an improved skill.

    Args:
        skill_content: Current skill .md file content
        lessons: List of lesson dicts (text, confidence, source_projects)
        model_cmd: Command to invoke Claude

    Returns:
        str: The full updated skill content, or None on failure
    """
    lessons_text = "\n".join(
        f"- [{l.get('confidence', 0):.2f}] {l['text']} "
        f"(from: {', '.join(l.get('source_projects', ['unknown']))})"
        for l in sorted(lessons, key=lambda x: x.get("confidence", 0), reverse=True)
    )

    prompt = f"""You are improving a Claude Code skill based on validated lessons learned from real usage. The skill's current content and the lessons are provided below.

RULES:
- Integrate lessons naturally into the existing content
- Don't create a separate "lessons" section — weave guidance into the flow where it belongs
- Preserve the skill's existing structure, voice, and formatting
- Higher-confidence lessons should be treated as more authoritative
- If a lesson contradicts existing guidance, the lesson wins (it's from real usage)
- Don't add preamble or meta-commentary
- Output the complete updated skill content, nothing else

CURRENT SKILL CONTENT:
<skill>
{skill_content}
</skill>

LESSONS TO INTEGRATE (sorted by confidence):
<lessons>
{lessons_text}
</lessons>"""

    try:
        result = subprocess.run(
            ["bash", "-c", model_cmd],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        sys.stderr.write(f"[skill-evolution] claude call failed: {e}\n")

    return None


def generate_append_fallback(lessons):
    """Generate a '## Learned patterns' section for appending.

    Args:
        lessons: List of lesson dicts

    Returns:
        str: Markdown section to append
    """
    lines = [
        "\n\n## Learned patterns\n",
        "<!-- Auto-generated by autocontext skill evolution. Do not edit manually. -->\n",
    ]
    for l in sorted(lessons, key=lambda x: x.get("confidence", 0), reverse=True):
        sources = ", ".join(l.get("source_projects", ["unknown"]))
        lines.append(f"\n- **[{l.get('confidence', 0):.2f}]** {l['text']}")
        lines.append(f"  _Sources: {sources}_")

    return "\n".join(lines) + "\n"
```

- [ ] **Step 2: Write apply-edit.py**

```python
#!/usr/bin/env python3
"""Apply approved skill edits with backup and rollback support."""

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def backup_skill(skill_path, backup_dir=None):
    """Create a timestamped backup of the skill file.

    Returns:
        str: Path to the backup file
    """
    if backup_dir is None:
        backup_dir = os.path.expanduser("~/.claude/skill-lessons/backups")

    os.makedirs(backup_dir, exist_ok=True)

    skill_name = Path(skill_path).stem
    if skill_name == "SKILL":
        skill_name = Path(skill_path).parent.name

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    backup_path = os.path.join(backup_dir, f"{skill_name}-{timestamp}.md")

    shutil.copy2(skill_path, backup_path)
    return backup_path


def apply_edit(skill_path, new_content, backup_dir=None):
    """Apply new content to a skill file, creating a backup first.

    Returns:
        tuple: (backup_path, success)
    """
    backup_path = backup_skill(skill_path, backup_dir)

    try:
        with open(skill_path, "w") as f:
            f.write(new_content)
        return backup_path, True
    except Exception as e:
        # Restore from backup on failure
        shutil.copy2(backup_path, skill_path)
        return backup_path, False


def rollback(skill_name, backup_dir=None):
    """Restore a skill from its most recent backup.

    Returns:
        tuple: (backup_path_used, skill_path_restored) or (None, None)
    """
    if backup_dir is None:
        backup_dir = os.path.expanduser("~/.claude/skill-lessons/backups")

    if not os.path.isdir(backup_dir):
        return None, None

    # Find most recent backup for this skill
    backups = sorted([
        f for f in os.listdir(backup_dir)
        if f.startswith(f"{skill_name}-") and f.endswith(".md")
    ], reverse=True)

    if not backups:
        return None, None

    backup_path = os.path.join(backup_dir, backups[0])

    # Find the skill path from index
    store_path = os.path.expanduser("~/.claude/skill-lessons")
    index_path = os.path.join(store_path, "index.json")
    try:
        with open(index_path) as f:
            index = json.load(f)
        skill_path = index.get("skills", {}).get(skill_name, {}).get("skill_path")
    except Exception:
        skill_path = None

    if not skill_path or not os.path.exists(backup_path):
        return None, None

    shutil.copy2(backup_path, skill_path)
    return backup_path, skill_path


def find_skill_path(skill_name):
    """Resolve the path to a skill's .md file.

    Searches plugin directories for the skill.

    Returns:
        str or None: Path to the skill .md file
    """
    # Check index first (cached path)
    store_path = os.path.expanduser("~/.claude/skill-lessons")
    index_path = os.path.join(store_path, "index.json")
    try:
        with open(index_path) as f:
            index = json.load(f)
        cached = index.get("skills", {}).get(skill_name, {}).get("skill_path")
        if cached and os.path.exists(cached):
            return cached
    except Exception:
        pass

    # Search plugin directories
    search_dirs = [
        os.path.expanduser("~/.claude/plugins/marketplaces"),
        os.path.expanduser("~/.claude/plugins/cache"),
    ]

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            if os.path.basename(root) == skill_name and "SKILL.md" in files:
                return os.path.join(root, "SKILL.md")

    return None
```

- [ ] **Step 3: Write evolve.sh — the main entry point**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Skill evolution engine entry point
# Called by /autocontext-evolve command
# Handles: evolve (default), --rollback, --export, --import

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(dirname "$0")")")}"
SCRIPT_DIR="$(dirname "$0")"

source "$PLUGIN_ROOT/scripts/config-utils.sh"

STORE_PATH=$(read_config "skill_learning.global_store" "$HOME/.claude/skill-lessons")
STORE_PATH="${STORE_PATH/#\~/$HOME}"

EVOLUTION_CONFIDENCE=$(read_config "skill_learning.evolution_confidence" "0.85")
EVOLUTION_MIN_VALIDATIONS=$(read_config "skill_learning.evolution_min_validations" "3")
BACKUP_DIR=$(read_config "skill_learning.backup_dir" "$HOME/.claude/skill-lessons/backups")
BACKUP_DIR="${BACKUP_DIR/#\~/$HOME}"
MODEL_CMD=$(read_config "skill_learning.evolution_model" "claude -p")

# Ensure store exists
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from store import ensure_store
ensure_store('$STORE_PATH')
"

# Scan for eligible skills and output JSON summary
python3 - <<PYEOF
import sys
import json
sys.path.insert(0, "$SCRIPT_DIR")
from store import load_index, get_eligible_lessons

index = load_index("$STORE_PATH")
summary = {}
for skill_name in index.get("skills", {}):
    eligible = get_eligible_lessons(
        skill_name,
        min_confidence=float("$EVOLUTION_CONFIDENCE"),
        min_validations=int("$EVOLUTION_MIN_VALIDATIONS"),
        store_path="$STORE_PATH",
    )
    if eligible:
        avg_conf = sum(l.get("confidence", 0) for l in eligible) / len(eligible)
        projects = set()
        for l in eligible:
            projects.update(l.get("source_projects", []))
        summary[skill_name] = {
            "count": len(eligible),
            "avg_confidence": round(avg_conf, 2),
            "source_projects": sorted(projects),
            "lessons": eligible,
        }

if not summary:
    print("No skills have lessons eligible for evolution.")
else:
    print(json.dumps(summary, indent=2))
PYEOF
```

- [ ] **Step 4: Make scripts executable**

```bash
chmod +x scripts/skill-evolution/evolve.sh
chmod +x scripts/skill-evolution/generate-diff.py
chmod +x scripts/skill-evolution/apply-edit.py
```

- [ ] **Step 5: Write tests for generate-diff and apply-edit**

Create `tests/test_evolution.py`:

```python
#!/usr/bin/env python3
"""Tests for evolution engine components."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "skill-evolution"))
from apply_edit import backup_skill, apply_edit, rollback
from generate_diff import generate_append_fallback


class TestApplyEdit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.skill_path = os.path.join(self.tmpdir, "SKILL.md")
        self.backup_dir = os.path.join(self.tmpdir, "backups")
        with open(self.skill_path, "w") as f:
            f.write("# Original content\n\nSome guidance here.\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_backup_creates_file(self):
        backup_path = backup_skill(self.skill_path, self.backup_dir)
        self.assertTrue(os.path.exists(backup_path))
        with open(backup_path) as f:
            self.assertIn("Original content", f.read())

    def test_apply_edit_writes_and_backs_up(self):
        new_content = "# Updated content\n\nBetter guidance.\n"
        backup_path, success = apply_edit(self.skill_path, new_content, self.backup_dir)
        self.assertTrue(success)
        with open(self.skill_path) as f:
            self.assertEqual(f.read(), new_content)
        self.assertTrue(os.path.exists(backup_path))


class TestAppendFallback(unittest.TestCase):
    def test_generates_markdown(self):
        lessons = [
            {"text": "Use Selenium for JS sites", "confidence": 0.92, "source_projects": ["proj-a"]},
            {"text": "Set User-Agent header", "confidence": 0.88, "source_projects": ["proj-b"]},
        ]
        result = generate_append_fallback(lessons)
        self.assertIn("## Learned patterns", result)
        self.assertIn("Use Selenium", result)
        self.assertIn("Set User-Agent", result)
        self.assertIn("proj-a", result)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run tests**

Run: `cd autocontext && python3 -m pytest tests/test_evolution.py -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add scripts/skill-evolution/evolve.sh scripts/skill-evolution/generate-diff.py scripts/skill-evolution/apply-edit.py tests/test_evolution.py
git commit -m "feat(skill-evolution): add evolution engine (generate-diff, apply-edit, evolve entry point)"
```

### Task 10: Create the /autocontext-evolve command

**Files:**
- Create: `commands/evolve.md`
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Write evolve.md command**

```markdown
---
description: Evolve skill files by integrating validated lessons from real usage
---

This command improves skill .md files based on lessons accumulated in the global skill lesson store.

## Argument handling

The user may invoke this command with arguments:
- `/autocontext-evolve` — default: scan and evolve interactively
- `/autocontext-evolve --rollback <skill-name>` — restore from backup
- `/autocontext-evolve --export` — export lessons to JSON
- `/autocontext-evolve --import <path>` — import lessons from JSON

Parse the arguments from the user's input. If `--rollback` is present, run the rollback flow. If `--export` or `--import`, run the sync flow. Otherwise, run the default evolution flow.

## Default evolution flow

1. Run the scan script to find eligible skills:
   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution/evolve.sh"
   ```

2. If no skills are eligible, report that and exit.

3. Present the summary to the user using AskUserQuestion: which skill(s) to evolve? Include lesson count and average confidence per skill. Add an "All" option and a "Skip" option.

4. For each selected skill:
   a. Read the current skill .md file using the `find_skill_path` function:
      ```bash
      python3 -c "
      import sys
      sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
      from apply_edit import find_skill_path
      path = find_skill_path('SKILL_NAME')
      print(path or 'NOT_FOUND')
      "
      ```
   b. If NOT_FOUND, warn and skip.
   c. Read the skill file content.
   d. Run generate-diff to create an improved version:
      ```bash
      python3 -c "
      import sys, json
      sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
      from generate_diff import generate_evolved_skill
      from store import get_eligible_lessons

      lessons = get_eligible_lessons('SKILL_NAME')
      with open('SKILL_PATH') as f:
          content = f.read()
      result = generate_evolved_skill(content, lessons)
      if result:
          print(result)
      else:
          print('GENERATION_FAILED')
      "
      ```
   e. If generation failed, offer the append fallback.
   f. Show a diff between the original and evolved content.
   g. Ask the user via AskUserQuestion:
      - **Accept** — apply the edit
      - **Edit** — let user make manual changes first
      - **Reject** — skip, lessons stay
      - **Append instead** — use the fallback section
   h. Apply the chosen action using apply-edit functions.
   i. Mark evolved lessons as folded.

## Rollback flow

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from apply_edit import rollback
backup, restored = rollback('SKILL_NAME')
if restored:
    print(f'Restored {restored} from {backup}')
else:
    print('No backup found for SKILL_NAME')
"
```

## Export flow

```bash
python3 -c "
import sys, json, os
from datetime import datetime, timezone
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from store import load_index, load_skill_lessons, get_store_path, ensure_store

store = ensure_store()
index = load_index()
export = {'exported': datetime.now(timezone.utc).isoformat(), 'skills': {}}
for skill_name in index.get('skills', {}):
    lessons = load_skill_lessons(skill_name)
    if lessons:
        export['skills'][skill_name] = lessons

date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
export_path = os.path.join(store, 'exports', f'{date}-export.json')
with open(export_path, 'w') as f:
    json.dump(export, f, indent=2)
print(f'Exported to {export_path}')
"
```

## Import flow

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts/skill-evolution')
from store import load_skill_lessons, save_skill_lessons, ensure_store

ensure_store()
with open('IMPORT_PATH') as f:
    data = json.load(f)

for skill_name, lessons in data.get('skills', {}).items():
    existing = load_skill_lessons(skill_name)
    existing_ids = {l['id'] for l in existing}
    added = 0
    for lesson in lessons:
        if lesson['id'] not in existing_ids:
            existing.append(lesson)
            added += 1
        else:
            # Merge: additive validated_count, highest confidence, newest timestamp
            for e in existing:
                if e['id'] == lesson['id']:
                    e['validated_count'] = e.get('validated_count', 0) + lesson.get('validated_count', 0)
                    e['confidence'] = max(e.get('confidence', 0), lesson.get('confidence', 0))
                    if lesson.get('last_validated', '') > e.get('last_validated', ''):
                        e['last_validated'] = lesson['last_validated']
                    if lesson.get('folded'):
                        e['folded'] = True
                    break
    save_skill_lessons(skill_name, existing)
    print(f'{skill_name}: added {added}, merged {len(lessons) - added}')
"
```
```

- [ ] **Step 2: Register the command in plugin.json**

Add to `.claude-plugin/plugin.json`:

```json
{
  "name": "autocontext",
  "version": "1.1.0",
  "description": "Accumulates project knowledge across sessions and developers through structured lessons and hooks",
  "author": {
    "name": "Joe Amditis",
    "email": "jamditis@gmail.com"
  }
}
```

Note: Claude Code auto-discovers commands in the `commands/` directory by convention. No explicit registration is needed in `plugin.json` for commands — just placing `evolve.md` in `commands/` is sufficient.

- [ ] **Step 3: Commit**

```bash
git add commands/evolve.md .claude-plugin/plugin.json
git commit -m "feat(skill-evolution): add /autocontext-evolve command with evolve, rollback, export, import"
```

---

## Chunk 4: Setup integration and sync

### Task 11: Add skill learning steps to setup wizard

**Files:**
- Modify: `commands/setup.md`

- [ ] **Step 1: Read the full setup.md**

Read `commands/setup.md` to understand the current step structure and batch grouping.

- [ ] **Step 2: Add batch 6 (steps 11-12)**

Append after the existing final batch:

```markdown
### Batch 6 (steps 11-12)

#### Step 11: Skill learning

Track which skills are active when corrections happen. This enables lessons to accumulate per-skill and eventually improve the skill files via `/autocontext-evolve`.

**Question:** Do you want autocontext to track corrections per-skill?

**Options:**
- Yes, track all skills (recommended)
- Only specific skills (will ask which ones)
- No, skip skill tracking

If "Yes": set `skill_learning.enabled = true`, `skill_learning.scope = "all"`
If "Only specific skills": ask a follow-up text input for comma-separated skill names, set `skill_learning.scope = ["name1", "name2"]`
If "No": set `skill_learning.enabled = false`

#### Step 12: Evolution aggressiveness

Controls the minimum evidence threshold for `/autocontext-evolve` to consider a lesson ready.

**Question:** How aggressive should skill evolution be?

**Options:**
- Conservative (confidence >= 0.9, 5+ validations) — only well-proven lessons
- Moderate (confidence >= 0.85, 3+ validations) (recommended)
- Aggressive (confidence >= 0.7, 2+ validations) — faster evolution, more risk

Set `skill_learning.evolution_confidence` and `skill_learning.evolution_min_validations` based on selection.
```

- [ ] **Step 3: Commit**

```bash
git add commands/setup.md
git commit -m "feat(skill-evolution): add skill learning steps to /autocontext-setup wizard"
```

### Task 12: Create sync.py for export/import

**Files:**
- Create: `scripts/skill-evolution/sync.py`

- [ ] **Step 1: Write sync.py**

```python
#!/usr/bin/env python3
"""Export/import skill lessons for cross-machine sharing.

Uses union merge semantics:
- Additive validated_count
- Highest confidence wins
- Newest last_validated timestamp wins
- New lessons (by ID) are added
- folded state preserved (if folded on either side, stays folded)
"""

import json
import os
from datetime import datetime, timezone

import sys
sys.path.insert(0, os.path.dirname(__file__))
from store import (
    load_index, load_skill_lessons, save_skill_lessons,
    ensure_store, get_store_path,
)


def export_all(store_path=None):
    """Export all skill lessons to a single JSON file.

    Returns:
        str: Path to the export file
    """
    store = ensure_store(store_path)
    index = load_index(store_path)

    export_data = {
        "exported": datetime.now(timezone.utc).isoformat(),
        "exporter": os.uname().nodename,
        "skills": {},
    }

    for skill_name in index.get("skills", {}):
        lessons = load_skill_lessons(skill_name, store_path)
        if lessons:
            export_data["skills"][skill_name] = lessons

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    export_path = os.path.join(store, "exports", f"{date}-export.json")
    os.makedirs(os.path.dirname(export_path), exist_ok=True)

    with open(export_path, "w") as f:
        json.dump(export_data, f, indent=2)

    return export_path


def import_lessons(import_path, store_path=None):
    """Import lessons from an export file using union merge.

    Returns:
        dict: Summary of changes per skill {skill: {"added": N, "merged": N}}
    """
    ensure_store(store_path)

    with open(import_path) as f:
        data = json.load(f)

    summary = {}
    for skill_name, incoming_lessons in data.get("skills", {}).items():
        existing = load_skill_lessons(skill_name, store_path)
        existing_by_id = {l["id"]: l for l in existing}

        added = 0
        merged = 0

        for lesson in incoming_lessons:
            lid = lesson.get("id")
            if lid not in existing_by_id:
                existing.append(lesson)
                added += 1
            else:
                e = existing_by_id[lid]
                # Additive validated_count
                e["validated_count"] = e.get("validated_count", 0) + lesson.get("validated_count", 0)
                # Highest confidence
                e["confidence"] = max(e.get("confidence", 0), lesson.get("confidence", 0))
                # Newest timestamp
                if lesson.get("last_validated", "") > e.get("last_validated", ""):
                    e["last_validated"] = lesson["last_validated"]
                # Folded wins
                if lesson.get("folded"):
                    e["folded"] = True
                # Union source_projects
                e_projects = set(e.get("source_projects", []))
                l_projects = set(lesson.get("source_projects", []))
                e["source_projects"] = sorted(e_projects | l_projects)
                merged += 1

        save_skill_lessons(skill_name, existing, store_path)
        summary[skill_name] = {"added": added, "merged": merged}

    return summary
```

- [ ] **Step 2: Write test for sync**

Create `tests/test_sync.py`:

```python
#!/usr/bin/env python3
"""Tests for export/import sync."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "skill-evolution"))
from sync import export_all, import_lessons
from store import ensure_store, save_skill_lessons, load_skill_lessons


class TestSync(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store_a = os.path.join(self.tmpdir, "store-a")
        self.store_b = os.path.join(self.tmpdir, "store-b")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_export_import_round_trip(self):
        ensure_store(self.store_a)
        lessons = [
            {"id": "sl_1", "text": "Lesson one", "confidence": 0.9,
             "validated_count": 3, "source_projects": ["proj-a"],
             "folded": False, "last_validated": "2026-03-14T10:00:00Z"},
        ]
        save_skill_lessons("web-scraping", lessons, self.store_a)

        export_path = export_all(self.store_a)
        self.assertTrue(os.path.exists(export_path))

        # Import into a fresh store
        ensure_store(self.store_b)
        summary = import_lessons(export_path, self.store_b)
        self.assertEqual(summary["web-scraping"]["added"], 1)

        imported = load_skill_lessons("web-scraping", self.store_b)
        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[0]["text"], "Lesson one")

    def test_union_merge_semantics(self):
        ensure_store(self.store_b)
        existing = [
            {"id": "sl_1", "text": "Lesson one", "confidence": 0.8,
             "validated_count": 2, "source_projects": ["proj-a"],
             "folded": False, "last_validated": "2026-03-10T10:00:00Z"},
        ]
        save_skill_lessons("web-scraping", existing, self.store_b)

        # Create an export with higher confidence and more validations
        export_data = {
            "exported": "2026-03-14T10:00:00Z",
            "skills": {
                "web-scraping": [
                    {"id": "sl_1", "text": "Lesson one", "confidence": 0.95,
                     "validated_count": 5, "source_projects": ["proj-b"],
                     "folded": False, "last_validated": "2026-03-14T10:00:00Z"},
                    {"id": "sl_2", "text": "New lesson", "confidence": 0.7,
                     "validated_count": 1, "source_projects": ["proj-b"],
                     "folded": False, "last_validated": "2026-03-14T10:00:00Z"},
                ],
            },
        }
        export_path = os.path.join(self.tmpdir, "import.json")
        with open(export_path, "w") as f:
            json.dump(export_data, f)

        summary = import_lessons(export_path, self.store_b)
        self.assertEqual(summary["web-scraping"]["added"], 1)
        self.assertEqual(summary["web-scraping"]["merged"], 1)

        merged = load_skill_lessons("web-scraping", self.store_b)
        sl_1 = next(l for l in merged if l["id"] == "sl_1")
        # Additive validated_count
        self.assertEqual(sl_1["validated_count"], 7)  # 2 + 5
        # Highest confidence
        self.assertEqual(sl_1["confidence"], 0.95)
        # Union projects
        self.assertIn("proj-a", sl_1["source_projects"])
        self.assertIn("proj-b", sl_1["source_projects"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests**

Run: `cd autocontext && python3 -m pytest tests/test_sync.py -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/skill-evolution/sync.py tests/test_sync.py
git commit -m "feat(skill-evolution): add export/import sync with union merge"
```

---

## Chunk 5: Backward compatibility and final verification

### Task 13: Verify backward compatibility

**Files:**
- None (test-only)

- [ ] **Step 1: Test that autocontext works with skill_learning disabled (default)**

Run existing tests and verify no regressions:

```bash
cd autocontext
bash tests/test-skill-tracking.sh
bash tests/test-skill-tagging.sh
bash tests/test-session-end-cleanup.sh
python3 -m pytest tests/ -v
```

All should pass.

- [ ] **Step 2: Test that hooks exit cleanly when no .autocontext/ exists**

```bash
cd /tmp
echo '{"tool_name":"Skill","tool_input":{"skill":"test"},"session_id":"compat-test","cwd":"/tmp"}' | \
    bash ~/.claude/plugins/marketplaces/claude-skills-journalism/autocontext/hooks/post-tool-use.sh
echo $?  # Should be 0
rm -f /tmp/claude-skills-compat-test
```

- [ ] **Step 3: Test that hooks exit cleanly when skill_learning is disabled**

```bash
mkdir -p /tmp/compat-test/.autocontext/cache
echo '{"skill_learning": {"enabled": false}}' > /tmp/compat-test/.autocontext/config.json
cd /tmp/compat-test
echo '{"user_message":"no use X instead","session_id":"compat-test2"}' | \
    bash ~/.claude/plugins/marketplaces/claude-skills-journalism/autocontext/hooks/user-prompt-submit.sh
# Should complete without errors; pending lesson should have active_skills: []
rm -rf /tmp/compat-test
```

- [ ] **Step 4: Commit test results (if any test fixtures added)**

```bash
git add -A tests/
git commit -m "test(skill-evolution): verify backward compatibility"
```

### Task 14: Bump version and final commit

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `../../CHANGELOG.md` (repo root)

- [ ] **Step 1: Bump version to 1.1.0**

Update `.claude-plugin/plugin.json`:
```json
"version": "1.1.0"
```

- [ ] **Step 2: Add changelog entry**

Add to the top of `CHANGELOG.md`:

```markdown
## [1.1.0] - 2026-03-14

### Added
- Skill evolution: skills can now self-improve based on accumulated lessons
- `post-tool-use.sh` tracks which skills are active during a session
- `user-prompt-submit.sh` tags corrections with active skill names
- Global skill lesson store at `~/.claude/skill-lessons/`
- New `/autocontext-evolve` command: scan, evolve, rollback, export, import
- `skill-lesson-injector.md` hook injects global lessons when skills load
- "Promote to global" action in `/autocontext-review`
- Steps 11-12 in `/autocontext-setup` for skill learning configuration
- Shared `config-utils.sh` for consistent config resolution
- Export/import sync with union merge for cross-machine sharing
```

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json ../../CHANGELOG.md
git commit -m "chore: bump autocontext to v1.1.0 with skill evolution"
```
