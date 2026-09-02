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

import new_project
from _common import copy_contents, deterministic_zip, read_json, relative_web_path, utc_now, validate_output_stem, validate_slug, write_json
from build_picker import ensure_direction_metadata, relative_from_page
from make_asset_variants import main as make_asset_variants_main, render_svg as render_variant_svg
from make_palette import main as make_palette_main
from optimize_video import main as optimize_video_main
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


def check_output_stem_guards(parent: Path) -> None:
    """Output names must stay single portable file stems before any writes."""
    for safe in ("palette", "brand.v2", "logo_01", "hero-image"):
        if validate_output_stem(safe) != safe:
            raise RuntimeError(f"Safe output name was changed: {safe}")
    for unsafe in (".", "..", "../outside", "nested/name", "C:\\outside", "name.", "name ", "CON", "lpt9.txt"):
        try:
            validate_output_stem(unsafe)
        except ValueError:
            continue
        raise RuntimeError(f"Unsafe output name was accepted: {unsafe}")

    with tempfile.TemporaryDirectory(prefix="web-design-picker-output-stem-", dir=parent) as temporary:
        root = Path(temporary)
        output = root / "output"
        source = root / "source.svg"
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>', encoding="utf-8")
        commands = (
            (make_asset_variants_main, [str(source), str(output), "--name", "../escape"]),
            (make_palette_main, [str(output), "--name", "../escape", "primary=#112233"]),
            (optimize_video_main, [str(root / "source.mp4"), str(output), "--name", "../escape"]),
        )
        for command, arguments in commands:
            if command(arguments) == 0 or output.exists():
                raise RuntimeError("An output helper accepted an escaping output name or created output")


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


def check_package_output_symlink_guards(parent: Path) -> None:
    """Packaging must not unlink or write through symlinked output directories."""
    with tempfile.TemporaryDirectory(prefix="web-design-picker-package-symlink-", dir=parent) as temporary:
        root = Path(temporary)
        script = Path(__file__).with_name("package_delivery.py")
        for output_name in ("deliverables", "qa"):
            project = root / output_name
            config = project / "config"
            config.mkdir(parents=True)
            write_json(config / "project.json", {"name": "Package fixture", "slug": "package-fixture"})
            write_json(config / "directions.json", [{"key": "first"}, {"key": "second"}])
            write_json(config / "assets.json", {})
            (project / "dist").mkdir()
            (project / "dist/index.html").write_text("fixture\n", encoding="utf-8")

            external = root / f"external-{output_name}"
            external.mkdir()
            sentinel = external / "sentinel.txt"
            archive = external / "existing.zip"
            sentinel.write_text("preserve sentinel\n", encoding="utf-8")
            archive.write_bytes(b"preserve archive\n")
            (project / output_name).symlink_to(external, target_is_directory=True)

            internal_archive = None
            if output_name == "qa":
                deliverables = project / "deliverables"
                deliverables.mkdir()
                internal_archive = deliverables / "existing.zip"
                internal_archive.write_bytes(b"preserve internal archive\n")
            else:
                (project / "qa").mkdir()

            result = subprocess.run(
                [sys.executable, str(script), str(project)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if result.returncode == 0 or "Symlinks are not allowed" not in result.stdout:
                raise RuntimeError(f"Packaging did not reject symlinked {output_name} output")
            if sentinel.read_text(encoding="utf-8") != "preserve sentinel\n" or archive.read_bytes() != b"preserve archive\n":
                raise RuntimeError(f"Packaging modified external {output_name} output before rejecting its symlink")
            if internal_archive and internal_archive.read_bytes() != b"preserve internal archive\n":
                raise RuntimeError("Packaging cleaned deliverables before rejecting a symlinked QA directory")


def check_svg_variant_dimensions(parent: Path) -> None:
    """SVG variant exports must use the requested longest edge in either orientation."""
    with tempfile.TemporaryDirectory(prefix="web-design-picker-svg-variants-", dir=parent) as temporary:
        root = Path(temporary)
        for name, width, height in (("portrait", 100, 200), ("landscape", 300, 100)):
            source = root / f"{name}.svg"
            source.write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}"><rect width="{width}" height="{height}"/></svg>',
                encoding="utf-8",
            )
            image = render_variant_svg(source, 320)
            if max(image.width, image.height) != 320:
                raise RuntimeError(f"{name} SVG variant did not honor its requested longest edge: {image.size}")
            if (image.width < image.height) != (name == "portrait"):
                raise RuntimeError(f"{name} SVG variant changed its orientation: {image.size}")


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


