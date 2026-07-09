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
import importlib.util
import json
import platform
import re
import shlex
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
# The exact hook-command paths this scaffold writes (see cmd() in claude_settings).
# We identify our own hook entries by exact match on these strings, so a re-run
# replaces only what we generated and never a user's hook that merely lives at a
# similarly named path elsewhere (e.g. /opt/shared/.claude/hooks/okf-anchor.py).
OKF_HOOK_PATHS = frozenset(f"${{CLAUDE_PROJECT_DIR}}/.claude/hooks/{s}" for s in HOOK_SCRIPTS)

# validate.py imports PyYAML to parse frontmatter; a scaffolded project declares it
# so the dependency is explicit, not discovered via a traceback. Mirrors the skill's
# own requirements.txt.
REQUIREMENTS_TXT = (
    "# The validator (scripts/validate.py) parses YAML frontmatter with PyYAML.\n"
    "PyYAML>=5.1\n"
)


def slugify(name: str) -> str:
    return "-".join("".join(c if c.isalnum() else " " for c in name.lower()).split())


def write_if_absent(path: Path, content: str, preserved: list[Path]) -> None:
    """Write content unless the file already exists. On --force into a populated
    directory an existing file is the user's own, so preserve it instead of
    clobbering it with a generic template. On a fresh scaffold nothing exists, so
    every file is written as before."""
    if path.exists():
        preserved.append(path)
        return
    path.write_text(content, encoding="utf-8")


def copy_if_absent(src: Path, dst: Path, preserved: list[Path]) -> None:
    """copy2 src to dst unless dst exists (see write_if_absent for the rationale)."""
    if dst.exists():
        preserved.append(dst)
        return
    shutil.copy2(src, dst)


