#!/usr/bin/env python3
"""Original procedural short film: GPT // SIGNAL IN, WORLDS OUT.

No external visual/audio assets are used. Everything is generated deterministically.
"""
from __future__ import annotations

import argparse
import math
import os
import random
import subprocess
import tempfile
import wave
from array import array
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

W, H = 1280, 720
FPS = 30
DURATION = 26.0
SEED = 5606

BG = (7, 10, 14)
FG = (232, 241, 239)
MUTED = (117, 135, 140)
MINT = (106, 237, 194)
CYAN = (97, 204, 255)
VIOLET = (174, 138, 255)
AMBER = (255, 190, 102)
ROSE = (255, 128, 154)


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def smooth(x: float) -> float:
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x: float) -> float:
    x = clamp(x)
    return 1 - (1 - x) ** 3


def window(t: float, start: float, end: float, fade: float = 0.45) -> float:
    if t < start or t > end:
        return 0.0
    a = smooth((t - start) / max(fade, 1e-6))
    b = smooth((end - t) / max(fade, 1e-6))
    return min(a, b)


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def alpha(c, a):
    return (*c, int(clamp(a) * 255))


def find_font(size: int, mono: bool = False, bold: bool = False):
    candidates = []
    if mono:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONTS = {
    "xs": find_font(18, mono=True),
    "sm": find_font(24, mono=True),
    "md": find_font(32),
    "lg": find_font(54, bold=True),
    "xl": find_font(78, bold=True),
    "mono_lg": find_font(44, mono=True, bold=True),
}


def text_center(draw: ImageDraw.ImageDraw, xy, text, font, fill, anchor="mm", spacing=4):
    draw.multiline_text(xy, text, font=font, fill=fill, anchor=anchor, align="center", spacing=spacing)


def background() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    px = im.load()
    # Deterministic radial/vertical gradient, no external assets.
    for y in range(H):
        vy = y / (H - 1)
        for x in range(W):
            dx = (x - W * 0.52) / W
            dy = (y - H * 0.46) / H
            r = math.sqrt(dx * dx + dy * dy)
            glow = max(0.0, 1.0 - r * 1.75)
            rr = int(BG[0] + 4 * glow + 2 * (1 - vy))
            gg = int(BG[1] + 8 * glow + 2 * (1 - vy))
            bb = int(BG[2] + 10 * glow + 3 * (1 - vy))
            px[x, y] = (rr, gg, bb)
    return im


BASE = background()
RNG = random.Random(SEED)
STARS = [(RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(0.4, 1.8), RNG.uniform(0, math.tau)) for _ in range(90)]
TOKEN_WORDS = ["why", "shape", "if", "proof", "maybe", "code", "you", "next", "because", "pattern", "?", "42", "loop", "memory", "tool", "world"]
ORBIT_LABELS = ["WEB", "CODE", "FILES", "TOOLS"]
BRANCH_LABELS = ["explain", "solve", "invent", "check", "ask"]


def draw_grid(draw: ImageDraw.ImageDraw, t: float):
    # Perspective-like sparse grid.
    alpha_v = int(18 + 6 * math.sin(t * 0.6))
    for x in range(0, W, 80):
        draw.line((x, 0, x, H), fill=(30, 50, 55, alpha_v), width=1)
    for y in range(40, H, 72):
        draw.line((0, y, W, y), fill=(30, 50, 55, 12), width=1)


def draw_stars(draw: ImageDraw.ImageDraw, t: float):
    for x, y, r, phase in STARS:
        a = 0.12 + 0.16 * (0.5 + 0.5 * math.sin(t * 0.9 + phase))
        rr = r * (0.8 + 0.25 * math.sin(t * 0.6 + phase))
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=alpha(FG, a))


def knot_points(cx: float, cy: float, radius: float, phase: float, lobes: int = 6, n: int = 160):
    pts = []
    for i in range(n + 1):
        a = math.tau * i / n
        rr = radius * (0.68 + 0.12 * math.sin(lobes * a + phase))
        x = cx + rr * math.cos(a + 0.18 * math.sin(2 * a + phase))
        y = cy + rr * math.sin(a + 0.18 * math.sin(2 * a + phase))
        pts.append((x, y))
    return pts


