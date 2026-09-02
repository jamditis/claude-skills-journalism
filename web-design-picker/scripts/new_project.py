#!/usr/bin/env python3
"""Scaffold a two-to-five direction web-design-picker project."""
from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from itertools import combinations
from pathlib import Path

from _common import SKILL_ROOT, ensure_clean_dir, slugify, validate_slug, write_json, write_text
from make_favicons import FaviconError, generate_favicon_set, render_svg

DIRECTION_SEEDS = [
    {
        "key": "evidence-led",
        "label": "Evidence-led editorial",
        "description": "A proof-first direction organized around real work, artifacts, and outcomes.",
        "accent": "#d84a32",
        "background": "#f3f1ea",
        "text": "#151719",
        "line": "#9b9c98",
    },
    {
        "key": "operational-system",
        "label": "Operational system",
        "description": "A task-oriented direction that makes workflow, tools, and handoffs visible.",
        "accent": "#41b6d4",
        "background": "#101416",
        "text": "#f3f6f7",
        "line": "#4d575b",
    },
    {
        "key": "brand-statement",
        "label": "Brand statement",
        "description": "A forceful, typography-led direction built around one memorable organizing idea.",
        "accent": "#f06428",
        "background": "#f0eee8",
        "text": "#121212",
        "line": "#121212",
    },
    {
        "key": "reference-manual",
        "label": "Reference manual",
        "description": "A structured, information-dense direction that behaves like a useful field guide.",
        "accent": "#1d6c5b",
        "background": "#f6f7f3",
        "text": "#15201d",
        "line": "#75827e",
    },
    {
        "key": "human-narrative",
        "label": "Human narrative",
        "description": "A story-led direction that foregrounds people, context, and consequences.",
        "accent": "#9c3f56",
        "background": "#fffaf4",
        "text": "#261b1e",
        "line": "#a79b9e",
    },
]

DISTINCTNESS_DIMENSIONS = [
    "positioning-and-primary-message",
    "information-architecture",
    "hero-opening-composition",
    "typography",
    "grid-and-spatial-rhythm",
    "shape-and-edge-language",
    "color-logic",
    "image-and-video-treatment",
    "interaction-model",
    "cta-and-conversion-pattern",
    "emotional-register",
]


def mark_svg(label: str, accent: str, background: str, text: str, index: int) -> str:
    safe = html.escape(label[:1].upper())
    if index % 3 == 0:
        form = f'<path d="M38 30 70 64 38 98M90 30 58 64 90 98" fill="none" stroke="{text}" stroke-width="12" stroke-linecap="square"/>'
    elif index % 3 == 1:
        form = f'<rect x="29" y="29" width="70" height="70" fill="none" stroke="{text}" stroke-width="10"/><path d="M29 82 99 46" stroke="{accent}" stroke-width="12"/>'
    else:
        form = f'<circle cx="64" cy="64" r="40" fill="none" stroke="{text}" stroke-width="10"/><text x="64" y="78" text-anchor="middle" font-family="Arial,Helvetica,sans-serif" font-size="48" font-weight="700" fill="{accent}">{safe}</text>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128" role="img" aria-label="Placeholder mark for {html.escape(label)}"><rect width="128" height="128" fill="{background}"/>{form}</svg>'''


