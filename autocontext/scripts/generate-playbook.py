#!/usr/bin/env python3
"""Generate a human-readable playbook.md from lessons.json"""
import json
import sys
from datetime import datetime
from collections import defaultdict


def main():
    if len(sys.argv) != 3:
        print("Usage: generate-playbook.py <lessons.json path> <playbook.md path>", file=sys.stderr)
        sys.exit(1)

    lessons_path = sys.argv[1]
    playbook_path = sys.argv[2]

    # Read lessons
    with open(lessons_path) as f:
        lessons = json.load(f)

    # Filter out deleted lessons
    active_lessons = [l for l in lessons if not l.get("deleted", False)]

    # Group by category
    by_category = defaultdict(list)
    for lesson in active_lessons:
        category = lesson.get("category", "uncategorized")
        by_category[category].append(lesson)

    # Sort within each category by confidence (descending)
    for category in by_category:
        by_category[category].sort(key=lambda x: x.get("confidence", 0), reverse=True)

    # Generate markdown
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    output = []
    output.append("# Project playbook (auto-generated)")
    output.append(f"Last updated: {now} | {len(active_lessons)} active lessons")
    output.append("")

    # Sort categories for consistent output
    for category in sorted(by_category.keys()):
        lessons_in_cat = by_category[category]
        output.append(f"## {category.capitalize()} ({len(lessons_in_cat)} lessons)")

        for lesson in lessons_in_cat:
            confidence = lesson.get("confidence", 0)
            text = lesson.get("text", "")
            tags = lesson.get("tags", [])

            # Format: - **[confidence]** text (tag1, tag2, ...)
            tag_str = ", ".join(tags) if tags else ""
            if tag_str:
                output.append(f"- **[{confidence}]** {text} ({tag_str})")
            else:
                output.append(f"- **[{confidence}]** {text}")

        output.append("")

    # Write playbook
    with open(playbook_path, "w") as f:
        f.write("\n".join(output))


if __name__ == "__main__":
    main()