def draw_core(draw: ImageDraw.ImageDraw, t: float, cx: float = W / 2, cy: float = H / 2, scale: float = 1.0, intensity: float = 1.0):
    phase = t * 0.65
    radius = 92 * scale * (1.0 + 0.035 * math.sin(t * 2.4))
    pts1 = knot_points(cx, cy, radius, phase)
    pts2 = knot_points(cx, cy, radius * 0.82, -phase * 1.15 + 1.2)
    draw.line(pts1, fill=alpha(MINT, 0.10 * intensity), width=max(1, int(18 * scale)), joint="curve")
    draw.line(pts2, fill=alpha(CYAN, 0.08 * intensity), width=max(1, int(13 * scale)), joint="curve")
    draw.line(pts1, fill=alpha(MINT, 0.88 * intensity), width=max(1, int(3 * scale)), joint="curve")
    draw.line(pts2, fill=alpha(CYAN, 0.72 * intensity), width=max(1, int(2 * scale)), joint="curve")
    for i in range(6):
        a = phase + math.tau * i / 6
        rr = radius * 0.87
        x, y = cx + rr * math.cos(a), cy + rr * math.sin(a)
        dot = 3.5 * scale
        draw.ellipse((x - dot, y - dot, x + dot, y + dot), fill=alpha(FG, 0.8 * intensity))


def draw_intro(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 0, 3.8, 0.55)
    if not a:
        return
    # console line emerges from darkness
    u = ease_out((t - 0.3) / 1.6)
    x0 = 170
    y0 = 285
    draw.text((x0, y0), ">", font=FONTS["mono_lg"], fill=alpha(MINT, a), anchor="lm")
    phrase = "hello, GPT"
    chars = int(clamp((t - 0.75) / 1.35) * len(phrase) + 1e-6)
    draw.text((x0 + 58, y0), phrase[:chars], font=FONTS["mono_lg"], fill=alpha(FG, a), anchor="lm")
    if t > 2.05 and (int(t * 3) % 2 == 0):
        tx = x0 + 58 + draw.textlength(phrase[:chars], font=FONTS["mono_lg"])
        draw.rectangle((tx + 6, y0 - 25, tx + 10, y0 + 25), fill=alpha(MINT, a * 0.9))
    wake = smooth((t - 2.0) / 1.5)
    if wake > 0:
        draw_core(draw, t, 925, 360, 0.58 + 0.15 * wake, a * wake)
        text_center(draw, (925, 510), "signal received", FONTS["sm"], alpha(MUTED, a * wake))


def draw_tokens(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 3.6, 7.9, 0.45)
    if not a:
        return
    scene = clamp((t - 3.6) / 4.3)
    cx, cy = W / 2, H / 2
    draw_core(draw, t, cx, cy, 0.72, a)
    text_center(draw, (W / 2, 88), "YOU SEND A SIGNAL", FONTS["lg"], alpha(FG, a))
    text_center(draw, (W / 2, 134), "I SPLIT IT INTO PIECES", FONTS["sm"], alpha(MUTED, a))
    for i, word in enumerate(TOKEN_WORDS):
        phase = i * 0.73
        ang = phase + t * (0.18 + (i % 3) * 0.025)
        start_r = 520 + (i % 4) * 28
        end_r = 132 + (i % 5) * 8
        u = smooth(clamp(scene * 1.25 - (i % 7) * 0.055))
        r = lerp(start_r, end_r, u)
        x = cx + r * math.cos(ang)
        y = cy + 0.58 * r * math.sin(ang)
        pad_x, pad_y = 11, 7
        bbox = draw.textbbox((0, 0), word, font=FONTS["xs"])
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        box = (x - tw / 2 - pad_x, y - th / 2 - pad_y, x + tw / 2 + pad_x, y + th / 2 + pad_y)
        draw.rounded_rectangle(box, radius=10, outline=alpha((80, 118, 122), a * 0.45), fill=alpha((15, 24, 27), a * 0.55), width=1)
        draw.text((x, y), word, font=FONTS["xs"], fill=alpha(FG, a * 0.88), anchor="mm")


def draw_attention(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 7.7, 12.0, 0.45)
    if not a:
        return
    cx, cy = W / 2, H / 2 + 18
    text_center(draw, (W / 2, 88), "RELATIONSHIPS LIGHT UP", FONTS["lg"], alpha(FG, a))
    text_center(draw, (W / 2, 134), "not every connection matters equally", FONTS["sm"], alpha(MUTED, a))
    nodes = []
    for i in range(14):
        ang = math.tau * i / 14 + 0.12 * math.sin(t * 0.5 + i)
        r = 210 + 42 * math.sin(i * 1.8 + t * 0.7)
        nodes.append((cx + r * math.cos(ang), cy + 0.68 * r * math.sin(ang)))
    # weighted attention edges
    for i, (x1, y1) in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            if (i * 7 + j * 11) % 13 < 3:
                x2, y2 = nodes[j]
                weight = 0.22 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.8 + i + j * 0.4))
                draw.line((x1, y1, x2, y2), fill=alpha(CYAN if (i + j) % 2 else VIOLET, a * weight * 0.45), width=1 + int(weight * 2))
    for i, (x, y) in enumerate(nodes):
        r = 5 + 3 * (0.5 + 0.5 * math.sin(t * 2 + i))
        col = MINT if i % 3 == 0 else (CYAN if i % 3 == 1 else VIOLET)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=alpha(col, a * 0.9))
    draw_core(draw, t, cx, cy, 0.86, a)


