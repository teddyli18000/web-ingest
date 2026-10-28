#!/usr/bin/env python3
"""Prove exact outer-construction equivalence inside the three LB=31 classes.

The cheap 2040-transform scan grouped the 18 global-best semilinear transforms
into three six-member classes by identical lower-bound distributions.  That alone
was not an exact-cost equivalence proof.

This script proves the stronger statement for the retained-18-core construction.
For every nonrepresentative member of each class it constructs a bijection on the
nine product planes and the three orientations of each plane such that, for every
one of the 3^9 orientation vectors:

* the prelinear target set is exactly identical after reindexing;
* the transposed-output target set is exactly identical after reindexing;
* the middle correction equation is carried by an invertible 4-bit map M;
* the same plane permutation and M are an automorphism of the nine live core
  factors: F_{sigma(i)}(M y) = F_i(y).

Therefore every physical prelinear network (including helper choices), middle
correction support, and output network transports with exactly the same gate cost.
Each six-member class is an exact search-equivalence orbit, not merely a heuristic
lower-bound class.
"""
from __future__ import annotations

import itertools
import json

import search_plane_middle5 as mid
import search_semilinear_outer as outer


CLASSES = {
    "A": [(0x01, 0), (0xBC, 0), (0xBD, 0), (0x1B, 4), (0x66, 4), (0x7D, 4)],
    "B": [(0x6B, 3), (0x9D, 3), (0xF6, 3), (0x13, 7), (0xEA, 7), (0xF9, 7)],
    "C": [(0x5B, 3), (0xA9, 3), (0xF2, 3), (0x7E, 7), (0xB9, 7), (0xC7, 7)],
}


def plane_set(pair):
    a, b = pair
    return frozenset((a, b, a ^ b))


def selected(pair, choice, dual=False):
    a, b = pair
    if not dual:
        values = ((a, b), (a, a ^ b), (a ^ b, b))[choice]
    else:
        values = ((a, b), (a ^ b, b), (a, a ^ b))[choice]
    return frozenset(values)


def plane_permutation(source, target):
    lookup = {plane_set(pair): i for i, pair in enumerate(target)}
    assert len(lookup) == 9
    sigma = tuple(lookup[plane_set(pair)] for pair in source)
    assert sorted(sigma) == list(range(9))
    return sigma


def choice_maps(source, target, sigma, dual=False):
    maps = []
    for i, pair in enumerate(source):
        target_pair = target[sigma[i]]
        row = []
        for choice in range(3):
            want = selected(pair, choice, dual=dual)
            hits = [
                c for c in range(3)
                if selected(target_pair, c, dual=dual) == want
            ]
            assert len(hits) == 1
            row.append(hits[0])
        assert sorted(row) == [0, 1, 2]
        maps.append(tuple(row))
    return tuple(maps)


def rank4(columns):
    rows = [0] * 4
    rank = 0
    for value in columns:
        x = value
        for p in range(3, -1, -1):
            if not ((x >> p) & 1):
                continue
            if rows[p]:
                x ^= rows[p]
            else:
                rows[p] = x
                rank += 1
                break
    return rank


def apply4(columns, value):
    out = 0
    for i in range(4):
        if (value >> i) & 1:
            out ^= columns[i]
    return out


def middle_map_for_sigma(sigma):
    hits = []
    for columns in itertools.product(range(1, 16), repeat=4):
        if rank4(columns) != 4:
            continue
        if all(
            apply4(columns, mid.COLS[i]) == mid.COLS[sigma[i]]
            for i in range(9)
        ):
            hits.append(tuple(columns))
    assert len(hits) == 1
    return hits[0]


def core_factors(value):
    a, b, c, d = ((value >> i) & 1 for i in range(4))
    q42 = a & b
    q43 = q42 ^ c
    q44 = q43 & d
    q45 = b ^ q44
    q46 = q42 & c
    q47 = d ^ q46
    q48 = a & q47
    q49 = q43 ^ q48
    q50 = q48 ^ b
    q51 = q49 & q50
    q52 = q51 ^ a
    q53 = q52 ^ q49
    q54 = q45 & q53
    q55 = q54 ^ q47
    q56 = q55 ^ q49
    q57 = q53 ^ q45
    q58 = q56 ^ q57
    q59 = q55 ^ q45
    return (q45, q59, q52, q57, q53, q49, q58, q55, q56)


