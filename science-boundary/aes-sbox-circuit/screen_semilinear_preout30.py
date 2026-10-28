#!/usr/bin/env python3
"""Exact prelinear+output screen for retained-core p008 semilinear representatives.

Any 101-gate construction in the retained-18-core family has

    prelinear + middle_support + output_transpose <= 36.

Therefore a middle support of six or more is possible only if the two independent
outer linear networks satisfy exact

    prelinear + output_transpose <= 30.

For one transform/prefix this script exhausts all 3^7 tail orientations.  It
computes exact minimum two-input XOR/XNOR costs for the prelinear and transposed
output target sets using the helper-closure synthesis in search_semilinear_outer.
It records every orientation whose exact sum is <=30.  A complete zero-hit matrix
for a transform proves that support >=6 cannot participate in a 101 construction
for that transform, independently of the middle correction values.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import search_plane_prelinear17 as lin
import search_semilinear_outer as outer


def target_set(pairs, choices, dual=False):
    out = set()
    for pair, choice in zip(pairs, choices):
        out.update(
            outer.dual_columns(pair, choice)
            if dual else outer.orient(pair, choice)
        )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--k", type=int, required=True, choices=range(8))
    ap.add_argument("--prefix", type=int, required=True, choices=range(9))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    planes, outpairs, _corrections = outer.transported_data(args.c, args.k)
    first, second = divmod(args.prefix, 3)
    started = time.time()
    counts = {
        "orientations": 0,
        "target_count_pruned": 0,
        "output_infeasible_under_30": 0,
        "prelinear_infeasible_under_30": 0,
        "hits_pre_plus_out_le_30": 0,
    }
    best_sum = 10**9
    best = []

    for tail in itertools.product(range(3), repeat=7):
        choices = (first, second) + tail
        counts["orientations"] += 1
        pre_targets = target_set(planes, choices, dual=False)
        out_targets = target_set(outpairs, choices, dual=True)
        npre = len(pre_targets - lin.INPUTS - {0})
        nout = len(out_targets - lin.INPUTS - {0})
        if npre + nout > 30:
            counts["target_count_pruned"] += 1
            continue

        # Output and prelinear networks are independent.  Exact minimum output
        # cost is found first; its target count gives the tightest possible cap.
        out_hit = outer.linear_min(out_targets, 30 - npre)
        if out_hit is None:
            counts["output_infeasible_under_30"] += 1
            continue
        pre_hit = outer.linear_min(pre_targets, 30 - out_hit["cost"])
        if pre_hit is None:
            counts["prelinear_infeasible_under_30"] += 1
            continue

        total = pre_hit["cost"] + out_hit["cost"]
        assert total <= 30
        counts["hits_pre_plus_out_le_30"] += 1
        witness = {
            "orientations": list(choices),
            "prelinear_cost": pre_hit["cost"],
            "output_transpose_cost": out_hit["cost"],
            "sum": total,
            "prelinear": pre_hit,
            "output_transpose": out_hit,
        }
        if total < best_sum:
            best_sum = total
            best = [witness]
        elif total == best_sum and len(best) < 100:
            best.append(witness)
        print(json.dumps({"HIT": witness}, sort_keys=True), flush=True)

    summary = {
        "c": args.c,
        "c_hex": f"0x{args.c:02x}",
        "k": args.k,
        "prefix": args.prefix,
        "counts": counts,
        "best_pre_plus_out_le_30": None if best_sum == 10**9 else best_sum,
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": (
            "exact exclusion of retained-core middle support >=6 when no orientation "
            "has exact prelinear+output_transpose cost <=30"
        ),
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "hits.json").write_text(json.dumps(best, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
