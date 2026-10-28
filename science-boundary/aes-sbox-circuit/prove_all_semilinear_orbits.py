#!/usr/bin/env python3
"""Prove exact six-element equivalence orbits for all 2040 semilinear transforms.

The retained-18-core construction is parameterized by

    P(x) = c * x^(2^k), c != 0, k=0..7.

There are 2040 such transforms.  This script groups them by the unordered sets of
nine transported input product planes and nine transported output product planes,
then proves every member of every group is exactly equivalent to its representative
for the complete retained-core outer-construction search.

For each representative/member pair it proves:

* one permutation sigma maps all nine input planes and the same sigma maps all nine
  output planes;
* the per-plane ternary orientation relabeling is identical on input and dual-output
  plane bases;
* sigma is induced by a genuine automorphism M of both the nine middle columns and
  the nine live 18-gate-core factors;
* the middle desired-delta relation is transported by M.  Since desired_delta is
  an XOR sum of independent per-plane contributions, checking the all-zero choice
  vector plus both nonzero choices in each one-plane perturbation (19 vectors total)
  proves the identity for all 3^9 orientations.

The result is 340 exact orbits of size six.  Therefore any exact retained-core
outer search only needs one semilinear representative per orbit.  This is specific
to this retained-core family, not a global AES-circuit equivalence claim.
"""
from __future__ import annotations

import argparse
import itertools
import json
from collections import defaultdict
from pathlib import Path

import prove_semilinear_class_automorphisms as proof
import search_plane_middle5 as mid
import search_semilinear_outer as outer


def plane_key(pair):
    a, b = pair
    return tuple(sorted((a, b, a ^ b)))


def transport_key(c, k):
    planes, outpairs, _corrections = outer.transported_data(c, k)
    return (
        tuple(sorted(plane_key(pair) for pair in planes)),
        tuple(sorted(plane_key(pair) for pair in outpairs)),
    )


def full_core_automorphisms():
    """Return sigma -> M for the complete middle-column/core-factor automorphism group."""
    col_index = {value: i for i, value in enumerate(mid.COLS)}
    assert len(col_index) == 9
    autos = {}
    for columns in itertools.product(range(1, 16), repeat=4):
        if proof.rank4(columns) != 4:
            continue
        sigma = []
        ok = True
        for value in mid.COLS:
            mapped = proof.apply4(columns, value)
            if mapped not in col_index:
                ok = False
                break
            sigma.append(col_index[mapped])
        if not ok or len(set(sigma)) != 9:
            continue
        sigma = tuple(sigma)
        try:
            proof.prove_core_covariance(sigma, columns)
        except AssertionError:
            continue
        assert sigma not in autos
        autos[sigma] = tuple(columns)
    assert len(autos) == 6
    return autos


def check_pair(representative, member, autos):
    rplanes, rout, rcorr = proof.transported(*representative)
    mplanes, mout, mcorr = proof.transported(*member)

    sigma = proof.plane_permutation(rplanes, mplanes)
    assert sigma == proof.plane_permutation(rout, mout)
    assert sigma in autos
    matrix = autos[sigma]

    pre_maps = proof.choice_maps(rplanes, mplanes, sigma, dual=False)
    out_maps = proof.choice_maps(rout, mout, sigma, dual=True)
    assert pre_maps == out_maps

    # Per-plane set equality is already exact by choice_maps.  For the middle map,
    # desired_delta is separable across planes, so baseline + two perturbations per
    # plane is a complete proof over the ternary product domain.
    tests = [(0,) * 9]
    for i in range(9):
        for choice in (1, 2):
            row = [0] * 9
            row[i] = choice
            tests.append(tuple(row))
    assert len(tests) == 19

    for choices in tests:
        mapped = proof.map_choices(choices, sigma, pre_maps)
        lhs = proof.apply_middle_rows(
            matrix, proof.desired_delta(rplanes, rcorr, choices)
        )
        rhs = proof.desired_delta(mplanes, mcorr, mapped)
        assert lhs == rhs

    return {
        "member": [member[0], member[1]],
        "plane_permutation": list(sigma),
        "middle_matrix_columns": list(matrix),
        "choice_maps": [list(row) for row in pre_maps],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()

    autos = full_core_automorphisms()
    groups = defaultdict(list)
    for k in range(8):
        for c in range(1, 256):
            groups[transport_key(c, k)].append((c, k))

    assert len(groups) == 340
    assert {len(members) for members in groups.values()} == {6}

    orbit_rows = []
    member_checks = 0
    for members in groups.values():
        members = sorted(members, key=lambda ck: (ck[1], ck[0]))
        representative = members[0]
        checks = []
        for member in members[1:]:
            checks.append(check_pair(representative, member, autos))
            member_checks += 1
        orbit_rows.append({
            "representative": [representative[0], representative[1]],
            "members": [[c, k] for c, k in members],
            "checks": checks,
        })

    orbit_rows.sort(key=lambda row: (row["representative"][1], row["representative"][0]))
    assert member_checks == 340 * 5 == 1700

    summary = {
        "semilinear_transforms": 2040,
        "exact_orbits": len(orbit_rows),
        "orbit_size": 6,
        "nonrepresentative_member_checks": member_checks,
        "core_middle_automorphism_group_size": len(autos),
        "core_middle_automorphisms": [
            {
                "plane_permutation": list(sigma),
                "middle_matrix_columns": list(matrix),
            }
            for sigma, matrix in sorted(autos.items())
        ],
        "derived_orbit_counts_from_existing_best_lb_distribution": {
            "31": 3,
            "32": 5,
            "33": 4,
            "34": 13,
            "35": 25,
            "36": 39,
            "37": 56,
            "38": 99,
            "39": 96,
        },
        "retained_core_101_survivor_orbits_lb_le_36": 89,
        "conclusion": (
            "all 2040 semilinear transforms split into 340 exact six-element "
            "retained-core outer-construction equivalence orbits"
        ),
    }

    result = {"summary": summary, "orbits": orbit_rows}
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
