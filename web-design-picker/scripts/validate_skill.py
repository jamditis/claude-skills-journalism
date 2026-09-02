#!/usr/bin/env python3
"""Validate an Agent Skill package and compile its Python helpers."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required to validate skill frontmatter") from exc

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must begin with YAML frontmatter at byte 0")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter closing delimiter not found")
    data = yaml.safe_load(text[4:end])
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a YAML mapping")
    return data, text[end + 5 :]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path, nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()

    root = args.skill_dir.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    skill_file = root / "SKILL.md"
    if not skill_file.exists():
        errors.append("SKILL.md is missing")
        metadata: dict[str, Any] = {}
        body = ""
    else:
        text = skill_file.read_text(encoding="utf-8")
        try:
            metadata, body = parse_frontmatter(text)
        except Exception as exc:
            errors.append(str(exc))
            metadata, body = {}, ""

    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        errors.append("frontmatter name must use lowercase letters, digits, and single hyphens")
    elif name != root.name:
        errors.append(f"frontmatter name {name!r} must match parent directory {root.name!r}")
    if not isinstance(description, str) or not description.strip():
        errors.append("frontmatter description is required")
    elif len(description) > 1024:
        errors.append("frontmatter description exceeds 1024 characters")
    compatibility = metadata.get("compatibility")
    if compatibility is not None and (not isinstance(compatibility, str) or len(compatibility) > 500):
        errors.append("compatibility must be a string no longer than 500 characters")

    if skill_file.exists():
        line_count = len(skill_file.read_text(encoding="utf-8").splitlines())
        if line_count > 500:
            warnings.append(f"SKILL.md has {line_count} lines; progressive disclosure recommends fewer than 500")
        for target in LINK_RE.findall(body):
            if "://" in target or target.startswith("#"):
                continue
            target_path = (root / target.split("#", 1)[0]).resolve()
            try:
                target_path.relative_to(root)
            except ValueError:
                errors.append(f"SKILL.md link leaves skill root: {target}")
                continue
            if not target_path.exists():
                errors.append(f"SKILL.md link target missing: {target}")

    manifest = root / "manifest.txt"
    actual_files = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path.name != "manifest.txt" and "__pycache__" not in path.parts and path.suffix != ".pyc")
    if manifest.exists():
        listed = [line.strip() for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        if listed != sorted(set(listed)):
            warnings.append("manifest.txt is not sorted or contains duplicates")
        missing = sorted(set(actual_files) - set(listed))
        extra = sorted(set(listed) - set(actual_files))
        if missing:
            errors.append(f"manifest.txt omits: {', '.join(missing)}")
        if extra:
            errors.append(f"manifest.txt lists missing files: {', '.join(extra)}")
    python_files = sorted((root / "scripts").glob("*.py"))
    if python_files:
        with tempfile.TemporaryDirectory(prefix="web-design-picker-pyc-") as pycache:
            env = dict(os.environ)
            env["PYTHONPYCACHEPREFIX"] = pycache
            result = subprocess.run([sys.executable, "-m", "py_compile", *map(str, python_files)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        if result.returncode != 0:
            errors.append(f"Python compile failure:\n{result.stderr.strip()}")

    report = {
        "skill": name,
        "root": str(root),
        "errors": errors,
        "warnings": warnings,
        "file_count": len(actual_files) + (1 if manifest.exists() else 0),
        "python_scripts": len(python_files),
    }
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"Skill: {name or '(unknown)'}")
    for error in errors:
        print(f"ERROR   {error}")
    for warning in warnings:
        print(f"WARNING {warning}")
    print(f"Files: {report['file_count']} | Python scripts: {report['python_scripts']}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
