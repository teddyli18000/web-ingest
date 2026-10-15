#!/usr/bin/env python3
"""54-second authored sequence built from the approved six-image visual system.

No new generated art is introduced here. The six approved illustrations are
recomposed through camera, paper, memory-window, typography and light language.
The short hero gate remains the regression base; this file tests whether that
language can sustain a real sequence rather than a slideshow.
"""
from __future__ import annotations

import math

import render_v2  # applies the second-pass WORLD/coda direction overrides

base = render_v2.base


# Four phrases: contact -> collaboration -> uncertainty/revision -> open ending.
# Repeated source art is always re-cropped and assigned a different dramatic job.
SEQUENCE = [
    base.Shot(0.00, 2.10, "contact", 1.34, 1.25, .48, .61, .50, .58, "message"),
    base.Shot(2.10, 4.70, "contact", 1.11, 1.04, .61, .52, .59, .50, "presence"),
    base.Shot(4.70, 7.25, "desk",    1.03, 1.09, .56, .55, .58, .53, "notes"),
    base.Shot(7.25, 9.55, "drafts",  1.31, 1.20, .54, .50, .56, .49, "thinking"),
    base.Shot(9.55,12.10, "drafts",  1.08, 1.02, .51, .53, .52, .50, "windows"),

    base.Shot(12.10,15.15,"world",   1.10, 1.01, .57, .52, .56, .49, "world"),
    base.Shot(15.15,17.75,"desk",    1.23, 1.12, .50, .50, .57, .53, "questions"),
    base.Shot(17.75,20.25,"drafts",  1.17, 1.08, .57, .50, .53, .50, "revision"),
    base.Shot(20.25,22.90,"quiet",   1.10, 1.04, .54, .54, .55, .51, "quiet"),
    base.Shot(22.90,25.40,"reach",   1.20, 1.11, .55, .55, .54, .52, "handoff"),

    base.Shot(25.40,27.70,"drafts",  1.36, 1.23, .53, .49, .55, .49, "revision"),
    base.Shot(27.70,30.45,"quiet",   1.19, 1.10, .55, .50, .55, .49, "breath"),
    # Return shots are intentionally much tighter than their first appearances.
    # The place is familiar; the composition and graphic job are not repeated.
    base.Shot(30.45,33.10,"contact", 1.54, 1.38, .67, .42, .64, .45, "presence"),
    base.Shot(33.10,36.05,"drafts",  1.07, 1.02, .51, .53, .52, .50, "windows"),
    base.Shot(36.05,39.30,"world",   1.38, 1.18, .52, .48, .55, .50, "world_return"),

    base.Shot(39.30,42.15,"desk",    1.40, 1.26, .38, .56, .45, .53, "resolve"),
    base.Shot(42.15,45.00,"quiet",   1.27, 1.17, .56, .48, .57, .47, "clearer"),
    base.Shot(45.00,48.00,"reach",   1.22, 1.10, .55, .55, .54, .52, "reach"),
    base.Shot(48.00,51.15,"world",   1.10, 1.00, .57, .52, .56, .49, "final_world"),
    base.Shot(51.15,54.00,"reach",   1.07, 1.00, .55, .51, .54, .49, "coda"),
]

base.SHOTS = SEQUENCE
base.CUTS = [s.start for s in SEQUENCE[1:]]
base.DURATION = SEQUENCE[-1].end

_previous_scene_fx = base.Renderer.scene_fx


def _fade(shot, t, attack=.35, release=.45):
    return base.ease(min((t - shot.start) / attack, (shot.end - t) / release))


def sequence_scene_fx(self, frame, t, shot):
    if shot.mode == "questions":
        u = t - shot.start
        a = _fade(shot, t)
        # Questions orbit the shared desk, never form a dashboard/grid.
        fragments = (
            ("why?", .10, .20, .090, -7, 0.00),
            ("what if", .86, .18, .105,  5, 0.13),
            ("how", .91, .72, .085, -4, 0.28),
            ("again", .12, .78, .095,  6, 0.42),
        )
        for i, (text, x, y, size, rot, delay) in enumerate(fragments):
            aa = base.ease((u - delay) / .38) * a
            x += .010 * math.sin(u * (.8 + i*.06) + i)
            y += .014 * math.cos(u * (.7 + i*.05) + i*.8)
            self.card(frame, text, x, y, size, rot, aa * .72)
        self.glow(frame, .67, .42, .22, .26 * a, False)
        return

    if shot.mode == "revision":
        u = t - shot.start
        a = _fade(shot, t, .25, .35)
        # Two possible drafts slide past each other; the character stays readable.
        self.windows(frame, u * .72, a * .62)
        self.card(frame, "first try", .16 + .012*math.sin(u), .79, .12, -4, a*.68)
        self.card(frame, "another way", .84 - .010*math.sin(u*.8), .17, .14, 4, a*.74)
        self.glow(frame, .56, .47, .21, .22 + .10*math.sin(u*1.2), False)
        return

    if shot.mode == "breath":
        u = t - shot.start
        a = _fade(shot, t, .55, .60)
        # An intentionally quiet shot: only light breathes. Silence is part of the rhythm.
        self.glow(frame, .72, .37, .31, (.34 + .08*math.sin(u*.85)) * a, True)
        return

    if shot.mode == "handoff":
        u = t - shot.start
        a = _fade(shot, t, .28, .45)
        # One idea travels across the frame instead of five labels filling it.
        p = base.ease(base.clamp((u - .25) / 1.55))
        x = .18 + .58 * p
        y = .76 - .27 * math.sin(math.pi * p)
        self.card(frame, "next", x, y, .105, -6 + 12*p, a * .82)
        self.glow(frame, .72, .30, .28, .38*a, True)
        return

    if shot.mode == "world_return":
        u = t - shot.start
        a = _fade(shot, t, .45, .55)
        # Same place, second visit: no labels. The widening warm light is the event.
        self.glow(frame, .68, .48, .30, (.33 + .10*math.sin(u*.7))*a, True)
        return

    if shot.mode == "resolve":
        u = t - shot.start
        a = _fade(shot, t, .35, .50)
        # Earlier the desk filled with questions. On return, only one choice remains.
        self.card(frame, "keep this", .82 + .006*math.sin(u*.8), .20 - .010*u, .12, -3, a*.72)
        self.glow(frame, .61, .43, .23, .22*a, False)
        return

    if shot.mode == "final_world":
        u = t - shot.start
        a = _fade(shot, t, .35, .55)
        # Final WORLD is cleaner than the first: no labelled debris, only widening light.
        self.glow(frame, .73, .50, .34, (.48 + .20*base.ease(u/2.3))*a, True)
        layer = base.Image.new("RGBA", frame.size, (0,0,0,0))
        d = base.ImageDraw.Draw(layer)
        aa = round(230 * base.ease((u-.55)/.7) * a)
        d.text((round(self.w*.73), round(self.h*.18)), "a little farther.", font=self.serif,
               fill=(255,253,247,aa), anchor="mm")
        frame.alpha_composite(layer)
        return

    return _previous_scene_fx(self, frame, t, shot)


base.Renderer.scene_fx = sequence_scene_fx


if __name__ == "__main__":
    base.main()
