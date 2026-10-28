#!/usr/bin/env python3
"""Exact proof that middle support >=6 cannot yield a 101-gate LB=31 representative.

For the retained-18-core outer construction, a 101 circuit needs

    prelinear + middle_support + output_transpose <= 36.

Hence support >=6 requires exact prelinear+output_transpose <=30.

This script avoids full linear minimization.  For each of the three exact LB=31
class representatives and all 3^9 plane orientations it computes the number of
non-input targets in the independent prelinear/output networks.  For every target
set that can possibly fit the <=30 budget, it then exactly asks whether the set is
synthesizable with zero or one helper-only XOR/XNOR wire using the complete helper
closure search in search_plane_prelinear17.feasible.

If a target set is not feasible with one helper, it needs at least two helpers.
Adding these rigorously proved helper lower bounds to the target counts gives a
lower bound on exact prelinear+output cost.  The exhaustive result is >30 for every
orientation of all three representatives, so middle support >=6 is impossible in
a 101 construction.  Combined with prove_semilinear_class_automorphisms.py, the
same exclusion transports to all 18 LB=31 transforms.
"""
from __future__ import annotations

import itertools
import json
import time

import search_plane_prelinear17 as lin
import search_semilinear_outer as outer


REPRESENTATIVES = {
    "A": (0x01, 0),
    "B": (0x9D, 3),
    "C": (0x5B, 3),
}


def target_set(pairs, choices, dual=False):
    out = set()
    for pair, choice in zip(pairs, choices):
        out.update(
            outer.dual_columns(pair, choice)
            if dual else outer.orient(pair, choice)
        )
    return frozenset(out - lin.INPUTS - {0})


def helper_lower_bound(targets):
    """Return exact 0/1 helper result, or the rigorous lower bound 2."""
    ok0, _helpers0, _sequence0 = lin.feasible(targets, 0)
    if ok0:
        return 0
    ok1, _helpers1, _sequence1 = lin.feasible(targets, 1)
    if ok1:
        return 1
    return 2


def prove_transform(c, k):
    planes, outpairs, _corrections = outer.transported_data(c, k)
    started = time.time()
    counts = {
        "orientations": 0,
        "target_sum_gt_30": 0,
        "target_sum_30": 0,
        "target_sum_29": 0,
        "target_sum_28": 0,
        "target_sum_lt_28": 0,
        "budget_survivors": 0,
    }
    helper_hist_pre = {0: 0, 1: 0, 2: 0}
    helper_hist_out = {0: 0, 1: 0, 2: 0}
    min_lower_bound = 999
    best_rows = []

    # Cache the exact 0/1-helper classification by target set because the same
    # target set can recur across orientation vectors.
    cache = {}

    def hlb(targets):
        if targets not in cache:
            cache[targets] = helper_lower_bound(targets)
        return cache[targets]

    for choices in itertools.product(range(3), repeat=9):
        counts["orientations"] += 1
        pre = target_set(planes, choices, dual=False)
        out = target_set(outpairs, choices, dual=True)
        target_sum = len(pre) + len(out)
        if target_sum > 30:
            counts["target_sum_gt_30"] += 1
            continue
        if target_sum < 28:
            counts["target_sum_lt_28"] += 1
        else:
            counts[f"target_sum_{target_sum}"] += 1

        hp = hlb(pre)
        ho = hlb(out)
        helper_hist_pre[hp] += 1
        helper_hist_out[ho] += 1
        lower = target_sum + hp + ho
        if lower < min_lower_bound:
            min_lower_bound = lower
            best_rows = [{
                "orientations": list(choices),
                "pre_targets": len(pre),
                "out_targets": len(out),
                "pre_helper_lb": hp,
                "out_helper_lb": ho,
                "pre_plus_out_lb": lower,
            }]
        elif lower == min_lower_bound and len(best_rows) < 100:
            best_rows.append({
                "orientations": list(choices),
                "pre_targets": len(pre),
                "out_targets": len(out),
                "pre_helper_lb": hp,
                "out_helper_lb": ho,
                "pre_plus_out_lb": lower,
            })
        if lower <= 30:
            counts["budget_survivors"] += 1

    result = {
        "c": c,
        "c_hex": f"0x{c:02x}",
        "k": k,
        "counts": counts,
        "helper_hist_pre": helper_hist_pre,
        "helper_hist_out": helper_hist_out,
        "min_exact_0_1_helper_lower_bound_pre_plus_out": min_lower_bound,
        "best_rows": best_rows,
        "distinct_target_sets_classified": len(cache),
        "elapsed_seconds": round(time.time() - started, 3),
    }
    assert counts["orientations"] == 3**9
    assert counts["target_sum_lt_28"] == 0
    assert counts["budget_survivors"] == 0, result
    assert min_lower_bound >= 31, result
    return result


def main():
    results = {}
    for name, (c, k) in REPRESENTATIVES.items():
        result = prove_transform(c, k)
        results[name] = result
        print(json.dumps({name: result}, sort_keys=True), flush=True)

    summary = {
        "representatives": len(results),
        "orientations_per_representative": 3**9,
        "minimum_pre_plus_out_lower_bounds": {
            name: row["min_exact_0_1_helper_lower_bound_pre_plus_out"]
            for name, row in results.items()
        },
        "budget_survivors": {
            name: row["counts"]["budget_survivors"]
            for name, row in results.items()
        },
        "conclusion": (
            "middle support >=6 cannot fit the <=101 retained-core budget for "
            "any LB=31 representative; class automorphisms transport the result "
            "to all 18 LB=31 transforms"
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
