#!/usr/bin/env python3
"""Build, inspect, browser-test, and package a web-design-picker project."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from _common import load_project, read_json, utc_now, write_json


class FactoryError(RuntimeError):
    pass


def run_step(name: str, command: list[str], log_path: Path, *, required: bool = True) -> dict[str, Any]:
    print(f"[{name}] {' '.join(command)}")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(result.stdout, encoding="utf-8")
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if required and result.returncode != 0:
        raise FactoryError(f"{name} failed; see {log_path}")
    return {"name": name, "command": command, "returncode": result.returncode, "log": str(log_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--skip-browser", action="store_true", help="Skip Playwright screenshots and interaction tests")
    parser.add_argument("--test-downloads", action="store_true", help="Generate family and all-assets ZIPs in the browser during QA")
    parser.add_argument("--strict", action="store_true", help="Require completed distinctness scores and fail on static warnings")
    parser.add_argument("--fail-on-slop", action="store_true", help="Treat heuristic anti-slop findings as a build failure")
    parser.add_argument("--skip-package-validation", action="store_true")
    args = parser.parse_args()

    root = args.project_dir.resolve()
    project, _, _ = load_project(root)
    qa = root / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    scripts = Path(__file__).resolve().parent
    steps: list[dict[str, Any]] = []

    try:
        steps.append(run_step("build", [sys.executable, str(scripts / "build_picker.py"), str(root)], qa / "build.txt"))

        static_cmd = [
            sys.executable,
            str(scripts / "validate_site.py"),
            str(root / "dist"),
            "--manifest",
            str(root / "config/assets.json"),
            "--cloudflare",
            "--report-json",
            str(qa / "static-validation.json"),
        ]
        if args.strict:
            static_cmd.append("--strict")
        steps.append(run_step("static validation", static_cmd, qa / "static-validation.txt"))

        distinct_cmd = [
            sys.executable,
            str(scripts / "check_distinctness.py"),
            str(root),
            "--report-json",
            str(qa / "distinctness.json"),
        ]
        if args.strict:
            distinct_cmd.append("--strict")
        steps.append(run_step("direction distinctness", distinct_cmd, qa / "distinctness.txt", required=args.strict))

        slop_cmd = [
            sys.executable,
            str(scripts / "slop_lint.py"),
            str(root / "dist"),
            "--json",
            str(qa / "anti-slop.json"),
        ]
        if args.fail_on_slop:
            slop_cmd.append("--fail-on-findings")
        steps.append(run_step("anti-slop review", slop_cmd, qa / "anti-slop.txt", required=args.fail_on_slop))

        if not args.skip_browser:
            browser_cmd = [
                sys.executable,
                str(scripts / "browser_qa.py"),
                str(root),
                "--report-json",
                str(qa / "browser-qa.json"),
            ]
            if args.test_downloads:
                browser_cmd.append("--test-downloads")
            steps.append(run_step("browser QA", browser_cmd, qa / "browser-qa.txt"))

        package_cmd = [sys.executable, str(scripts / "package_delivery.py"), str(root)]
        if args.skip_package_validation:
            package_cmd.append("--skip-validation")
        steps.append(run_step("package", package_cmd, qa / "package.txt"))

    except FactoryError as exc:
        report = {"generated_at": utc_now(), "project": project["name"], "passed": False, "error": str(exc), "steps": steps}
        write_json(qa / "factory-report.json", report)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    delivery_manifest = root / "deliverables/delivery-manifest.json"
    report = {
        "generated_at": utc_now(),
        "project": project["name"],
        "passed": True,
        "steps": steps,
        "delivery": read_json(delivery_manifest) if delivery_manifest.exists() else None,
    }
    write_json(qa / "factory-report.json", report)
    print(json.dumps({"passed": True, "deliverables": str(root / "deliverables")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
