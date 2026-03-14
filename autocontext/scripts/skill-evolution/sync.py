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
