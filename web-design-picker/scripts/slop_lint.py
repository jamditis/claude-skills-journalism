#!/usr/bin/env python3
"""Heuristically flag common generic AI-site design patterns for human review."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Finding:
    severity: str
    rule: str
    file: str
    detail: str


TEXT_SUFFIXES = {".html", ".htm", ".css", ".js", ".jsx", ".tsx", ".vue", ".svelte"}


def scan_file(path: Path, root: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8", errors="replace")
    low = text.lower()
    rel = path.relative_to(root).as_posix()
    findings: list[Finding] = []

    def add(severity: str, rule: str, detail: str) -> None:
        findings.append(Finding(severity, rule, rel, detail))

    font_hits = [name for name in ("inter", "geist mono", "geist", "space grotesk") if re.search(rf"font-family\s*:[^;]*\b{re.escape(name)}\b", low)]
    if font_hits:
        add("review", "default-font-stack", "Potentially generic default font choice: " + ", ".join(font_hits))
    gradient_count = len(re.findall(r"(?:linear|radial|conic)-gradient\s*\(", low))
    if gradient_count > 8:
        add("review", "gradient-overuse", f"Contains {gradient_count} CSS gradients; verify each has a functional or brand reason.")
    if "backdrop-filter" in low or "-webkit-backdrop-filter" in low:
        add("review", "glassmorphism", "Uses backdrop-filter; verify glass treatment is not decorative default styling.")
    pill_count = len(re.findall(r"border-radius\s*:\s*(?:999\w*|50px|100px|9999px)", low)) + len(re.findall(r"class\s*=\s*['\"][^'\"]*(?:pill|chip)[^'\"]*['\"]", low))
    if pill_count >= 4:
        add("review", "gratuitous-pills", f"Detected {pill_count} pill/chip signals.")
    if re.search(r"@keyframes\s+[\w-]*pulse|animation(?:-name)?\s*:[^;]*pulse", low):
        add("review", "pulse-animation", "Contains a pulse animation.")
    if "intersectionobserver" in low or re.search(r"(?:scroll|reveal)[-_ ]?(?:trigger|animation|effect)", low):
        add("review", "scroll-reveal", "Contains scroll/reveal logic; confirm content is not hidden until scrolling.")
    if re.search(r"cursor\s*:\s*url\(", low) or re.search(r"custom[-_ ]cursor|cursor[-_ ]follower", low):
        add("review", "oversized-custom-cursor", "Contains custom cursor styling or logic.")
    if re.search(r"class\s*=\s*['\"][^'\"]*bento[^'\"]*['\"]|grid-template-areas[^;]*bento", low):
        add("review", "bento-grid", "Contains an explicitly named bento layout.")
    eyebrow_count = len(re.findall(r"(?:class|id)\s*=\s*['\"][^'\"]*(?:eyebrow|kicker|pretitle|overline)[^'\"]*['\"]", low))
    if eyebrow_count >= 4:
        add("review", "repeated-eyebrows", f"Detected {eyebrow_count} eyebrow/kicker/pretitle elements.")
    if re.search(r"<h1\b[^>]*>.*?<(?:(?:em)|(?:i))\b", low, re.S):
        add("review", "italicized-headline-word", "Main headline contains italic emphasis; verify it is conceptually necessary.")
    if re.search(r">\s*0[1-9]\s*<", text):
        add("review", "leading-zero-section-numbers", "Contains leading-zero display numbers.")
    if "mailto:" in low:
        form_count = len(re.findall(r"<form\b", low))
        if form_count == 0:
            add("review", "mailto-only-contact", "Contains mailto contact behavior and no form.")
    if "newsletter" in low and re.search(r"<form\b", low):
        add("review", "template-newsletter", "Contains a newsletter form; verify there is a specific value proposition and real endpoint.")
    tiny_sizes = [float(value) for value in re.findall(r"font-size\s*:\s*([0-9.]+)px", low) if float(value) < 10.5]
    if tiny_sizes:
        add("review", "tiny-text", f"Contains {len(tiny_sizes)} font-size declaration(s) below 10.5px.")
    if re.search(r"#(?:7c3aed|8b5cf6|9333ea|a855f7|6d28d9|c084fc)\b", low) and gradient_count:
        add("review", "purple-gradient-default", "Uses common purple gradient colors.")
    card_count = len(re.findall(r"class\s*=\s*['\"][^'\"]*(?:card|tile)[^'\"]*['\"]", low))
    if card_count >= 8 and len(re.findall(r"border-radius\s*:", low)) >= 4:
        add("review", "rounded-card-system", f"Contains {card_count} card/tile class uses with repeated rounded-corner styling.")
    if "join our newsletter" in low or "subscribe to our newsletter" in low:
        add("review", "generic-newsletter-copy", "Uses generic newsletter copy.")
    if re.search(r"<h[1-3]\b[^>]*>[^<]{0,50}(?:innovative solutions|trusted partner|bringing .* to life)", low):
        add("review", "generic-positioning-copy", "Headline contains generic positioning language.")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Flag generic AI-site design patterns for human review.")
    parser.add_argument("root", type=Path)
    parser.add_argument("--json", type=Path, dest="json_path")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)
    if not args.root.exists():
        print(f"ERROR: path does not exist: {args.root}", file=sys.stderr)
        return 2
    root = args.root.resolve()
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES]
    findings = [finding for path in files for finding in scan_file(path, root)]
    report = {"root": str(root), "files_scanned": len(files), "finding_count": len(findings), "findings": [asdict(f) for f in findings]}
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not findings:
        print(f"No heuristic anti-slop findings across {len(files)} files.")
        return 0
    print(f"{len(findings)} heuristic finding(s) across {len(files)} files. Review; do not treat as automatic defects.\n")
    for finding in findings:
        print(f"[{finding.severity}] {finding.rule}, {finding.file}\n  {finding.detail}")
    return 3 if args.fail_on_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
