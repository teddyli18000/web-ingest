#!/usr/bin/env python3
"""Solver-free exclusion of 496/512 zero-state completions for five-AND cores.

The fixed 102 tail allows each of the nine core factors to take either value at
core state 0000 while requiring exact values on the other 15 states.  Hence there
are 2^9=512 factor-completion patterns.

Work modulo affine functions.  The 512 patterns split into 16 rank-4 target
subspaces and 496 rank-5 patterns; all 496 rank-5 patterns span the same 5D
nonlinear quotient space U.

In a circuit with exactly five AND gates computing a rank-5 target space, the five
AND-output classes must be independent and span U exactly.  In particular the
first AND class must lie in U.  Before the first AND, both operands are affine
functions of the four core inputs.  Exhaustively enumerate every product of two
such affine functions and strip affine terms.  None of the 35 nonzero possible
first-AND classes lies in U.  Therefore every rank-5 completion needs at least six
AND gates.

This leaves exactly 16 rank-4 completion patterns for any possible five-AND
17-gate direct-core construction.
"""
from __future__ import annotations

import json


def mobius16(x: int) -> int:
    x ^= (x & 0x5555) << 1
    x ^= (x & 0x3333) << 2
    x ^= (x & 0x0F0F) << 4
    x ^= (x & 0x00FF) << 8
    return x & 0xFFFF


def strip_affine(x: int) -> int:
    anf = mobius16(x)
    anf &= ~0x0117 & 0xFFFF  # remove monomials 1, x0, x1, x2, x3
    return mobius16(anf)


def var(i: int) -> int:
    return sum((((x >> i) & 1) << x) for x in range(16))


def canonical_basis(vectors):
    rows = [0] * 16
    for x in vectors:
        y = x
        for p in range(15, -1, -1):
            if not ((y >> p) & 1):
                continue
            if rows[p]:
                y ^= rows[p]
                continue
            for q in range(p - 1, -1, -1):
                if rows[q] and ((y >> q) & 1):
                    y ^= rows[q]
            p = y.bit_length() - 1
            for q in range(p + 1, 16):
                if rows[q] and ((rows[q] >> p) & 1):
                    rows[q] ^= y
            rows[p] = y
            break
    return tuple(x for x in rows if x)


def span_values(basis):
    values = [0]
    for v in basis:
        values += [x ^ v for x in values]
    return values


def source_targets(inputs):
    a, b, c, d = inputs
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
    return [q45, q59, q52, q57, q53, q49, q58, q55, q56]


def main():
    inputs = [var(i) for i in range(4)]
    targets = source_targets(inputs)
    care_nonzero = 0xFFFE

    by_basis = {}
    rank_distribution = {}
    rank4_patterns = []
    for pattern in range(1 << 9):
        residues = [
            strip_affine(targets[i] ^ (care_nonzero if ((pattern >> i) & 1) else 0))
            for i in range(9)
        ]
        basis = canonical_basis(residues)
        rank_distribution[len(basis)] = rank_distribution.get(len(basis), 0) + 1
        by_basis.setdefault(basis, []).append(pattern)
        if len(basis) == 4:
            rank4_patterns.append(pattern)

    rank5_bases = [basis for basis in by_basis if len(basis) == 5]
    assert rank_distribution == {4: 16, 5: 496}, rank_distribution
    assert len(rank5_bases) == 1, len(rank5_bases)
    nonlinear_u = rank5_bases[0]
    u_span = set(span_values(nonlinear_u))

    # All affine functions of four inputs: span{x0,x1,x2,x3,1}.
    affine_inputs = span_values(inputs + [0xFFFF])
    assert len(affine_inputs) == 32
    first_and_classes = set()
    for i, left in enumerate(affine_inputs):
        for right in affine_inputs[: i + 1]:
            residue = strip_affine(left & right)
            if residue:
                first_and_classes.add(residue)

    intersection = sorted(first_and_classes & u_span)
    assert len(first_and_classes) == 35, len(first_and_classes)
    assert not intersection, [f"0x{x:04x}" for x in intersection]

    result = {
        "completion_patterns": 512,
        "rank_distribution": rank_distribution,
        "distinct_rank5_target_spaces": len(rank5_bases),
        "rank5_patterns_excluded_from_5_and": 496,
        "remaining_rank4_patterns": len(rank4_patterns),
        "remaining_rank4_patterns_binary": [f"{p:09b}" for p in rank4_patterns],
        "first_and_nonzero_classes": len(first_and_classes),
        "first_and_classes_intersect_rank5_target_space": len(intersection),
        "rank5_basis": [f"0x{x:04x}" for x in nonlinear_u],
        "conclusion": (
            "Every rank-5 zero-state completion needs at least six AND gates; "
            "only the 16 rank-4 completion patterns remain for five-AND cores."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
