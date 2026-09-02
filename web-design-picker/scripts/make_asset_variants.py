#!/usr/bin/env python3
"""Create reusable SVG/raster asset variants without distributing font files."""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path
from xml.etree import ElementTree

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: pip install Pillow") from exc

from _common import validate_output_stem
from make_favicons import FaviconError, render_svg as render_svg_png


def parse_sizes(value: str) -> list[int]:
    sizes = []
    for piece in value.split(","):
        piece = piece.strip()
        if not piece:
            continue
        size = int(piece)
        if size < 16 or size > 10000:
            raise argparse.ArgumentTypeError("sizes must be between 16 and 10000 pixels")
        sizes.append(size)
    return sorted(set(sizes))


def svg_aspect_ratio(source: Path) -> float | None:
    try:
        root = ElementTree.parse(source).getroot()
    except ElementTree.ParseError:
        return None
    view_box = root.get("viewBox", "").replace(",", " ").split()
    if len(view_box) == 4:
        try:
            width, height = float(view_box[2]), float(view_box[3])
            if width > 0 and height > 0:
                return width / height
        except ValueError:
            pass
    return None


def fit_longest_edge(image: Image.Image, long_edge: int) -> Image.Image:
    longest = max(image.width, image.height)
    if longest == long_edge:
        return image
    ratio = long_edge / longest
    width = max(1, round(image.width * ratio))
    height = max(1, round(image.height * ratio))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def render_svg(source: Path, long_edge: int) -> Image.Image:
    aspect_ratio = svg_aspect_ratio(source)
    render_width = long_edge if aspect_ratio is None or aspect_ratio >= 1 else max(1, round(long_edge * aspect_ratio))
    try:
        png = render_svg_png(source, render_width)
    except FaviconError as exc:
        raise SystemExit(str(exc)) from exc
    return fit_longest_edge(Image.open(io.BytesIO(png)).convert("RGBA"), long_edge)


def render_raster(source: Path, long_edge: int) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    ratio = long_edge / max(image.width, image.height)
    width = max(1, round(image.width * ratio))
    height = max(1, round(image.height * ratio))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--name", help="Output stem; source stem by default")
    parser.add_argument("--sizes", type=parse_sizes, default=[512, 1800], help="Comma-separated longest-edge PNG sizes")
    parser.add_argument("--copy-vector", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args(argv)

    source = args.source.resolve()
    if not source.exists():
        print(f"error: source not found: {source}", file=sys.stderr)
        return 1
    try:
        stem = validate_output_stem(args.name or source.stem)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = []
    if source.suffix.lower() == ".svg" and args.copy_vector:
        vector_path = output_dir / f"{stem}.svg"
        shutil.copy2(source, vector_path)
        outputs.append(vector_path)

    for size in args.sizes:
        if source.suffix.lower() == ".svg":
            image = render_svg(source, size)
        else:
            image = render_raster(source, size)
        path = output_dir / f"{stem}-{size}.png"
        image.save(path, "PNG", optimize=True)
        outputs.append(path)

    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
