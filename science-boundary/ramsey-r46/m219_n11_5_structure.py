#!/usr/bin/env python3
"""Finite catalogue proof for the m=219, n11=5 local structure.

Starting from m219_structure.py, the five degree-11 vertices induce
L=K5 minus a matching, with four L-degree-3 vertices a,b,c,d and unmatched
L-degree-4 vertex e.  The four degree-3 vertices have S=129 and hence the
extreme local pair (A26,B116).  This script uses the two complete A26 types to
prove that e cannot have a degree-13 neighbour.  Consequently every external
neighbour of every degree-11 vertex is degree 12, so E(L,H)=0 for H={deg>=13}.

It also authenticates that the eligible distinguished P3s in the two A26
catalogue types have exactly four automorphism orbits total.  These are the
four local branches used by m219_n11_5_fixedA_sat.py.
"""
from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path

import networkx as nx

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
EXPECTED_REPS = (
    (0, (0, 1, 2)),
    (0, (1, 0, 5)),
    (1, (0, 1, 3)),
    (1, (1, 0, 2)),
)


def decode_graph6(s: str) -> nx.Graph:
    n = ord(s[0]) - 63
    bits = []
    for ch in s[1:]:
        v = ord(ch) - 63
        bits.extend((v >> k) & 1 for k in range(5, -1, -1))
    g = nx.Graph(); g.add_nodes_from(range(n)); p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]: g.add_edge(i, j)
            p += 1
    return g


def eligible_p3(g: nx.Graph):
    out = []
    for c in g:
        for u, v in itertools.combinations(g.neighbors(c), 2):
            if g.has_edge(u, v): continue
            if set(nx.common_neighbors(g, u, v)) == {c}:
                out.append((min(u, v), c, max(u, v)))
    return sorted(out)


def p3_orbits(g: nx.Graph):
    p3 = set(eligible_p3(g))
    autos = list(nx.algorithms.isomorphism.GraphMatcher(g, g).isomorphisms_iter())
    unseen = set(p3); orbits = []
    while unseen:
        t = min(unseen); u, c, v = t; orb = set()
        for f in autos:
            uu, vv = f[u], f[v]
            orb.add((min(uu, vv), f[c], max(uu, vv)))
        orb &= p3
        unseen -= orb; orbits.append(sorted(orb))
    return autos, sorted(orbits, key=lambda o: o[0])


def induced_c4_degree_multisets(g: nx.Graph):
    out = set()
    for vs in itertools.combinations(g.nodes, 4):
        h = g.subgraph(vs)
        if h.number_of_edges() == 4 and all(d == 2 for _, d in h.degree()):
            out.add(tuple(sorted(g.degree(v) for v in vs)))
    return sorted(out)


