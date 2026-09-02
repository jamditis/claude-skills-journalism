#!/usr/bin/env python3
"""Create Cloudflare Drop, review, design-assets, source, and full-handoff ZIPs."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from _common import deterministic_zip, format_bytes, load_project, utc_now, write_checksum, write_json, write_text

EXCLUDE_NAMES = {".DS_Store", "Thumbs.db", "__pycache__", ".git", "node_modules"}


def copy_tree(source: Path, destination: Path) -> None:
    if source.exists():
        shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(*EXCLUDE_NAMES))


def remove_archives(root: Path) -> list[str]:
    removed = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".zip", ".7z", ".rar"}:
            removed.append(path.relative_to(root).as_posix())
            path.unlink()
    return removed


def inspect_zip(zip_path: Path, *, require_root_index: bool, max_file_bytes: int | None = None) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP CRC failure: {bad}")
        names = archive.namelist()
        unsafe = [name for name in names if Path(name).is_absolute() or ".." in Path(name).parts]
        if unsafe:
            raise RuntimeError(f"Unsafe ZIP entries: {unsafe[:5]}")
        if require_root_index and (not names or names[0] != "index.html" or "index.html" not in names):
            raise RuntimeError(f"{zip_path.name} must contain index.html at archive root and write it first")
        nested = [name for name in names if Path(name).suffix.lower() in {".zip", ".7z", ".rar"}]
        oversize = []
        if max_file_bytes:
            oversize = [{"path": item.filename, "bytes": item.file_size} for item in archive.infolist() if item.file_size > max_file_bytes]
        return {
            "entries": len(names),
            "first_entry": names[0] if names else None,
            "root_index": "index.html" in names,
            "nested_archives": nested,
            "oversize_files": oversize,
        }


def validate_extracted(zip_path: Path, project_root: Path, *, cloudflare: bool) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="web-design-picker-validation-") as temp:
        extracted = Path(temp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extracted)
        report_path = project_root / "qa" / f"{zip_path.stem}-validation.json"
        log_path = project_root / "qa" / f"{zip_path.stem}-validation.txt"
        command = [
            sys.executable,
            str(Path(__file__).with_name("validate_site.py")),
            str(extracted),
            "--report-json",
            str(report_path),
        ]
        if cloudflare:
            command.append("--cloudflare")
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log_path.write_text(result.stdout, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"Static validation failed for {zip_path.name}; see {log_path}")
        return {"report": str(report_path), "log": str(log_path)}


def stage_source(root: Path, destination: Path) -> None:
    for name in ["config", "src", "design-package"]:
        copy_tree(root / name, destination / name)
    for name in ["BRIEF.md", "CLAIM-LEDGER.md", "DIRECTION-BRIEFS.md", "README.md"]:
        source = root / name
        if source.exists():
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination / name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument("--max-file-bytes", type=int, default=25_000_000, help="Conservative per-file Drop limit used by the packager")
    args = parser.parse_args()

    root = args.project_dir.resolve()
    project, _, _ = load_project(root)
    dist = root / "dist"
    if not (dist / "index.html").is_file():
        print("error: build the site before packaging", file=sys.stderr)
        return 1

    deliverables = root / "deliverables"
    deliverables.mkdir(parents=True, exist_ok=True)
    for stale in deliverables.glob("*.zip*"):
        stale.unlink()
    qa = root / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    slug = project["slug"]
    results: dict[str, Any] = {"project": project["name"], "slug": slug, "generated_at": utc_now(), "packages": {}}

    try:
        with tempfile.TemporaryDirectory(prefix="web-design-picker-stage-") as temp:
            temp_root = Path(temp)
            drop_stage = temp_root / "drop-site"
            review_stage = temp_root / "review-site"
            design_stage = temp_root / f"{slug}-design-assets"
            source_stage = temp_root / f"{slug}-source-project"
            handoff_stage = temp_root / f"{slug}-website-design-handoff"

            copy_tree(dist, drop_stage)
            copy_tree(dist, review_stage)
            copy_tree(root / "design-package", design_stage)
            stage_source(root, source_stage)

            removed = remove_archives(drop_stage)
            if removed:
                print("Removed nested archive(s) from Drop stage: " + ", ".join(removed))

            drop_zip = deliverables / f"{slug}-cloudflare-drop.zip"
            drop_result = deterministic_zip(drop_stage, drop_zip, include_root=False, exclude_names=EXCLUDE_NAMES, allow_zip64=False)
            drop_result["inspection"] = inspect_zip(drop_zip, require_root_index=True, max_file_bytes=args.max_file_bytes)
            if drop_result["inspection"]["nested_archives"]:
                raise RuntimeError("Cloudflare Drop package contains a nested archive")
            if drop_result["inspection"]["oversize_files"]:
                raise RuntimeError(f"Cloudflare Drop package contains files above {args.max_file_bytes} bytes")
            write_checksum(drop_zip)
            results["packages"]["cloudflare_drop"] = drop_result

            review_zip = deliverables / f"{slug}-review-site.zip"
            review_result = deterministic_zip(review_stage, review_zip, include_root=False, exclude_names=EXCLUDE_NAMES, allow_zip64=False)
            review_result["inspection"] = inspect_zip(review_zip, require_root_index=True)
            write_checksum(review_zip)
            results["packages"]["review_site"] = review_result

            design_zip = deliverables / f"{slug}-design-assets.zip"
            design_result = deterministic_zip(design_stage, design_zip, include_root=True, exclude_names=EXCLUDE_NAMES, allow_zip64=False)
            design_result["inspection"] = inspect_zip(design_zip, require_root_index=False)
            write_checksum(design_zip)
            results["packages"]["design_assets"] = design_result

            source_zip = deliverables / f"{slug}-source-project.zip"
            source_result = deterministic_zip(source_stage, source_zip, include_root=True, exclude_names=EXCLUDE_NAMES, allow_zip64=False)
            source_result["inspection"] = inspect_zip(source_zip, require_root_index=False)
            write_checksum(source_zip)
            results["packages"]["source_project"] = source_result

            # Full handoff contains expanded folders, not a ZIP-inside-ZIP deployment trap.
            copy_tree(dist, handoff_stage / "site")
            copy_tree(root / "design-package", handoff_stage / "design-assets")
            stage_source(root, handoff_stage / "source")
            copy_tree(root / "previews", handoff_stage / "previews")
            copy_tree(root / "qa", handoff_stage / "qa")
            write_text(
                handoff_stage / "DELIVERY-README.txt",
                f"""{project['name']} website design handoff

