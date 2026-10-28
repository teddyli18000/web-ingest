#!/usr/bin/env python3
"""Enumerate the complete nonlinear-envelope frontier for a six-AND p008 core.

This is a cheap exact decomposition for the remaining fixed-interface
`6 AND + 11 linear` route.  Work modulo affine functions of the four core inputs.
The live nine-factor target space T has quotient rank four.  In the rank-six case
all six ANDs add independent nonlinear classes, so the final raw-AND span is a
six-dimensional envelope E containing T.

Before `span(current,T)` first reaches rank six it has rank five.  At the first
rank-five -> rank-six transition the final envelope E is fixed: every later
independent raw-AND class must remain inside E.  Therefore we can enumerate every
reachable rank-five frontier state, collect the envelope at each first rank-six
transition, and stop following that branch.  This avoids enumerating the much
larger full six-AND span DAG while still giving a complete envelope set.

The result is a set of exact-search shards, not a 101 construction and not a proof
that every envelope admits a physical six-AND / eleven-linear realization.
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


def candidate_residues(basis):
    """All independent next nonlinear classes reachable from the current span."""
    function_space = span_values(canonical_basis(LINEAR_BASIS + basis))
    residues = set()
    for i in range(1, len(function_space)):
        u = function_space[i]
        for j in range(1, i):
            residue = STRIP[u & function_space[j]]
            if residue and reduce_by_basis(residue, basis):
                residues.add(residue)
    return residues


def first_step_spans():
    return {canonical_basis((r,)) for r in candidate_residues(())}


def transition_rank5(frontier):
    """Advance every reachable join-rank-five span by one independent AND.

    Returns `(next_rank5_frontier, exposed_rank6_envelopes)`.  If the next residue
    lies in J=span(current,T), the join rank stays five.  Otherwise J plus that
    residue is the first rank-six envelope for that branch.
    """
    stay = set()
    envelopes = set()
    for basis in frontier:
        joined = canonical_basis(basis + TARGET_BASIS)
        assert len(joined) == 5
        for residue in candidate_residues(basis):
            if not reduce_by_basis(residue, joined):
                stay.add(canonical_basis(basis + (residue,)))
            else:
                envelopes.add(canonical_basis(joined + (residue,)))
    return stay, envelopes


def main():
    assert len(TARGET_BASIS) == 4

    level1 = first_step_spans()
    join1 = collections.Counter(len(canonical_basis(b + TARGET_BASIS)) for b in level1)
    assert join1 == collections.Counter({5: 35})

    # First possible exposure is at the second AND.  Keep only branches whose join
    # rank remains five; rank-six branches have already fixed their final envelope.
    frontier2, exposed2 = transition_rank5(level1)
    all_envelopes = set(exposed2)
    rows = [{
        "and_depth": 2,
        "rank5_frontier": len(frontier2),
        "rank6_envelopes_exposed": len(exposed2),
        "new_rank6_envelopes": len(exposed2),
        "rank6_envelopes_total": len(all_envelopes),
    }]

    frontier = frontier2
    for depth in range(3, 7):
        frontier, exposed = transition_rank5(frontier)
        new = exposed - all_envelopes
        all_envelopes.update(exposed)
        rows.append({
            "and_depth": depth,
            "rank5_frontier": len(frontier),
            "rank6_envelopes_exposed": len(exposed),
            "new_rank6_envelopes": len(new),
            "rank6_envelopes_total": len(all_envelopes),
        })

    summary = {
        "target_quotient_rank": len(TARGET_BASIS),
        "first_and_spans": len(level1),
        "first_join_rank_distribution": dict(sorted(join1.items())),
        "frontier_log": rows,
        "unique_reachable_rank6_envelopes": len(all_envelopes),
    }
    print(json.dumps(summary, sort_keys=True))

    assert summary == {
        "target_quotient_rank": 4,
        "first_and_spans": 35,
        "first_join_rank_distribution": {5: 35},
        "frontier_log": [
            {"and_depth": 2, "rank5_frontier": 60, "rank6_envelopes_exposed": 585,
             "new_rank6_envelopes": 585, "rank6_envelopes_total": 585},
            {"and_depth": 3, "rank5_frontier": 210, "rank6_envelopes_exposed": 1515,
             "new_rank6_envelopes": 960, "rank6_envelopes_total": 1545},
            {"and_depth": 4, "rank5_frontier": 270, "rank6_envelopes_exposed": 1515,
             "new_rank6_envelopes": 0, "rank6_envelopes_total": 1545},
            {"and_depth": 5, "rank5_frontier": 30, "rank6_envelopes_exposed": 1515,
             "new_rank6_envelopes": 0, "rank6_envelopes_total": 1545},
            {"and_depth": 6, "rank5_frontier": 0, "rank6_envelopes_exposed": 1515,
             "new_rank6_envelopes": 0, "rank6_envelopes_total": 1545},
        ],
        "unique_reachable_rank6_envelopes": 1545,
    }


if __name__ == "__main__":
    main()
