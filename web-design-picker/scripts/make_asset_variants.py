#!/usr/bin/env python3
"""Create reusable SVG/raster asset variants without distributing font files."""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required: pip install Pillow") from exc

try:
    import cairosvg
except ImportError:
    cairosvg = None


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


def render_svg(source: Path, long_edge: int) -> Image.Image:
    if cairosvg is None:
        raise SystemExit("CairoSVG is required for SVG input: pip install CairoSVG")
    png = cairosvg.svg2png(url=str(source), output_width=long_edge)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def render_raster(source: Path, long_edge: int) -> Image.Image:
    image = Image.open(source).convert("RGBA")
    ratio = long_edge / max(image.width, image.height)
    width = max(1, round(image.width * ratio))
    height = max(1, round(image.height * ratio))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--name", help="Output stem; source stem by default")
    parser.add_argument("--sizes", type=parse_sizes, default=[512, 1800], help="Comma-separated longest-edge PNG sizes")
    parser.add_argument("--copy-vector", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.exists():
        print(f"error: source not found: {source}", file=sys.stderr)
        return 1
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.name or source.stem

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
