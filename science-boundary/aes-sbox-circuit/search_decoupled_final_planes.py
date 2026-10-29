#!/usr/bin/env python3
"""Search independent final-product plane orientations around the merged 102 p008 circuit.

The live 102 construction uses the same pair basis for two separate purposes:

1. the first nine norm ANDs, and
2. the final eighteen ANDs, where each pair of prelinear factors is multiplied by
   one common inversion-core factor.

Existing plane-orientation searches couple these choices: changing a pair basis in
(1) also applies the corresponding dual column change to the final output map in
(2).  Coupling is economical because only two pair forms must be materialized, but
it is not logically required.  We may retain the live basis for the first norm
product and independently choose one of the three equivalent bases for the final
pair.  If the choices differ, the prelinear network must expose the union of the
needed pair forms (possibly all of a,b,a^b); the final AND count is unchanged and
the output map receives only the final choice's dual column transform.

This script fixes the live-102 field transform and first-product orientation, keeps
its five middle injections unchanged, and exhausts the 3^9 independent final-pair
choices.  For each choice it exactly synthesizes the required prelinear target
union and transposed output target set with the established helper-closure solver.

Gate accounting is

    65 + prelinear + 5 middle injections + output_transpose
  = 70 + prelinear + output_transpose.

Thus a <=101 candidate exists in this family exactly when the two exact linear
costs sum to <=31.  Choice 0^9 is the merged-102 regression point and must recover
prelinear=18, output_transpose=14, total=102.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import search_plane_middle5 as mid
import search_plane_prelinear17 as lin
import search_semilinear_outer as outer

LIVE_C = 0x1B
LIVE_K = 4
FRONT_CHOICES = (0,) * 9
FIXED_SUPPORT = 5
FIXED_TOTAL_BASE = 65 + FIXED_SUPPORT


def oriented_targets(pairs, choices):
    out = set()
    for pair, choice in zip(pairs, choices):
        out.update(outer.orient(pair, choice))
    return out


def output_targets(outpairs, choices):
    out = set()
    for pair, choice in zip(outpairs, choices):
        out.update(outer.dual_columns(pair, choice))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", type=int, required=True, choices=range(9))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    planes, outpairs, transported_corrections = outer.transported_data(LIVE_C, LIVE_K)
    # At the live transform, transport is the identity relative to the merged 102
    # representation.  These assertions protect the accounting from convention drift.
    assert planes == list(lin.live_planes())
    assert transported_corrections == list(mid.BASE_CORRECTION)

    front_targets = oriented_targets(planes, FRONT_CHOICES)
    correction_targets = {x for x in transported_corrections if x}
    fixed_pre_targets = front_targets | correction_targets

    live_pre = outer.linear_min(fixed_pre_targets, 18)
    live_out_targets = output_targets(outpairs, FRONT_CHOICES)
    live_out = outer.linear_min(live_out_targets, 14)
    assert live_pre is not None and live_pre["cost"] == 18, live_pre
    assert live_out is not None and live_out["cost"] == 14, live_out
    assert FIXED_TOTAL_BASE + live_pre["cost"] + live_out["cost"] == 102

    first, second = divmod(args.prefix, 3)
    started = time.time()
    counts = {
        "orientations": 0,
        "target_count_pruned": 0,
        "output_infeasible": 0,
        "prelinear_infeasible": 0,
        "candidates_101": 0,
    }
    best_total = 10**9
    best = []

    for tail in itertools.product(range(3), repeat=7):
        final_choices = (first, second) + tail
        counts["orientations"] += 1

        final_pre_targets = oriented_targets(planes, final_choices)
        pre_targets = fixed_pre_targets | final_pre_targets
        out_targets = output_targets(outpairs, final_choices)
        npre = len(pre_targets - lin.INPUTS - {0})
        nout = len(out_targets - lin.INPUTS - {0})

        # <=101 iff pre+out <=31.  Distinct non-input targets are rigorous lower
        # bounds on the corresponding exact two-input linear-network costs.
        if npre + nout > 31:
            counts["target_count_pruned"] += 1
            continue

        out_hit = outer.linear_min(out_targets, 31 - npre)
        if out_hit is None:
            counts["output_infeasible"] += 1
            continue
        pre_hit = outer.linear_min(pre_targets, 31 - out_hit["cost"])
        if pre_hit is None:
            counts["prelinear_infeasible"] += 1
            continue

        total = FIXED_TOTAL_BASE + pre_hit["cost"] + out_hit["cost"]
        assert total <= 101
        counts["candidates_101"] += 1
        witness = {
            "final_orientations": list(final_choices),
            "front_orientations": list(FRONT_CHOICES),
            "prelinear": pre_hit,
            "output_transpose": out_hit,
            "middle_support": FIXED_SUPPORT,
            "total_gate_upper_bound": total,
            "component_costs": {
                "prelinear": pre_hit["cost"],
                "first_and": 9,
                "middle": 10 + FIXED_SUPPORT,
                "core": 18,
                "final_and": 18,
                "output": 10 + out_hit["cost"],
            },
        }
        if total < best_total:
            best_total = total
            best = [witness]
        elif total == best_total and len(best) < 200:
            best.append(witness)
        print(json.dumps({"CANDIDATE_101": witness}, sort_keys=True), flush=True)

    summary = {
        "prefix": args.prefix,
        "live_regression": {
            "prelinear": live_pre["cost"],
            "output_transpose": live_out["cost"],
            "total": 102,
        },
        "counts": counts,
        "best_total_gate_upper_bound": None if best_total == 10**9 else best_total,
        "best_witnesses_saved": len(best),
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": (
            "exact over all final-pair orientations in this prefix, with live-102 "
            "front norm planes and five middle injections fixed"
        ),
    }
    assert counts["orientations"] == 3**7
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "best.json").write_text(json.dumps(best, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
