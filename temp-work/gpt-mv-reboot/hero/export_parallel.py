#!/usr/bin/env python3
"""Parallel full-film exporter for the GPT MV sequence.

The renderer is a pure function of absolute film time/frame number, so the full
frame range can be split into independent contiguous chunks. Each worker renders
one chunk to an identically encoded H.264 segment; ffmpeg concatenates those
segments without re-encoding, then the deterministic tonal bed is muxed once.

This is an export-speed tool only. It does not own scene logic.
"""
from __future__ import annotations

import argparse
import math
import multiprocessing as mp
import shutil
import subprocess
import tempfile
from pathlib import Path

import sequence

base = sequence.base
ROOT = Path(__file__).resolve().parent.parent


def run(cmd):
    subprocess.run(cmd, check=True)


def render_chunk(job):
    (
        index,
        first,
        last,
        width,
        height,
        fps,
        asset_dir,
        fixtures,
        temp_dir,
        crf,
    ) = job
    renderer = base.Renderer(width, height, fps, Path(asset_dir), fixtures)
    path = Path(temp_dir) / f"chunk-{index:03d}.mp4"
    ff = subprocess.Popen(
        [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0",
            "-an", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", str(crf), "-pix_fmt", "yuv420p", "-threads", "1",
            str(path),
        ],
        stdin=subprocess.PIPE,
    )
    assert ff.stdin is not None
    for n in range(first, last):
        ff.stdin.write(renderer.render(n / fps, n).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError(f"chunk {index} encode failed")
    return index, str(path), first, last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--workers", type=int, default=max(1, min(4, (mp.cpu_count() or 2) - 1)))
    ap.add_argument("--assets", type=Path, default=base.DEFAULT_ASSETS)
    ap.add_argument("--fixtures", action="store_true")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--out", type=Path, default=ROOT / "out" / "hero" / "gpt_sequence_parallel.mp4")
    ap.add_argument("--keep-segments", action="store_true")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()

    if args.width % 2 or args.height % 2:
        ap.error("width and height must be even for yuv420p")
    if args.fps < 1:
        ap.error("fps must be >= 1")

    total = round(base.DURATION * args.fps)
    workers = max(1, min(args.workers, total))
    bounds = [round(total * i / workers) for i in range(workers + 1)]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="gpt-mv-export-", dir=args.out.parent))
    try:
        jobs = [
            (
                i,
                bounds[i],
                bounds[i + 1],
                args.width,
                args.height,
                args.fps,
                str(args.assets),
                args.fixtures,
                str(temp_root),
                args.crf,
            )
            for i in range(workers)
        ]

        # spawn works on GitHub runners and avoids relying on inherited ffmpeg or
        # Pillow state. Absolute frame numbers keep grain/camera/cuts identical.
        ctx = mp.get_context("spawn")
        with ctx.Pool(workers) as pool:
            rendered = pool.map(render_chunk, jobs)
        rendered.sort(key=lambda x: x[0])

        listing = temp_root / "chunks.txt"
        listing.write_text("".join(f"file '{Path(p).as_posix()}'\n" for _, p, _, _ in rendered))
        stitched = temp_root / "stitched.mp4"
        run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-f", "concat", "-safe", "0", "-i", str(listing),
                "-c", "copy", str(stitched),
            ]
        )

        wav = temp_root / "bed.wav"
        base.make_audio(wav, base.DURATION)
        run(
            [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(stitched), "-i", str(wav),
                "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", str(args.out),
            ]
        )

        if args.validate:
            run(["ffmpeg", "-v", "error", "-i", str(args.out), "-f", "null", "-"])

        print(
            f"wrote {args.out}  frames={total}  duration={base.DURATION:.3f}s  "
            f"workers={workers}"
        )

        if args.keep_segments:
            keep = args.out.with_name(args.out.stem + "-segments")
            if keep.exists():
                shutil.rmtree(keep)
            shutil.copytree(temp_root, keep)
            print(f"kept segments at {keep}")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
