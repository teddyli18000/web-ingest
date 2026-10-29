#!/usr/bin/env python3
"""Finite support classification for 9-product GF(16) bilinear multipliers.

The companion C++ exact enumerator proves that exactly three of the eleven
semilinear support orbits below admit a physical rank-9 multiplier.  This script
handles the independent combinatorial/symmetry/linear-network parts:

* enumerate all 9-subsets of nonzero four-bit right forms satisfying the necessary
  rank-subadditivity condition that every nonzero y activates at least four terms;
* partition them under the 60 exact GF(16) semilinear autotopisms;
* compute the exact minimum number of XOR gates needed to materialize a support
  from the four coordinate inputs;
* summarize the 40 supports in the three physically realizable orbits identified
  by `prove_gf16_rank9_right_supports.cpp`.
"""
from __future__ import annotations

import collections
import itertools
import json
from collections import deque

from prove_gf16_right8_semilinear_orbits import dot, rank4, semilinear_covector_actions


ORBIT_REPRESENTATIVES = [
    ((1,2,3,4,5,8,9,14,15),30),
    ((1,2,3,4,5,8,10,12,15),15),
    ((1,2,3,4,5,8,10,13,14),60),
    ((1,2,3,4,5,8,11,12,14),15),
    ((1,2,3,4,5,8,11,13,15),60),
    ((1,2,3,4,5,9,10,12,14),30),
    ((1,2,3,4,5,9,10,13,15),60),
    ((1,2,3,4,5,10,11,12,13),60),
    ((1,2,3,4,6,8,10,13,15),15),
    ((1,2,3,4,6,8,11,14,15),30),
    ((1,2,3,5,7,9,10,12,13),10),
]

# Exact physical witnesses are found only for these three representatives by the
# companion grouped-matrix exhaustive search.
REALIZABLE_ORBITS = (1, 8, 10)


def candidate_supports():
    out = set()
    for support in itertools.combinations(range(1, 16), 9):
        if rank4(support) != 4:
            continue
        if all(sum(dot(r, y) for r in support) >= 4 for y in range(1, 16)):
            out.add(frozenset(support))
    return out


def xor_distances():
    # State bit f-1 records that nonzero form f is available.  One XOR adds the
    # xor of two already available forms.  The full state space has only 2^15.
    def bit(f):
        return 1 << (f - 1)

    initial = bit(1) | bit(2) | bit(4) | bit(8)
    inf = 99
    dist = [inf] * (1 << 15)
    dist[initial] = 0
    q = deque([initial])
    while q:
        state = q.popleft()
        available = [f for f in range(1, 16) if state & bit(f)]
        new_forms = set()
        for i, a in enumerate(available):
            for b in available[i + 1:]:
                c = a ^ b
                if c and not (state & bit(c)):
                    new_forms.add(c)
        for c in new_forms:
            nxt = state | bit(c)
            if dist[nxt] > dist[state] + 1:
                dist[nxt] = dist[state] + 1
                q.append(nxt)
    return dist


def support_cost(support, dist):
    target = 0
    for f in support:
        target |= 1 << (f - 1)
    return min(d for state, d in enumerate(dist) if (state & target) == target)


def main():
    candidates = candidate_supports()
    assert len(candidates) == 385
    actions = semilinear_covector_actions()

    covered = set()
    orbits = []
    for idx, (rep_tuple, expected_size) in enumerate(ORBIT_REPRESENTATIVES):
        rep = frozenset(rep_tuple)
        assert rep in candidates
        orbit = {frozenset(action[r] for r in rep) for action in actions}
        assert len(orbit) == expected_size
        assert orbit <= candidates
        assert not (orbit & covered)
        covered |= orbit
        orbits.append(orbit)
    assert covered == candidates

    dist = xor_distances()
    all_costs = collections.Counter(support_cost(s, dist) for s in candidates)
    realizable = set().union(*(orbits[i] for i in REALIZABLE_ORBITS))
    assert len(realizable) == 40
    realizable_costs = collections.Counter(support_cost(s, dist) for s in realizable)
    assert realizable_costs == collections.Counter({5: 2, 6: 14, 7: 20, 8: 4})

    cheapest = sorted(tuple(sorted(s)) for s in realizable if support_cost(s, dist) == 5)
    assert cheapest == [
        (1,2,3,4,5,8,10,12,15),
        (1,2,4,6,7,8,9,10,13),
    ]

    summary = {
        "necessary_supports": len(candidates),
        "semilinear_orbits": len(orbits),
        "orbit_sizes": [len(o) for o in orbits],
        "realizable_orbit_indices": list(REALIZABLE_ORBITS),
        "realizable_supports": len(realizable),
        "necessary_support_xor_cost_distribution": dict(sorted(all_costs.items())),
        "realizable_support_xor_cost_distribution": dict(sorted(realizable_costs.items())),
        "cheapest_realizable_supports": [list(s) for s in cheapest],
        "conclusion": (
            "conditional only on the companion exact physical-orbit classification: "
            "all rank-9 GF16 right supports lie in three semilinear orbits, and only "
            "two coordinate representatives can be generated from the standard four bits in five XOR gates"
        ),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
