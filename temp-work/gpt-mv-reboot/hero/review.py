#!/usr/bin/env python3
"""Fast review exports for the GPT MV sequence.

This tool deliberately wraps the already-validated renderer instead of adding a
second scene implementation. It can render exact timeline stills into a contact
sheet or export only a requested time range, which keeps later section review
cheap and reproducible.
"""
from __future__ import annotations

import argparse
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

import sequence

base = sequence.base
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def run(cmd):
    subprocess.run(cmd, check=True)


def parse_times(raw: str) -> list[float]:
    out = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        value = float(item)
        if not 0 <= value < base.DURATION:
            raise ValueError(f"review time outside film: {value}")
        out.append(value)
    if not out:
        raise ValueError("at least one review time is required")
    return out


def render_sheet(renderer, times: list[float], out: Path, cols: int):
    frames = []
    label_h = max(24, round(renderer.h * 0.055))
    for t in times:
        n = round(t * renderer.fps)
        frame = renderer.render(t, n)
        card = Image.new("RGB", (renderer.w, renderer.h + label_h), "white")
        card.paste(frame, (0, 0))
        d = ImageDraw.Draw(card)
        d.text((10, renderer.h + 4), f"{t:.3f}s", fill=(28, 34, 48), font=renderer.small)
        frames.append(card)

    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGB", (renderer.w * cols, (renderer.h + label_h) * rows), "white")
    for i, frame in enumerate(frames):
        sheet.paste(frame, ((i % cols) * renderer.w, (i // cols) * (renderer.h + label_h)))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=94)
    print(out)


def render_segment(renderer, start: float, end: float, out: Path):
    if not 0 <= start < end <= base.DURATION:
        raise ValueError(f"invalid segment {start}..{end} for duration {base.DURATION}")

    # Snap to the same absolute timeline frame grid as a full export. This makes
    # a reviewed segment directly comparable to those frames in a complete film.
    first = math.ceil(start * renderer.fps - 1e-9)
    last = math.ceil(end * renderer.fps - 1e-9)
    actual_start = first / renderer.fps
    duration = (last - first) / renderer.fps

    out.parent.mkdir(parents=True, exist_ok=True)
    video = out.with_suffix(".video.mp4")
    wav = out.with_suffix(".full.wav")

    ff = subprocess.Popen(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{renderer.w}x{renderer.h}", "-r", str(renderer.fps),
            "-i", "pipe:0", "-an", "-c:v", "libx264",
            "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
            str(video),
        ],
        stdin=subprocess.PIPE,
    )
    assert ff.stdin is not None
    for n in range(first, last):
        ff.stdin.write(renderer.render(n / renderer.fps, n).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("segment video encode failed")

    # Generate the same deterministic full-film tonal bed, then take the exact
    # absolute interval so cut chimes and ambience remain aligned with the film.
    base.make_audio(wav, base.DURATION)
    run(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(video), "-ss", f"{actual_start:.6f}", "-t", f"{duration:.6f}",
            "-i", str(wav), "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", str(out),
        ]
    )
    video.unlink(missing_ok=True)
    wav.unlink(missing_ok=True)
    print(f"{out}  timeline={actual_start:.6f}..{actual_start + duration:.6f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=960)
    ap.add_argument("--height", type=int, default=540)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--assets", type=Path, default=base.DEFAULT_ASSETS)
    ap.add_argument("--fixtures", action="store_true")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sheet", type=Path)
    mode.add_argument("--segment", type=Path)
    ap.add_argument("--times", help="comma-separated absolute film times for --sheet")
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--start", type=float)
    ap.add_argument("--end", type=float)
    args = ap.parse_args()

    renderer = base.Renderer(args.width, args.height, args.fps, args.assets, args.fixtures)
    if args.sheet:
        if not args.times:
            ap.error("--sheet requires --times")
        render_sheet(renderer, parse_times(args.times), args.sheet, max(1, args.cols))
    else:
        if args.start is None or args.end is None:
            ap.error("--segment requires --start and --end")
        render_segment(renderer, args.start, args.end, args.segment)


if __name__ == "__main__":
    main()
