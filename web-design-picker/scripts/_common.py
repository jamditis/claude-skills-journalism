#!/usr/bin/env python3
"""Shared helpers for the web-design-picker skill."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
ALREADY_COMPRESSED = {
    ".7z", ".avif", ".gif", ".gz", ".ico", ".jpeg", ".jpg", ".mov",
    ".mp3", ".mp4", ".pdf", ".png", ".webm", ".webp", ".zip",
}
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "website-project"


def validate_slug(value: str) -> str:
    if not isinstance(value, str) or not SLUG_PATTERN.fullmatch(value):
        raise ValueError("Slug must contain lowercase letters, numbers, and single hyphens only")
    return value


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Required JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def format_bytes(size: int) -> str:
    units = ["B", "KiB", "MiB", "GiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024
    return f"{size} B"


def copy_contents(source: Path, destination: Path, *, overwrite: bool = True) -> None:
    reject_symlinks(source)
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        elif overwrite or not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def reject_symlinks(root: Path, *, exclude_names: set[str] | None = None) -> None:
    """Fail before copying a tree that could follow an external link."""
    exclude_names = exclude_names or set()
    if root.is_symlink():
        raise ValueError(f"Symlinks are not allowed in delivery packages: {root}")
    if not root.exists():
        return
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in exclude_names for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in delivery packages: {path}")


def safe_archive_path(relative_path: Path) -> str:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe archive path: {relative_path}")
    return relative_path.as_posix()


def iter_files(root: Path, *, exclude_names: set[str] | None = None) -> Iterable[Path]:
    exclude_names = exclude_names or set()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not allowed in delivery packages: {path}")
        if path.is_file() and not any(part in exclude_names for part in path.parts):
            yield path


def _zip_order(path: Path, root: Path) -> tuple[int, str]:
    relative = path.relative_to(root).as_posix()
    # Static hosts are happiest when the entry point is obvious and first.
    return (0 if relative == "index.html" else 1, relative)


def deterministic_zip(
    source_dir: Path,
    output_zip: Path,
    *,
    include_root: bool = False,
    exclude_suffixes: tuple[str, ...] = (),
    exclude_names: set[str] | None = None,
    allow_zip64: bool = False,
) -> dict[str, Any]:
    """Create a deterministic, portable ZIP and test its CRCs.

    Media that is already compressed is stored rather than recompressed. The
    root index is written first when present. ZIP64 is disabled by default so a
    package that silently exceeds conservative static-host limits fails loudly.
    """
    source_dir = source_dir.resolve()
    source_files = list(iter_files(source_dir, exclude_names=exclude_names))
    source_maps = [path.relative_to(source_dir).as_posix() for path in source_files if path.suffix.lower() == ".map"]
    if source_maps:
        raise ValueError(f"Source map files are not allowed in delivery archives: {', '.join(source_maps)}")

    files = [
        path for path in source_files
        if not (exclude_suffixes and path.name.lower().endswith(exclude_suffixes))
    ]
    files.sort(key=lambda path: _zip_order(path, source_dir))

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    output_zip.unlink(missing_ok=True)

    with zipfile.ZipFile(output_zip, "w", allowZip64=allow_zip64) as archive:
        for path in files:
            relative = path.relative_to(source_dir)
            if include_root:
                relative = Path(source_dir.name) / relative
            arcname = safe_archive_path(relative)
            info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
            info.create_system = 0
            info.external_attr = 0o100644 << 16
            compression = zipfile.ZIP_STORED if path.suffix.lower() in ALREADY_COMPRESSED else zipfile.ZIP_DEFLATED
            info.compress_type = compression
            archive.writestr(info, path.read_bytes(), compress_type=compression, compresslevel=9)

    with zipfile.ZipFile(output_zip, "r") as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity check failed at {bad}")
        names = archive.namelist()

    return {
        "path": str(output_zip),
        "file_count": len(files),
        "size_bytes": output_zip.stat().st_size,
        "sha256": sha256_file(output_zip),
        "entries": names,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def temporary_directory(prefix: str = "web-design-picker-"):
    return tempfile.TemporaryDirectory(prefix=prefix)


def replace_tokens(template: str, replacements: dict[str, str]) -> str:
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"__{key}__", value)
    missing = sorted(set(re.findall(r"__[A-Z0-9_]+__", rendered)))
    if missing:
        raise ValueError(f"Unreplaced template tokens: {', '.join(missing)}")
    return rendered


def ensure_clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def load_project(project_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    project_root = project_root.resolve()
    config = project_root / "config"
    project = read_json(config / "project.json")
    directions = read_json(config / "directions.json")
    assets = read_json(config / "assets.json")
    if not isinstance(project, dict):
        raise SystemExit("project.json must contain a JSON object")
    try:
        validate_slug(project.get("slug"))
    except ValueError as exc:
        raise SystemExit(f"project.json has an invalid slug: {exc}") from exc
    if not isinstance(directions, list) or not 2 <= len(directions) <= 5:
        raise SystemExit("directions.json must contain two to five directions")
    if not isinstance(assets, dict):
        raise SystemExit("assets.json must contain a JSON object")
    return project, directions, assets


def relative_web_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    parts = normalized.split("/")
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[a-zA-Z]:", normalized)
        or ".." in parts
    ):
        raise ValueError(f"Path must stay inside the static site: {path}")
    return normalized


def write_checksum(path: Path) -> Path:
    checksum_path = path.with_suffix(path.suffix + ".sha256.txt")
    checksum_path.write_text(f"{sha256_file(path)}  {path.name}\n", encoding="utf-8")
    return checksum_path
