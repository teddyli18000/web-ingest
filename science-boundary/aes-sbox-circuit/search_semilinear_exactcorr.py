#!/usr/bin/env python3
"""Exact-correction joint outer search for a 101-gate p008 construction.

This strengthens `search_semilinear_outer.py`.  Instead of first choosing one
minimum prelinear network and then asking whether its incidental helper wires can
serve as middle corrections, it enumerates middle correction *positions*, solves
their byte masks exactly, adds those masks to the prelinear target set, and then
synthesizes that complete target set exactly.

For now the exhaustive correction enumeration covers support sizes 0..4 whose
selected 4-bit middle columns are linearly independent.  In those cases every
8-bit correction value is uniquely determined by the four byte equations.  This
already covers the important 101 regime `output_transpose=15, prelinear=17,
support=4` (and all smaller-support variants).  Dependent supports and the
rank-4/support-5 affine family are intentionally left for a follow-up search.

With the retained 18-gate inversion core and both nonlinear layers, total size is

    65 + prelinear + support + output_transpose.

A printed CANDIDATE_101 is therefore a concrete component-level witness, but it
still requires full circuit materialization plus independent 256-byte and official
Few Shots verification before any record claim.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import search_plane_prelinear17 as lin
import search_plane_middle5 as mid
import search_semilinear_outer as outer


def rank4(columns):
    basis = []
    for x in columns:
        y = x
        for b in basis:
            y = min(y, y ^ b)
        if y:
            basis.append(y)
            basis.sort(reverse=True)
    return len(basis)


def xor_columns(columns, selector):
    out = 0
    for i, c in enumerate(columns):
        if (selector >> i) & 1:
            out ^= c
    return out


def unique_corrections_for_support(indices, want_bytes):
    """Return the unique correction bytes for a full-column-rank support.

    `want_bytes[j]` is the byte required at middle output coordinate j.  For each
    byte bit we solve A_S * coeff = rhs by exhaustive enumeration over at most
    four coefficient bits.  Full column rank makes the solution unique whenever
    the rhs lies in the selected column span.
    """
    columns = [mid.COLS[i] for i in indices]
    s = len(columns)
    if rank4(columns) != s:
        return None

    correction = [0] * s
    for bit in range(8):
        rhs = sum((((want_bytes[j] >> bit) & 1) << j) for j in range(4))
        solutions = [m for m in range(1 << s) if xor_columns(columns, m) == rhs]
        if len(solutions) != 1:
            return None
        mask = solutions[0]
        for i in range(s):
            if (mask >> i) & 1:
                correction[i] |= 1 << bit

    # The declared support is exact: zero-valued selected positions belong to a
    # smaller support and are handled there instead.
    if any(v == 0 for v in correction):
        return None

    check = [0, 0, 0, 0]
    for pos, value in zip(indices, correction):
        check = outer.xor4(check, outer.contribution(mid.COLS[pos], value))
    assert check == list(want_bytes)
    return correction


def orientation_targets(planes, choices):
    targets = set()
    for pair, choice in zip(planes, choices):
        targets.update(outer.orient(pair, choice))
    return targets


def output_targets(outpairs, choices):
    targets = set()
    for pair, choice in zip(outpairs, choices):
        targets.update(outer.dual_columns(pair, choice))
    return targets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--k", type=int, required=True, choices=range(8))
    ap.add_argument("--prefix", type=int, required=True, choices=range(9))
    ap.add_argument("--max-support", type=int, default=4, choices=range(5))
    ap.add_argument("--max-pre", type=int, default=19)
    ap.add_argument("--max-out", type=int, default=17)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if not 1 <= args.c <= 255:
        raise SystemExit("c must be 1..255")

    planes, outpairs, corrections = outer.transported_data(args.c, args.k)
    first, second = divmod(args.prefix, 3)
    started = time.time()
    counts = {
        "orientations": 0,
        "output_infeasible": 0,
        "support_systems": 0,
        "support_inconsistent": 0,
        "target_count_pruned": 0,
        "prelinear_infeasible": 0,
        "candidates_101": 0,
    }
    best_total = 10**9
    best = []

    for tail in itertools.product(range(3), repeat=7):
        choices = (first, second) + tail
        counts["orientations"] += 1

        pre_base = orientation_targets(planes, choices)
        npre_base = len(pre_base - lin.INPUTS - {0})
        out_base = output_targets(outpairs, choices)
        nout = len(out_base - lin.INPUTS - {0})

        # Even with zero middle support, target counts alone may rule out 101.
        if npre_base + nout > 36:
            counts["target_count_pruned"] += 1
            continue

        out_cap = min(args.max_out, 36 - npre_base)
        out_hit = outer.linear_min(out_base, out_cap)
        if out_hit is None:
            counts["output_infeasible"] += 1
            continue

        want = tuple(outer.desired_delta(planes, corrections, choices))
        max_s = min(args.max_support, 36 - out_hit["cost"] - npre_base)
        if max_s < 0:
            counts["target_count_pruned"] += 1
            continue

        for support in range(max_s + 1):
            for positions in itertools.combinations(range(9), support):
                counts["support_systems"] += 1
                values = unique_corrections_for_support(positions, want)
                if values is None:
                    counts["support_inconsistent"] += 1
                    continue

                pre_targets = set(pre_base)
                pre_targets.update(values)
                npre = len(pre_targets - lin.INPUTS - {0})
                pre_cap = min(args.max_pre, 36 - out_hit["cost"] - support)
                if npre > pre_cap:
                    counts["target_count_pruned"] += 1
                    continue
                pre_hit = outer.linear_min(pre_targets, pre_cap)
                if pre_hit is None:
                    counts["prelinear_infeasible"] += 1
                    continue

                variable = pre_hit["cost"] + support + out_hit["cost"]
                total = 65 + variable
                witness = {
                    "c": args.c,
                    "k": args.k,
                    "orientations": list(choices),
                    "support_positions": list(positions),
                    "correction_values": values,
                    "middle_delta": list(want),
                    "prelinear": pre_hit,
                    "output_transpose": out_hit,
                    "variable_cost": variable,
                    "total_gate_upper_bound": total,
                    "component_costs": {
                        "prelinear": pre_hit["cost"],
                        "first_and": 9,
                        "middle": 10 + support,
                        "core": 18,
                        "final_and": 18,
                        "output": 10 + out_hit["cost"],
                    },
                }
                if total < best_total:
                    best_total = total
                    best = [witness]
                    print(json.dumps({"NEW_BEST": witness}, sort_keys=True), flush=True)
                elif total == best_total and len(best) < 200:
                    best.append(witness)
                if total <= 101:
                    counts["candidates_101"] += 1
                    print(json.dumps({"CANDIDATE_101": witness}, sort_keys=True), flush=True)

    summary = {
        "c": args.c,
        "k": args.k,
        "prefix": args.prefix,
        "max_support": args.max_support,
        "counts": counts,
        "best_total_gate_upper_bound": None if best_total == 10**9 else best_total,
        "best_witnesses_saved": len(best),
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": "exact for full-column-rank middle supports of size <= max_support",
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "best.json").write_text(json.dumps(best, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
