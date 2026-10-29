#!/usr/bin/env python3
"""Exact d=11 fixed-A/B gluing with only universal degree and edge lower bounds.

For a hypothetical Ramsey(4,6,36) graph, fix a degree-11 anchor v, let
A=N(v) (11 vertices) and B be the 24 non-neighbours. After A and B are
fixed, the only variables are the 264 A--B edges.

This encoder is deliberately between two existing formulations:
  * d11_extreme_glue_dimacs.py: mixed Ramsey clauses only;
  * the m=219 label encodings: exact global degree sequence and edge count.

Here we add only constraints true for every valid 36-vertex graph:
  * each non-anchor vertex has degree in [11,17];
  * prior exact work proves every valid graph has at least 219 edges.
Thus UNSAT for a fixed pair closes that pair for every possible edge count,
while SAT is a genuine 36-vertex certificate after decoding.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import d11_extreme_glue_dimacs as base

NA, NB = 11, 24
MIN_TOTAL_EDGES = 219


def vm(a: int, b: int) -> int:
    return a * NB + b + 1


class VarPool:
    def __init__(self, start: int):
        self.next = start

    @property
    def top(self) -> int:
        return self.next - 1

    def new(self) -> int:
        v = self.next
        self.next += 1
        return v


def add_atmost(clauses: list[list[int]], lits: list[int], bound: int, pool: VarPool) -> int:
    """Sinz sequential-counter encoding of sum(lits) <= bound."""
    n = len(lits)
    before = len(clauses)
    if bound < 0:
        clauses.append([])
        return 1
    if bound >= n:
        return 0
    if bound == 0:
        clauses.extend([[-x] for x in lits])
        return len(clauses) - before

    aux = [[0] * (bound + 1) for _ in range(n)]
    for i in range(1, n):
        for j in range(1, bound + 1):
            aux[i][j] = pool.new()

    clauses.append([-lits[0], aux[1][1]])
    for j in range(2, bound + 1):
        clauses.append([-aux[1][j]])
    for i in range(2, n):
        clauses.append([-lits[i - 1], aux[i][1]])
        clauses.append([-aux[i - 1][1], aux[i][1]])
        for j in range(2, bound + 1):
            clauses.append([-lits[i - 1], -aux[i - 1][j - 1], aux[i][j]])
            clauses.append([-aux[i - 1][j], aux[i][j]])
    for i in range(2, n + 1):
        clauses.append([-lits[i - 1], -aux[i - 1][bound]])
    return len(clauses) - before


def add_atleast(clauses: list[list[int]], lits: list[int], bound: int, pool: VarPool) -> int:
    return add_atmost(clauses, [-x for x in lits], len(lits) - bound, pool)


def generate(acat: Path, bcat: Path, ao: int, bo: int, cnf: Path, meta: Path) -> None:
    ag6, A, ae = base.select(acat, ao, NA)
    bg6, B, be = base.select(bcat, bo, NB)
    base.validate(A, B)
    if (ae, be) != (26, 116):
        raise ValueError((ae, be))

    clauses: list[list[int]] = []
    counts = {k: 0 for k in (
        'k4_1a3b', 'k4_2a2b', 'i6_5a1b', 'i6_4a2b', 'i6_3a3b', 'i6_2a4b',
        'row_degree_bounds', 'column_degree_bounds', 'global_edge_lower_bound')}

    btri = base.subs(B, 3, True)
    aedge = base.subs(A, 2, True)
    bedge = base.subs(B, 2, True)
    ai5 = base.subs(A, 5, False)
    ai4 = base.subs(A, 4, False)
    bnon = base.subs(B, 2, False)
    ai3 = base.subs(A, 3, False)
    bi3 = base.subs(B, 3, False)
    anon = base.subs(A, 2, False)
    bi4 = base.subs(B, 4, False)

    for a in range(NA):
        for bs in btri:
            clauses.append([-vm(a, b) for b in bs])
            counts['k4_1a3b'] += 1
    for aa in aedge:
        for bb in bedge:
            clauses.append([-vm(a, b) for a in aa for b in bb])
            counts['k4_2a2b'] += 1
    for aa in ai5:
        for b in range(NB):
            clauses.append([vm(a, b) for a in aa])
            counts['i6_5a1b'] += 1
    for aa in ai4:
        for bb in bnon:
            clauses.append([vm(a, b) for a in aa for b in bb])
            counts['i6_4a2b'] += 1
    for aa in ai3:
        for bb in bi3:
            clauses.append([vm(a, b) for a in aa for b in bb])
            counts['i6_3a3b'] += 1
    for aa in anon:
        for bb in bi4:
            clauses.append([vm(a, b) for a in aa for b in bb])
            counts['i6_2a4b'] += 1

    pool = VarPool(NA * NB + 1)
    da = [x.bit_count() for x in A]
    db = [x.bit_count() for x in B]
    row_bounds = []
    col_bounds = []

    for a in range(NA):
        lits = [vm(a, b) for b in range(NB)]
        lo = max(0, 11 - 1 - da[a])
        hi = min(NB, 17 - 1 - da[a])
        row_bounds.append({'vertex': a, 'internal_degree': da[a], 'cross_min': lo, 'cross_max': hi})
        counts['row_degree_bounds'] += add_atleast(clauses, lits, lo, pool)
        counts['row_degree_bounds'] += add_atmost(clauses, lits, hi, pool)

    for b in range(NB):
        lits = [vm(a, b) for a in range(NA)]
        lo = max(0, 11 - db[b])
        hi = min(NA, 17 - db[b])
        col_bounds.append({'vertex': b, 'internal_degree': db[b], 'cross_min': lo, 'cross_max': hi})
        counts['column_degree_bounds'] += add_atleast(clauses, lits, lo, pool)
        counts['column_degree_bounds'] += add_atmost(clauses, lits, hi, pool)

    cross_min = max(0, MIN_TOTAL_EDGES - (11 + ae + be))
    all_cross = [vm(a, b) for a in range(NA) for b in range(NB)]
    counts['global_edge_lower_bound'] += add_atleast(clauses, all_cross, cross_min, pool)

    cnf.parent.mkdir(parents=True, exist_ok=True)
    with cnf.open('w', encoding='ascii') as f:
        f.write(f'p cnf {pool.top} {len(clauses)}\n')
        for cl in clauses:
            f.write(' '.join(map(str, cl)) + ' 0\n')

    d = {
        'campaign': 'd11-extreme-degree-bounded-glue-v1',
        'logical_scope': 'fixed A26/B116 pair; all possible total edge counts consistent with a valid R(4,6,36) graph',
        'a_ordinal': ao, 'b_ordinal': bo, 'a_graph6': ag6, 'b_graph6': bg6,
        'a_edges': ae, 'b_edges': be, 'edge_variables': NA * NB,
        'variables': pool.top, 'clauses': len(clauses), 'clauses_by_kind': counts,
        'minimum_total_edges': MIN_TOTAL_EDGES, 'cross_edge_minimum': cross_min,
        'degree_interval': [11, 17], 'row_bounds': row_bounds, 'column_bounds': col_bounds,
        'provenance': {
            'minimum_edge_bound': 'science-boundary/ramsey-r46/results/m216-218-exclusion.json',
            'endpoint_catalogues': 'McKay complete R(3,6,11) and R(4,5,24) catalogues; A26 has 2 graphs, B116 has 9 graphs'
        }
    }
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps(d, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in d.items() if k not in ('row_bounds', 'column_bounds')}, sort_keys=True))


def decode(acat: Path, bcat: Path, ao: int, bo: int, model: Path, out: Path) -> None:
    base.decode(acat, bcat, ao, bo, model, out)


def self_test() -> None:
    assert MIN_TOTAL_EDGES == 219
    assert max(0, MIN_TOTAL_EDGES - (11 + 26 + 116)) == 66
    assert (11 - 1 - 4, 17 - 1 - 4) == (6, 12)
    assert (11 - 7, 17 - 7) == (4, 10)
    print('d11 extreme degree-bounded encoder self-test ok')


def main() -> int:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest='cmd', required=True)
    ge = sp.add_parser('generate')
    ge.add_argument('a_catalog', type=Path); ge.add_argument('b_catalog', type=Path)
    ge.add_argument('a_ordinal', type=int); ge.add_argument('b_ordinal', type=int)
    ge.add_argument('cnf', type=Path); ge.add_argument('meta', type=Path)
    de = sp.add_parser('decode')
    de.add_argument('a_catalog', type=Path); de.add_argument('b_catalog', type=Path)
    de.add_argument('a_ordinal', type=int); de.add_argument('b_ordinal', type=int)
    de.add_argument('model', type=Path); de.add_argument('output', type=Path)
    sp.add_parser('self-test')
    a = ap.parse_args()
    if a.cmd == 'generate':
        generate(a.a_catalog, a.b_catalog, a.a_ordinal, a.b_ordinal, a.cnf, a.meta)
    elif a.cmd == 'decode':
        decode(a.a_catalog, a.b_catalog, a.a_ordinal, a.b_ordinal, a.model, a.output)
    else:
        self_test()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
