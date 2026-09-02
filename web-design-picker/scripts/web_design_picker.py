#!/usr/bin/env python3
"""Unified command-line entry point for the web-design-picker skill."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def run_script(script: str, arguments: list[str]) -> int:
    command = [sys.executable, str(SCRIPTS / script), *arguments]
    return subprocess.call(command)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scaffold, build, validate, preview, and package a multi-direction "
            "website design picker project."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Scaffold a new two-to-five direction project")
    init_parser.add_argument("project_dir", type=Path)
    init_parser.add_argument("--name", required=True)
    init_parser.add_argument("--slug")
    init_parser.add_argument("--directions", type=int, choices=range(2, 6), default=3)
    init_parser.add_argument("--force", action="store_true")

    build_parser = subparsers.add_parser("build", help="Build the picker, concepts, and asset catalog")
    build_parser.add_argument("project_dir", type=Path)
    build_parser.add_argument("--no-clean", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Run static, distinctness, and anti-slop checks")
    validate_parser.add_argument("project_dir", type=Path)
    validate_parser.add_argument("--strict", action="store_true")
    validate_parser.add_argument("--allow-external", action="store_true")
    validate_parser.add_argument("--fail-on-slop", action="store_true")

    preview_parser = subparsers.add_parser("preview", help="Capture responsive previews and run browser QA")
    preview_parser.add_argument("project_dir", type=Path)
    preview_parser.add_argument("--chromium", type=Path)
    preview_parser.add_argument("--wait-ms", type=int, default=350)
    preview_parser.add_argument("--test-downloads", action="store_true")

    package_parser = subparsers.add_parser("package", help="Create Cloudflare Drop and design-handoff archives")
    package_parser.add_argument("project_dir", type=Path)
    package_parser.add_argument("--skip-validation", action="store_true")
    package_parser.add_argument("--max-file-bytes", type=int, default=25_000_000)

    run_parser = subparsers.add_parser("run", help="Run the complete factory pipeline")
    run_parser.add_argument("project_dir", type=Path)
    run_parser.add_argument("--skip-browser", action="store_true")
    run_parser.add_argument("--test-downloads", action="store_true")
    run_parser.add_argument("--strict", action="store_true")
    run_parser.add_argument("--allow-external", action="store_true", help="Permit external http(s) references during static validation")
    run_parser.add_argument("--fail-on-slop", action="store_true")
    run_parser.add_argument("--skip-package-validation", action="store_true")

    self_test_parser = subparsers.add_parser("self-test", help="Exercise the full skill pipeline on a synthetic project")
    self_test_parser.add_argument("--work-dir", type=Path)
    self_test_parser.add_argument("--browser", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "init":
        forwarded = [str(args.project_dir), "--name", args.name, "--directions", str(args.directions)]
        if args.slug:
            forwarded.extend(["--slug", args.slug])
        if args.force:
            forwarded.append("--force")
        return run_script("new_project.py", forwarded)

    if args.command == "build":
        forwarded = [str(args.project_dir)]
        if args.no_clean:
            forwarded.append("--no-clean")
        return run_script("build_picker.py", forwarded)

    if args.command == "validate":
        root = args.project_dir.resolve()
        qa = root / "qa"
        qa.mkdir(parents=True, exist_ok=True)

        static_args = [
            str(root / "dist"),
            "--manifest",
            str(root / "config/assets.json"),
            "--cloudflare",
            "--report-json",
            str(qa / "static-validation.json"),
        ]
        if args.strict:
            static_args.append("--strict")
        if args.allow_external:
            static_args.append("--allow-external")
        code = run_script("validate_site.py", static_args)
        if code:
            return code

        distinct_args = [str(root), "--report-json", str(qa / "distinctness.json")]
        if args.strict:
            distinct_args.append("--strict")
        code = run_script("check_distinctness.py", distinct_args)
        if code and args.strict:
            return code

        slop_args = [str(root / "dist"), "--json", str(qa / "anti-slop.json")]
        if args.fail_on_slop:
            slop_args.append("--fail-on-findings")
        return run_script("slop_lint.py", slop_args)

    if args.command == "preview":
        forwarded = [
            str(args.project_dir),
            "--wait-ms",
            str(args.wait_ms),
            "--report-json",
            str(args.project_dir.resolve() / "qa/browser-qa.json"),
        ]
        if args.chromium:
            forwarded.extend(["--chromium", str(args.chromium)])
        if args.test_downloads:
            forwarded.append("--test-downloads")
        return run_script("browser_qa.py", forwarded)

    if args.command == "package":
        forwarded = [str(args.project_dir), "--max-file-bytes", str(args.max_file_bytes)]
        if args.skip_validation:
            forwarded.append("--skip-validation")
        return run_script("package_delivery.py", forwarded)

    if args.command == "run":
        forwarded = [str(args.project_dir)]
        for enabled, flag in (
            (args.skip_browser, "--skip-browser"),
            (args.test_downloads, "--test-downloads"),
            (args.strict, "--strict"),
            (args.allow_external, "--allow-external"),
            (args.fail_on_slop, "--fail-on-slop"),
            (args.skip_package_validation, "--skip-package-validation"),
        ):
            if enabled:
                forwarded.append(flag)
        return run_script("run_factory.py", forwarded)

    forwarded: list[str] = []
    if args.work_dir:
        forwarded.extend(["--work-dir", str(args.work_dir)])
    if args.browser:
        forwarded.append("--browser")
    return run_script("self_test.py", forwarded)


if __name__ == "__main__":
    raise SystemExit(main())