def check_secret_archive_guard(parent: Path) -> None:
    """Delivery archives must reject common secrets before writing output."""
    fixtures = {
        ".env": b"TOKEN=secret\n",
        "nested/.ENV.production": b"TOKEN=secret\n",
        "keys/client.KEY": b"key fixture\n",
        "keys/certificate.PFX": b"container fixture\n",
        "keys/id_ED25519": b"ssh key fixture\n",
        "keys/material.txt": b"-----BEGIN OPENSSH PRIVATE KEY-----\nfixture\n",
    }
    with tempfile.TemporaryDirectory(prefix="web-design-picker-secret-", dir=parent) as temporary:
        root = Path(temporary)
        for index, (relative, content) in enumerate(fixtures.items()):
            source = root / f"source-{index}"
            target = source / relative
            target.parent.mkdir(parents=True)
            target.write_bytes(content)
            output = root / f"delivery-{index}.zip"
            try:
                deterministic_zip(source, output)
            except ValueError as exc:
                if "Secret files" not in str(exc):
                    raise RuntimeError("Secret archive guard raised an unexpected error") from exc
            else:
                raise RuntimeError(f"Secret fixture was accepted into a delivery archive: {relative}")
            if output.exists():
                raise RuntimeError(f"Secret archive guard wrote output for: {relative}")

        safe_source = root / "safe"
        safe_source.mkdir()
        (safe_source / ".envrc").write_text("export DEMO=1\n", encoding="utf-8")
        (safe_source / "id_ed25519.pub").write_text("ssh-ed25519 public-key\n", encoding="utf-8")
        deterministic_zip(safe_source, root / "safe.zip")


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


def check_force_scaffold_preserves_existing_project(parent: Path) -> None:
    """A failed forced scaffold must not replace an existing project."""
    with tempfile.TemporaryDirectory(prefix="web-design-picker-force-", dir=parent) as temporary:
        root = Path(temporary)
        project = root / "project"
        project.mkdir()
        marker = project / "keep.txt"
        marker.write_text("preserve this project\n", encoding="utf-8")
        original_generator = new_project.generate_favicon_set

        def fail_scaffold(*_args, **_kwargs):
            raise new_project.FaviconError("injected scaffold failure")

        new_project.generate_favicon_set = fail_scaffold
        try:
            result = new_project.main([str(project), "--name", "Failure fixture", "--force"])
        finally:
            new_project.generate_favicon_set = original_generator

        if result != 1 or marker.read_text(encoding="utf-8") != "preserve this project\n":
            raise RuntimeError("Forced scaffold failure did not preserve the existing project")
        if [path.name for path in project.iterdir()] != ["keep.txt"]:
            raise RuntimeError("Forced scaffold failure replaced the destination with partial output")
        if any(root.glob(".project.staging-*")):
            raise RuntimeError("Forced scaffold failure left a staging project behind")


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
        check_output_stem_guards(project.parent)
        check_package_output_symlink_guards(project.parent)
        check_svg_variant_dimensions(project.parent)
        check_source_map_guard(project.parent)
        check_secret_archive_guard(project.parent)
        check_favicon_metadata_variants(project.parent)
        check_aria_labelledby_controls(project.parent)
        check_force_scaffold_preserves_existing_project(project.parent)
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
