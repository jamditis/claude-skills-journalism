#!/usr/bin/env python3
"""Run browser interaction, responsive, media, and download QA with Playwright."""
from __future__ import annotations

import argparse
import functools
import http.server
import json
import shutil
import socketserver
import sys
import threading
from pathlib import Path
from typing import Any

from _common import load_project, utc_now, write_json


class QAError(RuntimeError):
    pass


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        pass


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--chromium", type=Path, help="Path to a Chromium executable")
    parser.add_argument("--wait-ms", type=int, default=350)
    parser.add_argument("--test-downloads", action="store_true", help="Build one family ZIP and the all-assets ZIP in the browser")
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        print("ERROR: Playwright is required: python -m pip install playwright", file=sys.stderr)
        return 2

    root = args.project_dir.resolve()
    project, directions, _ = load_project(root)
    dist = root / "dist"
    if not (dist / "index.html").is_file():
        print("ERROR: build the project before browser QA", file=sys.stderr)
        return 2
    previews = root / "previews"
    previews.mkdir(parents=True, exist_ok=True)
    downloads = root / "qa/browser-downloads"
    downloads.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []
    captures: list[dict[str, Any]] = []
    console_errors: list[str] = []
    request_failures: list[str] = []

    handler = functools.partial(QuietHandler, directory=str(dist))
    server = ReusableTCPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"
    executable = str(args.chromium) if args.chromium else shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")

    def record_console(message) -> None:
        if message.type == "error":
            console_errors.append(message.text)

    def record_failure(request) -> None:
        request_failures.append(f"{request.url}: {request.failure}")

    try:
        with sync_playwright() as playwright:
            launch_args: dict[str, Any] = {"headless": True, "args": ["--no-sandbox", "--disable-dev-shm-usage"]}
            if executable:
                launch_args["executable_path"] = executable
            browser = playwright.chromium.launch(**launch_args)

            for size_name, width, height in (
                ("desktop", 1440, 1000),
                ("laptop", 1280, 800),
                ("tablet", 768, 1024),
                ("mobile", 390, 844),
            ):
                context = browser.new_context(viewport={"width": width, "height": height}, accept_downloads=True)
                page = context.new_page()
                page.on("console", record_console)
                page.on("requestfailed", record_failure)

                for index, direction in enumerate(directions):
                    key = direction["key"]
                    page.goto(f"{base}/index.html#{key}", wait_until="networkidle")
                    page.wait_for_timeout(args.wait_ms)
                    selected = page.locator(f'[role="tab"][data-key="{key}"]').get_attribute("aria-selected")
                    active = page.locator(f'iframe[data-key="{key}"]').get_attribute("data-active")
                    if selected != "true" or active != "true":
                        errors.append(f"Picker did not activate {key} at {size_name} size")
                    if page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"):
                        errors.append(f"Picker has horizontal overflow at {width}px for {key}")
                    iframe_overflow = page.locator(f'iframe[data-key="{key}"]').evaluate(
                        "frame => frame.contentDocument ? frame.contentDocument.documentElement.scrollWidth > frame.contentWindow.innerWidth + 1 : false"
                    )
                    if iframe_overflow:
                        errors.append(f"Direction {key} overflows horizontally inside the picker at {width}px")
                    shot = previews / f"review-{key}-{size_name}.png"
                    page.screenshot(path=str(shot), full_page=False)
                    captures.append({"page": "review", "direction": key, "size": size_name, "path": shot.name})

                    open_href = page.locator("[data-open-selected]").get_attribute("href")
                    if open_href != direction["file"]:
                        errors.append(f"Open-selected link is wrong for {key}: {open_href!r}")

                    if index == 0:
                        page.locator("[data-presentation]").click()
                        page.wait_for_timeout(100)
                        if not page.locator("body").evaluate("body => body.classList.contains('presentation')"):
                            errors.append("Presentation mode did not apply its fallback class")
                        page.locator("[data-restore]").click()
                        page.wait_for_timeout(100)
                        if page.locator("body").evaluate("body => body.classList.contains('presentation')"):
                            errors.append("Restore control did not exit presentation mode")

                    page.goto(f"{base}/{direction['file']}", wait_until="networkidle")
                    page.wait_for_timeout(args.wait_ms)
                    if page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"):
                        errors.append(f"Standalone direction {key} overflows horizontally at {width}px")
                    if page.locator('link[rel~="icon"]').count() == 0:
                        errors.append(f"Standalone direction {key} has no favicon declaration")
                    shot = previews / f"{key}-{size_name}.png"
                    page.screenshot(path=str(shot), full_page=True)
                    captures.append({"page": "standalone", "direction": key, "size": size_name, "path": shot.name})

                page.goto(f"{base}/design-assets.html", wait_until="networkidle")
                page.wait_for_timeout(args.wait_ms)
                if page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1"):
                    errors.append(f"Asset catalog overflows horizontally at {width}px")
                broken_media = page.evaluate("""() => [...document.querySelectorAll('img')].filter(img => img.complete && img.naturalWidth === 0).map(img => img.src)""")
                if broken_media:
                    errors.extend(f"Broken image in asset catalog: {url}" for url in broken_media)
                manifest_paths = page.evaluate("""async () => (await (await fetch('asset-manifest.json')).json()).assets.map(asset => asset.path)""")
                failed_fetches = page.evaluate("""async paths => {
                  const results = [];
                  for (const path of paths) {
                    const response = await fetch(path);
                    if (!response.ok) results.push(`${response.status} ${path}`);
                  }
                  return results;
                }""", manifest_paths)
                if failed_fetches:
                    errors.extend(f"Asset download failed: {item}" for item in failed_fetches)
                shot = previews / f"asset-catalog-{size_name}.png"
                page.screenshot(path=str(shot), full_page=True)
                captures.append({"page": "assets", "size": size_name, "path": shot.name})

                if args.test_downloads and size_name == "desktop" and manifest_paths:
                    family = page.locator("[data-download-family]").first
                    if family.count():
                        try:
                            with page.expect_download(timeout=30_000) as download_info:
                                family.click()
                            download = download_info.value
                            target = downloads / download.suggested_filename
                            download.save_as(target)
                            if target.stat().st_size == 0:
                                errors.append("Family ZIP download was empty")
                        except PlaywrightTimeoutError:
                            errors.append("Timed out while generating a family ZIP")
                    all_button = page.locator("[data-download-all]")
                    if all_button.count():
                        try:
                            with page.expect_download(timeout=60_000) as download_info:
                                all_button.click()
                            download = download_info.value
                            target = downloads / download.suggested_filename
                            download.save_as(target)
                            if target.stat().st_size == 0:
                                errors.append("All-assets ZIP download was empty")
                        except PlaywrightTimeoutError:
                            errors.append("Timed out while generating the all-assets ZIP")

                context.close()
            browser.close()
    except Exception as exc:
        errors.append(f"Browser QA runtime failure: {exc}")
    finally:
        server.shutdown()
        server.server_close()

    # Avoid duplicating the same browser message dozens of times across pages.
    for message in sorted(set(console_errors)):
        errors.append(f"Browser console error: {message}")
    for failure in sorted(set(request_failures)):
        errors.append(f"Request failed: {failure}")

    report = {
        "generated_at": utc_now(),
        "project": project["name"],
        "base_url": base,
        "errors": errors,
        "warnings": warnings,
        "captures": captures,
        "download_tests": args.test_downloads,
        "passed": not errors,
    }
    report_path = args.report_json or (root / "qa/browser-qa.json")
    write_json(report_path, report)
    print(f"Browser QA: {len(errors)} error(s), {len(warnings)} warning(s), {len(captures)} screenshot(s)")
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
