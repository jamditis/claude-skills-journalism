#!/usr/bin/env python3
"""WCAG 2.2 AA remediation patcher for docs/ static HTML pages.

Idempotent. Re-runnable. Prints a summary of files changed and changes per file.

Marker tags used to detect prior application:
- <!-- a11y-patch-v1 --> in <head>
- /* a11y-patch-v1 */ inside <style>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

HEAD_MARKER = "<!-- a11y-patch-v1 -->"
STYLE_MARKER = "/* a11y-patch-v1 */"

UNIVERSAL_CSS = """
""" + STYLE_MARKER + """
.skip-link { position: absolute; left: -9999px; top: 0; z-index: 10000; }
.skip-link:focus { left: 1rem; top: 1rem; padding: 0.75rem 1.25rem; background: #121212; color: #ede6d4; font-weight: 700; text-decoration: none; }
:focus-visible { outline: 2px solid #3d4b40; outline-offset: 4px; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
p a:not(.btn-primary):not(.btn-outline):not(.skill-card):not(.deckle-card):not(.feature-card),
li a:not(.btn-primary):not(.btn-outline),
.prose a {
  text-decoration: underline;
  text-underline-offset: 0.15em;
  text-decoration-thickness: 1px;
}
a[class~="text-accent"]:not(.btn-primary):not(.btn-outline),
a[class~="text-accentDark"]:not(.btn-primary):not(.btn-outline),
a[class~="text-accentDeep"]:not(.btn-primary):not(.btn-outline) { color: #1e293b !important; }
a[class~="text-accent"]:not(.btn-primary):not(.btn-outline):hover,
a[class~="text-accentDark"]:not(.btn-primary):not(.btn-outline):hover { color: #0f172a !important; }
strong[class~="text-accent"], em[class~="text-accent"], code[class~="text-accent"],
strong[class~="text-accentDark"], em[class~="text-accentDark"] { color: #1e293b !important; }
.bg-canvas [class~="text-mist"], main [class~="text-mist"], [class~="text-mist"] { color: #3a3a3a !important; }
.bg-ink [class~="text-accent"], [class~="bg-ink"] [class~="text-accent"],
.bg-zinc-900 [class~="text-accent"], .bg-gray-900 [class~="text-accent"],
[class*="bg-zinc-9"] [class~="text-accent"], [class*="bg-gray-9"] [class~="text-accent"],
[class*="text-white"] [class~="text-accent"],
[style*="background:#1"] [class~="text-accent"], [style*="background-color:#1"] [class~="text-accent"] {
  color: #ddd6fe !important;
}
.bg-ink [class~="text-mist"], [class~="bg-ink"] [class~="text-mist"],
[class*="text-white"] [class~="text-mist"] {
  color: #d4d4d4 !important;
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  .reveal-section, .reveal { opacity: 1 !important; transform: none !important; }
}
"""

HERO_OVERLAY_CSS = """
.hero-gradient { position: relative; }
.hero-gradient::before {
  content: "";
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.18);
  pointer-events: none;
  z-index: 1;
}
.hero-gradient > * { position: relative; z-index: 2; }
"""

REVEAL_NOSCRIPT_CSS = """
.reveal-section, .reveal { opacity: 1; transform: none; }
"""

SKIP_LINK_HTML = '<a href="#main" class="skip-link">Skip to main content</a>'


class PageReport:
    __slots__ = ("path", "changes")

    def __init__(self, path: Path):
        self.path = path
        self.changes: list[str] = []

    def add(self, change: str) -> None:
        self.changes.append(change)


def find_pages() -> list[Path]:
    return sorted(p for p in DOCS.rglob("index.html"))


def has_marker(html: str) -> bool:
    return HEAD_MARKER in html


def inject_universal_css(html: str, report: PageReport) -> str:
    if STYLE_MARKER in html:
        return html
    if "</style>" not in html:
        # No <style>, inject one before </head>
        block = "<style>" + UNIVERSAL_CSS + "</style>"
        new = html.replace("</head>", block + "\n</head>", 1)
        if new != html:
            report.add("inject <style> + universal a11y CSS")
        return new
    new = html.replace("</style>", UNIVERSAL_CSS + "</style>", 1)
    if new != html:
        report.add("inject universal a11y CSS into existing <style>")
    return new


def inject_hero_overlay(html: str, report: PageReport) -> str:
    if "hero-gradient" not in html:
        return html
    if "hero-gradient::before" in html:
        return html
    if "</style>" not in html:
        return html
    new = html.replace("</style>", HERO_OVERLAY_CSS + "</style>", 1)
    if new != html:
        report.add("add hero-gradient ::before dark overlay")
    return new


def inject_reveal_noscript(html: str, report: PageReport) -> str:
    # Detect via JS pattern, not CSS selector — our own injected CSS contains .reveal-section.
    if "IntersectionObserver" not in html and ".reveal-section.visible" not in html:
        return html
    if "noscript-reveal-fallback" in html:
        return html
    block = (
        '<noscript id="noscript-reveal-fallback">'
        '<style>' + REVEAL_NOSCRIPT_CSS + '</style>'
        '</noscript>'
    )
    new = html.replace("</head>", block + "\n</head>", 1)
    if new != html:
        report.add("add <noscript> fallback for opacity:0 reveal sections")
    return new


def add_skip_link(html: str, report: PageReport) -> str:
    if 'class="skip-link"' in html or 'href="#main"' in html:
        return html
    new = re.sub(
        r"(<body[^>]*>)",
        lambda m: m.group(1) + "\n    " + SKIP_LINK_HTML,
        html,
        count=1,
    )
    if new != html:
        report.add("add skip link after <body>")
    return new


def add_main_id(html: str, report: PageReport) -> str:
    if re.search(r'<main[^>]*\bid\s*=', html):
        return html
    new = re.sub(
        r"<main(\s|>)",
        lambda m: '<main id="main"' + m.group(1),
        html,
        count=1,
    )
    if new != html:
        report.add('add id="main" to <main>')
    return new


def add_aria_hidden_to_svgs(html: str, report: PageReport) -> str:
    pattern = re.compile(r"<svg(?![^>]*\baria-hidden=)(?![^>]*\brole\s*=\s*[\"']img[\"'])([^>]*)>")
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        attrs = m.group(1)
        if "focusable=" in attrs:
            return f'<svg aria-hidden="true"{attrs}>'
        return f'<svg aria-hidden="true" focusable="false"{attrs}>'

    new = pattern.sub(repl, html)
    if count:
        report.add(f'add aria-hidden + focusable=false to {count} inline svg')
    return new


def add_rel_noopener(html: str, report: PageReport) -> str:
    pattern = re.compile(r"<a\b([^>]*?\btarget\s*=\s*[\"']_blank[\"'][^>]*)>")
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        attrs = m.group(1)
        rel_match = re.search(r'\brel\s*=\s*[\"\']([^\"\']*)[\"\']', attrs)
        if rel_match:
            rel_val = rel_match.group(1)
            tokens = set(rel_val.split())
            if "noopener" in tokens and "noreferrer" in tokens:
                return m.group(0)
            tokens.update({"noopener", "noreferrer"})
            new_rel = " ".join(sorted(tokens))
            count += 1
            new_attrs = attrs[: rel_match.start()] + f'rel="{new_rel}"' + attrs[rel_match.end():]
            return f'<a{new_attrs}>'
        count += 1
        return f'<a{attrs} rel="noopener noreferrer">'

    new = pattern.sub(repl, html)
    if count:
        report.add(f'add rel="noopener noreferrer" to {count} target=_blank link')
    return new


def add_aria_label_to_icon_links(html: str, report: PageReport) -> str:
    """Find <a> elements containing only an <svg> (no visible text) and no aria-label.

    Heuristic: anchors whose entire content is whitespace + one <svg>.
    Add aria-label based on href hint (github -> GitHub, twitter -> Twitter, etc.).
    """
    anchor_re = re.compile(
        r'(<a\b([^>]*?)>)([\s\S]*?)(</a>)',
        re.IGNORECASE,
    )
    count = 0
    label_map = [
        ("github.com", "GitHub"),
        ("twitter.com", "Twitter"),
        ("x.com", "X (Twitter)"),
        ("linkedin.com", "LinkedIn"),
        ("mastodon", "Mastodon"),
        ("bsky.app", "Bluesky"),
        ("youtube.com", "YouTube"),
        ("instagram.com", "Instagram"),
    ]

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        open_tag, attrs, body, close_tag = m.group(1), m.group(2), m.group(3), m.group(4)
        if "aria-label=" in attrs:
            return m.group(0)
        text_only = re.sub(r"<[^>]+>", "", body)
        text_only = re.sub(r"&[#\w]+;", "", text_only).strip()
        if text_only:
            return m.group(0)
        if "<svg" not in body and "data-lucide" not in body:
            return m.group(0)
        href_match = re.search(r'href\s*=\s*[\"\']([^\"\']+)[\"\']', attrs)
        if not href_match:
            return m.group(0)
        href = href_match.group(1).lower()
        label = None
        for needle, candidate in label_map:
            if needle in href:
                label = candidate
                break
        if not label:
            label = "External link"
        count += 1
        new_attrs = f' aria-label="{label}"' + attrs
        return f'<a{new_attrs}>{body}{close_tag}'

    new = anchor_re.sub(repl, html)
    if count:
        report.add(f'add aria-label to {count} icon-only link')
    return new


def add_tabindex_to_scrollable(html: str, report: PageReport) -> str:
    pattern = re.compile(
        r'(<(?:div|pre)\b[^>]*\bclass\s*=\s*[\"\'][^\"\']*overflow-x-auto[^\"\']*[\"\'][^>]*)>'
    )
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        attrs = m.group(1)
        if "tabindex=" in attrs or "role=" in attrs:
            return m.group(0)
        count += 1
        return attrs + ' tabindex="0" role="region" aria-label="Scrollable content">'

    new = pattern.sub(repl, html)
    if count:
        report.add(f'add tabindex=0 + role=region to {count} scrollable container')
    return new


def fix_text_clay_60(html: str, report: PageReport) -> str:
    pattern = re.compile(r'\btext-clay/60\b')
    count = len(pattern.findall(html))
    if not count:
        return html
    new = pattern.sub('text-clay/80', html)
    report.add(f'bump text-clay/60 -> text-clay/80 ({count} occurrences)')
    return new


def fix_text_clay_50(html: str, report: PageReport) -> str:
    pattern = re.compile(r'\btext-clay/50\b')
    count = len(pattern.findall(html))
    if not count:
        return html
    new = pattern.sub('text-clay/80', html)
    report.add(f'bump text-clay/50 -> text-clay/80 ({count} occurrences)')
    return new


def add_tabindex_to_pre(html: str, report: PageReport) -> str:
    pattern = re.compile(r'<pre\b((?![^>]*\btabindex=)[^>]*)>')
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        attrs = m.group(1)
        count += 1
        return f'<pre tabindex="0"{attrs}>'

    new = pattern.sub(repl, html)
    if count:
        report.add(f'add tabindex=0 to {count} <pre> block')
    return new


def swap_link_accent_to_dark(html: str, report: PageReport) -> str:
    """Swap text-accent -> text-accentDark on <a> tags (only if accentDark exists in tailwind config)."""
    if "accentDark" not in html:
        return html
    pattern = re.compile(
        r'(<a\b[^>]*\bclass\s*=\s*[\"\'])([^\"\']*\btext-accent\b[^\"\']*)([\"\'])'
    )
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        prefix, classes, suffix = m.group(1), m.group(2), m.group(3)
        # Skip only if BASE text-accentDark exists (not hover:text-accentDark variant)
        if re.search(r'(?<![\w:-])text-accentDark\b', classes):
            return m.group(0)
        new_classes = re.sub(r'(?<![\w:-])text-accent\b', 'text-accentDark', classes)
        if new_classes == classes:
            return m.group(0)
        count += 1
        return prefix + new_classes + suffix

    new = pattern.sub(repl, html)
    if count:
        report.add(f'swap text-accent -> text-accentDark on {count} <a> tag')
    return new


def fix_pill_text_accent(html: str, report: PageReport) -> str:
    """Tag pills like <span class="bg-accent/10 text-accent ...">label</span> have
    accent-on-tinted-accent (too low contrast). Swap text-accent -> text-ink so
    pill text becomes dark on the lightly-tinted background.
    """
    pattern = re.compile(
        r'(<span\b[^>]*\bclass\s*=\s*[\"\'])([^\"\']*\bbg-accent\b[^\"\']*\btext-accent\b[^\"\']*|[^\"\']*\btext-accent\b[^\"\']*\bbg-accent\b[^\"\']*)([\"\'])'
    )
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        prefix, classes, suffix = m.group(1), m.group(2), m.group(3)
        new_classes = re.sub(r'(?<![\w:-])text-accent\b', 'text-ink', classes)
        if new_classes == classes:
            return m.group(0)
        count += 1
        return prefix + new_classes + suffix

    new = pattern.sub(repl, html)
    if count:
        report.add(f'pill text-accent -> text-ink on {count} <span> with bg-accent tint')
    return new


def fix_text_mist_60(html: str, report: PageReport) -> str:
    pattern = re.compile(r'\btext-mist/(60|80)\b')
    matches = pattern.findall(html)
    if not matches:
        return html
    new = pattern.sub('text-mist', html)
    report.add(f'bump text-mist/60|80 -> text-mist ({len(matches)} occurrences)')
    return new


def fix_stat_accent_on_dark(html: str, report: PageReport) -> str:
    """Stat cards like <p class="text-5xl ... text-accent ..."> on bg-ink fail.

    Inject a CSS override that bumps text-accent to a lighter shade specifically
    when its parent has bg-ink or similar dark background. Simpler: target the
    pattern directly via class.
    """
    if "text-5xl" not in html or "text-accent" not in html:
        return html
    if "/* stat-on-dark-fix */" in html:
        return html
    block = """
/* stat-on-dark-fix */
.bg-ink .text-accent, .bg-zinc-900 .text-accent, .bg-gray-900 .text-accent,
.bg-ink .text-accentDark, .bg-zinc-900 .text-accentDark, .bg-gray-900 .text-accentDark {
  filter: brightness(1.6) saturate(0.85);
}
"""
    if "</style>" not in html:
        return html
    new = html.replace("</style>", block + "</style>", 1)
    if new != html:
        report.add('add stat-on-dark accent brightness fix')
    return new


def fix_green_600(html: str, report: PageReport) -> str:
    pattern = re.compile(r'\btext-green-600\b')
    count = len(pattern.findall(html))
    if not count:
        return html
    new = pattern.sub('text-green-700', html)
    report.add(f'bump text-green-600 -> text-green-700 ({count})')
    return new


def fix_code_red_600(html: str, report: PageReport) -> str:
    """text-red-600 inside <code> on light bg fails contrast. Bump to text-red-700."""
    pattern = re.compile(r'(<code\b[^>]*\bclass\s*=\s*[\"\'][^\"\']*)\btext-red-600\b')
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return m.group(1) + 'text-red-700'

    new = pattern.sub(repl, html)
    if count:
        report.add(f'<code> text-red-600 -> text-red-700 ({count})')
    return new


def fix_terminal_mockup_opacity(html: str, report: PageReport) -> str:
    """Persistent-sessions has a dark terminal mockup. text-white/40 fails on bg-zinc-900-ish."""
    if "text-white/40" not in html:
        return html
    new = html.replace("text-white/40", "text-white/70")
    if new != html:
        report.add('terminal mockup: text-white/40 -> text-white/70')
    return new


def fix_banned_word_color(html: str, report: PageReport) -> str:
    """ai-writing-detox: .banned-word red #ef4444 on #fef2f2 fails contrast (3.44:1).

    Swap to a darker red that passes 4.5:1 against the same pink background.
    """
    if ".banned-word" not in html:
        return html
    if "/* banned-word-fix */" in html:
        return html
    pattern = re.compile(r'(\.banned-word\s*\{[^}]*color\s*:\s*)#ef4444', re.IGNORECASE)
    if not pattern.search(html):
        return html
    new = pattern.sub(r'\g<1>#b91c1c /* banned-word-fix */', html)
    if new != html:
        report.add('banned-word color: #ef4444 -> #b91c1c (passes AA)')
    return new


def fix_venmo_button(html: str, report: PageReport) -> str:
    if ".s-venmo{background:#008CFF}" not in html and ".s-venmo{background:#008cff}" not in html:
        return html
    new = html.replace(".s-venmo{background:#008CFF}", ".s-venmo{background:#006bbf}")
    new = new.replace(".s-venmo{background:#008cff}", ".s-venmo{background:#006bbf}")
    if new != html:
        report.add('Venmo support button: bg #008CFF -> #006bbf (passes AA)')
    return new


def fix_about_page_links(html: str, report: PageReport) -> str:
    """about/index.html has no accentDark token. Add CSS override for prose links to a darker accent."""
    if 'accent' not in html or 'accentDark' in html:
        return html
    if '/* about-link-fix */' in html:
        return html
    block = """
/* about-link-fix */
main p a, main li a { color: #155e75; text-decoration: underline; text-underline-offset: 0.15em; }
"""
    if "</style>" not in html:
        return html
    new = html.replace("</style>", block + "</style>", 1)
    if new != html:
        report.add('about-page: add darker link color override')
    return new


def fix_text_accent_bold(html: str, report: PageReport) -> str:
    """Bold accent text on white cards fails AA (#0891b2 ~3.4:1).

    Only target <span> elements with class containing both 'text-accent' and 'font-bold'.
    Replace text-accent -> text-accentDark on those spans only.
    """
    pattern = re.compile(
        r'(<span\b[^>]*\bclass\s*=\s*[\"\'])([^\"\']*\btext-accent\b[^\"\']*\bfont-bold\b[^\"\']*|[^\"\']*\bfont-bold\b[^\"\']*\btext-accent\b[^\"\']*)([\"\'])'
    )
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        prefix, classes, suffix = m.group(1), m.group(2), m.group(3)
        if "text-accentDark" in classes:
            return m.group(0)
        new_classes = re.sub(r'\btext-accent\b', 'text-accentDark', classes)
        count += 1
        return prefix + new_classes + suffix

    new = pattern.sub(repl, html)
    if count:
        report.add(f'swap text-accent -> text-accentDark on {count} bold label')
    return new


def fix_text_mist_token(html: str, report: PageReport) -> str:
    """Replace mist token color #6b6b6b with #525252 in tailwind config block.

    Only affects pages that define a tailwind theme.colors.mist override.
    """
    pattern = re.compile(r"(mist\s*:\s*['\"])#6b6b6b(['\"])")
    if not pattern.search(html):
        return html
    new = pattern.sub(r"\g<1>#525252\g<2>", html)
    report.add('update mist token #6b6b6b -> #525252')
    return new


def fix_homepage_footer_canvas_opacity(html: str, report: PageReport) -> str:
    """Homepage footer uses text-canvas/20 and text-canvas/30 on bg-ink.

    Composite contrast ~1.5:1. Bump to /60 (~3.6:1, passes AA large) and /70.
    The h6 labels are 10px tracked-letterspaced uppercase — visually small but
    semantically headings. Bumping to /70 gives ~5:1 which passes AA normal.
    """
    changed = False
    new = html
    if "text-canvas/20" in new:
        new = new.replace('text-canvas/20', 'text-canvas/70')
        changed = True
    if "text-canvas/30" in new:
        new = new.replace('text-canvas/30', 'text-canvas/70')
        changed = True
    if changed:
        report.add('homepage footer: text-canvas/20|30 -> text-canvas/70')
    return new


def fix_pdf_playground_opacity_60(html: str, report: PageReport) -> str:
    """opacity-60 on mockup feature cards dims everything below contrast threshold.

    Bump to opacity-90 — preserves "older/dimmer" visual cue without breaking AA.
    Only targets pdf-playground's mockup pattern: feature-card + opacity-60.
    """
    pattern = re.compile(r'(class\s*=\s*[\"\'][^\"\']*\bfeature-card\b[^\"\']*?\b)opacity-60(\b[^\"\']*[\"\'])')
    count = 0

    def repl(m):
        nonlocal count
        count += 1
        return m.group(1) + 'opacity-90' + m.group(2)

    new = pattern.sub(repl, html)
    if count:
        report.add(f'feature-card opacity-60 -> opacity-90 ({count})')
    return new


def fix_pdf_playground_mockup_chrome(html: str, report: PageReport) -> str:
    """pdf-playground mockup uses bg-ink/20 text-ink badge + text-mist on cream.
    Inject targeted CSS overrides for those mockup-specific patterns.
    """
    if 'pdf-playground' not in html and 'bg-ink/20' not in html:
        return html
    if '/* pdf-mockup-fix */' in html:
        return html
    block = """
/* pdf-mockup-fix */
.bg-ink\\/20.text-ink, span.bg-ink\\/20.text-ink { background-color: rgba(18,18,18,0.85) !important; color: #ffffff !important; }
[class*="bg-canvas"] [class~="text-mist"], [class*="bg-cream"] [class~="text-mist"], [style*="background:#f8"] [class~="text-mist"], [style*="background-color:#f8"] [class~="text-mist"] { color: #2d2d2d !important; }
"""
    if "</style>" not in html:
        return html
    new = html.replace("</style>", block + "</style>", 1)
    if new != html:
        report.add('add pdf-playground mockup chrome contrast fix')
    return new


def fix_pdf_playground_mockup_h1(html: str, report: PageReport) -> str:
    if 'id="doc-title"' not in html:
        return html
    pattern = re.compile(r'<h1(\s+id="doc-title"[^>]*)>([\s\S]*?)</h1>')
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        attrs = m.group(1)
        body = m.group(2)
        count += 1
        return f'<div role="heading" aria-level="2"{attrs}>{body}</div>'

    new = pattern.sub(repl, html)
    if count:
        report.add(f'demote {count} mockup h1 to role=heading aria-level=2')
    return new


def add_nav_aria_label(html: str, report: PageReport) -> str:
    pattern = re.compile(r"<nav\b((?![^>]*\baria-label=)[^>]*)>", re.IGNORECASE)
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f'<nav aria-label="Primary"{m.group(1)}>'

    new = pattern.sub(repl, html, count=1)
    if count:
        report.add('add aria-label="Primary" to <nav>')
    return new


def stamp_marker(html: str) -> str:
    if HEAD_MARKER in html:
        return html
    return html.replace("</head>", "    " + HEAD_MARKER + "\n</head>", 1)


PASSES = [
    inject_universal_css,
    inject_hero_overlay,
    inject_reveal_noscript,
    add_skip_link,
    add_main_id,
    add_nav_aria_label,
    add_aria_hidden_to_svgs,
    add_rel_noopener,
    add_aria_label_to_icon_links,
    add_tabindex_to_scrollable,
    fix_text_clay_60,
    fix_text_clay_50,
    fix_text_accent_bold,
    swap_link_accent_to_dark,
    fix_text_mist_token,
    fix_homepage_footer_canvas_opacity,
    fix_pdf_playground_mockup_h1,
    fix_pdf_playground_opacity_60,
    fix_pdf_playground_mockup_chrome,
    fix_venmo_button,
    fix_about_page_links,
    fix_banned_word_color,
    fix_pill_text_accent,
    fix_text_mist_60,
    fix_code_red_600,
    fix_terminal_mockup_opacity,
    fix_stat_accent_on_dark,
    fix_green_600,
    add_tabindex_to_pre,
]


def patch_file(path: Path) -> PageReport:
    report = PageReport(path)
    original = path.read_text(encoding="utf-8")
    html = original
    for fn in PASSES:
        html = fn(html, report)
    if report.changes:
        html = stamp_marker(html)
    if html != original:
        path.write_text(html, encoding="utf-8")
    return report


def main() -> int:
    pages = find_pages()
    print(f"patching {len(pages)} pages under {DOCS}")
    changed = 0
    for p in pages:
        report = patch_file(p)
        if report.changes:
            changed += 1
            rel = p.relative_to(ROOT)
            print(f"\n{rel}")
            for c in report.changes:
                print(f"  - {c}")
    print(f"\nchanged: {changed} of {len(pages)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