def main_proof() -> dict:
    cat = json.loads((RESULTS / "m219-extreme-catalogs.json").read_text(encoding="utf-8"))
    arows = cat["A26"]["target_graphs"]
    assert len(arows) == 2
    graphs = [decode_graph6(r["graph6"]) for r in arows]
    assert [g.number_of_edges() for g in graphs] == [26, 26]

    local_options = set()
    orbit_summary = []
    got_reps = []
    for gi, g in enumerate(graphs):
        eps = eligible_p3(g)
        autos, orbits = p3_orbits(g)
        assert len(eps) in {5, 9}
        for u, c, v in eps:
            rest = set(g) - {u, c, v}
            # Complete A26 scan property: every residual vertex sees exactly one
            # distinguished P3 vertex.
            assert all(sum(g.has_edge(z, q) for q in (u, c, v)) == 1 for z in rest)
            local_options.add((g.degree(c), tuple(sorted((g.degree(u), g.degree(v))))))
        reps = [o[0] for o in orbits]
        got_reps.extend((gi, r) for r in reps)
        orbit_summary.append({
            "a26_type": gi,
            "graph6": arows[gi]["graph6"],
            "automorphism_order": len(autos),
            "eligible_p3_count": len(eps),
            "orbit_count": len(orbits),
            "orbit_sizes": [len(o) for o in orbits],
            "representatives": [list(x) for x in reps],
        })
    assert tuple(got_reps) == EXPECTED_REPS, (got_reps, EXPECTED_REPS)
    assert local_options == {(3,(4,5)), (4,(3,5)), (2,(5,5)), (5,(2,5))}

    # Lambda variables are common-neighbour counts on L edges.  The four cross
    # edges of the C4 on a,b,c,d are ac,ad,bc,bd.  The four e-edges are
    # ae,be,ce,de.  At each special vertex x its two cross-edge lambdas are the
    # endpoint degrees of the distinguished P3 in A_x and lambda_xe is the P3
    # center degree.
    consistent = []
    for ac, ad, bc, bd in itertools.product(range(2, 6), repeat=4):
        incident = ((ac,ad),(bc,bd),(ac,bc),(ad,bd))
        for ae, be, ce, de in itertools.product(range(2, 6), repeat=4):
            es = (ae,be,ce,de)
            if all((es[i], tuple(sorted(incident[i]))) in local_options for i in range(4)):
                consistent.append((ac,ad,bc,bd,ae,be,ce,de))
    assert len(consistent) == 31

    # If e had a high neighbour, S(e)<=129 forces exactly one degree-13 high
    # neighbour and six degree-12 external neighbours.  Then S(e)=129, so A_e
    # must itself be A26.  The four specials induce C4 in A_e, hence their
    # degrees there (ae,be,ce,de) must be one of the induced-C4 degree multisets
    # occurring in the two A26 types.
    c4_multisets = sorted(set().union(*(induced_c4_degree_multisets(g) for g in graphs)))
    c4_compatible = []
    for lam in consistent:
        e_lams = tuple(sorted(lam[4:]))
        if e_lams not in c4_multisets:
            continue
        # For special x, lambda_xe-2 counts common degree-12 neighbours of x,e:
        # their two common L neighbours contribute exactly 2.  These common-M
        # sets are pairwise disjoint: cross-pair overlap makes a K4 with e and
        # a cross L edge, while paired-special overlap is impossible because
        # the paired degree-12 neighbourhoods are disjoint (B116 min degree 8).
        common_m_incidence = sum(x - 2 for x in lam[4:])
        c4_compatible.append({
            "lambdas": list(lam),
            "e_lambda_multiset": list(e_lams),
            "required_distinct_common_M": common_m_incidence,
            "available_M_neighbours_of_e_if_high": 6,
            "possible": common_m_incidence <= 6,
        })
    assert c4_compatible, "expected to expose the final impossible candidates"
    assert all(not r["possible"] for r in c4_compatible)

    return {
        "campaign": "m219-n11-5-local-catalogue-proof",
        "a26_orbits": orbit_summary,
        "total_fixedA_local_orbits": sum(x["orbit_count"] for x in orbit_summary),
        "local_lambda_options": [
            {"lambda_e": c, "cross_lambdas": list(ep)} for c, ep in sorted(local_options)
        ],
        "consistent_lambda_assignments": len(consistent),
        "a26_induced_c4_degree_multisets": [list(x) for x in c4_multisets],
        "e_high_case_c4_compatible": c4_compatible,
        "e_high_case_impossible": True,
        "conclusion": "For m=219,n11=5, all five degree-11 vertices have only degree-12 external neighbours; E(L,H)=0.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--output", type=Path)
    args = ap.parse_args(); d = main_proof(); text = json.dumps(d, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text, encoding="utf-8")
    print(json.dumps({
        "local_orbits": d["total_fixedA_local_orbits"],
        "lambda_assignments": d["consistent_lambda_assignments"],
        "e_high_impossible": d["e_high_case_impossible"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__": raise SystemExit(main())