def draw_branches(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 11.8, 15.9, 0.45)
    if not a:
        return
    cx, cy = 360, H / 2 + 36
    text_center(draw, (W / 2, 85), "POSSIBILITIES COMPETE", FONTS["lg"], alpha(FG, a))
    text_center(draw, (W / 2, 132), "many continuations fit — one must win", FONTS["sm"], alpha(MUTED, a))
    draw_core(draw, t, cx, cy, 0.72, a)
    scene = clamp((t - 11.8) / 4.1)
    for i, label in enumerate(BRANCH_LABELS):
        ang = -0.8 + i * 0.4
        end_x = 820 + 250 * math.cos(ang)
        end_y = cy + 220 * math.sin(ang)
        u = smooth(clamp(scene * 1.5 - i * 0.06))
        x = lerp(cx + 90, end_x, u)
        y = lerp(cy, end_y, u)
        selected = i == 1
        col = MINT if selected else (VIOLET if i % 2 else CYAN)
        aa = a * (0.95 if selected else 0.36)
        draw.line((cx + 74, cy, x, y), fill=alpha(col, aa * 0.68), width=4 if selected else 2)
        rr = 9 if selected else 6
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=alpha(col, aa))
        draw.text((x + 18, y), label, font=FONTS["sm"], fill=alpha(FG, aa), anchor="lm")
    if scene > 0.62:
        v = smooth((scene - 0.62) / 0.38)
        draw.text((875, 548), "sampling →", font=FONTS["xs"], fill=alpha(MUTED, a * v), anchor="lm")
        draw.text((1055, 548), "one path", font=FONTS["sm"], fill=alpha(MINT, a * v), anchor="lm")


def draw_tools(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 15.7, 20.2, 0.45)
    if not a:
        return
    cx, cy = W / 2, H / 2 + 14
    text_center(draw, (W / 2, 82), "TOOLS EXTEND THE FRAME", FONTS["lg"], alpha(FG, a))
    text_center(draw, (W / 2, 130), "the answer can reach beyond the prompt", FONTS["sm"], alpha(MUTED, a))
    draw_core(draw, t, cx, cy, 0.82, a)
    for i, label in enumerate(ORBIT_LABELS):
        ang = t * 0.72 + math.tau * i / len(ORBIT_LABELS)
        r = 235 + 12 * math.sin(t + i)
        x = cx + r * math.cos(ang)
        y = cy + 0.55 * r * math.sin(ang)
        # orbit trail
        px = cx + r * math.cos(ang - 0.18)
        py = cy + 0.55 * r * math.sin(ang - 0.18)
        draw.line((px, py, x, y), fill=alpha((110, 150, 150), a * 0.30), width=2)
        col = [MINT, CYAN, VIOLET, AMBER][i]
        draw.rounded_rectangle((x - 44, y - 22, x + 44, y + 22), radius=11, outline=alpha(col, a * 0.75), fill=alpha((12, 20, 23), a * 0.75), width=2)
        draw.text((x, y), label, font=FONTS["xs"], fill=alpha(FG, a), anchor="mm")
        # connection flicker to core
        if (int(t * 4) + i) % 5 < 2:
            draw.line((cx, cy, x, y), fill=alpha(col, a * 0.22), width=1)


def draw_answer(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 20.0, 24.0, 0.45)
    if not a:
        return
    text_center(draw, (W / 2, 92), "ONE PATH BECOMES WORDS", FONTS["lg"], alpha(FG, a))
    panel = (160, 205, W - 160, 535)
    draw.rounded_rectangle(panel, radius=28, outline=alpha((70, 104, 108), a * 0.55), fill=alpha((11, 17, 21), a * 0.82), width=2)
    draw.text((205, 255), "GPT", font=FONTS["sm"], fill=alpha(MINT, a), anchor="la")
    response = "I can help with that.\nHere is one path through the problem."
    u = clamp((t - 20.55) / 2.4)
    chars = int(len(response) * smooth(u))
    shown = response[:chars]
    draw.multiline_text((205, 320), shown, font=FONTS["md"], fill=alpha(FG, a), anchor="la", spacing=16)
    if chars < len(response) and (int(t * 4) % 2 == 0):
        # simple cursor positioned after last line approximately
        lines = shown.split("\n")
        last = lines[-1]
        y = 320 + (len(lines) - 1) * 54
        x = 205 + draw.textlength(last, font=FONTS["md"])
        draw.rectangle((x + 5, y - 4, x + 9, y + 32), fill=alpha(MINT, a * 0.85))
    draw.text((W - 205, 500), "then you answer back", font=FONTS["xs"], fill=alpha(MUTED, a), anchor="ra")


