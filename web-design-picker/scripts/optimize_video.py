#!/usr/bin/env python3
"""Optimize supplied video for static website use and create poster frames."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from _common import format_bytes


def run(command: list[str]) -> None:
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed:\n{' '.join(command)}\n{result.stderr[-4000:]}")


def duration_seconds(source: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(source)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def parse_crop(value: str) -> tuple[int, int, int, int]:
    try:
        x, y, width, height = (int(part) for part in value.split(":"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Crop must use X:Y:W:H with integer values") from exc
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("Crop X and Y must be non-negative; W and H must be positive")
    return x, y, width, height


def crop_filter(crop: tuple[int, int, int, int] | None) -> str | None:
    if crop is None:
        return None
    x, y, width, height = crop
    return f"crop={width}:{height}:{x}:{y}"


def scale_filter(width: int, fps: int, crop: tuple[int, int, int, int] | None = None) -> str:
    filters = [filter_value for filter_value in (crop_filter(crop), f"scale='min({width},iw)':-2:flags=lanczos", f"fps={fps}") if filter_value]
    return ",".join(filters)


def poster_filter(width: int, crop: tuple[int, int, int, int] | None = None) -> str:
    filters = [filter_value for filter_value in (crop_filter(crop), f"scale='min({width},iw)':-2:flags=lanczos") if filter_value]
    return ",".join(filters)


def poster_times(duration: float, supplied: list[float] | None) -> list[float]:
    if supplied:
        return [max(0.0, min(value, max(0.0, duration - 0.05))) for value in supplied]
    if duration <= 1:
        return [0.0]
    return [min(0.5, duration * 0.1), duration * 0.5, duration * 0.78]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--name", help="Output stem; source stem by default")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--mp4-crf", type=int, default=24)
    parser.add_argument("--webm-crf", type=int, default=34)
    parser.add_argument("--keep-audio", action="store_true")
    parser.add_argument("--crop", type=parse_crop, metavar="X:Y:W:H", help="Crop before scaling video, poster, and GIF derivatives")
    parser.add_argument("--poster-times", type=float, nargs="*")
    parser.add_argument("--gif", action="store_true", help="Create a short GIF fallback")
    parser.add_argument("--gif-start", type=float, default=0.0)
    parser.add_argument("--gif-duration", type=float, default=6.0)
    parser.add_argument("--gif-width", type=int, default=800)
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        print("error: ffmpeg and ffprobe must be installed", file=sys.stderr)
        return 1
    source = args.source.resolve()
    if not source.exists():
        print(f"error: source not found: {source}", file=sys.stderr)
        return 1
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.name or source.stem
    audio = [] if args.keep_audio else ["-an"]
    vf = scale_filter(args.width, args.fps, args.crop)

    mp4 = output_dir / f"{stem}.mp4"
    webm = output_dir / f"{stem}.webm"
    try:
        run([
            "ffmpeg", "-y", "-i", str(source), "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", str(args.mp4_crf),
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", *audio, str(mp4),
        ])
        run([
            "ffmpeg", "-y", "-i", str(source), "-vf", vf,
            "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", str(args.webm_crf),
            "-row-mt", "1", *audio, str(webm),
        ])

        duration = duration_seconds(source)
        labels = ["overview", "middle", "detail"]
        poster_outputs: list[Path] = []
        for index, timestamp in enumerate(poster_times(duration, args.poster_times)):
            label = labels[index] if index < len(labels) else f"frame-{index + 1}"
            jpg = output_dir / f"{stem}-poster-{label}.jpg"
            webp = output_dir / f"{stem}-poster-{label}.webp"
            run([
                "ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(source),
                "-frames:v", "1", "-vf", poster_filter(args.width, args.crop),
                "-q:v", "3", str(jpg),
            ])
            run([
                "ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(source),
                "-frames:v", "1", "-vf", poster_filter(args.width, args.crop),
                "-quality", "82", str(webp),
            ])
            poster_outputs.extend([jpg, webp])

        gif = None
        if args.gif:
            gif = output_dir / f"{stem}-loop.gif"
            palette = output_dir / f".{stem}-palette.png"
            gif_vf = scale_filter(args.gif_width, 12, args.crop)
            run([
                "ffmpeg", "-y", "-ss", str(args.gif_start), "-t", str(args.gif_duration),
                "-i", str(source), "-vf", f"{gif_vf},palettegen=max_colors=128", str(palette),
            ])
            run([
                "ffmpeg", "-y", "-ss", str(args.gif_start), "-t", str(args.gif_duration),
                "-i", str(source), "-i", str(palette),
                "-lavfi", f"{gif_vf}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5", str(gif),
            ])
            palette.unlink(missing_ok=True)

    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    outputs = [mp4, webm, *poster_outputs] + ([gif] if gif else [])
    for path in outputs:
        print(f"{path}  {format_bytes(path.stat().st_size)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
