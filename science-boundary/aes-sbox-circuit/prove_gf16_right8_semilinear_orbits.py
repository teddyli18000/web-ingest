#!/usr/bin/env python3
"""Exact symmetry reduction for the eight-right-factor GF(16) rank-9 boundary.

A 9-product bilinear scheme using exactly eight distinct nonzero right forms has
multiplicities (2,1,1,1,1,1,1,1).  For every nonzero y the multiplication map
x -> x*y is invertible, so rank subadditivity gives the necessary count condition

    sum_{r(y)=1} multiplicity(r) >= 4.

This script exhausts all eight-subsets of the 15 nonzero four-bit forms and all
choices of the doubled ("heavy") form.  Exactly 960 weighted supports pass.

GF(16) multiplication has the 60 right-side semilinear autotopisms

    y -> c * y^(2^k),  c != 0, k in {0,1,2,3}.

Together with the corresponding Frobenius/scaling maps on the left and output,
these preserve the multiplication tensor.  We act contragrediently on right
linear forms and verify that the 960 candidates split into exactly 16 disjoint
orbits of size 60.  The hard-coded representatives are exactly those consumed by
`prove_gf16_rank9_right8_exhaustive.cpp`.
"""
from __future__ import annotations

import itertools
import json


REPRESENTATIVES = [
    ((2,3,4,5,11,12,13,14),4),
    ((2,3,5,10,11,12,13,15),11),
    ((2,4,5,10,11,12,13,15),12),
    ((2,3,4,5,6,10,12,13),13),
    ((1,3,7,9,11,13,14,15),11),
    ((5,6,7,8,12,13,14,15),12),
    ((2,3,7,10,11,13,14,15),11),
    ((1,3,4,6,9,11,12,14),14),
    ((1,2,5,6,9,10,12,13),2),
    ((1,3,5,7,8,10,12,14),8),
    ((2,5,6,7,8,9,12,13),6),
    ((2,8,9,10,12,13,14,15),9),
    ((1,4,6,8,10,11,13,15),8),
    ((1,2,3,5,6,10,13,14),10),
    ((1,2,4,6,7,9,10,12),9),
    ((1,5,6,9,10,12,13,14),14),
]


def gf16mul(a: int, b: int) -> int:
    p = 0
    for i in range(4):
        if (b >> i) & 1:
            p ^= a << i
    for d in range(6, 3, -1):
        if (p >> d) & 1:
            p ^= 1 << d
            p ^= 1 << (d - 3)
            p ^= 1 << (d - 4)
    return p & 0xF


def gfpow(a: int, n: int) -> int:
    out = 1
    while n:
        if n & 1:
            out = gf16mul(out, a)
        a = gf16mul(a, a)
        n >>= 1
    return out


def dot(a: int, b: int) -> int:
    return (a & b).bit_count() & 1


def rank4(vectors) -> int:
    pivots = [0] * 4
    rank = 0
    for x in vectors:
        y = x
        for p in range(3, -1, -1):
            if not ((y >> p) & 1):
                continue
            if pivots[p]:
                y ^= pivots[p]
            else:
                pivots[p] = y
                rank += 1
                break
    return rank


def semilinear_covector_actions():
    actions = []
    for c in range(1, 16):
        for k in range(4):
            table = [0] * 16
            for y in range(16):
                table[y] = 0 if y == 0 else gf16mul(c, gfpow(y, 1 << k))
            assert len(set(table)) == 16
            inverse = [0] * 16
            for y, z in enumerate(table):
                inverse[z] = y

            action = [0] * 16
            for r in range(16):
                truth = [dot(r, inverse[z]) for z in range(16)]
                matches = [rp for rp in range(16) if all(dot(rp, z) == truth[z] for z in range(16))]
                assert len(matches) == 1
                action[r] = matches[0]
            actions.append(tuple(action))
    assert len(set(actions)) == 60
    return tuple(actions)


def candidate_weighted_supports():
    out = set()
    for support in itertools.combinations(range(1, 16), 8):
        if rank4(support) != 4:
            continue
        for heavy in support:
            if all(
                sum((2 if r == heavy else 1) for r in support if dot(r, y)) >= 4
                for y in range(1, 16)
            ):
                out.add((frozenset(support), heavy))
    return out


def main():
    candidates = candidate_weighted_supports()
    assert len(candidates) == 960
    actions = semilinear_covector_actions()

    covered = set()
    orbit_sizes = []
    for support_tuple, heavy in REPRESENTATIVES:
        support = frozenset(support_tuple)
        assert (support, heavy) in candidates
        orbit = set()
        for action in actions:
            transformed_support = frozenset(action[r] for r in support)
            transformed_heavy = action[heavy]
            orbit.add((transformed_support, transformed_heavy))
        assert len(orbit) == 60
        assert orbit <= candidates
        assert not (orbit & covered)
        covered |= orbit
        orbit_sizes.append(len(orbit))

    assert covered == candidates
    summary = {
        "weighted_support_candidates": len(candidates),
        "semilinear_autotopisms": len(actions),
        "orbits": len(REPRESENTATIVES),
        "orbit_sizes": orbit_sizes,
        "covered_candidates": len(covered),
        "representatives": [
            {"support": list(support), "heavy": heavy}
            for support, heavy in REPRESENTATIVES
        ],
        "conclusion": "the 16 representatives exactly cover all 960 necessary eight-right-factor multiplicity patterns",
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
