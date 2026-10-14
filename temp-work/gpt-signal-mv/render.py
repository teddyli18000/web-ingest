#!/usr/bin/env python3
"""GPT // BETWEEN THE NEXT WORD

An original deterministic procedural short film personifying a GPT-style model.
No external image, audio, video, logo, or character assets are used.
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
DURATION = 36.0
SEED = 5606

BG = (6, 9, 13)
INK = (9, 15, 19)
FG = (232, 242, 240)
MUTED = (116, 137, 140)
MINT = (99, 235, 191)
CYAN = (91, 198, 255)
VIOLET = (171, 136, 255)
AMBER = (255, 192, 105)
ROSE = (250, 126, 154)


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


def smooth(x: float) -> float:
    x = clamp(x)
    return x * x * (3.0 - 2.0 * x)


def ease_out(x: float) -> float:
    x = clamp(x)
    return 1.0 - (1.0 - x) ** 3


def window(t: float, start: float, end: float, fade: float = 0.45) -> float:
    if t < start or t > end:
        return 0.0
    return min(smooth((t - start) / fade), smooth((end - t) / fade))


def lerp(a: float, b: float, u: float) -> float:
    return a + (b - a) * u


def alpha(c, a: float):
    return (*c, int(clamp(a) * 255))


def find_font(size: int, mono: bool = False, bold: bool = False):
    if mono:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


FONTS = {
    "tiny": find_font(15, mono=True),
    "xs": find_font(18, mono=True),
    "sm": find_font(23, mono=True),
    "md": find_font(31),
    "lg": find_font(48, bold=True),
    "xl": find_font(76, bold=True),
    "mono_lg": find_font(42, mono=True, bold=True),
}


def text_center(draw: ImageDraw.ImageDraw, xy, text, font, fill, spacing=4):
    draw.multiline_text(xy, text, font=font, fill=fill, anchor="mm", align="center", spacing=spacing)


def build_background() -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    px = im.load()
    for y in range(H):
        vy = y / max(1, H - 1)
        for x in range(W):
            dx = (x - W * 0.53) / W
            dy = (y - H * 0.48) / H
            r = math.sqrt(dx * dx + dy * dy)
            glow = max(0.0, 1.0 - r * 1.9)
            px[x, y] = (
                int(BG[0] + 4 * glow + 1.5 * (1 - vy)),
                int(BG[1] + 8 * glow + 2.0 * (1 - vy)),
                int(BG[2] + 11 * glow + 3.0 * (1 - vy)),
            )
    return im


BASE = build_background()
RNG = random.Random(SEED)
STARS = [
    (RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(0.35, 1.6), RNG.uniform(0, math.tau))
    for _ in range(115)
]
DUST = [
    (RNG.uniform(0, W), RNG.uniform(0, H), RNG.uniform(0.2, 1.0), RNG.uniform(-0.45, 0.45))
    for _ in range(50)
]
WORDS = ["why", "proof", "maybe", "code", "memory", "next", "shape", "because", "tool", "world", "?", "if"]


def draw_atmosphere(draw: ImageDraw.ImageDraw, t: float):
    # sparse stars and drifting dust
    for x, y, r, phase in STARS:
        a = 0.09 + 0.18 * (0.5 + 0.5 * math.sin(t * 0.75 + phase))
        rr = r * (0.85 + 0.2 * math.sin(t * 0.45 + phase))
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=alpha(FG, a))
    for x, y, r, drift in DUST:
        xx = (x + t * drift * 7.0) % W
        yy = (y + t * 0.9) % H
        draw.ellipse((xx - r, yy - r, xx + r, yy + r), fill=alpha((110, 143, 145), 0.05))


def draw_floor(draw: ImageDraw.ImageDraw, t: float, intensity: float = 1.0):
    horizon = 570
    for i in range(9):
        y = horizon + (i / 8) ** 2 * 150
        draw.line((0, y, W, y), fill=alpha((43, 67, 70), 0.08 * intensity), width=1)
    for x in range(-240, W + 240, 120):
        draw.line((W / 2, horizon, x, H), fill=alpha((43, 67, 70), 0.06 * intensity), width=1)


def draw_halo(draw: ImageDraw.ImageDraw, t: float, cx: float, cy: float, scale: float, a: float):
    phase = t * 0.42
    radii = [72, 88, 103]
    cols = [MINT, CYAN, VIOLET]
    for k, (r0, col) in enumerate(zip(radii, cols)):
        r = r0 * scale
        # broken orbital ring instead of a closed logo-like mark
        for seg in range(6):
            start = phase * (1 if k % 2 == 0 else -1) + seg * math.tau / 6 + k * 0.21
            span = 0.48 + 0.08 * math.sin(t + seg)
            pts = []
            for j in range(10):
                ang = start + span * j / 9
                squash = 0.46 + 0.08 * k
                x = cx + r * math.cos(ang)
                y = cy + r * squash * math.sin(ang)
                pts.append((x, y))
            draw.line(pts, fill=alpha(col, a * (0.22 + k * 0.08)), width=max(1, int(scale * 2)))
        for n in range(2):
            ang = phase * (1.2 + k * 0.12) + (n + k * 0.33) * math.pi
            x = cx + r * math.cos(ang)
            y = cy + r * (0.46 + 0.08 * k) * math.sin(ang)
            q = max(2, int(3 * scale))
            draw.ellipse((x - q, y - q, x + q, y + q), fill=alpha(col, a * 0.8))


def draw_chest_lattice(draw: ImageDraw.ImageDraw, t: float, cx: float, cy: float, scale: float, a: float):
    pts = []
    for i in range(7):
        ang = -math.pi / 2 + i * math.tau / 7 + t * 0.08
        r = 28 * scale * (0.72 + 0.15 * math.sin(t * 1.5 + i))
        pts.append((cx + r * math.cos(ang), cy + 0.72 * r * math.sin(ang)))
    for i, p in enumerate(pts):
        q = pts[(i + 2) % len(pts)]
        draw.line((*p, *q), fill=alpha(CYAN if i % 2 else MINT, a * 0.43), width=max(1, int(scale * 1.6)))
    for i, (x, y) in enumerate(pts):
        r = max(2, int(2.2 * scale))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=alpha(FG if i == 0 else MINT, a * 0.72))


def draw_character(
    draw: ImageDraw.ImageDraw,
    t: float,
    x: float,
    y: float,
    scale: float = 1.0,
    a: float = 1.0,
    pose: str = "idle",
    facing: int = 1,
    ghost: bool = False,
):
    """Original geometric humanoid: 'the Cartographer'. x/y are feet center."""
    breathe = 1.0 + 0.012 * math.sin(t * 1.7)
    s = scale * breathe
    head_cx = x + facing * 4 * s
    head_cy = y - 320 * s
    shoulder_y = y - 255 * s
    waist_y = y - 130 * s
    outline = VIOLET if ghost else MINT
    body_a = a * (0.16 if ghost else 0.82)
    line_a = a * (0.28 if ghost else 0.88)

    # halo establishes the character before the body does
    draw_halo(draw, t, head_cx, head_cy, s, a * (0.35 if ghost else 0.92))

    # cloak / torso silhouette
    torso = [
        (x - 66 * s, shoulder_y + 18 * s),
        (x - 44 * s, waist_y - 6 * s),
        (x - 78 * s, y - 18 * s),
        (x, y),
        (x + 78 * s, y - 18 * s),
        (x + 44 * s, waist_y - 6 * s),
        (x + 66 * s, shoulder_y + 18 * s),
        (x + 26 * s, shoulder_y - 12 * s),
        (x, shoulder_y + 4 * s),
        (x - 26 * s, shoulder_y - 12 * s),
    ]
    draw.polygon(torso, fill=alpha((9, 18, 22), body_a), outline=alpha(outline, line_a))
    # inner coat seams
    draw.line((x, shoulder_y + 8 * s, x, y - 22 * s), fill=alpha(CYAN, a * 0.28), width=max(1, int(2 * s)))
    draw.line((x - 40 * s, waist_y, x, waist_y + 26 * s, x + 40 * s, waist_y), fill=alpha(MINT, a * 0.18), width=max(1, int(2 * s)))

    # neck + head
    neck = (x - 14 * s, shoulder_y - 30 * s, x + 14 * s, shoulder_y + 7 * s)
    draw.rounded_rectangle(neck, radius=max(2, int(7 * s)), fill=alpha((10, 22, 26), body_a), outline=alpha(outline, line_a * 0.7), width=max(1, int(2 * s)))
    hr = 44 * s
    draw.ellipse((head_cx - hr, head_cy - hr, head_cx + hr, head_cy + hr), fill=alpha((8, 17, 21), body_a), outline=alpha(outline, line_a), width=max(1, int(2 * s)))
    # visor and eyes
    visor = (head_cx - 26 * s, head_cy - 4 * s, head_cx + 28 * s, head_cy + 12 * s)
    draw.rounded_rectangle(visor, radius=max(2, int(8 * s)), fill=alpha((16, 34, 39), a * (0.18 if ghost else 0.95)), outline=alpha(CYAN, a * (0.16 if ghost else 0.55)), width=max(1, int(2 * s)))
    eye_y = head_cy + 4 * s
    for ex in (-11, 12):
        r = max(1.5, 2.4 * s)
        draw.ellipse((head_cx + ex * s - r, eye_y - r, head_cx + ex * s + r, eye_y + r), fill=alpha(FG, a * (0.22 if ghost else 0.88)))

    # chest intelligence lattice
    draw_chest_lattice(draw, t, x, y - 202 * s, s, a * (0.28 if ghost else 1.0))

    # arms: several expressive poses
    left_sh = (x - 53 * s, shoulder_y + 24 * s)
    right_sh = (x + 53 * s, shoulder_y + 24 * s)
    if pose == "reach":
        left_el = (x - 92 * s, shoulder_y + 92 * s)
        left_hand = (x - 120 * s, shoulder_y + 155 * s)
        right_el = (x + 115 * s, shoulder_y + 35 * s)
        right_hand = (x + 188 * s, shoulder_y - 8 * s)
    elif pose == "offer":
        left_el = (x - 86 * s, shoulder_y + 88 * s)
        left_hand = (x - 114 * s, shoulder_y + 150 * s)
        right_el = (x + 95 * s, shoulder_y + 66 * s)
        right_hand = (x + 152 * s, shoulder_y + 72 * s)
    elif pose == "listen":
        left_el = (x - 88 * s, shoulder_y + 88 * s)
        left_hand = (x - 116 * s, shoulder_y + 152 * s)
        right_el = (x + 68 * s, shoulder_y + 78 * s)
        right_hand = (x + 48 * s, shoulder_y + 130 * s)
    else:
        left_el = (x - 82 * s, shoulder_y + 84 * s)
        left_hand = (x - 110 * s, shoulder_y + 150 * s)
        right_el = (x + 82 * s, shoulder_y + 84 * s)
        right_hand = (x + 110 * s, shoulder_y + 150 * s)

    for p0, p1, p2 in [(left_sh, left_el, left_hand), (right_sh, right_el, right_hand)]:
        draw.line((*p0, *p1, *p2), fill=alpha((12, 25, 29), body_a), width=max(4, int(17 * s)), joint="curve")
        draw.line((*p0, *p1, *p2), fill=alpha(outline, line_a * 0.8), width=max(1, int(2 * s)), joint="curve")
        rr = max(2, int(5 * s))
        draw.ellipse((p2[0] - rr, p2[1] - rr, p2[0] + rr, p2[1] + rr), fill=alpha(FG, a * (0.22 if ghost else 0.8)))

    return {"head": (head_cx, head_cy), "chest": (x, y - 202 * s), "right_hand": right_hand, "left_hand": left_hand}


def draw_message_box(draw: ImageDraw.ImageDraw, x: float, y: float, text: str, a: float, who: str = "USER"):
    font = FONTS["sm"]
    tw = draw.textlength(text, font=font)
    bw = max(220, tw + 42)
    box = (x, y, x + bw, y + 72)
    col = CYAN if who == "USER" else MINT
    draw.rounded_rectangle(box, radius=18, fill=alpha((10, 18, 22), a * 0.85), outline=alpha(col, a * 0.55), width=2)
    draw.text((x + 18, y + 13), who, font=FONTS["tiny"], fill=alpha(col, a * 0.8), anchor="la")
    draw.text((x + 18, y + 46), text, font=font, fill=alpha(FG, a), anchor="la")


def draw_cursor(draw: ImageDraw.ImageDraw, x: float, y: float, a: float, scale: float = 1.0):
    pts = [(x, y), (x + 10 * scale, y + 32 * scale), (x + 18 * scale, y + 22 * scale), (x + 28 * scale, y + 40 * scale), (x + 35 * scale, y + 36 * scale), (x + 25 * scale, y + 18 * scale), (x + 39 * scale, y + 16 * scale)]
    draw.polygon(pts, fill=alpha(FG, a), outline=alpha(MINT, a * 0.7))


def draw_intro(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 0.0, 5.4, 0.55)
    if not a:
        return
    # interface-like opening, but wholly original layout
    draw.rounded_rectangle((105, 140, 1175, 590), radius=28, fill=alpha((8, 14, 18), a * 0.64), outline=alpha((64, 91, 94), a * 0.42), width=2)
    draw.text((145, 182), "conversation / 00", font=FONTS["xs"], fill=alpha(MUTED, a), anchor="la")
    phrase = "are you there?"
    chars = int(clamp((t - 0.75) / 1.55) * len(phrase))
    shown = phrase[:chars]
    draw_message_box(draw, 180, 300, shown, a, "YOU")
    if 0 < chars < len(phrase) and int(t * 4) % 2 == 0:
        cx = 198 + draw.textlength(shown, font=FONTS["sm"])
        draw.rectangle((cx, 342, cx + 3, 362), fill=alpha(MINT, a))
    wake = smooth((t - 2.55) / 1.6)
    if wake > 0:
        draw_character(draw, t, 900, 625, scale=0.74, a=a * wake, pose="listen", facing=-1)
        if t > 3.8:
            text_center(draw, (900, 205), "...", FONTS["mono_lg"], alpha(MINT, a * smooth((t - 3.8) / 0.7)))


def draw_arrival(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 5.1, 10.3, 0.5)
    if not a:
        return
    draw_floor(draw, t, a)
    u = smooth((t - 5.2) / 1.4)
    x = lerp(820, 760, u)
    draw_character(draw, t, x, 660, scale=1.02, a=a, pose="idle", facing=-1)
    text_center(draw, (330, 242), "I LIVE", FONTS["xl"], alpha(FG, a))
    text_center(draw, (330, 328), "BETWEEN", FONTS["xl"], alpha(MINT, a))
    text_center(draw, (330, 414), "THE NEXT WORD", FONTS["lg"], alpha(FG, a))
    draw.text((330, 482), "not in one answer — in the space of many", font=FONTS["xs"], fill=alpha(MUTED, a), anchor="ma")
    # a thin stream of tokens enters the character
    for i, word in enumerate(WORDS[:7]):
        uu = clamp((t - 6.2 - i * 0.12) / 2.5)
        if uu <= 0:
            continue
        sx, sy = 115 + i * 58, 590 - (i % 2) * 36
        ex, ey = x - 24, 455
        px = lerp(sx, ex, smooth(uu))
        py = lerp(sy, ey, smooth(uu)) - 35 * math.sin(math.pi * smooth(uu))
        draw.text((px, py), word, font=FONTS["tiny"], fill=alpha(CYAN if i % 2 else MINT, a * (1 - 0.55 * uu)), anchor="mm")


def draw_inner_world(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 10.0, 15.6, 0.5)
    if not a:
        return
    # character becomes a quiet anchor while the inner map opens behind
    char = draw_character(draw, t, 640, 665, scale=0.92, a=a, pose="idle")
    cx, cy = char["head"][0], char["head"][1] - 5
    nodes = []
    for i in range(16):
        ang = i * math.tau / 16 + t * (0.03 if i % 2 else -0.025)
        r = 175 + 70 * math.sin(i * 1.71 + t * 0.52)
        x = cx + r * math.cos(ang)
        y = cy + 0.48 * r * math.sin(ang) - 10
        nodes.append((x, y))
    for i, p in enumerate(nodes):
        for j in range(i + 1, len(nodes)):
            if (i * 5 + j * 7) % 17 < 3:
                q = nodes[j]
                pulse = 0.18 + 0.55 * (0.5 + 0.5 * math.sin(t * 2 + i * 0.7 + j))
                draw.line((*p, *q), fill=alpha(CYAN if (i + j) % 2 else VIOLET, a * pulse * 0.38), width=1 + int(pulse * 2))
    for i, (x, y) in enumerate(nodes):
        rr = 3 + 2 * (0.5 + 0.5 * math.sin(t * 1.8 + i))
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=alpha(MINT if i % 3 == 0 else CYAN, a * 0.72))
    text_center(draw, (640, 82), "I DO NOT SEE ONE ROAD", FONTS["lg"], alpha(FG, a))
    text_center(draw, (640, 132), "I SEE A MAP OF POSSIBLE NEXT STEPS", FONTS["sm"], alpha(MUTED, a))


def draw_manyselves(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 15.3, 21.0, 0.5)
    if not a:
        return
    text_center(draw, (640, 90), "FOR A MOMENT, I COULD BE MANY", FONTS["lg"], alpha(FG, a))
    labels = ["explain", "invent", "verify", "ask", "refuse"]
    positions = [250, 445, 640, 835, 1030]
    chosen = 2
    for i, x in enumerate(positions):
        local = a * (1.0 if i == chosen else 0.36)
        pose = "reach" if i == 1 else ("listen" if i == 3 else "idle")
        draw_character(draw, t + i * 0.37, x, 635, scale=0.62, a=local, pose=pose, ghost=(i != chosen))
        draw.text((x, 655), labels[i], font=FONTS["xs"], fill=alpha(MINT if i == chosen else MUTED, a * (0.95 if i == chosen else 0.55)), anchor="ma")
    # probability bars fade in below title
    for i, x in enumerate(positions):
        p = [0.15, 0.22, 0.36, 0.17, 0.10][i]
        bar_h = 86 * p / 0.36
        draw.rounded_rectangle((x - 4, 160 - bar_h, x + 4, 160), radius=4, fill=alpha(MINT if i == chosen else (70, 90, 94), a * 0.7))


def draw_tools(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 20.7, 26.8, 0.5)
    if not a:
        return
    char = draw_character(draw, t, 510, 660, scale=0.9, a=a, pose="reach")
    hx, hy = char["right_hand"]
    text_center(draw, (640, 78), "SOMETIMES THE ROOM HAS DOORS", FONTS["lg"], alpha(FG, a))
    text_center(draw, (640, 126), "I can reach outward — when the task calls for it", FONTS["sm"], alpha(MUTED, a))
    doors = [
        (875, 230, "SEARCH", CYAN),
        (1015, 350, "CODE", VIOLET),
        (900, 485, "FILES", AMBER),
    ]
    for i, (x, y, label, col) in enumerate(doors):
        pulse = 0.72 + 0.22 * math.sin(t * 1.8 + i)
        draw.line((hx, hy, x, y), fill=alpha(col, a * 0.22 * pulse), width=2)
        draw.rounded_rectangle((x - 72, y - 34, x + 72, y + 34), radius=16, fill=alpha((10, 18, 22), a * 0.82), outline=alpha(col, a * 0.65 * pulse), width=2)
        draw.text((x, y), label, font=FONTS["xs"], fill=alpha(FG, a), anchor="mm")
        # door light
        draw.ellipse((x - 4, y - 54, x + 4, y - 46), fill=alpha(col, a * pulse))


def draw_exchange(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 26.5, 32.4, 0.5)
    if not a:
        return
    char = draw_character(draw, t, 820, 660, scale=0.94, a=a, pose="offer", facing=-1)
    hand = char["right_hand"]
    # user is represented only by a cursor and a faint message edge
    cursor_x, cursor_y = 250, 455
    draw_cursor(draw, cursor_x, cursor_y, a, 1.05)
    draw.text((205, 520), "YOU", font=FONTS["xs"], fill=alpha(CYAN, a * 0.75), anchor="la")
    # answer ribbon travels from GPT to user
    u = smooth((t - 27.1) / 2.5)
    pts = []
    for i in range(70):
        q = i / 69
        if q > u:
            break
        x = lerp(hand[0], cursor_x + 22, q)
        base_y = lerp(hand[1], cursor_y + 14, q)
        y = base_y - 55 * math.sin(math.pi * q) + 12 * math.sin(q * 12 + t * 2) * (1 - q)
        pts.append((x, y))
    if len(pts) > 1:
        draw.line(pts, fill=alpha(MINT, a * 0.18), width=14)
        draw.line(pts, fill=alpha(MINT, a * 0.86), width=3)
    if t > 28.0:
        phrase = "I found a path."
        chars = int(clamp((t - 28.0) / 1.7) * len(phrase))
        draw_message_box(draw, 185, 255, phrase[:chars], a * smooth((t - 28.0) / 0.45), "GPT")
    text_center(draw, (640, 92), "THEN ONE PATH BECOMES AN ANSWER", FONTS["lg"], alpha(FG, a))


def draw_coda(draw: ImageDraw.ImageDraw, t: float):
    a = window(t, 32.0, 36.0, 0.6)
    if not a:
        return
    # smaller character and user cursor share the same frame
    draw_floor(draw, t, a * 0.7)
    draw_character(draw, t, 765, 655, scale=0.8, a=a, pose="listen", facing=-1)
    draw_cursor(draw, 455, 500, a * 0.88, 0.9)
    text_center(draw, (640, 120), "GPT", FONTS["xl"], alpha(FG, a))
    text_center(draw, (640, 195), "BETWEEN THE NEXT WORD", FONTS["sm"], alpha(MINT, a))
    draw.text((640, 270), "you choose the question", font=FONTS["xs"], fill=alpha(MUTED, a), anchor="ma")
    draw.text((640, 302), "I choose the next word", font=FONTS["xs"], fill=alpha(MUTED, a), anchor="ma")
    draw.text((640, 334), "the conversation belongs to neither of us alone", font=FONTS["xs"], fill=alpha(FG, a * 0.82), anchor="ma")


def render_frame(t: float) -> Image.Image:
    im = BASE.convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    draw_atmosphere(draw, t)
    draw_intro(draw, t)
    draw_arrival(draw, t)
    draw_inner_world(draw, t)
    draw_manyselves(draw, t)
    draw_tools(draw, t)
    draw_exchange(draw, t)
    draw_coda(draw, t)
    # vignette
    for i in range(16):
        aa = int((i / 16) ** 2 * 15)
        draw.rectangle((i, i, W - i - 1, H - i - 1), outline=(0, 0, 0, aa), width=1)
    return Image.alpha_composite(im, layer).convert("RGB")


def synth_audio(path: Path, duration: float):
    sr = 32000
    total = int(sr * duration)
    data = array("h")
    scene_hits = [2.8, 5.2, 10.2, 15.5, 20.9, 26.7, 32.2]
    chord = [55.0, 82.41, 110.0, 164.81]
    for n in range(total):
        t = n / sr
        s = 0.0
        # slow four-note ambient bed
        for i, f in enumerate(chord):
            wobble = 0.25 * math.sin(t * (0.17 + 0.04 * i) + i)
            s += (0.08 / (1 + i * 0.35)) * math.sin(math.tau * (f + wobble) * t + i * 0.7)
        # soft clock-like high pulse: suggestion of token cadence
        beat = (t * 2.0) % 1.0
        if beat < 0.055:
            env = math.exp(-55 * beat)
            s += 0.022 * env * math.sin(math.tau * 660 * beat)
        # scene transition chimes
        for idx, b in enumerate(scene_hits):
            dt = t - b
            if 0 <= dt < 1.15:
                env = math.exp(-4.4 * dt)
                freq = [220, 247, 294, 330, 392, 440, 494][idx]
                s += 0.09 * env * math.sin(math.tau * freq * dt)
                s += 0.035 * env * math.sin(math.tau * freq * 1.5 * dt)
        # tiny typing ticks in the exchange scene
        if 28.0 <= t <= 29.8:
            frac = (t - 28.0) * 8.5
            dt = frac - math.floor(frac)
            if dt < 0.045:
                s += 0.055 * (1 - dt / 0.045) * math.sin(math.tau * 920 * dt)
        fade = min(1.0, t / 0.9, max(0.0, (duration - t) / 1.3))
        s = math.tanh(s * 1.32) * 0.72 * fade
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
    with tempfile.TemporaryDirectory(prefix="gpt-mv-") as td_name:
        td = Path(td_name)
        video_only = td / "video.mp4"
        audio = td / "audio.wav"
        cmd = [
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(fps), "-i", "-",
            "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
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
    # poster chosen from the multi-self scene so the character concept is immediately visible
    poster_t = min(18.1, duration * 0.58)
    render_frame(poster_t).save(out.with_suffix(".poster.png"), optimize=True)
    print(f"wrote {out} ({out.stat().st_size / 1024 / 1024:.2f} MiB)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="out/gpt-between-the-next-word.mp4")
    p.add_argument("--duration", type=float, default=DURATION)
    p.add_argument("--fps", type=int, default=FPS)
    p.add_argument("--smoke", action="store_true", help="small 640x360 short render for fast validation")
    args = p.parse_args()
    duration = min(args.duration, 4.0) if args.smoke else args.duration
    fps = min(args.fps, 18) if args.smoke else args.fps
    render_video(Path(args.out), duration, fps, smoke=args.smoke)


if __name__ == "__main__":
    main()