def draw_coda(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 23.8, 26.0, 0.45)
    if not a:
        return
    cx, cy = W / 2, 315
    grow = 0.9 + 0.14 * smooth((t - 23.8) / 0.9)
    draw_core(draw, t, cx, cy, grow, a)
    text_center(draw, (W / 2, 505), "GPT", FONTS["xl"], alpha(FG, a))
    text_center(draw, (W / 2, 578), "SIGNAL IN  //  WORLDS OUT", FONTS["sm"], alpha(MINT, a))
    text_center(draw, (W / 2, 640), "the loop continues when you speak again", FONTS["xs"], alpha(MUTED, a))


def render_frame(t: float) -> Image.Image:
    im = BASE.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    draw_grid(draw, t)
    draw_stars(draw, t)
    draw_intro(draw, t)
    draw_tokens(draw, t)
    draw_attention(draw, t)
    draw_branches(draw, t)
    draw_tools(draw, t)
    draw_answer(draw, t)
    draw_coda(draw, t)
    # soft vignette using translucent bands, cheap and deterministic
    for i in range(12):
        aa = int((i / 12) ** 2 * 18)
        draw.rectangle((i, i, W - i - 1, H - i - 1), outline=(0, 0, 0, aa), width=1)
    return Image.alpha_composite(im, overlay).convert("RGB")


def synth_audio(path: Path, duration: float):
    sr = 32000
    total = int(sr * duration)
    data = array("h")
    boundaries = [2.0, 4.0, 8.0, 12.0, 16.0, 20.0, 24.0]
    for n in range(total):
        t = n / sr
        # low evolving drone + quiet upper partial
        s = 0.18 * math.sin(math.tau * 55.0 * t + 0.22 * math.sin(t * 0.31))
        s += 0.07 * math.sin(math.tau * 110.0 * t + 0.35 * math.sin(t * 0.47))
        s += 0.035 * math.sin(math.tau * (220.0 + 9.0 * math.sin(t * 0.2)) * t)
        # scene boundary pulses
        for b in boundaries:
            dt = t - b
            if 0.0 <= dt < 0.55:
                env = math.exp(-8.0 * dt)
                s += 0.13 * env * math.sin(math.tau * (180.0 + b * 4.0) * dt)
        # typing-like tick near answer scene
        if 20.45 <= t <= 22.95:
            frac = (t - 20.45) * 9.0
            dt = frac - math.floor(frac)
            if dt < 0.045:
                s += 0.07 * (1 - dt / 0.045) * math.sin(math.tau * 860.0 * dt)
        # global fade
        fade = min(1.0, t / 0.8, max(0.0, (duration - t) / 1.2))
        s *= fade
        # soft saturation
        s = math.tanh(s * 1.25) * 0.78
        data.append(int(max(-1.0, min(1.0, s)) * 32767))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())


def run_ffmpeg(args):
    proc = subprocess.run(args, check=False)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def render_video(out: Path, duration: float, fps: int, smoke: bool = False):
    out.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    width, height = (640, 360) if smoke else (W, H)
    with tempfile.TemporaryDirectory(prefix="gpt-mv-") as td:
        td = Path(td)
        video_only = td / "video.mp4"
        audio = td / "audio.wav"
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
            "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-pix_fmt", "yuv420p", str(video_only),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = int(duration * fps)
        for i in range(frames):
            t = i / fps
            frame = render_frame(t)
            if smoke:
                frame = frame.resize((width, height), Image.Resampling.LANCZOS)
            assert proc.stdin is not None
            proc.stdin.write(frame.tobytes())
            if i % max(1, fps * 2) == 0:
                print(f"render {i:04d}/{frames}  t={t:05.2f}s", flush=True)
        assert proc.stdin is not None
        proc.stdin.close()
        code = proc.wait()
        if code != 0:
            raise SystemExit(code)
        synth_audio(audio, duration)
        run_ffmpeg([
            ffmpeg, "-y", "-loglevel", "error",
            "-i", str(video_only), "-i", str(audio),
            "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
            "-movflags", "+faststart", "-shortest", str(out),
        ])
    # poster frame around the attention scene
    poster = render_frame(min(10.0, duration * 0.5))
    poster.save(out.with_suffix(".poster.png"), optimize=True)
    print(f"wrote {out} ({out.stat().st_size / 1024 / 1024:.2f} MiB)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="out/gpt-signal-worlds-out.mp4")
    p.add_argument("--duration", type=float, default=DURATION)
    p.add_argument("--fps", type=int, default=FPS)
    p.add_argument("--smoke", action="store_true", help="small 640x360 render for fast validation")
    args = p.parse_args()
    duration = min(args.duration, 4.0) if args.smoke else args.duration
    fps = min(args.fps, 18) if args.smoke else args.fps
    render_video(Path(args.out), duration, fps, smoke=args.smoke)


if __name__ == "__main__":
    main()
