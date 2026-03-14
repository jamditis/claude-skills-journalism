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

    # Search plugin directories and user skill directories
    search_dirs = [
        os.path.expanduser("~/.claude/plugins/marketplaces"),
        os.path.expanduser("~/.claude/plugins/cache"),
        os.path.expanduser("~/.claude/skills"),
    ]

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            if os.path.basename(root) == skill_name and "SKILL.md" in files:
                return os.path.join(root, "SKILL.md")

    return None
