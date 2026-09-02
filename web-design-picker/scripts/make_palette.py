#!/usr/bin/env python3
"""Generate SVG/PNG palette sheets and CSS/JSON design tokens."""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

from make_favicons import FaviconError, render_svg

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def parse_token(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("tokens must use name=#rrggbb")
    name, color = value.split("=", 1)
    name = re.sub(r"[^a-z0-9-]+", "-", name.strip().lower()).strip("-")
    color = color.strip()
    if not name or not HEX.match(color):
        raise argparse.ArgumentTypeError(f"invalid token: {value}")
    return name, color.lower()


def contrast_text(hex_color: str) -> str:
    r, g, b = (int(hex_color[index:index + 2], 16) for index in (1, 3, 5))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#111111" if luminance > 0.6 else "#ffffff"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--name", default="palette")
    parser.add_argument("--title", default="Color palette")
    parser.add_argument("tokens", nargs="+", type=parse_token, help="Token assignments such as background=#f2efe8")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    tokens = dict(args.tokens)

    swatch_width = 260
    swatch_height = 150
    width = swatch_width * len(tokens)
    height = 220
    swatches = []
    for index, (name, color) in enumerate(tokens.items()):
        x = index * swatch_width
        text = contrast_text(color)
        swatches.append(
            f'<rect x="{x}" y="0" width="{swatch_width}" height="{swatch_height}" fill="{color}"/>'
            f'<text x="{x + 18}" y="42" fill="{text}" font-family="Arial, Helvetica, sans-serif" font-size="18" font-weight="700">{html.escape(name)}</text>'
            f'<text x="{x + 18}" y="126" fill="{text}" font-family="Courier New, monospace" font-size="16">{color.upper()}</text>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
        + "".join(swatches)
        + f'<text x="18" y="194" fill="#111111" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="700">{html.escape(args.title)}</text>'
        + '</svg>'
    )

    svg_path = output_dir / f"{args.name}.svg"
    png_path = output_dir / f"{args.name}.png"
    css_path = output_dir / "color-tokens.css"
    json_path = output_dir / "color-tokens.json"

    svg_path.write_text(svg, encoding="utf-8")
    try:
        png_path.write_bytes(render_svg(svg_path, width, height))
    except FaviconError as exc:
        raise SystemExit(str(exc)) from exc
    css_lines = [":root {"] + [f"  --color-{name}: {color};" for name, color in tokens.items()] + ["}"]
    css_path.write_text("\n".join(css_lines) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps({"color": tokens}, indent=2) + "\n", encoding="utf-8")

    for path in [svg_path, png_path, css_path, json_path]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
