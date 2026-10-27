#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path

import generalized9 as g
import rank3_square_relax as rs


def bit_indices(mask):
    out = []
    while mask:
        bit = mask & -mask
        out.append(bit.bit_length() - 1)
        mask ^= bit
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = rs.load_rank3_state(r0, digits)
    supports, _ = g.support_masks(r, digits)

    kset = set(rs.RANK3_K9)
    bidx = [i for i in range(g.R_SIZE) if i not in kset]
    bmask = sum(1 << i for i in bidx)
    bvals = {r[i] for i in bidx}

    endpoints_by_owners = defaultdict(list)
    for v, sm in enumerate(supports):
        if v in bvals:
            continue
        owners = tuple(bit_indices(sm & bmask))
        if len(owners) <= 2:
            endpoints_by_owners[owners].append(v)

    x_by_owners = defaultdict(list)
    for xi, xv in enumerate(xset):
        owners = tuple(bit_indices(supports[xv] & bmask))
        if len(owners) <= 2:
            x_by_owners[owners].append(xi)

    one = defaultdict(list)   # oriented square vertex -> raw port descriptors
    two = defaultdict(list)   # sorted pair of oriented square vertices -> raw ports

    # Only nonzero square-conflict candidates matter here. x-conflict-zero ports
    # are handled by the separate x294 expansion.
    for eowners, endpoints in endpoints_by_owners.items():
        if not eowners:
            continue
        for xowners, xis in x_by_owners.items():
            if not xowners:
                continue
            cost = len(eowners) * len(xowners)
            if cost not in (1, 2):
                continue
            for e in endpoints:
                for xi in xis:
                    hs = tuple(sorted((a, b) for a in eowners for b in xowners))
                    vs = tuple(sorted((b, a) for a in eowners for b in xowners))
                    hdesc = ["H", xi, e]
                    vdesc = ["V", xi, e]
                    if cost == 1:
                        one[hs[0]].append(hdesc)
                        one[vs[0]].append(vdesc)
                    else:
                        two[hs].append(hdesc)
                        two[vs].append(vdesc)

    # A deletion pair S unlocks all exact-cost-2 candidates with conflict set S,
    # plus the exact-cost-1 candidate(s) attached to either member of S.
    records = []
    all_pairs = set(two)
    # Also include pairs formed solely from two cost-1 square vertices; they can
    # never beat raw gain 2, but including them makes the maximum statement exact.
    one_keys = sorted(one)
    max_one_mult = max((len(v) for v in one.values()), default=0)
    max_two_mult = max((len(v) for v in two.values()), default=0)

    for pair in all_pairs:
        a, b = pair
        unlocked = len(two[pair]) + len(one.get(a, ())) + len(one.get(b, ()))
        records.append({
            "square_pair": [list(a), list(b)],
            "raw_unlocked": unlocked,
            "cost2_candidates": len(two[pair]),
            "cost1_at_first": len(one.get(a, ())),
            "cost1_at_second": len(one.get(b, ())),
            "sample_cost2": two[pair][:8],
            "sample_cost1_first": one.get(a, [])[:4],
            "sample_cost1_second": one.get(b, [])[:4],
        })
    records.sort(key=lambda z: (-z["raw_unlocked"], z["square_pair"]))

    best_cost2_pair = records[0]["raw_unlocked"] if records else 0
    # If there is no exact-cost-2 candidate, two independent cost-1 deletions can
    # unlock at most 2*max_one_mult; cost1 multiplicity is also reported explicitly.
    raw_pair_upper = max(best_cost2_pair, 2 * max_one_mult)

    out = {
        "state": rs.STATE_INDEX,
        "k9": list(rs.RANK3_K9),
        "endpoint_owner_group_histogram": {
            str(k): sum(1 for owners, vs in endpoints_by_owners.items() if len(owners) == k for _ in vs)
            for k in (0, 1, 2)
        },
        "companion_owner_group_histogram": {
            str(k): sum(1 for owners, xs in x_by_owners.items() if len(owners) == k for _ in xs)
            for k in (0, 1, 2)
        },
        "cost1_square_vertices": len(one),
        "cost2_square_pairs": len(two),
        "max_cost1_candidates_per_square": max_one_mult,
        "max_cost2_candidates_same_pair": max_two_mult,
        "max_raw_ports_unlocked_by_two_deletions": raw_pair_upper,
        "top_pairs": records[:100],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
