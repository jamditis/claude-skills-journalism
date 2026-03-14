#!/usr/bin/env python3
"""Extract lessons from an existing CLAUDE.md file and seed lessons.json.

Usage: seed-from-claude-md.py <CLAUDE.md path> <lessons.json path>
"""
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone


# Bullet prefixes to extract from
BULLET_PREFIXES = ("- ", "* ")

# Minimum character length for a bullet to be considered a lesson
MIN_LENGTH = 15

# Generic phrases that indicate a bullet is not project-specific
GENERIC_STARTS = (
    "use git",
    "python is",
    "install",
    "run the",
    "see the",
    "check the",
    "read the",
    "refer to",
)

# Keywords that map to categories
OPTIMIZATION_KEYWORDS = (
    "slow", "performance", "cache", "latency", "timeout", "memory",
)
CODEBASE_KEYWORDS = (
    "schema", "struct", "model", "database", "column", "table", "architecture",
)


def categorize(text):
    lower = text.lower()
    for kw in OPTIMIZATION_KEYWORDS:
        if kw in lower:
            return "optimization"
    for kw in CODEBASE_KEYWORDS:
        if kw in lower:
            return "codebase"
    return "efficiency"


def is_generic(text):
    lower = text.lower()
    for prefix in GENERIC_STARTS:
        if lower.startswith(prefix):
            return True
    return False


def extract_bullets(content):
    """Extract lesson candidates from bullet points in markdown content."""
    lessons = []
    for line in content.splitlines():
        stripped = line.strip()
        for prefix in BULLET_PREFIXES:
            if stripped.startswith(prefix):
                text = stripped[len(prefix):].strip()
                if len(text) < MIN_LENGTH:
                    break
                if is_generic(text):
                    break
                lessons.append(text)
                break
    return lessons


def try_claude_extraction(content):
    """Attempt to extract lessons using claude -p. Returns list of strings or None."""
    prompt = (
        "You are a knowledge extractor. Read the following CLAUDE.md content and "
        "extract only project-specific, actionable lessons that would save a future "
        "developer time. Skip general programming knowledge. "
        "Output as a JSON array of strings, one lesson per string. "
        "Output ONLY the JSON array, no explanation.\n\n"
        f"CLAUDE.md content:\n{content}"
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.strip()
        # Find JSON array in output
        start = output.find("[")
        end = output.rfind("]")
        if start == -1 or end == -1:
            return None
        parsed = json.loads(output[start:end + 1])
        if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            return parsed
        return None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
        return None


def build_lesson(text):
    """Build a lesson record from a text string."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": "lesson_" + uuid.uuid4().hex[:8],
        "schema_version": 1,
        "category": categorize(text),
        "text": text,
        "context": "",
        "tags": [],
        "confidence": 0.6,
        "validated_count": 0,
        "last_validated": now,
        "created": now,
        "created_by": "seed",
        "supersedes": None,
        "deleted": False,
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: seed-from-claude-md.py <CLAUDE.md path> <lessons.json path>", file=sys.stderr)
        sys.exit(1)

    claude_md_path = sys.argv[1]
    lessons_path = sys.argv[2]

    with open(claude_md_path) as f:
        content = f.read()

    # Try smart extraction via claude -p, fall back to bullet extraction
    candidates = try_claude_extraction(content)
    if candidates is None:
        candidates = extract_bullets(content)

    # Load existing lessons to check for duplicates
    with open(lessons_path) as f:
        existing = json.load(f)

    existing_texts = {l.get("text", "") for l in existing if l.get("text")}

    new_lessons = []
    seen_texts = set()
    for text in candidates:
        if text in existing_texts:
            continue
        if text in seen_texts:
            continue
        seen_texts.add(text)
        new_lessons.append(build_lesson(text))

    updated = existing + new_lessons

    with open(lessons_path, "w") as f:
        json.dump(updated, f, indent=2)

    print(f"Added {len(new_lessons)} lessons ({len(existing)} already existed)")


if __name__ == "__main__":
    main()
