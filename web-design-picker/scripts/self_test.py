#!/usr/bin/env python3
"""Exercise the skill's scaffold, build, validation, and packaging pipeline."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from _common import copy_contents, deterministic_zip, read_json, relative_web_path, utc_now, validate_slug, write_json
from build_picker import ensure_direction_metadata, relative_from_page
from package_delivery import copy_tree
from validate_site import check_html


def run(command: list[str]) -> None:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0:
        raise RuntimeError("Command failed: " + " ".join(command))


def check_path_helpers() -> None:
    try:
        validate_slug("../../outside")
    except ValueError:
        pass
    else:
        raise RuntimeError("Unsafe project slug was accepted")
    if relative_web_path("concepts\\example.html") != "concepts/example.html":
        raise RuntimeError("Relative static paths must normalize to forward slashes")
    if relative_from_page("assets/brand/example/favicon.svg", "concepts/example.html") != "../assets/brand/example/favicon.svg":
        raise RuntimeError("Relative browser paths must use forward slashes")
    for unsafe in ("/absolute.html", "C:\\absolute.html", "../outside.html", "folder/../outside.html"):
        try:
            relative_web_path(unsafe)
        except ValueError:
            continue
        raise RuntimeError(f"Unsafe static path was accepted: {unsafe}")


def check_symlink_guards(parent: Path) -> None:
    """Delivery staging must reject links before copying external content."""
    with tempfile.TemporaryDirectory(prefix="web-design-picker-symlink-", dir=parent) as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        external = root / "outside.txt"
        external.write_text("outside\n", encoding="utf-8")
        link = source / "external.txt"
        try:
            link.symlink_to(external)
        except OSError as exc:
            raise RuntimeError("Could not create the symlink security fixture") from exc

        for copy, name in ((copy_contents, "contents"), (copy_tree, "tree")):
            destination = root / f"{name}-stage"
            try:
                copy(source, destination)
            except ValueError:
                pass
            else:
                raise RuntimeError(f"Symlinked source was copied by {name} staging")
            if destination.exists():
                raise RuntimeError(f"{name} staging created output before rejecting a symlink")


def check_source_map_guard(parent: Path) -> None:
    """Delivery archives must reject nested source maps before writing output."""
    with tempfile.TemporaryDirectory(prefix="web-design-picker-source-map-", dir=parent) as temporary:
        root = Path(temporary)
        source = root / "source" / "nested"
        source.mkdir(parents=True)
        (source / "app.MAP").write_text("source map fixture\n", encoding="utf-8")
        output = root / "delivery.zip"
        try:
            deterministic_zip(root / "source", output)
        except ValueError as exc:
            if "Source map files" not in str(exc):
                raise RuntimeError("Source map guard raised an unexpected error") from exc
        else:
            raise RuntimeError("Source map was accepted into a delivery archive")
        if output.exists():
            raise RuntimeError("Source map guard wrote a delivery archive")


def check_favicon_metadata_variants(parent: Path) -> None:
    """Every required favicon variant must survive one-off authored icons."""
    with tempfile.TemporaryDirectory(prefix="web-design-picker-favicon-", dir=parent) as temporary:
        root = Path(temporary)
        page = root / "concepts" / "first.html"
        page.parent.mkdir(parents=True)
        page.write_text(
            '<!doctype html><html><head><link rel="icon" href="authored-icon.svg"></head><body></body></html>',
            encoding="utf-8",
        )
        direction = {"key": "first", "file": "concepts/first.html"}
        ensure_direction_metadata(root, direction)
        ensure_direction_metadata(root, direction)
        rendered = page.read_text(encoding="utf-8")
        expected = (
            "../assets/brand/first/favicon.svg",
            "../assets/brand/first/favicon.ico",
            "../assets/brand/first/favicon-180.png",
        )
        if any(rendered.count(href) != 1 for href in expected):
            raise RuntimeError("Required favicon variants were missing or duplicated")
        if rendered.count("authored-icon.svg") != 1:
            raise RuntimeError("Authored favicon link was unexpectedly changed")


def check_aria_labelledby_controls(parent: Path) -> None:
    """Skipped controls must not be checked for labels or label references."""
    with tempfile.TemporaryDirectory(prefix="web-design-picker-aria-", dir=parent) as temporary:
        root = Path(temporary)
        page = root / "index.html"
        page.write_text(
            '<!doctype html><html lang="en"><head><title>Fixture</title><meta name="viewport" content="width=device-width"><link rel="icon" href="data:,x"></head><body><h1>Fixture</h1><input type="hidden" aria-labelledby="missing-hidden"><input aria-labelledby="missing-visible"></body></html>',
            encoding="utf-8",
        )
        findings = []
        check_html(root, page, findings, allow_external=False)
        labelled_by = [finding for finding in findings if finding.code == "aria-labelledby"]
        if len(labelled_by) != 1 or "missing-visible" not in labelled_by[0].message:
            raise RuntimeError("aria-labelledby validation did not reject the visible control correctly")
        if any("missing-hidden" in finding.message for finding in findings):
            raise RuntimeError("Hidden control was checked for aria-labelledby")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, help="Keep the generated test project at this location")
    parser.add_argument("--browser", action="store_true", help="Also run Playwright browser QA")
    args = parser.parse_args()

    check_path_helpers()

    scripts = Path(__file__).resolve().parent
    temporary = None
    if args.work_dir:
        project = args.work_dir.resolve()
        if project.exists():
            shutil.rmtree(project)
    else:
        temporary = tempfile.TemporaryDirectory(prefix="web-design-picker-selftest-")
        project = Path(temporary.name) / "project"

    try:
        project.parent.mkdir(parents=True, exist_ok=True)
        check_symlink_guards(project.parent)
        check_source_map_guard(project.parent)
        check_favicon_metadata_variants(project.parent)
        check_aria_labelledby_controls(project.parent)
        with tempfile.TemporaryDirectory(prefix="web-design-picker-slug-guard-", dir=project.parent) as guard_dir:
            slug_guard = Path(guard_dir)
            marker = slug_guard / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")
            invalid_slug = subprocess.run(
                [
                    sys.executable,
                    str(scripts / "new_project.py"),
                    str(slug_guard),
                    "--name",
                    "Invalid slug guard",
                    "--slug",
                    "../outside",
                    "--force",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if invalid_slug.returncode == 0 or not marker.is_file():
                raise RuntimeError("Invalid slug validation modified the target project")

        run([sys.executable, str(scripts / "new_project.py"), str(project), "--name", "Factory self-test", "--directions", "3"])

        assets_path = project / "config/assets.json"
        assets = read_json(assets_path)
        original_assets = json.loads(json.dumps(assets))
        assets["shared"].append({
            "title": "Unsafe path fixture",
            "files": [{"label": "Outside", "href": "../outside.txt"}],
        })
        write_json(assets_path, assets)
        unsafe_asset = subprocess.run(
            [sys.executable, str(scripts / "build_picker.py"), str(project)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if unsafe_asset.returncode == 0 or "Traceback" in unsafe_asset.stdout:
            raise RuntimeError("Unsafe asset path did not produce a clean validation error")
        write_json(assets_path, original_assets)

        distinctness_path = project / "config/distinctness.json"
        distinctness = read_json(distinctness_path)
        for pair in distinctness["pairs"]:
            pair["scores"] = {dimension: 2 for dimension in distinctness["dimensions"]}
            pair["notes"] = "Synthetic self-test score; not a design judgment."
        write_json(distinctness_path, distinctness)

        run([sys.executable, str(scripts / "build_picker.py"), str(project)])
        run([
            sys.executable,
            str(scripts / "validate_site.py"),
            str(project / "dist"),
            "--manifest",
            str(project / "config/assets.json"),
            "--cloudflare",
            "--strict",
            "--report-json",
            str(project / "qa/static-validation.json"),
        ])
        run([sys.executable, str(scripts / "check_distinctness.py"), str(project), "--strict"])
        run([sys.executable, str(scripts / "slop_lint.py"), str(project / "dist"), "--fail-on-findings"])
        if args.browser:
            run([sys.executable, str(scripts / "browser_qa.py"), str(project), "--test-downloads"])
        run([sys.executable, str(scripts / "package_delivery.py"), str(project)])

        drop_zip = project / "deliverables/factory-self-test-cloudflare-drop.zip"
        with zipfile.ZipFile(drop_zip) as archive:
            names = archive.namelist()
            if not names or names[0] != "index.html":
                raise RuntimeError("Drop ZIP does not begin with root index.html")
            if archive.testzip():
                raise RuntimeError("Drop ZIP has a CRC error")
            if any(Path(name).suffix.lower() == ".zip" for name in names):
                raise RuntimeError("Drop ZIP contains a nested ZIP")

        design_zip = project / "deliverables/factory-self-test-design-assets.zip"
        with zipfile.ZipFile(design_zip) as archive:
            manifest_name = "factory-self-test-design-assets/asset-manifest.json"
            if manifest_name not in archive.namelist():
                raise RuntimeError("Design-assets ZIP omits the generated asset manifest")

        report = {
            "generated_at": utc_now(),
            "passed": True,
            "project": str(project),
            "browser_tested": args.browser,
            "drop_zip": str(drop_zip),
            "drop_entries": len(names),
        }
        write_json(project / "qa/self-test.json", report)
        print(json.dumps(report, indent=2))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if temporary:
            temporary.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
