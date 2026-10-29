#!/usr/bin/env python3
"""Solver-free lower bound on distinct right factors in rank-9 GF(16) multiplication.

Consider any bilinear decomposition

    T = sum_j l_j (x) r_j (y) c_j

of GF(16) multiplication over GF(2), and group terms having the same nonzero
right linear form r.  Their left/output outer products sum to a 4x4 matrix A_r.
If n_r terms use r then rank(A_r) <= n_r.

For every nonzero y, multiplication by y is invertible, hence

    rank(sum_{r: r(y)=1} A_r) = 4.

By rank subadditivity this implies

    sum_{r: r(y)=1} rank(A_r) >= 4.

Thus a rank-9 decomposition using a support S of distinct right forms must admit
integer weights rho_r in {1,2,3,4} with sum rho_r <= 9 satisfying all 15
inequalities above.  This script exhausts every support S subset GF(2)^4\{0}.
It proves no support of size <=7 passes even these necessary inequalities.

The size-8 census is included as a regression/sanity check: the relaxation first
becomes feasible there, so this script does not claim that eight factors are
actually realizable by a rank-9 decomposition.
"""
from __future__ import annotations

import itertools
import json


def rank4(vectors):
    basis = [0] * 4
    rank = 0
    for x in vectors:
        y = x
        for p in range(3, -1, -1):
            if not ((y >> p) & 1):
                continue
            if basis[p]:
                y ^= basis[p]
            else:
                basis[p] = y
                rank += 1
                break
    return rank


def dot(a, b):
    return (a & b).bit_count() & 1


def patterns(n, budget=9):
    # rank(A_r) is positive for a genuinely used support element and at most four.
    return [p for p in itertools.product(range(1, 5), repeat=n) if sum(p) <= budget]


def feasible_weight(S, ps):
    supports = [tuple(i for i, r in enumerate(S) if dot(r, y)) for y in range(1, 16)]
    for rho in ps:
        if all(sum(rho[i] for i in support) >= 4 for support in supports):
            return rho
    return None


def census(size):
    ps = patterns(size)
    spanning = 0
    feasible = []
    for S in itertools.combinations(range(1, 16), size):
        if rank4(S) != 4:
            continue
        spanning += 1
        rho = feasible_weight(S, ps)
        if rho is not None:
            feasible.append((S, rho))
    return spanning, feasible


def main():
    rows = []
    for size in range(4, 9):
        spanning, feasible = census(size)
        rows.append({
            "distinct_right_forms": size,
            "spanning_supports": spanning,
            "supports_passing_rank_sum_le_9": len(feasible),
            "example": None if not feasible else {
                "support": list(feasible[0][0]),
                "rank_weights": list(feasible[0][1]),
            },
        })

    # Exact regression counts for the finite search.
    assert [row["supports_passing_rank_sum_le_9"] for row in rows[:4]] == [0, 0, 0, 0]
    assert rows[4]["supports_passing_rank_sum_le_9"] == 855

    summary = {
        "rank_budget": 9,
        "right_support_lower_bound": 8,
        "census": rows,
        "scope": (
            "necessary rank-subadditivity conditions only; proves <=7 distinct right forms "
            "impossible for every rank-9 GF(16) bilinear multiplier, while size 8 remains open"
        ),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
