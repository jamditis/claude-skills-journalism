#!/usr/bin/env python3
"""Generate a complete SVG/ICO/PNG favicon family."""
from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class FaviconError(RuntimeError):
    pass


def render_svg(source: Path, render_width: int, render_height: int | None = None) -> bytes:
    """Render SVG bytes with resvg, or use CairoSVG when resvg is unavailable."""
    render_height = render_height or render_width
    executable_name = "resvg.exe" if sys.platform == "win32" else "resvg"
    resvg = shutil.which("resvg")
    if not resvg:
        adjacent = Path(sys.executable).with_name(executable_name)
        if adjacent.is_file():
            resvg = str(adjacent)

    if resvg:
        with tempfile.TemporaryDirectory(prefix="web-design-picker-svg-") as temporary:
            output = Path(temporary) / "rendered.png"
            result = subprocess.run(
                [
                    resvg,
                    str(source),
                    str(output),
                    "--width",
                    str(render_width),
                    "--height",
                    str(render_height),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and output.is_file():
                return output.read_bytes()
            detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
            raise FaviconError(f"resvg could not render {source.name}: {detail}")

    try:
        import cairosvg

        return cairosvg.svg2png(
            url=str(source),
            output_width=render_width,
            output_height=render_height,
        )
    except (ImportError, OSError) as exc:
        raise FaviconError(
            "SVG input requires resvg-cli, or CairoSVG with its native Cairo library: "
            "python -m pip install resvg-cli"
        ) from exc


def load_image(source: Path, render_size: int):
    try:
        from PIL import Image
    except ImportError as exc:
        raise FaviconError("Pillow is required: python -m pip install Pillow") from exc
    if source.suffix.lower() == ".svg":
        png = render_svg(source, render_size)
        return Image.open(io.BytesIO(png)).convert("RGBA")
    return Image.open(source).convert("RGBA")


def square_fit(image, size: int, background: str, padding: float):
    from PIL import Image, ImageColor

    fill = (0, 0, 0, 0) if background == "transparent" else ImageColor.getcolor(background, "RGBA")
    canvas = Image.new("RGBA", (size, size), fill)
    inner = max(1, round(size * (1 - padding * 2)))
    work = image.copy()
    work.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    x = (size - work.width) // 2
    y = (size - work.height) // 2
    canvas.alpha_composite(work, (x, y))
    return canvas


def generate_favicon_set(
    source: Path,
    output_dir: Path,
    *,
    background: str = "transparent",
    padding: float = 0.08,
) -> list[Path]:
    """Generate SVG (when supplied), ICO, 32, 180, 192 and 512 PNGs."""
    from PIL import Image

    source = source.resolve()
    output_dir = output_dir.resolve()
    if not source.is_file():
        raise FaviconError(f"Source image does not exist: {source}")
    if not 0 <= padding <= 0.35:
        raise FaviconError("padding must be between 0 and .35")
    output_dir.mkdir(parents=True, exist_ok=True)

    base = load_image(source, 1024)
    master = square_fit(base, 1024, background, padding)
    generated: list[Path] = []
    for size in (32, 180, 192, 512):
        path = output_dir / f"favicon-{size}.png"
        master.resize((size, size), Image.Resampling.LANCZOS).save(path, "PNG", optimize=True)
        generated.append(path)

    ico = output_dir / "favicon.ico"
    master.save(ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    generated.append(ico)

    if source.suffix.lower() == ".svg":
        svg = output_dir / "favicon.svg"
        if source != svg.resolve():
            shutil.copy2(source, svg)
        generated.insert(0, svg)
    else:
        png = output_dir / "favicon.png"
        master.save(png, "PNG", optimize=True)
        generated.insert(0, png)
    return generated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--background", default="transparent", help="transparent or a CSS color such as #ffffff")
    parser.add_argument("--padding", type=float, default=0.08, help="Fractional edge padding, from 0 to .35")
    args = parser.parse_args(argv)
    try:
        generated = generate_favicon_set(
            args.source,
            args.output_dir,
            background=args.background,
            padding=args.padding,
        )
        print("Generated:")
        for path in generated:
            print(path)
        return 0
    except (FaviconError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