def root_index(title: str, sections: list[str]) -> str:
    nav = "\n".join(f"- [{s}]({s}/index.md)" for s in sections)
    return (
        '---\nokf_version: "0.2"\n---\n'
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
        "## Requirements\n\n"
        "The validator parses YAML frontmatter with PyYAML:\n\n"
        "```bash\n"
        "pip install -r requirements.txt    # or: pip install pyyaml\n"
        "```\n\n"
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

    The hook scripts are cross-platform python3; only the interpreter changes per OS
    (python3 on macOS/Linux, python on Windows). Each hook uses exec form -- the
    interpreter as `command` and the script path as a single `args` element -- which
    Claude Code spawns directly with no shell, so a project path with spaces or other
    special characters needs no quoting (the hooks docs recommend exec form for any
    hook that references a path placeholder). The path uses the ${CLAUDE_PROJECT_DIR}
    placeholder so it resolves even when the hook cwd has drifted from the project
    root, and stays correct when the bundle is cloned to another path -- unlike a
    baked-in absolute path. PreToolUse omits a matcher so it sees the first tool call
    of any kind.
    """
    interp = interpreter_for(hooks_os)

    def cmd(script: str) -> dict:
        path = f"${{CLAUDE_PROJECT_DIR}}/.claude/hooks/{script}"
        # exec form: the script path is one args element, spawned with no shell, so a
        # project path with spaces or special characters needs no quoting.
        return {"type": "command", "command": interp, "args": [path]}

    return {
        "hooks": {
            "SessionStart": [{"hooks": [cmd("okf-anchor.py")]}],
            "PreToolUse": [{"hooks": [cmd("okf-orient.py")]}],
        }
    }


def _is_okf_hook(h: dict) -> bool:
    """True if a hook entry launches one of the OKF orientation scripts we generate.

    We match the exact project-local path we write (`${CLAUDE_PROJECT_DIR}/.claude/
    hooks/<script>`), found either as an exec-form `args` element or, after shlex-
    splitting, as a token of a shell-form `command` string. Exact matching against
    OKF_HOOK_PATHS -- not a suffix or substring test -- means a re-run replaces only
    our own entries and never a user's hook that merely ends in the same filename
    (`okf-anchor.py.bak`) or sits at a different absolute path. The check is total: any
    hook shape returns a bool and never raises, so a malformed entry (e.g. a non-list
    `args`) is simply judged "not ours" and left in place rather than crashing --force.
    """
    args = h.get("args")
    tokens = list(args) if isinstance(args, (list, tuple)) else []
    cmd = h.get("command")
    if isinstance(cmd, str):
        try:
            tokens.extend(shlex.split(cmd))
        except ValueError:
            pass  # unbalanced quotes: nothing we generate parses to this
    return any(str(t) in OKF_HOOK_PATHS for t in tokens)


def merge_hook_settings(existing: dict, new: dict) -> dict:
    """Merge our hook groups into existing settings without losing anything recoverable.

    Every top-level key (e.g. permissions) and every unrelated hook event is preserved.
    Within an event we register, only our own hook entries are stripped: a group that
    also holds the user's hooks keeps them, and a group is dropped only when it empties.
    Then our fresh group is appended, so a re-run is idempotent and never deletes a
    user's hook that shared a group with ours. The function is total -- a non-dict
    `hooks`, a non-list event value, or a malformed group/entry holds no mergeable hook
    config and is treated as empty, so no input shape raises. write_claude_hooks backs
    up the original first when it had to reset such a malformed subtree.
    """
    merged = dict(existing)
    eh = merged.get("hooks")
    hooks = dict(eh) if isinstance(eh, dict) else {}
    for event, groups in new["hooks"].items():
        prior = hooks.get(event)
        prior = prior if isinstance(prior, list) else []
        kept = []
        for g in prior:
            inner = g.get("hooks") if isinstance(g, dict) else None
            if not isinstance(inner, list):
                kept.append(g)  # a shape we don't manage -- leave it untouched
                continue
            remaining = [h for h in inner if not (isinstance(h, dict) and _is_okf_hook(h))]
            if len(remaining) == len(inner):
                kept.append(g)                          # no OKF hooks here
            elif remaining:
                kept.append({**g, "hooks": remaining})  # keep the user's hooks
            # else: the group held only our hooks -- drop it
        hooks[event] = kept + list(groups)
    merged["hooks"] = hooks
    return merged


def write_claude_hooks(target: Path, hooks_os: str) -> None:
    """Copy the hook scripts into target/.claude/hooks and write settings.json.

    If settings.json already exists (e.g. --force into a project that already uses
    Claude Code), merge the OKF hooks into it rather than overwriting: the user's other
    settings and hook events survive, and re-running replaces only our own entries. A
    file that is not a JSON object at all is backed up to settings.json.bak and replaced.
    A JSON object whose hook subtree is malformed is repaired in place -- unrelated keys
    stay in the live file and the original is copied to settings.json.bak first, so the
    malformed copy is still recoverable.
    """
    hooks_dir = target / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    for script in HOOK_SCRIPTS:
        dest = hooks_dir / script
        shutil.copy2(SRC_HOOKS / script, dest)
        # make executable for the shebang case; exec form also names the interpreter
        # explicitly, so this is belt-and-suspenders.
        dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = target / ".claude" / "settings.json"
    new_settings = claude_settings(hooks_os)
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            existing = None
        if isinstance(existing, dict):
            # The merge preserves every top-level key and unrelated event. If the hook
            # subtree itself is malformed (hooks not an object, or an event we write into
            # not a list), the merge resets just that subtree -- so copy the original to
            # .bak first to keep the malformed version recoverable, then merge in place so
            # unrelated settings (e.g. permissions) stay in the live file.
            existing_hooks = existing.get("hooks")
            clean = (existing_hooks is None or isinstance(existing_hooks, dict)) and (
                existing_hooks is None or all(
                    isinstance(existing_hooks.get(ev), (list, type(None)))
                    for ev in new_settings["hooks"]
                )
            )
            if not clean:
                backup = settings_path.with_name(settings_path.name + ".bak")
                shutil.copy2(settings_path, backup)
                print(f"warning: {settings_path.name} had malformed hook settings; "
                      f"repaired in place, original backed up to {backup.name}", file=sys.stderr)
            new_settings = merge_hook_settings(existing, new_settings)
        else:
            backup = settings_path.with_name(settings_path.name + ".bak")
            settings_path.replace(backup)
            print(f"warning: existing {settings_path.name} could not be merged "
                  f"(not a JSON object); backed up to {backup.name}", file=sys.stderr)
    settings_path.write_text(json.dumps(new_settings, indent=2) + "\n", encoding="utf-8")


def _canonical_req_name(line: str) -> str | None:
    """The PEP 503-normalized distribution name a requirements.txt line pins, or None
    when the line names no installable package (blank, comment, option, URL, or path).
    Used only to spot whether PyYAML is declared, so it is a name sniffer, not a full
    requirements parser."""
    s = line.split("#", 1)[0].strip()  # drop full-line and inline comments
    if not s or s.startswith("-") or s.startswith("."):
        return None  # option/include (-r, -e, ...) or a local path, not a bare name
    # The project name is the leading token, ending at the first version specifier,
    # marker, extras bracket, whitespace, or "@" direct-reference separator.
    name = re.split(r"[<>=!~;,@\[ (]", s, maxsplit=1)[0].strip()
    if not name or "://" in name or "/" in name:
        return None  # a bare URL or path names no distribution we can normalize
    return re.sub(r"[-_.]+", "-", name).lower()


def _preserved_requirements_lacks_pyyaml(path: Path) -> bool:
    """True only when we can say with confidence that a preserved requirements.txt does
    not declare PyYAML: it is readable, no line names PyYAML, and it carries no include or
    editable directive (-r, -e) that could pull PyYAML from a file we do not read. An
    unreadable file or such a directive returns False, so the targeted warning fires only
    when the gap is certain and never nags a user who did declare it. A constraint file
    (-c/--constraint) only pins versions of packages installed elsewhere and cannot supply
    a missing one, so it does not suppress the note."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    for raw in text.splitlines():
        s = raw.strip()
        if s.startswith(("-r", "--requirement", "-e", "--editable")):
            return False  # PyYAML may live in the included (-r) or editable (-e) target
        if _canonical_req_name(raw) == "pyyaml":
            return False
    return True


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

    # Skip-if-exists so --force into a populated directory never overwrites a user's
    # own SPEC.md/README.md/validator/bundle content with a generic template. (A
    # fresh scaffold has none of these, so all are written.) The .claude/ hooks are
    # stateless machinery, refreshed in place; settings.json is merged with backup.
    preserved: list[Path] = []
    copy_if_absent(SRC_SPEC, target / "SPEC.md", preserved)
    copy_if_absent(SRC_VALIDATOR, target / "scripts" / "validate.py", preserved)
    write_if_absent(target / "requirements.txt", REQUIREMENTS_TXT, preserved)
    write_if_absent(target / "README.md",
                    readme(title, write_hooks, interpreter_for(hooks_os)), preserved)
    write_if_absent(bundle / "index.md", root_index(title, sections), preserved)
    for s in sections:
        sdir = bundle / s
        sdir.mkdir(parents=True, exist_ok=True)
        write_if_absent(sdir / "index.md", section_index(s), preserved)
        write_if_absent(sdir / "example-concept.md", example_concept(today), preserved)
    if write_hooks:
        write_claude_hooks(target, hooks_os)

    print(f"Scaffolded OKF project at {target}")
    print(f"  title: {title}")
    print(f"  sections: {', '.join(sections)}")
    if write_hooks:
        print(f"  hooks: .claude/ written for {hooks_os} (Claude Code asks you to approve them on first open)")
    else:
        print("  hooks: skipped (--no-hooks)")
    if preserved:
        rels = ", ".join(str(p.relative_to(target)) for p in sorted(preserved))
        print(f"  preserved {len(preserved)} existing file(s), not overwritten: {rels}")
        print("  (delete a file and re-run to regenerate it from the template)")

    if args.no_validate:
        return 0

    # The "validates by construction" guarantee only holds when the scaffold wrote
    # everything fresh. Once --force preserves any existing file, the result is not
    # guaranteed valid, and scripts/validate.py and bundle/index.md may themselves be
    # the user's own preserved files -- so running validation here could execute an
    # unrelated preserved validator or blame the scaffold for preserved user content.
    # Skip it and tell the user to validate when they have reconciled their files.
    if preserved:
        print("\nScaffold written, but skipping validation: existing files were "
              "preserved, so the bundle is not guaranteed valid by construction and "
              "scripts/validate.py may be your own.", file=sys.stderr)
        # A preserved requirements.txt is the user's own (#142), so we never edit it. But
        # if it omits PyYAML, the validate step below fails with ModuleNotFoundError, so
        # name the exact dependency here rather than leaving them to decode the traceback.
        req = target / "requirements.txt"
        if req in preserved and _preserved_requirements_lacks_pyyaml(req):
            print("  note: the preserved requirements.txt does not list PyYAML, which "
                  "scripts/validate.py imports. Add PyYAML>=5.1 to it (or run "
                  "`pip install pyyaml`) before validating. Without it, validation "
                  "fails with ModuleNotFoundError.", file=sys.stderr)
        print("  reconcile the preserved files, then validate when ready:", file=sys.stderr)
        print(f"    cd {target} && {interpreter_for(hooks_os)} scripts/validate.py --bundle bundle", file=sys.stderr)
        return 0

    # validate.py runs under this same interpreter, so its `import yaml` succeeds
    # only if PyYAML is findable here. Check first: an absent dependency is a setup
    # gap, not a scaffold bug, and the scaffold itself succeeded. Report it plainly
    # and exit 0 rather than letting the subprocess traceback be mislabeled below.
    if importlib.util.find_spec("yaml") is None:
        print("\nScaffold written, but skipping validation: PyYAML is not installed "
              "for this interpreter.", file=sys.stderr)
        print("  install it, then validate:", file=sys.stderr)
        print("    pip install -r requirements.txt    # or: pip install pyyaml", file=sys.stderr)
        print(f"    cd {target} && {interpreter_for(hooks_os)} scripts/validate.py --bundle bundle", file=sys.stderr)
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
