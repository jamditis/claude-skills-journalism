#!/usr/bin/env python3
"""scaffold.py: generate a conforming OKF (Open Knowledge Format) starter bundle.

Creates a project that passes its own validator by construction:

    <target>/
      SPEC.md                 the format contract (copied from the skill)
      README.md               how to use and validate this bundle
      scripts/validate.py     the validator (copied from the skill)
      .claude/                session hooks that orient Claude on the bundle
        settings.json         registers the hooks (Claude Code asks you to approve once)
        hooks/okf-anchor.py   SessionStart: load the index into context
        hooks/okf-orient.py   PreToolUse: gate the first action on orientation
      bundle/                 the OKF bundle (this is what gets validated)
        index.md              carries okf_version
        <section>/
          index.md            section navigation
          example-concept.md  a starter concept with full frontmatter

SPEC.md and README.md live at the project root, NOT inside bundle/, because the
validator treats every non-reserved .md inside the bundle as a concept that needs
frontmatter. Keeping docs out of bundle/ means a fresh scaffold validates clean.

The .claude/ hooks are one cross-platform python3 script each; only the launch
command in settings.json differs per OS (python3 on macOS/Linux, python on Windows).
Claude Code treats a checked-in .claude/settings.json as untrusted, so the user
approves the hooks once on first session open. See SKILL.md for the hook contract.

Usage:
  scaffold.py ./my-knowledge-base
  scaffold.py ./kb --title "Team knowledge base" --sections concepts,services,decisions
  scaffold.py ./kb --no-validate        # skip the post-scaffold validation run
  scaffold.py ./kb --no-hooks           # do not write the .claude/ session hooks
  scaffold.py ./kb --hooks-os windows   # force the Windows launch command (default: this OS)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SRC_SPEC = SKILL_ROOT / "spec" / "SPEC.md"
SRC_VALIDATOR = SKILL_ROOT / "scripts" / "validate.py"
SRC_HOOKS = SKILL_ROOT / "templates" / "hooks"
HOOK_SCRIPTS = ("okf-anchor.py", "okf-orient.py")


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


def readme(title: str, hooks: bool, interp: str = "python3") -> str:
    hooks_section = (
        "## Session hooks\n\n"
        "`.claude/` ships two hooks that orient Claude on this knowledge base before it works:\n\n"
        "- `okf-anchor.py` (SessionStart) loads the bundle index into the session context.\n"
        "- `okf-orient.py` (PreToolUse) blocks the first action once per session until Claude\n"
        "  confirms it has read the index, then unblocks for the rest of the session.\n\n"
        "They are one cross-platform python3 script each. No single interpreter name works on\n"
        "every OS, so `settings.json` names the one for the OS this bundle was scaffolded on\n"
        "(`python3` on macOS/Linux, `python` on Windows). If you move the bundle to a different\n"
        "OS, change that one token in `settings.json` (or re-run the scaffolder there). Claude\n"
        "Code treats a checked-in `.claude/settings.json` as untrusted, so the first time you\n"
        "open this project it asks you to approve the hooks. They run automatically after that.\n"
        "Delete `.claude/` (or set `disableAllHooks`) to turn them off.\n\n"
    ) if hooks else ""
    return (
        f"# {title}\n\n"
        "An Open Knowledge Format (OKF) knowledge base: small markdown files, one concept each,\n"
        "with provenance in YAML frontmatter. See `SPEC.md` for the full contract.\n\n"
        "## Validate\n\n"
        "```bash\n"
        f"{interp} scripts/validate.py --bundle bundle\n"
        "```\n\n"
        "It must exit 0. Run it before every commit.\n\n"
        "## Add a concept\n\n"
        "1. Create `bundle/<section>/<concept>.md` with the required frontmatter\n"
        "   (`type, title, description, source, verified, timestamp, tags`).\n"
        "2. Add a bullet for it in that section's `index.md`.\n"
        "3. Validate.\n\n"
        f"{hooks_section}"
        "## Security\n\n"
        "Never put secret values in a concept. A credential concept documents the key name and\n"
        "where it is retrieved, not the value. The validator scans for leaked secrets and fails on a hit.\n"
    )


def resolve_hooks_os(choice: str) -> str:
    """Map --hooks-os (auto|posix|windows) to the concrete launch target."""
    if choice == "auto":
        return "windows" if platform.system() == "Windows" else "posix"
    return choice


def interpreter_for(hooks_os: str) -> str:
    """The python command for an OS. No single name works everywhere: macOS/Linux
    have python3, stock Windows has python (python3 is usually absent there)."""
    return "python" if hooks_os == "windows" else "python3"


def claude_settings(hooks_os: str) -> dict:
    """Build the .claude/settings.json that registers the orientation hooks.

    The hook scripts are cross-platform python3; only the interpreter in the launch
    command changes per OS (python3 on macOS/Linux, python on Windows). The script
    path uses the ${CLAUDE_PROJECT_DIR} placeholder, which Claude Code substitutes
    with the project root before running the command on every OS. That resolves the
    hook even when its working directory has drifted (the hook cwd is not guaranteed
    to be the project root), and stays correct when the bundle is cloned to another
    path -- unlike a baked-in absolute path. PreToolUse omits a matcher so it sees
    the first tool call of any kind.
    """
    interp = interpreter_for(hooks_os)

    def cmd(script: str) -> dict:
        path = f"${{CLAUDE_PROJECT_DIR}}/.claude/hooks/{script}"
        return {"type": "command", "command": f'{interp} "{path}"'}

    return {
        "hooks": {
            "SessionStart": [{"hooks": [cmd("okf-anchor.py")]}],
            "PreToolUse": [{"hooks": [cmd("okf-orient.py")]}],
        }
    }


def write_claude_hooks(target: Path, hooks_os: str) -> None:
    """Copy the hook scripts into target/.claude/hooks and write settings.json."""
    hooks_dir = target / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for script in HOOK_SCRIPTS:
        dest = hooks_dir / script
        shutil.copy2(SRC_HOOKS / script, dest)
        # make executable for the shebang case; the launch command also names the
        # interpreter explicitly, so this is belt-and-suspenders.
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    settings = target / ".claude" / "settings.json"
    settings.write_text(json.dumps(claude_settings(hooks_os), indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a conforming OKF starter bundle.")
    ap.add_argument("target", help="directory to create the project in")
    ap.add_argument("--title", default=None, help="bundle title (default: derived from target dir name)")
    ap.add_argument("--sections", default="concepts",
                    help="comma-separated section names (default: concepts)")
    ap.add_argument("--date", default=None, help="ISO date for sample frontmatter (default: today)")
    ap.add_argument("--force", action="store_true", help="write into a non-empty target directory")
    ap.add_argument("--no-validate", action="store_true", help="skip the post-scaffold validation run")
    ap.add_argument("--no-hooks", action="store_true", help="do not write the .claude/ session hooks")
    ap.add_argument("--hooks-os", choices=("auto", "posix", "windows"), default="auto",
                    help="launch command for the hooks (default: auto-detect this OS)")
    args = ap.parse_args()

    if not SRC_SPEC.exists() or not SRC_VALIDATOR.exists():
        print(f"FAIL: skill assets missing ({SRC_SPEC} / {SRC_VALIDATOR})", file=sys.stderr)
        return 1
    if not args.no_hooks and not all((SRC_HOOKS / s).exists() for s in HOOK_SCRIPTS):
        print(f"FAIL: hook templates missing in {SRC_HOOKS} (or pass --no-hooks)", file=sys.stderr)
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

    write_hooks = not args.no_hooks
    hooks_os = resolve_hooks_os(args.hooks_os)

    shutil.copy2(SRC_SPEC, target / "SPEC.md")
    shutil.copy2(SRC_VALIDATOR, target / "scripts" / "validate.py")
    (target / "README.md").write_text(
        readme(title, write_hooks, interpreter_for(hooks_os)), encoding="utf-8")
    (bundle / "index.md").write_text(root_index(title, sections), encoding="utf-8")
    for s in sections:
        sdir = bundle / s
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "index.md").write_text(section_index(s), encoding="utf-8")
        (sdir / "example-concept.md").write_text(example_concept(today), encoding="utf-8")
    if write_hooks:
        write_claude_hooks(target, hooks_os)

    print(f"Scaffolded OKF project at {target}")
    print(f"  title: {title}")
    print(f"  sections: {', '.join(sections)}")
    if write_hooks:
        print(f"  hooks: .claude/ written for {hooks_os} (Claude Code asks you to approve them on first open)")
    else:
        print("  hooks: skipped (--no-hooks)")

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
