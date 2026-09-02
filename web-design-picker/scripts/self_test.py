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

from _common import read_json, relative_web_path, utc_now, validate_slug, write_json
from build_picker import relative_from_page


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