site/                Combined picker, standalone directions, and asset catalog
design-assets/       Editable and export-ready assets
source/              Project manifests, source concepts, and working documents
previews/            Desktop and mobile QA screenshots
qa/                  Validation and browser reports

Upload `{slug}-cloudflare-drop.zip` from the separate deliverables folder to Cloudflare Drop. Do not upload this full handoff ZIP as the site.
The asset catalog builds family and all-assets ZIPs in the browser from static files; the Drop package itself contains no nested ZIP.
""",
            )
            handoff_zip = deliverables / f"{slug}-website-design-handoff.zip"
            handoff_result = deterministic_zip(handoff_stage, handoff_zip, include_root=True, exclude_names=EXCLUDE_NAMES, allow_zip64=True)
            handoff_result["inspection"] = inspect_zip(handoff_zip, require_root_index=False)
            write_checksum(handoff_zip)
            results["packages"]["full_handoff"] = handoff_result

            if not args.skip_validation:
                results["packages"]["cloudflare_drop"]["validation"] = validate_extracted(drop_zip, root, cloudflare=True)
                results["packages"]["review_site"]["validation"] = validate_extracted(review_zip, root, cloudflare=False)

    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    manifest_path = deliverables / "delivery-manifest.json"
    write_json(manifest_path, results)
    print(f"Created delivery packages in {deliverables}")
    for key, info in results["packages"].items():
        print(f"{key:18} {Path(info['path']).name:52} {format_bytes(info['size_bytes'])}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