def lockup_svg(project_name: str, label: str, mark_href: str, background: str, text: str, accent: str) -> str:
    # Uses live text for easy editing. Production work should also export outlined artwork.
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-label="{html.escape(project_name)} {html.escape(label)} placeholder lockup"><rect width="1200" height="300" fill="{background}"/><image href="{html.escape(mark_href)}" x="50" y="50" width="200" height="200"/><text x="300" y="142" font-family="Arial,Helvetica,sans-serif" font-size="72" font-weight="700" fill="{text}">{html.escape(project_name)}</text><text x="303" y="199" font-family="Courier New,monospace" font-size="26" fill="{accent}">{html.escape(label)}</text></svg>'''


def palette_files(output_dir: Path, direction: dict) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    colors = {
        "background": direction["background"],
        "text": direction["text"],
        "accent": direction["accent"],
        "line": direction["line"],
    }
    swatch_w = 280
    swatches = []
    for index, (name, color) in enumerate(colors.items()):
        x = index * swatch_w
        swatches.append(
            f'<rect x="{x}" width="{swatch_w}" height="180" fill="{color}"/>'
            f'<text x="{x + 18}" y="218" font-family="Arial,Helvetica,sans-serif" font-size="22" font-weight="700" fill="#111">{name}</text>'
            f'<text x="{x + 18}" y="252" font-family="Courier New,monospace" font-size="18" fill="#333">{color.upper()}</text>'
        )
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{swatch_w * len(colors)}" height="280" viewBox="0 0 {swatch_w * len(colors)} 280"><rect width="100%" height="100%" fill="#fff"/>{"".join(swatches)}</svg>'
    svg_path = output_dir / "palette.svg"
    css_path = output_dir / "color-tokens.css"
    json_path = output_dir / "color-tokens.json"
    write_text(svg_path, svg)
    write_text(css_path, ":root {\n" + "\n".join(f"  --color-{name}: {value};" for name, value in colors.items()) + "\n}\n")
    write_json(json_path, {"color": colors})
    png_path = output_dir / "palette.png"
    try:
        png_path.write_bytes(render_svg(svg_path, swatch_w * len(colors), 280))
    except FaviconError:
        return [svg_path, css_path, json_path]
    return [svg_path, png_path, css_path, json_path]


def favicon_file_entries(prefix: str) -> list[dict[str, str]]:
    return [
        {"label": "SVG", "href": f"{prefix}/favicon.svg", "format": "SVG", "notes": "Editable vector"},
        {"label": "ICO", "href": f"{prefix}/favicon.ico", "format": "ICO", "notes": "Browser fallback"},
        {"label": "32 PNG", "href": f"{prefix}/favicon-32.png", "format": "PNG", "dimensions": "32×32"},
        {"label": "Touch", "href": f"{prefix}/favicon-180.png", "format": "PNG", "dimensions": "180×180"},
        {"label": "192 PNG", "href": f"{prefix}/favicon-192.png", "format": "PNG", "dimensions": "192×192"},
        {"label": "512 PNG", "href": f"{prefix}/favicon-512.png", "format": "PNG", "dimensions": "512×512"},
    ]


def render_concept(template: str, project_name: str, direction: dict) -> str:
    replacements = {
        "__PROJECT_NAME__": html.escape(project_name),
        "__DIRECTION_LABEL__": html.escape(str(direction["label"])),
        "__DIRECTION_DESCRIPTION__": html.escape(str(direction["description"])),
        "__DIRECTION_KEY__": direction["key"],
        "__BACKGROUND__": direction["background"],
        "__TEXT__": direction["text"],
        "__ACCENT__": direction["accent"],
        "__LINE__": direction["line"],
    }
    for old, new in replacements.items():
        template = template.replace(old, str(new))
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--name", required=True, help="Organization or project name")
    parser.add_argument("--slug", help="Output slug; generated from name by default")
    parser.add_argument("--directions", type=int, default=3, choices=range(2, 6))
    parser.add_argument("--force", action="store_true", help="Replace an existing project directory")
    args = parser.parse_args()

    root = args.project_dir.resolve()
    if root.exists() and any(root.iterdir()) and not args.force:
        print(f"error: {root} is not empty; use --force to replace it", file=sys.stderr)
        return 1
    try:
        slug = validate_slug(args.slug) if args.slug else slugify(args.name)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    ensure_clean_dir(root)
    directions = []
    for index, seed in enumerate(DIRECTION_SEEDS[: args.directions]):
        direction = dict(seed)
        direction["file"] = f"concepts/{direction['key']}.html"
        direction["tradeoff"] = "Replace with the real strategic tradeoff before presentation."
        directions.append(direction)

    project = {
        "name": args.name,
        "slug": slug,
        "language": "en",
        "review_title": f"{args.name}: website design review",
        "review_subtitle": "Website direction review",
        "review_description": f"Compare responsive website design directions for {args.name}.",
        "theme_color": "#111315",
        "active_color": directions[0]["accent"],
        "robots": "noindex,nofollow",
        "default_direction": directions[0]["key"],
        "library_note": "Concept assets are supplied for review. Confirm trademark, licensing, font, privacy, and production requirements before public use.",
        "review_favicon": "assets/brand/review/favicon.svg",
        "asset_zip_name": f"{slug}-all-design-assets.zip",
    }

    for directory in [
        "config",
        "src/concepts",
        "src/assets/brand/review",
        "src/assets/brand",
        "src/assets/media/originals",
        "src/assets/media/web",
        "design-package/logos",
        "design-package/favicons",
        "design-package/palettes",
        "design-package/graphic-elements",
        "design-package/media/originals",
        "design-package/media/web",
        "design-package/notes",
        "dist",
        "previews",
        "qa",
        "deliverables",
    ]:
        (root / directory).mkdir(parents=True, exist_ok=True)

    concept_template = (SKILL_ROOT / "assets/concept-starter.html").read_text(encoding="utf-8")

    # Neutral review-shell identity.
    review_mark = root / "src/assets/brand/review/favicon.svg"
    write_text(review_mark, mark_svg(args.name, "#f06428", "#111315", "#ffffff", 1))
    generate_favicon_set(review_mark, review_mark.parent, padding=0.05)
    shared_favicon_dir = root / "design-package/favicons/review-shell"
    shutil.copytree(review_mark.parent, shared_favicon_dir, dirs_exist_ok=True)

    shared_groups = [
        {
            "title": "Review-shell favicon family",
            "description": "Neutral icons used by the comparison picker and asset catalog.",
            "preview": "assets/design-package/favicons/review-shell/favicon-192.png",
            "preview_alt": f"Placeholder review favicon for {args.name}",
            "files": favicon_file_entries("assets/design-package/favicons/review-shell"),
        }
    ]
    asset_directions = []

    for index, direction in enumerate(directions):
        key = direction["key"]
        concept_file = root / "src" / direction["file"]
        write_text(concept_file, render_concept(concept_template, args.name, direction))

        logo_dir = root / "design-package/logos" / key
        logo_dir.mkdir(parents=True, exist_ok=True)
        mark_path = logo_dir / f"{slug}-{key}-mark.svg"
        write_text(mark_path, mark_svg(direction["label"], direction["accent"], direction["background"], direction["text"], index))
        lockup_path = logo_dir / f"{slug}-{key}-lockup.svg"
        write_text(lockup_path, lockup_svg(args.name, direction["label"], mark_path.name, direction["background"], direction["text"], direction["accent"]))

        favicon_dir = root / "src/assets/brand" / key
        generate_favicon_set(mark_path, favicon_dir, padding=0.05)
        design_favicon_dir = root / "design-package/favicons" / key
        shutil.copytree(favicon_dir, design_favicon_dir, dirs_exist_ok=True)
        palette_output = root / "design-package/palettes" / key
        palette_outputs = palette_files(palette_output, direction)

        group_prefix = f"assets/design-package"
        groups = [
            {
                "title": "Concept identity",
                "description": "Starter mark and editable lockup. Replace with approved production artwork.",
                "preview": f"{group_prefix}/logos/{key}/{slug}-{key}-lockup.svg",
                "preview_alt": f"Placeholder identity for {direction['label']}",
                "files": [
                    {"label": "Mark SVG", "href": f"{group_prefix}/logos/{key}/{slug}-{key}-mark.svg", "format": "SVG"},
                    {"label": "Lockup SVG", "href": f"{group_prefix}/logos/{key}/{slug}-{key}-lockup.svg", "format": "SVG", "notes": "Live text; export outlined artwork for final handoff"},
                ],
            },
            {
                "title": "Favicon family",
                "description": "Direction-specific SVG, ICO, touch icon, and app-icon sizes.",
                "preview": f"{group_prefix}/favicons/{key}/favicon-192.png",
                "preview_alt": f"Favicon for {direction['label']}",
                "files": favicon_file_entries(f"{group_prefix}/favicons/{key}"),
            },
            {
                "title": "Color palette and tokens",
                "description": "Visual palette sheet plus machine-readable CSS and JSON tokens.",
                "preview": f"{group_prefix}/palettes/{key}/palette.svg",
                "preview_alt": f"Color palette for {direction['label']}",
                "files": [
                    {
                        "label": output.suffix.lstrip(".").upper(),
                        "href": f"{group_prefix}/palettes/{key}/{output.name}",
                        "format": output.suffix.lstrip(".").upper(),
                    }
                    for output in palette_outputs
                ],
            },
        ]
        asset_directions.append({"key": key, "label": direction["label"], "accent": direction["accent"], "groups": groups})

    assets = {"shared": shared_groups, "directions": asset_directions}
    write_json(root / "config/project.json", project)
    write_json(root / "config/directions.json", directions)
    write_json(root / "config/assets.json", assets)

    pairs = []
    for a, b in combinations(directions, 2):
        pairs.append({
            "a": a["key"],
            "b": b["key"],
            "scores": {dimension: None for dimension in DISTINCTNESS_DIMENSIONS},
            "notes": "",
        })
    write_json(root / "config/distinctness.json", {"target": 15, "dimensions": DISTINCTNESS_DIMENSIONS, "pairs": pairs})

    brief = f"""# {args.name} website design brief

## Audience

## Primary decision or conversion

## Current site and source files

## Verified positioning and services

## Strongest differentiator or proof

## Required content

## Constraints and anti-patterns

## Unverified claims to exclude

## Hosting and delivery target
"""
    write_text(root / "BRIEF.md", brief)
    write_text(root / "CLAIM-LEDGER.md", "# Claim ledger\n\n| Claim | Source | Status | Use in concepts |\n|---|---|---|---|\n")
    write_text(
        root / "DIRECTION-BRIEFS.md",
        "# Direction briefs\n\nFor each direction, document the strategic thesis, five-second impression, content rule, visual grammar, proof placement, interaction ceiling, rejected conventions, tradeoff, and likely chooser.\n",
    )
    write_text(
        root / "README.md",
        f"""# {args.name} web-design-picker project

1. Complete `BRIEF.md`, `CLAIM-LEDGER.md`, and `DIRECTION-BRIEFS.md`.
2. Rename and refine the directions in `config/directions.json`.
3. Replace each starter page under `src/concepts/` with a genuinely distinct, complete responsive concept.
4. Add production assets to `design-package/` and register every variant in `config/assets.json`.
5. Score every pair in `config/distinctness.json`.
6. Run:

```bash
python PATH_TO_SKILL/scripts/run_factory.py . --test-downloads
```

Cloudflare Drop receives `deliverables/{slug}-cloudflare-drop.zip`.
""",
    )
    write_text(root / "design-package/notes/README.md", "# Asset notes\n\nRecord source, creator, license, modifications, trademark constraints, and intended use for every third-party or generated asset.\n")

    print(f"Created {root}")
    print("Next: complete the evidence and direction briefs, replace the starter concepts, register assets, and score distinctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
