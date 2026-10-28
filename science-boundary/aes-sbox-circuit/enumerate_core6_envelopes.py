#!/usr/bin/env python3
"""Enumerate the first two nonlinear quotient steps for a six-AND p008 core.

This is a cheap exact decomposition for the remaining fixed-interface
`6 AND + 11 linear` route.  Work modulo affine functions of the four core inputs.
The live nine-factor target space has quotient rank four.  Any six-AND circuit
whose six ANDs all add independent nonlinear classes has a six-dimensional final
nonlinear envelope E containing that target space.  Once two independent AND
classes make `span(current,target)` rank six, all later independent classes must
remain inside the same E.

We enumerate every quotient class realizable by the first AND and every independent
class realizable by the second AND, retaining only partial spans that can still fit
inside some rank-six envelope containing the target space.  The resulting unique E
spaces are natural exact-search shards; this script does not claim that every E
can be completed to a six-AND circuit with eleven linear gates.
"""
from __future__ import annotations

import collections
import json


def mobius16(x: int) -> int:
    x ^= (x & 0x5555) << 1
    x ^= (x & 0x3333) << 2
    x ^= (x & 0x0F0F) << 4
    x ^= (x & 0x00FF) << 8
    return x & 0xFFFF


def strip_affine(x: int) -> int:
    anf = mobius16(x)
    anf &= ~0x0117 & 0xFFFF  # remove monomials 1,x0,x1,x2,x3
    return mobius16(anf)


STRIP = [strip_affine(x) for x in range(1 << 16)]


def var(i: int) -> int:
    return sum((((x >> i) & 1) << x) for x in range(16))


INPUTS = tuple(var(i) for i in range(4))


def canonical_basis(vectors):
    rows = [0] * 16
    for x in vectors:
        y = x
        while y:
            p = y.bit_length() - 1
            if rows[p]:
                y ^= rows[p]
                continue
            for q in range(p - 1, -1, -1):
                if rows[q] and ((y >> q) & 1):
                    y ^= rows[q]
            if not y:
                break
            p = y.bit_length() - 1
            for q in range(p + 1, 16):
                if rows[q] and ((rows[q] >> p) & 1):
                    rows[q] ^= y
            rows[p] = y
            break
    return tuple(x for x in rows if x)


def reduce_by_basis(x, basis):
    y = x
    for v in reversed(basis):
        if (y >> (v.bit_length() - 1)) & 1:
            y ^= v
    return y


def span_values(basis):
    out = [0]
    for v in basis:
        out += [x ^ v for x in out]
    return out


def live_targets():
    a, b, c, d = INPUTS
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


LINEAR_BASIS = canonical_basis(INPUTS)
TARGET_BASIS = canonical_basis(tuple(STRIP[x] for x in live_targets()))


def next_spans(basis):
    joined = canonical_basis(basis + TARGET_BASIS)
    if len(joined) > 6:
        return set()
    # Once target+current already fills a six-dimensional envelope, every later
    # independent nonlinear class must lie in that envelope.
    allowed = set(span_values(joined)) if len(joined) == 6 else None
    function_space = span_values(canonical_basis(LINEAR_BASIS + basis))
    out = set()
    for i in range(1, len(function_space)):
        u = function_space[i]
        for j in range(1, i):
            v = function_space[j]
            residue = STRIP[u & v]
            if not residue or not reduce_by_basis(residue, basis):
                continue
            if allowed is not None and residue not in allowed:
                continue
            nxt = canonical_basis(basis + (residue,))
            if len(canonical_basis(nxt + TARGET_BASIS)) <= 6:
                out.add(nxt)
    return out


def main():
    assert len(TARGET_BASIS) == 4
    level1 = next_spans(())
    level2 = set()
    for basis in level1:
        level2.update(next_spans(basis))

    join1 = collections.Counter(len(canonical_basis(b + TARGET_BASIS)) for b in level1)
    join2 = collections.Counter(len(canonical_basis(b + TARGET_BASIS)) for b in level2)
    envelopes = {
        canonical_basis(b + TARGET_BASIS)
        for b in level2
        if len(canonical_basis(b + TARGET_BASIS)) == 6
    }

    summary = {
        "target_quotient_rank": len(TARGET_BASIS),
        "first_and_spans": len(level1),
        "first_join_rank_distribution": dict(sorted(join1.items())),
        "second_and_spans": len(level2),
        "second_join_rank_distribution": dict(sorted(join2.items())),
        "unique_rank6_envelopes": len(envelopes),
    }
    print(json.dumps(summary, sort_keys=True))

    # Regression values from the exact enumeration.  These make accidental model
    # changes visible and are small enough to reproduce directly.
    assert summary == {
        "target_quotient_rank": 4,
        "first_and_spans": 35,
        "first_join_rank_distribution": {5: 35},
        "second_and_spans": 2485,
        "second_join_rank_distribution": {5: 60, 6: 2425},
        "unique_rank6_envelopes": 585,
    }


if __name__ == "__main__":
    main()
