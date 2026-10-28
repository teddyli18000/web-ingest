#!/usr/bin/env python3
"""Recompute and materialize the exact neutral2 MaxSAT rank-3 tie (134753).

The original ten-rank MaxSAT campaign persisted only scores when the optimum did
not beat the public record.  This script deterministically reconstructs the same
eligible-state ordering, solves only rank 3 exactly with RC2, builds the complete
10D certificate, and persists it even though it ties 134753.  It is intended as
a reusable boundary state for exact recombination / surgery experiments.
"""
import argparse
import json
from itertools import combinations
from pathlib import Path

import generalized9 as g
import neutral2_maxsat as nm
import neutral2_sweep as ns

RANK = 3
EXPECTED = 134_753
K = 9


def eligible_records(r0, digits):
    xset = g.make_x(r0, digits)
    supports0, _ = g.support_masks(r0, digits)
    states = ns.enumerate_states(r0, digits, supports0)
    eligible = []
    for si, (r, rem, add) in enumerate(states, 1):
        supports, _ = g.support_masks(r, digits)
        owners = nm.owner_groups(r, supports)
        if len(owners) < K:
            continue
        for k9 in combinations(sorted(owners), K):
            kmask = sum(1 << i for i in k9)
            safe_count = sum(1 for sm in supports if sm & ~kmask == 0)
            eligible.append((safe_count, si, r, rem, add, supports, k9, len(owners)))
    eligible.sort(key=lambda z: (-z[0], z[1], z[6]))
    return xset, eligible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset, eligible = eligible_records(r0, digits)
    if len(eligible) <= RANK:
        raise RuntimeError(f"eligible ordering drift: {len(eligible)}")

    safe_count, si, r, rem, add, supports, k9, centers = eligible[RANK]
    model, stats = nm.solve_maxsat(k9, r, xset, digits, supports)
    if model is None or stats["score"] != EXPECTED:
        raise RuntimeError(f"rank3 optimum drift: {stats}")
    candidate = nm.build_candidate(k9, model, r, xset, digits)
    if len(candidate) != EXPECTED:
        raise RuntimeError(f"rank3 certificate score drift: {len(candidate)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n"
    )
    st = {
        "candidate": True,
        "method": "neutral2-rank3-exact-tie",
        "rank": RANK,
        "score": len(candidate),
        "eligible_count": len(eligible),
        "state_index": si,
        "safe_count": safe_count,
        "neutral_remove_indices": list(rem),
        "neutral_add": list(add),
        "selected_indices": list(k9),
        "selected_centers": [r[i] for i in k9],
        "centers_available": centers,
        "maxsat": stats,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    print(json.dumps(st, sort_keys=True))


if __name__ == "__main__":
    main()