def prove_core_covariance(sigma, matrix):
    for y in range(16):
        fy = core_factors(y)
        fmy = core_factors(apply4(matrix, y))
        for i in range(9):
            assert fmy[sigma[i]] == fy[i], (sigma, matrix, y, i)


def contribution(column, value):
    return [value if (column >> j) & 1 else 0 for j in range(4)]


def xor4(a, b):
    return [a[i] ^ b[i] for i in range(4)]


def desired_delta(planes, corrections, choices):
    delta = [0, 0, 0, 0]
    for i, value in enumerate(corrections):
        if value:
            delta = xor4(delta, contribution(mid.COLS[i], value))
    for i, ((a, b), choice) in enumerate(zip(planes, choices)):
        offset = 0 if choice == 0 else (a if choice == 1 else b)
        if offset:
            delta = xor4(delta, contribution(mid.COLS[i], offset))
    return delta


def apply_middle_rows(matrix, rows):
    out = [0, 0, 0, 0]
    for i, column in enumerate(matrix):
        for j in range(4):
            if (column >> j) & 1:
                out[j] ^= rows[i]
    return out


def map_choices(choices, sigma, maps):
    out = [None] * 9
    for i, choice in enumerate(choices):
        out[sigma[i]] = maps[i][choice]
    assert all(x is not None for x in out)
    return tuple(out)


def targets(pairs, choices, dual=False):
    out = set()
    for pair, choice in zip(pairs, choices):
        out.update(selected(pair, choice, dual=dual))
    return frozenset(out)


def transported(c, k):
    planes, outpairs, corrections = outer.transported_data(c, k)
    return tuple(planes), tuple(outpairs), tuple(corrections)


def prove_member(representative, member):
    rplanes, rout, rcorr = transported(*representative)
    mplanes, mout, mcorr = transported(*member)

    sigma = plane_permutation(rplanes, mplanes)
    assert sigma == plane_permutation(rout, mout)

    pre_maps = choice_maps(rplanes, mplanes, sigma, dual=False)
    out_maps = choice_maps(rout, mout, sigma, dual=True)
    assert pre_maps == out_maps

    matrix = middle_map_for_sigma(sigma)
    prove_core_covariance(sigma, matrix)

    checked = 0
    for choices in itertools.product(range(3), repeat=9):
        mapped = map_choices(choices, sigma, pre_maps)
        assert targets(rplanes, choices, dual=False) == targets(
            mplanes, mapped, dual=False
        )
        assert targets(rout, choices, dual=True) == targets(
            mout, mapped, dual=True
        )
        assert apply_middle_rows(matrix, desired_delta(rplanes, rcorr, choices)) == desired_delta(
            mplanes, mcorr, mapped
        )
        checked += 1

    return {
        "representative": [representative[0], representative[1]],
        "member": [member[0], member[1]],
        "plane_permutation": list(sigma),
        "middle_matrix_columns": list(matrix),
        "choice_maps": [list(row) for row in pre_maps],
        "orientations_checked": checked,
    }


def main():
    rows = []
    for name, members in CLASSES.items():
        representative = members[0]
        for member in members[1:]:
            row = prove_member(representative, member)
            row["class"] = name
            rows.append(row)
            print(json.dumps(row, sort_keys=True))

    assert len(rows) == 15
    assert all(row["orientations_checked"] == 3**9 for row in rows)
    permutations = {tuple(row["plane_permutation"]) for row in rows}
    matrices = {tuple(row["middle_matrix_columns"]) for row in rows}
    summary = {
        "classes": len(CLASSES),
        "members_proved_from_representatives": len(rows),
        "orientations_checked_per_member": 3**9,
        "distinct_plane_permutations": [list(x) for x in sorted(permutations)],
        "distinct_middle_matrices": [list(x) for x in sorted(matrices)],
        "conclusion": (
            "within each LB=31 six-member class, retained-core outer constructions "
            "are exactly gate-cost equivalent under plane/orientation relabeling and "
            "the verified 4-bit core automorphism"
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
