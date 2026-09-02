#!/usr/bin/env python3
"""Validate a static web-design-picker site, its assets, and common anti-slop risks."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from _common import format_bytes, read_json, utc_now, write_json

REFERENCE_ATTRS = {
    "a": ["href"],
    "link": ["href"],
    "script": ["src"],
    "img": ["src", "srcset"],
    "source": ["src", "srcset"],
    "video": ["src", "poster"],
    "audio": ["src"],
    "iframe": ["src"],
    "object": ["data"],
}
IGNORE_SCHEMES = {"http", "https", "mailto", "tel", "data", "javascript", "blob"}


@dataclass
class Finding:
    severity: str
    code: str
    file: str
    message: str


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[tuple[str, str, str]] = []
        self.external: list[str] = []
        self.html_lang = ""
        self.title_parts: list[str] = []
        self._in_title = False
        self.meta_names: dict[str, str] = {}
        self.icons: list[str] = []
        self.h1_count = 0
        self.images: list[dict[str, str]] = []
        self.videos: list[dict[str, str]] = []
        self.iframes: list[dict[str, str]] = []
        self.labels_for: set[str] = set()
        self.controls: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.inline_css: list[str] = []
        self.mailto_links: list[str] = []
        self.buttons_without_label = 0
        self._button_depth = 0
        self._button_has_text: list[bool] = []
        self._button_attrs: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = {key.lower(): (value or "") for key, value in attrs_list}
        tag = tag.lower()
        if tag == "html":
            self.html_lang = attrs.get("lang", "")
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            name = attrs.get("name", "").lower()
            if name:
                self.meta_names[name] = attrs.get("content", "")
        if tag == "link" and "icon" in attrs.get("rel", "").lower():
            self.icons.append(attrs.get("href", ""))
        if tag == "h1":
            self.h1_count += 1
        if tag == "img":
            self.images.append(attrs)
        if tag == "video":
            self.videos.append(attrs)
        if tag == "iframe":
            self.iframes.append(attrs)
        if tag == "label" and attrs.get("for"):
            self.labels_for.add(attrs["for"])
        if tag in {"input", "select", "textarea"}:
            self.controls.append((tag, attrs))
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "style":
            self._in_style = True
        if tag == "a" and attrs.get("href", "").lower().startswith("mailto:"):
            self.mailto_links.append(attrs["href"])
        if tag == "button":
            self._button_depth += 1
            self._button_has_text.append(False)
            self._button_attrs.append(attrs)

        for attr in REFERENCE_ATTRS.get(tag, []):
            value = attrs.get(attr)
            if not value:
                continue
            if attr == "srcset":
                for candidate in value.split(","):
                    url = candidate.strip().split()[0] if candidate.strip() else ""
                    if url:
                        self.references.append((tag, attr, url))
            else:
                self.references.append((tag, attr, value))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag == "style":
            self._in_style = False
        if tag == "button" and self._button_depth:
            has_text = self._button_has_text.pop()
            attrs = self._button_attrs.pop()
            if not has_text and not attrs.get("aria-label") and not attrs.get("aria-labelledby") and not attrs.get("title"):
                self.buttons_without_label += 1
            self._button_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if getattr(self, "_in_style", False):
            self.inline_css.append(data)
        if self._button_depth and data.strip():
            self._button_has_text[-1] = True


def add(findings: list[Finding], severity: str, code: str, file: Path | str, message: str) -> None:
    findings.append(Finding(severity, code, str(file), message))


def resolve_local(root: Path, html_file: Path, url: str) -> Path | None:
    parsed = urlsplit(url)
    if parsed.scheme.lower() in IGNORE_SCHEMES or parsed.netloc:
        return None
    raw = unquote(parsed.path)
    if not raw:
        return html_file
    if raw.startswith("/"):
        return root / raw.lstrip("/")
    return (html_file.parent / raw).resolve()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def check_html(root: Path, path: Path, findings: list[Finding], allow_external: bool) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = DocumentParser()
    try:
        parser.feed(text)
    except Exception as exc:
        add(findings, "error", "html-parse", path.relative_to(root), f"HTML parser failed: {exc}")
        return

    relative = path.relative_to(root)
    if not parser.html_lang:
        add(findings, "error", "missing-lang", relative, "Missing <html lang> attribute")
    if not "".join(parser.title_parts).strip():
        add(findings, "error", "missing-title", relative, "Missing non-empty <title>")
    if "viewport" not in parser.meta_names:
        add(findings, "error", "missing-viewport", relative, "Missing viewport meta tag")
    if not parser.icons:
        add(findings, "error", "missing-favicon", relative, "No favicon declaration found")
    is_picker_shell = 'role="tablist"' in text.lower() and '<iframe' in text.lower()
    if parser.h1_count != 1 and not is_picker_shell:
        add(findings, "warning", "h1-count", relative, f"Expected one H1; found {parser.h1_count}")

    for image in parser.images:
        if "alt" not in image:
            add(findings, "error", "missing-alt", relative, f"Image lacks alt attribute: {image.get('src', '(inline)')}")
    for video in parser.videos:
        if not video.get("poster"):
            add(findings, "warning", "video-poster", relative, f"Video lacks poster: {video.get('src', '(source child)')}")
        if "playsinline" not in video:
            add(findings, "warning", "video-playsinline", relative, "Video lacks playsinline")
    for iframe in parser.iframes:
        if not iframe.get("title"):
            add(findings, "error", "iframe-title", relative, f"Iframe lacks title: {iframe.get('src', '(unknown)')}")

    for tag, attrs in parser.controls:
        control_type = attrs.get("type", "").lower()
        if control_type in {"hidden", "submit", "button", "reset", "image"}:
            continue
        control_id = attrs.get("id")
        labelled = bool(attrs.get("aria-label") or attrs.get("aria-labelledby") or (control_id and control_id in parser.labels_for))
        if not labelled:
            add(findings, "error", "form-label", relative, f"Unlabelled {tag}: id={control_id or '(none)'} name={attrs.get('name', '(none)')}")
    if parser.buttons_without_label:
        add(findings, "error", "button-label", relative, f"{parser.buttons_without_label} button(s) have no accessible name")
    if parser.mailto_links:
        add(findings, "warning", "mailto-cta", relative, "mailto link present; do not present it as a submitted intake workflow")

    for tag, attr, url in parser.references:
        parsed = urlsplit(url)
        if parsed.scheme.lower() in {"http", "https"} or parsed.netloc:
            if not allow_external:
                add(findings, "warning", "external-reference", relative, f"External {attr}: {url}")
            continue
        if parsed.scheme.lower() in IGNORE_SCHEMES:
            continue
        target = resolve_local(root, path, url)
        if target is None:
            continue
        if not is_within(target, root):
            add(findings, "error", "path-escape", relative, f"Reference leaves site root: {url}")
            continue
        if parsed.path and not target.exists():
            add(findings, "error", "missing-reference", relative, f"Missing {tag} {attr} target: {url}")
        if parsed.fragment and target.exists() and target.suffix.lower() in {".html", ".htm", ""}:
            target_text = target.read_text(encoding="utf-8", errors="ignore")
            fragment = re.escape(unquote(parsed.fragment))
            if not re.search(rf'\bid=["\']{fragment}["\']', target_text):
                add(findings, "warning", "missing-fragment", relative, f"Fragment target not found: {url}")

    external_css = ""
    for tag, attr, url in parser.references:
        if tag == "link" and attr == "href" and urlsplit(url).path.lower().endswith(".css"):
            target = resolve_local(root, path, url)
            if target and target.exists() and is_within(target, root):
                external_css += "\n" + target.read_text(encoding="utf-8", errors="ignore")
    combined = (text + "\n" + external_css).lower()

    slop_checks = [
        (r"\b(inter|geist mono|geist|space grotesk)\b", "reflex-font", "Fashion-default font detected; verify a project-specific reason"),
        (r"backdrop-filter\s*:", "glassmorphism", "backdrop-filter detected; verify glass treatment is justified"),
        (r"border-radius\s*:\s*(999|9999|50%)", "pill-everything", "Pill/circle radius detected; verify it is an appropriate control shape"),
        (r"animation[^;{]*(pulse|pulsing)", "pulse-animation", "Pulse animation detected"),
        (r"intersectionobserver|scroll-reveal|reveal-on-scroll", "scroll-reveal", "Scroll-triggered reveal logic detected"),
        (r"\b(bento|marquee|ticker)\b", "template-pattern", "Bento/marquee/ticker pattern detected; verify content need"),
        (r"contact now", "contact-now", "Generic 'Contact now' copy detected"),
        (r"bringing your vision to life|where creativity meets precision|innovative solutions|one-stop shop|cutting-edge|trusted partner", "generic-copy", "Generic marketing phrase detected"),
        (r">\s*0[1-9]\s*<", "zero-padded-label", "Zero-padded decorative number label detected"),
    ]
    for pattern, code, message in slop_checks:
        if re.search(pattern, combined, re.I):
            add(findings, "warning", code, relative, message)

    gradient_count = len(re.findall(r"(?:linear|radial|conic)-gradient\s*\(", combined))
    checker_exception = ".preview.checker" in combined and gradient_count <= 4 and "radial-gradient" not in combined and "conic-gradient" not in combined
    if gradient_count and not checker_exception:
        add(findings, "warning", "gradients", relative, f"Found {gradient_count} CSS gradient(s); verify they are not decorative filler")


def manifest_paths(data: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in {"href", "preview", "poster", "path"} and isinstance(value, str):
                paths.append(value)
            else:
                paths.extend(manifest_paths(value))
    elif isinstance(data, list):
        for item in data:
            paths.extend(manifest_paths(item))
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_dir", type=Path)
    parser.add_argument("--manifest", type=Path, help="Optional config/assets.json to validate")
    parser.add_argument("--strict", action="store_true", help="Return failure when warnings remain")
    parser.add_argument("--allow-external", action="store_true")
    parser.add_argument("--cloudflare", action="store_true", help="Apply conservative Cloudflare Drop packaging checks")
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()

    root = args.site_dir.resolve()
    findings: list[Finding] = []
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 1
    if not (root / "index.html").is_file():
        add(findings, "error", "missing-index", ".", "index.html is not at site root")

    html_files = sorted(root.rglob("*.html"))
    if not html_files:
        add(findings, "error", "no-html", ".", "No HTML files found")
    for path in html_files:
        check_html(root, path, findings, args.allow_external)

    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            add(findings, "error", "symlink", path.relative_to(root), "Symlinks are not allowed in portable static packages")
        if path.is_file() and path.stat().st_size > 25 * 1024 * 1024:
            add(findings, "warning", "large-file", path.relative_to(root), f"Large file: {format_bytes(path.stat().st_size)}")
        if args.cloudflare and path.is_file() and path.suffix.lower() == ".zip":
            add(findings, "warning", "nested-zip", path.relative_to(root), "Nested ZIP excluded by default from conservative Drop package")

    if args.manifest:
        data = read_json(args.manifest.resolve())
        for raw in manifest_paths(data):
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (root / unquote(parsed.path).lstrip("/")).resolve()
            if not is_within(target, root):
                add(findings, "error", "manifest-path-escape", args.manifest, f"Manifest target leaves site root: {raw}")
                continue
            if not target.exists():
                add(findings, "error", "manifest-missing", args.manifest, f"Manifest target missing from site: {raw}")

    errors = [item for item in findings if item.severity == "error"]
    warnings = [item for item in findings if item.severity == "warning"]
    report = {
        "generated_at": utc_now(),
        "site_dir": str(root),
        "html_files": len(html_files),
        "errors": len(errors),
        "warnings": len(warnings),
        "findings": [asdict(item) for item in findings],
    }
    if args.report_json:
        write_json(args.report_json.resolve(), report)

    print(f"Checked {len(html_files)} HTML file(s) under {root}")
    for item in findings:
        print(f"{item.severity.upper():7} {item.code:22} {item.file}: {item.message}")
    print(f"Result: {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
