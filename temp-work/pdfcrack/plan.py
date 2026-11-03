#!/usr/bin/env python3
"""Search plan for the sharded PDF open-password search.

The plan is an ordered list of candidate spaces.  One "wave" runs WAVE_SHARDS
shards in parallel; shard i of the wave covers the contiguous index window

    [start + i * span, start + (i + 1) * span)

inside the space selected by --space.  Windows tile the space exactly, so no
candidate is skipped as long as every shard finishes its window.  If a shard
reports BUDGET (it ran out of time before finishing) the workflow re-runs the
same wave with a smaller span instead of advancing over unchecked candidates.

Nothing here prints a password: a hit is reported as an index inside the space.
"""

from __future__ import annotations

import argparse
import sys

WAVE_SHARDS = 20
DEFAULT_SPAN = 1_700_000_000

DIGITS = "0123456789"
LOWER = "abcdefghijklmnopqrstuvwxyz"
LOWER_DIGITS = LOWER + DIGITS
ALNUM = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# Ordered by prior probability.  Spaces already exhausted locally are omitted
# (digits 1-7, lowercase 1-5, common password lists).
PLAN: list[tuple[str, str, int]] = [
    ("digits8", DIGITS, 8),
    ("digits9", DIGITS, 9),
    ("lower6", LOWER, 6),
    ("digits10", DIGITS, 10),
    ("lowerdigits6", LOWER_DIGITS, 6),
    ("lowerdigits7", LOWER_DIGITS, 7),
    ("lower7", LOWER, 7),
    ("digits11", DIGITS, 11),
    ("lowerdigits8", LOWER_DIGITS, 8),
    ("alnum6", ALNUM, 6),
    ("lower8", LOWER, 8),
    ("alnum7", ALNUM, 7),
]


def space_size(charset: str, length: int) -> int:
    return len(charset) ** length


def effective_span(space: int, span: int) -> int:
    """Span per shard, never larger than a twentieth of the space."""
    _, charset, length = PLAN[space]
    total = space_size(charset, length)
    packed = max((total + WAVE_SHARDS - 1) // WAVE_SHARDS, 1)
    base = span if span > 0 else DEFAULT_SPAN
    return min(base, packed)


def window(space: int, start: int, shard: int, span: int) -> dict[str, str]:
    label, charset, length = PLAN[space]
    total = space_size(charset, length)
    used = effective_span(space, span)
    s0 = start + shard * used
    s1 = min(s0 + used, total)
    return {
        "label": label,
        "charset": charset,
        "len": str(length),
        "s0": str(s0),
        "s1": str(s1),
        "total": str(total),
        "span_used": str(used),
        "empty": "true" if s0 >= total else "false",
    }


def advance(space: int, start: int, span: int, shrink: bool) -> dict[str, str]:
    label, charset, length = PLAN[space]
    total = space_size(charset, length)
    used = effective_span(space, span)
    out: dict[str, str] = {}

    if shrink:
        new_span = max(int(used * 0.6), 2_000_000)
        out["next_space"] = str(space)
        out["next_start"] = str(start)
        out["next_span"] = str(new_span)
        out["stop"] = "false"
        out["note"] = f"time budget hit; retry same window with span {new_span}"
        return out

    next_start = start + WAVE_SHARDS * used
    if next_start < total:
        out["next_space"] = str(space)
        out["next_start"] = str(next_start)
        out["next_span"] = str(span)
        out["stop"] = "false"
        out["note"] = f"{label}: next window starts at {next_start}/{total}"
    elif space + 1 < len(PLAN):
        nlabel = PLAN[space + 1][0]
        out["next_space"] = str(space + 1)
        out["next_start"] = "0"
        out["next_span"] = str(span)
        out["stop"] = "false"
        out["note"] = f"{label} exhausted ({total} candidates); moving to {nlabel}"
    else:
        out["next_space"] = str(space)
        out["next_start"] = "0"
        out["next_span"] = str(span)
        out["stop"] = "true"
        out["note"] = "plan exhausted; every planned space finished"
    return out


def emit(rows: dict[str, str]) -> None:
    for k, v in rows.items():
        print(f"{k}={v}")


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("window")
    w.add_argument("--space", type=int, required=True)
    w.add_argument("--start", type=int, required=True)
    w.add_argument("--shard", type=int, default=0)
    w.add_argument("--span", type=int, default=0)

    a = sub.add_parser("advance")
    a.add_argument("--space", type=int, required=True)
    a.add_argument("--start", type=int, required=True)
    a.add_argument("--span", type=int, default=0)
    a.add_argument("--shrink", action="store_true")

    l = sub.add_parser("list")

    args = p.parse_args()

    if args.cmd == "window":
        if not 0 <= args.space < len(PLAN):
            print(f"error=space {args.space} out of range", file=sys.stderr)
            return 1
        emit(window(args.space, args.start, args.shard, args.span))
    elif args.cmd == "advance":
        if not 0 <= args.space < len(PLAN):
            print(f"error=space {args.space} out of range", file=sys.stderr)
            return 1
        emit(advance(args.space, args.start, args.span, args.shrink))
    else:
        for i, (label, charset, length) in enumerate(PLAN):
            print(f"{i}\t{label}\tlen={length}\tbase={len(charset)}\t"
                  f"space={space_size(charset, length)}\tspan={effective_span(i, 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
