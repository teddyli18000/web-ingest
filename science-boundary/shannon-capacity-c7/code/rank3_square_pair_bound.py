#!/usr/bin/env python3
import argparse
import json
from collections import Counter
from pathlib import Path

import generalized9 as g
import rank3_square_relax as rs


def bits(mask):
    out = []
    while mask:
        b = mask & -mask
        out.append(b.bit_length() - 1)
        mask ^= b
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

    outside = [supports[v] & bmask for v in range(g.U)]
    xmask = [supports[xv] & bmask for xv in xset]

    singles = Counter()
    pairs = Counter()
    total_new = 0

    for xi in range(g.R_SIZE):
        bb = bits(xmask[xi])
        if not bb:
            # These are zero-square-cost variables, not part of a deletion-pair bound.
            continue
        for e in range(g.U):
            if e in bvals:
                continue
            aa = bits(outside[e])
            cost = len(aa) * len(bb)
            if cost not in (1, 2):
                continue

            h = tuple(sorted((a, b) for a in aa for b in bb))
            v = tuple(sorted((b, a) for a in aa for b in bb))
            for supp in (h, v):
                total_new += 1
                if len(supp) == 1:
                    singles[supp[0]] += 1
                elif len(supp) == 2:
                    if supp[0] == supp[1]:
                        singles[supp[0]] += 1
                    else:
                        pairs[tuple(sorted(supp))] += 1
                else:
                    raise RuntimeError("unexpected support size")

    vertices = sorted(set(singles) | {p for ab in pairs for p in ab})
    ranked = []
    promising = 0
    max_unlock = 0
    for i, p in enumerate(vertices):
        for q in vertices[i + 1:]:
            n = singles[p] + singles[q] + pairs[(p, q)]
            if n > max_unlock:
                max_unlock = n
            if n >= 3:
                promising += 1
                ranked.append((n, p, q, singles[p], singles[q], pairs[(p, q)]))
    ranked.sort(key=lambda z: (-z[0], z[1], z[2]))

    out = {
        "state": rs.STATE_INDEX,
        "k9": list(rs.RANK3_K9),
        "base_port_optimum": 6589,
        "base_total_score": 134753,
        "new_port_variables_cost_1_or_2": total_new,
        "square_vertices_in_supports": len(vertices),
        "singleton_support_vertices": len(singles),
        "exact_pair_supports": len(pairs),
        "max_new_port_variables_unlocked_by_two_deletions": max_unlock,
        "promising_deletion_pairs_unlocking_at_least_3": promising,
        "radius2_impossible_by_count_bound": max_unlock <= 2,
        "top_pairs": [
            {
                "unlock": n,
                "square_vertices": [list(p), list(q)],
                "singleton_p": sp,
                "singleton_q": sq,
                "exact_pair": ep,
                "optimistic_total_upper_bound": 134751 + n,
            }
            for n, p, q, sp, sq, ep in ranked[:200]
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
