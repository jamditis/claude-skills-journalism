#!/usr/bin/env python3
"""SessionStart hook: orient Claude on this OKF knowledge base.

Prints the bundle's root index (the map of the knowledge base) so it lands in the
session context, and work starts from the map instead of from memory. Claude Code
injects a SessionStart hook's stdout into the session.

Resolves the bundle relative to $CLAUDE_PROJECT_DIR (set by Claude Code), then this
script's own location, then the cwd, so it works wherever the hook is launched from.
No-ops silently if there is no bundle index. Never fails a session: a genuine error
exits 0, but reports the reason on stderr so a broken bundle is not silently dropped.

This is one cross-platform python3 script; only the launch command in
.claude/settings.json differs per OS (python3 on macOS/Linux, python on Windows).
"""
import os
import sys
from pathlib import Path

REL_CANDIDATES = ("bundle/index.md", "index.md")


def find_index():
    """Resolve the bundle root index.md.

    Order: $CLAUDE_PROJECT_DIR, then this script's install dir (<project>/.claude/
    hooks/), then a walk up from the cwd. The first two pin the root directly. The
    cwd walk climbs upward looking for bundle/index.md, so a launch from inside
    bundle/<section>/ still resolves the root map, not the section's own index.md. A
    bare index.md at the cwd is the bundle-less last resort.
    """
    bases = []
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir:
        bases.append(Path(env_dir))
    bases.append(Path(__file__).resolve().parent.parent.parent)  # <project>/.claude/hooks/
    for base in bases:
        for rel in REL_CANDIDATES:
            p = base / rel
            if p.is_file():
                return p
    cwd = Path.cwd().resolve()
    for ancestor in (cwd, *cwd.parents):
        p = ancestor / "bundle" / "index.md"
        if p.is_file():
            return p
    p = cwd / "index.md"
    return p if p.is_file() else None


def strip_frontmatter(text):
    """Drop a leading YAML frontmatter block (--- ... ---) if present."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return "\n".join(lines[i + 1:]).strip()
    return text.strip()


def main():
    index = find_index()
    if index is None:
        return 0
    # utf-8-sig strips a leading BOM; without it a BOM defeats the "---" frontmatter
    # check in strip_frontmatter and the raw YAML block would leak into the context.
    body = strip_frontmatter(index.read_text(encoding="utf-8-sig"))
    if not body:
        return 0
    print(
        "OKF_ANCHOR: this project is an Open Knowledge Format (OKF) knowledge base. "
        "Orient on the index below before acting on it. It maps the concepts, their "
        "provenance, and how the bundle is organized. Drill into a section's index.md, "
        "then open only the concept you need; re-check the map when the task shifts area."
    )
    print("--- begin OKF index ---")
    print(body)
    print("--- end OKF index ---")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - last-resort guard around the whole hook
        # Stay fail-open (a broken bundle must not break the session), but not
        # silently: the orient gate tells Claude the index was injected, so a silent
        # anchor failure would make that claim false and hard to diagnose.
        sys.stderr.write(
            f"OKF anchor hook: could not inject the OKF index ({exc!r}); continuing "
            "without it. The orientation gate may reference an index that is not in "
            "context.\n"
        )
        sys.exit(0)
