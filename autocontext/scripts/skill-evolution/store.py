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
    """Promote a project lesson to the global skill store."""
    store = ensure_store(store_path)
    existing = load_skill_lessons(skill_name, store_path)

    # Check for duplicates by text
    existing_texts = {l["text"].strip().lower() for l in existing}
    if lesson.get("text", "").strip().lower() in existing_texts:
        return False

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
