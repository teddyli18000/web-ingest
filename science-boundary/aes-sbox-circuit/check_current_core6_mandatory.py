#!/usr/bin/env python3
"""Mandatory-affine-form lower bound for the live 102 circuit's six-AND core.

The live core has 6 raw AND outputs and 12 XOR gates (18 gates total).  A 17-gate
replacement that keeps *the same six raw AND truth tables* would have only 11
linear gates available.  The fixed tail observes the nine factor outputs on core
states 1..15 and has a complete don't-care at state 0000, so each factor may be
completed independently by either its exact truth table or its complement.

For the fixed raw-AND skeleton, every AND operand and every exposed target is an
affine combination of the four inputs and the raw AND outputs.  A non-unit affine
form cannot be obtained for free: it must be materialized by an XOR/XNOR gate.
This script enumerates all 2^9 zero-state completions and counts the distinct
mandatory non-free affine forms.  The minimum is 12, proving that the current
six-AND skeleton cannot fit in 17 gates, even with full zero-state ODC/XNOR use.

Scope: this is a lower bound only for the *current six raw AND truth tables*.
A different six-AND nonlinear skeleton remains possible.
"""
from __future__ import annotations

import collections

MASK16 = (1 << 16) - 1


def var(i: int) -> int:
    return sum((((x >> i) & 1) << x) for x in range(16))


def affine_coords(sources):
    pairs = [(0, 0)]
    for i, value in enumerate(sources):
        old = pairs[:]
        pairs += [(truth ^ value, mask | (1 << i)) for truth, mask in old]
    out = {}
    for truth, mask in pairs:
        out[truth] = (mask, 0)
        out[truth ^ MASK16] = (mask, 1)
    return out


def is_free(form):
    mask, const = form
    return const == 0 and mask > 0 and (mask & (mask - 1)) == 0


def gf2_rank(values):
    pivots = {}
    for value in values:
        y = value
        while y:
            p = y.bit_length() - 1
            if p in pivots:
                y ^= pivots[p]
            else:
                pivots[p] = y
                break
    return len(pivots)


def main():
    a, b, c, d = [var(i) for i in range(4)]

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

    raw_ands = [q42, q44, q46, q48, q51, q54]
    targets = [q45, q59, q52, q57, q53, q49, q58, q55, q56]

    # At each AND, express the exact operands in the primitive basis available
    # immediately before that AND.
    stages = [
        ([a, b, c, d], (a, b)),
        ([a, b, c, d, q42], (q43, d)),
        ([a, b, c, d, q42, q44], (q42, c)),
        ([a, b, c, d, q42, q44, q46], (a, q47)),
        ([a, b, c, d, q42, q44, q46, q48], (q49, q50)),
        ([a, b, c, d, q42, q44, q46, q48, q51], (q45, q53)),
    ]
    operand_forms = []
    for sources, operands in stages:
        coords = affine_coords(sources)
        operand_forms.extend(coords[x] for x in operands)

    primitive_sources = [a, b, c, d] + raw_ands
    assert gf2_rank(primitive_sources) == len(primitive_sources) == 10
    coords = affine_coords(primitive_sources)
    target_pairs = [(coords[t], coords[t ^ MASK16]) for t in targets]

    base = {form for form in operand_forms if not is_free(form)}
    distribution = collections.Counter()
    best = 99
    best_patterns = []

    for pattern in range(1 << len(targets)):
        mandatory = set(base)
        for i, pair in enumerate(target_pairs):
            form = pair[(pattern >> i) & 1]
            if not is_free(form):
                mandatory.add(form)
        count = len(mandatory)
        distribution[count] += 1
        if count < best:
            best = count
            best_patterns = [pattern]
        elif count == best:
            best_patterns.append(pattern)

    print("operand mandatory forms =", len(base), sorted(base))
    print("completion distribution =", dict(sorted(distribution.items())))
    print("minimum mandatory affine forms =", best)
    print("minimum completion count =", len(best_patterns))
    print("example completion patterns =", best_patterns[:20])

    assert distribution == collections.Counter({12: 64, 13: 192, 14: 192, 15: 64})
    assert best == 12
    assert len(best_patterns) == 64
    # Six ANDs + at least twelve linear gates => at least 18 gates for this skeleton.
    assert 6 + best == 18


if __name__ == "__main__":
    main()
