#!/usr/bin/env python3
"""scaffold.py — generate a conforming OKF (Open Knowledge Format) starter bundle.

Creates a project that passes its own validator by construction:

    <target>/
      SPEC.md                 the format contract (copied from the skill)
      README.md               how to use and validate this bundle
      scripts/validate.py     the validator (copied from the skill)
      bundle/                 the OKF bundle (this is what gets validated)
        index.md              carries okf_version
        <section>/
          index.md            section navigation
          example-concept.md  a starter concept with full frontmatter

SPEC.md and README.md live at the project root, NOT inside bundle/, because the
validator treats every non-reserved .md inside the bundle as a concept that needs
frontmatter. Keeping docs out of bundle/ means a fresh scaffold validates clean.

Usage:
  scaffold.py ./my-knowledge-base
  scaffold.py ./kb --title "Team knowledge base" --sections concepts,services,decisions
  scaffold.py ./kb --no-validate        # skip the post-scaffold validation run
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SRC_SPEC = SKILL_ROOT / "spec" / "SPEC.md"
SRC_VALIDATOR = SKILL_ROOT / "scripts" / "validate.py"


def slugify(name: str) -> str:
    return "-".join("".join(c if c.isalnum() else " " for c in name.lower()).split())


def root_index(title: str, sections: list[str]) -> str:
    nav = "\n".join(f"- [{s}]({s}/index.md)" for s in sections)
    return (
        '---\nokf_version: "0.1"\n---\n'
        f"# {title}\n\n"
        "An Open Knowledge Format bundle. One concept per file; provenance in each file's frontmatter.\n\n"
        "## Sections\n\n"
        f"{nav}\n"
    )


def section_index(section: str) -> str:
    return (
        f"# {section}\n\n"
        f"Concepts in the {section} section.\n\n"
        "- [example concept](example-concept.md)\n"
    )


def example_concept(today: str) -> str:
    return (
        "---\n"
        "type: Reference\n"
        "title: Example concept\n"
        "description: A starter concept showing the OKF frontmatter contract.\n"
        'source: ["SPEC.md", "scaffold.py"]\n'
        f"verified: {today}\n"
        f"timestamp: {today}\n"
        "tags: [example, starter]\n"
        "---\n"
        "# Example concept\n\n"
        "Replace this file with a real concept. Keep it to one concept per file.\n\n"
        "- Point every `source` element at real provenance (a path, command, URL, or event).\n"
        "- Update `verified` when you re-check the fact against reality.\n"
        "- Link related concepts with relative markdown links, like this one to [the section index](index.md).\n"
    )


def readme(title: str) -> str:
    return (
        f"# {title}\n\n"
        "An Open Knowledge Format (OKF) knowledge base: small markdown files, one concept each,\n"
        "with provenance in YAML frontmatter. See `SPEC.md` for the full contract.\n\n"
        "## Validate\n\n"
        "```bash\n"
        "python3 scripts/validate.py --bundle bundle\n"
        "```\n\n"
        "It must exit 0. Run it before every commit.\n\n"
        "## Add a concept\n\n"
        "1. Create `bundle/<section>/<concept>.md` with the required frontmatter\n"
        "   (`type, title, description, source, verified, timestamp, tags`).\n"
        "2. Add a bullet for it in that section's `index.md`.\n"
        "3. Validate.\n\n"
        "## Security\n\n"
        "Never put secret values in a concept. A credential concept documents the key name and\n"
        "where it is retrieved, not the value. The validator scans for leaked secrets and fails on a hit.\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a conforming OKF starter bundle.")
    ap.add_argument("target", help="directory to create the project in")
    ap.add_argument("--title", default=None, help="bundle title (default: derived from target dir name)")
    ap.add_argument("--sections", default="concepts",
                    help="comma-separated section names (default: concepts)")
    ap.add_argument("--date", default=None, help="ISO date for sample frontmatter (default: today)")
    ap.add_argument("--force", action="store_true", help="write into a non-empty target directory")
    ap.add_argument("--no-validate", action="store_true", help="skip the post-scaffold validation run")
    args = ap.parse_args()

    if not SRC_SPEC.exists() or not SRC_VALIDATOR.exists():
        print(f"FAIL: skill assets missing ({SRC_SPEC} / {SRC_VALIDATOR})", file=sys.stderr)
        return 1

    target = Path(args.target).resolve()
    if target.exists() and any(target.iterdir()) and not args.force:
        print(f"FAIL: {target} exists and is not empty (use --force to write anyway)", file=sys.stderr)
        return 1

    title = args.title or Path(args.target).name.replace("-", " ").replace("_", " ").strip() or "knowledge base"
    # A section name that is all punctuation slugifies to "" and would write its
    # index to bundle/index.md, clobbering the root index. Reject those, and
    # dedupe so a repeated name does not overwrite a directory mid-loop.
    sections: list[str] = []
    for raw in args.sections.split(","):
        if not raw.strip():
            continue
        slug = slugify(raw)
        if not slug:
            print(f"FAIL: section name {raw!r} has no alphanumeric characters", file=sys.stderr)
            return 1
        if slug not in sections:
            sections.append(slug)
    if not sections:
        print("FAIL: at least one section is required", file=sys.stderr)
        return 1
    today = args.date or dt.date.today().isoformat()
    try:
        dt.datetime.strptime(today, "%Y-%m-%d")
    except ValueError:
        print(f"FAIL: --date must be ISO YYYY-MM-DD, got {today!r}", file=sys.stderr)
        return 1

    bundle = target / "bundle"
    (target / "scripts").mkdir(parents=True, exist_ok=True)
    bundle.mkdir(parents=True, exist_ok=True)

    shutil.copy2(SRC_SPEC, target / "SPEC.md")
    shutil.copy2(SRC_VALIDATOR, target / "scripts" / "validate.py")
    (target / "README.md").write_text(readme(title), encoding="utf-8")
    (bundle / "index.md").write_text(root_index(title, sections), encoding="utf-8")
    for s in sections:
        sdir = bundle / s
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "index.md").write_text(section_index(s), encoding="utf-8")
        (sdir / "example-concept.md").write_text(example_concept(today), encoding="utf-8")

    print(f"Scaffolded OKF project at {target}")
    print(f"  title: {title}")
    print(f"  sections: {', '.join(sections)}")

    if args.no_validate:
        return 0

    print("\nValidating the new bundle...")
    res = subprocess.run(
        [sys.executable, str(target / "scripts" / "validate.py"), "--bundle", str(bundle)],
        capture_output=True, text=True)
    sys.stdout.write(res.stdout)
    if res.stderr:
        sys.stderr.write(res.stderr)
    if res.returncode != 0:
        print("FAIL: scaffold did not validate (this is a bug in scaffold.py)", file=sys.stderr)
        return res.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
