#!/usr/bin/env python3
"""Exact <=17-gate prelinear screen over the live-102 nine product-plane orientations.

For the fixed successful field transform of `aes102-field-plane-offsets`, each of the
nine norm-product planes has three equivalent operand orientations: (a,b), (a,a+b),
or (a+b,b).  This script exhausts the 3^9 choices (optionally sharded by the first two
orientations) and asks whether all chosen zero-constant operand linear forms can be
materialized from x0..x7 in at most 17 two-input XOR/XNOR gates.

Only linear masks matter: XOR and XNOR have the same linear part.  If there are n
distinct non-input target masks, at most 17-n helper-only linear wires are possible.
The helper search is exact: before introducing a helper, greedily close all target
masks already constructible; the first helper in any valid network must be the XOR of
two wires in that closure.  Recursing over all such helpers therefore covers every
<=17-gate linear network for the fixed target set.
"""
from __future__ import annotations

import argparse
import functools
import itertools
import json
import pathlib
import time

INPUTS = frozenset(1 << i for i in range(8))


def live_planes():
    x = [1 << i for i in range(8)]
    q = []
    q.append(x[5] ^ x[0])
    q.append(x[1] ^ x[5])
    q.append(q[1] ^ x[2])
    q.append(q[2] ^ x[0])
    q.append(q[2] ^ x[6])
    q.append(x[0] ^ x[1])
    q.append(q[5] ^ x[4])
    q.append(q[6] ^ q[4])
    q.append(q[7] ^ x[3])
    q.append(q[8] ^ x[7])
    q.append(q[9] ^ q[3])
    q.append(q[9] ^ q[5])
    q.append(q[10] ^ x[4])
    q.append(q[11] ^ x[6])
    q.append(q[12] ^ x[5])
    q.append(q[12] ^ q[0])
    q.append(q[14] ^ q[8])
    q.append(q[16] ^ q[10])
    return [
        (q[11], q[10]),
        (q[3], q[12]),
        (q[15], q[2]),
        (q[8], q[7]),
        (x[6], q[17]),
        (q[4], x[7]),
        (q[13], q[16]),
        (q[9], q[6]),
        (q[0], q[14]),
    ]


def orient(pair, choice):
    a, b = pair
    if choice == 0:
        return a, b
    if choice == 1:
        return a, a ^ b
    return a ^ b, b


def closure(targets):
    available = set(INPUTS)
    remaining = set(targets) - available
    sequence = []
    while True:
        changed = False
        current = tuple(available)
        for target in tuple(remaining):
            hit = None
            for a in current:
                b = a ^ target
                if b != a and b in available:
                    hit = a, b
                    break
            if hit:
                remaining.remove(target)
                available.add(target)
                sequence.append((hit[0], hit[1], target))
                changed = True
        if not changed:
            break
    return frozenset(available), frozenset(remaining), tuple(sequence)


@functools.lru_cache(maxsize=None)
def feasible(targets, helper_budget):
    available, remaining, sequence = closure(targets)
    if not remaining:
        return True, (), sequence
    if helper_budget <= 0:
        return False, (), sequence

    # In any valid completion the first helper is generated from two currently
    # available wires.  Enumerate exactly those possible helper masks.
    current = tuple(available)
    helper_candidates = set()
    for i, a in enumerate(current):
        for b in current[i + 1 :]:
            h = a ^ b
            if h and h not in targets and h not in INPUTS:
                helper_candidates.add(h)

    # Try helpers that unlock the most blocked targets first; ordering affects only
    # speed, not coverage.
    scored = []
    for h in helper_candidates:
        expanded = frozenset(set(targets) | {h})
        _a, rem, _s = closure(expanded)
        scored.append((len(rem), h, expanded))
    scored.sort()
    for _blocked, helper, expanded in scored:
        ok, rest, seq = feasible(expanded, helper_budget - 1)
        if ok:
            return True, (helper,) + rest, seq
    return False, (), sequence


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", type=int, default=-1,
                    help="0..8 fixes the first two ternary orientations; -1 scans all")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.prefix not in range(-1, 9):
        raise SystemExit("--prefix must be -1 or 0..8")

    planes = live_planes()
    if args.prefix < 0:
        orientations = itertools.product(range(3), repeat=9)
    else:
        first = args.prefix // 3
        second = args.prefix % 3
        orientations = ((first, second) + tail for tail in itertools.product(range(3), repeat=7))

    started = time.time()
    tested = 0
    target_count = {}
    hits = []
    for choices in orientations:
        tested += 1
        targets = set()
        for plane, choice in zip(planes, choices):
            targets.update(orient(plane, choice))
        targets = frozenset(targets - INPUTS)
        n = len(targets)
        target_count[n] = target_count.get(n, 0) + 1
        if n > 17:
            continue
        ok, helpers, sequence = feasible(targets, 17 - n)
        if ok:
            hit = {
                "orientations": list(choices),
                "target_count": n,
                "helpers": list(helpers),
                "linear_sequence": [list(x) for x in sequence],
                "targets": sorted(targets),
            }
            hits.append(hit)
            print(json.dumps({"HIT": hit}, sort_keys=True), flush=True)

    summary = {
        "prefix": args.prefix,
        "tested": tested,
        "target_count_distribution": dict(sorted(target_count.items())),
        "hits": len(hits),
        "memo_entries": feasible.cache_info().currsize,
        "seconds": round(time.time() - started, 3),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "hits.json").write_text(json.dumps(hits, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
