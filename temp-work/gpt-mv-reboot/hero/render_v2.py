#!/usr/bin/env python3
"""Second-pass direction overrides for the hero renderer.

Keeps the validated deterministic base renderer intact while replacing the two
compositions that failed visual review: the WORLD shot had too many equal-weight
cards, and the coda title needed stable contrast against the bright sky.
"""
from __future__ import annotations

import math

import render as base


_original_scene_fx = base.Renderer.scene_fx


def scene_fx_v2(self, frame, t, shot):
    if shot.mode != "world":
        return _original_scene_fx(self, frame, t, shot)

    u = t - shot.start
    tail = shot.end - t
    # The illustration carries the shot. Two larger scraps cross the foreground
    # at unequal depths; four labelled cards read too much like a slide deck.
    scraps = (
        ("places", 0.055, 0.22, 0.145, -7.0, 0.00),
        ("stories", 0.945, 0.74, 0.155, 6.0, 0.20),
    )
    for k, (text, x, y, size, angle, delay) in enumerate(scraps):
        a = base.ease((u - delay) / 0.48) * base.ease(tail / 0.55)
        drift = u * (0.012 + 0.002 * k)
        self.card(
            frame,
            text,
            x + (x - 0.5) * drift,
            y - drift,
            size,
            angle + 0.8 * math.sin(u * 0.8 + k),
            a * 0.64,
        )
    self.glow(frame, 0.73, 0.51, 0.28, 0.55 + 0.18 * math.sin(u * 0.8), True)


def title_v2(self, frame, line1, line2, p):
    if p <= 0:
        return
    a = round(255 * base.clamp(p))
    layer = base.Image.new("RGBA", frame.size, (0, 0, 0, 0))
    d = base.ImageDraw.Draw(layer)
    x, y = round(self.w * 0.69), round(self.h * 0.73)
    pad_x, pad_y = round(self.w * 0.18), round(self.h * 0.09)
    # A smoked strip is deliberately softer than a UI card: it stabilizes type
    # over the bright sunrise without closing the image back down.
    d.rounded_rectangle(
        (x - pad_x, y - pad_y, x + pad_x, y + pad_y),
        round(self.h * 0.02),
        fill=(23, 32, 48, round(a * 0.27)),
    )
    d.text(
        (x + 2, y + 3), line1, font=self.hero,
        fill=(18, 28, 48, round(a * 0.68)), anchor="mm",
    )
    d.text((x, y), line1, font=self.hero, fill=(255, 253, 248, a), anchor="mm")
    d.text(
        (x, y + round(self.h * 0.068)), line2, font=self.small,
        fill=(255, 253, 248, round(a * 0.95)), anchor="mm",
    )
    frame.alpha_composite(layer)


base.Renderer.scene_fx = scene_fx_v2
base.Renderer.title = title_v2


if __name__ == "__main__":
    base.main()
