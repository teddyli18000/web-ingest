#!/usr/bin/env python3
"""Rank-4/support-5 semilinear outer search for a 101-gate p008 circuit.

The merged 102 circuit itself uses five middle correction injections, so the
support<=4 exact-correction screen does not cover the most relevant tradeoff.
For a chosen 5-position support whose four-bit middle columns have rank four,
the correction system has nullity one. Across the eight independent byte bits,
all solutions are parameterized by one free byte z in 0..255. This script
exhausts those 256 assignments, requires exact five-position support, adds the
resulting correction bytes to the prelinear target set, and exact-synthesizes
that union.

The retained nonlinear layers give total size

    65 + prelinear + 5 + output_transpose.

Thus a 101 candidate needs `prelinear + output_transpose <= 31`.

Scope: exhaustive for rank-4 five-position correction supports. The nine
rank-3 five-position supports (nullity two) are not covered here.
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


def rank(columns):
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
    for i, col in enumerate(columns):
        if (selector >> i) & 1:
            out ^= col
    return out


def parameterize_rank4(indices, want):
    columns = [mid.COLS[i] for i in indices]
    if rank(columns) != 4:
        return None
    kernel = [m for m in range(1, 1 << 5) if xor_columns(columns, m) == 0]
    assert len(kernel) == 1
    null_mask = kernel[0]

    base = [0] * 5
    for bit in range(8):
        rhs = sum((((want[j] >> bit) & 1) << j) for j in range(4))
        sols = [m for m in range(1 << 5) if xor_columns(columns, m) == rhs]
        assert len(sols) == 2
        # The two solutions differ by the unique nonzero null vector.
        assert sols[0] ^ sols[1] == null_mask
        chosen = min(sols)
        for i in range(5):
            if (chosen >> i) & 1:
                base[i] |= 1 << bit
    return tuple(base), null_mask


def corrections(base, null_mask, z):
    return tuple(
        value ^ (z if ((null_mask >> i) & 1) else 0)
        for i, value in enumerate(base)
    )


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
    ap.add_argument("--max-pre", type=int, default=19)
    ap.add_argument("--max-out", type=int, default=17)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    planes, outpairs, base_corrections = outer.transported_data(args.c, args.k)
    first, second = divmod(args.prefix, 3)
    support_sets = [
        inds for inds in itertools.combinations(range(9), 5)
        if rank([mid.COLS[i] for i in inds]) == 4
    ]
    assert len(support_sets) == 117

    started = time.time()
    counts = {
        "orientations": 0,
        "output_infeasible": 0,
        "base_pre_infeasible": 0,
        "support_sets": 0,
        "assignments": 0,
        "zero_assignment_component": 0,
        "target_count_pruned": 0,
        "duplicate_target_set": 0,
        "prelinear_infeasible": 0,
        "candidates_101": 0,
    }
    best_total = 10**9
    best = []

    for tail in itertools.product(range(3), repeat=7):
        choices = (first, second) + tail
        counts["orientations"] += 1

        pre_base = orientation_targets(planes, choices)
        npre = len(pre_base - lin.INPUTS - {0})
        out_base = output_targets(outpairs, choices)

        # support=5 leaves pre+out<=31.
        out_cap = min(args.max_out, 31 - npre)
        if out_cap < 0:
            counts["target_count_pruned"] += 1
            continue
        out_hit = outer.linear_min(out_base, out_cap)
        if out_hit is None:
            counts["output_infeasible"] += 1
            continue

        pre_cap = min(args.max_pre, 31 - out_hit["cost"])
        if npre > pre_cap:
            counts["target_count_pruned"] += 1
            continue

        # A superset cannot need fewer gates than the base operand targets.  If
        # the base set already exceeds the remaining pre budget, no correction
        # assignment can rescue this orientation.
        base_pre_hit = outer.linear_min(pre_base, pre_cap)
        if base_pre_hit is None:
            counts["base_pre_infeasible"] += 1
            continue

        want = tuple(outer.desired_delta(planes, base_corrections, choices))
        seen_targets = set()
        for inds in support_sets:
            counts["support_sets"] += 1
            param = parameterize_rank4(inds, want)
            assert param is not None
            base, null_mask = param
            for z in range(256):
                counts["assignments"] += 1
                values = corrections(base, null_mask, z)
                if any(v == 0 for v in values):
                    counts["zero_assignment_component"] += 1
                    continue
                targets = frozenset((set(pre_base) | set(values)) - lin.INPUTS - {0})
                if len(targets) > pre_cap:
                    counts["target_count_pruned"] += 1
                    continue
                if targets in seen_targets:
                    counts["duplicate_target_set"] += 1
                    continue
                seen_targets.add(targets)
                pre_hit = outer.linear_min(targets, pre_cap)
                if pre_hit is None:
                    counts["prelinear_infeasible"] += 1
                    continue

                variable = pre_hit["cost"] + 5 + out_hit["cost"]
                total = 65 + variable
                witness = {
                    "c": args.c,
                    "k": args.k,
                    "orientations": list(choices),
                    "support_positions": list(inds),
                    "free_byte": z,
                    "correction_values": list(values),
                    "middle_delta": list(want),
                    "prelinear": pre_hit,
                    "output_transpose": out_hit,
                    "variable_cost": variable,
                    "total_gate_upper_bound": total,
                    "component_costs": {
                        "prelinear": pre_hit["cost"],
                        "first_and": 9,
                        "middle": 15,
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
        "counts": counts,
        "best_total_gate_upper_bound": None if best_total == 10**9 else best_total,
        "best_witnesses_saved": len(best),
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": "exact for rank-4 correction supports of size exactly 5",
    }
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "best.json").write_text(json.dumps(best, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
