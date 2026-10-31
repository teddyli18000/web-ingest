#!/usr/bin/env python3
"""Sound post-audit exclusion of the entire m=220, n11=3 layer.

No row-domain triangle-free predicate is used.

Structural input from m220_structure.py:
- a hypothetical 220-edge R(4,6,36) graph with exactly three degree-11
  vertices has those three vertices inducing K3;
- for any degree-11 anchor v, A=N(v) is one of the two complete A26
  R(3,6,11) graphs and B is one of the nine complete B116 R(4,5,24) graphs;
- the other two degree-11 vertices are an A-edge and all other A vertices
  have global degree 12.

The new recursive-neighbourhood lemma is that every degree-11 vertex u has
its own neighbourhood N(u) in the same A26 catalogue.  If u has degree 5
inside the original A, then the original anchor appears as a degree-5 vertex
p of this second A26.  The 5 cross-B neighbours of u are exactly the
non-neighbours H of p in that A26.  For h in H, the corresponding B vertex
must have at least
    1 + |N(h) intersect N(p)|
A-cross neighbours: u itself plus the neighbours of p adjacent to h.
Complete enumeration of the two A26 types shows that every degree-5 p has
some h requiring at least 5 such A-cross neighbours.

But every neighbour of a degree-11 vertex is either one of the other two
low vertices or has global degree exactly 12.  Therefore such a B vertex has
A-cross degree 12-d_B(h).  Every B116 type has minimum degree at least 8, so
12-d_B(h) <= 4, contradiction.

Across the two A26 graphs every edge except one has a degree-5 endpoint.  The
sole exception is the degree-(3,4) edge in A26 type 0.  It is excluded by a
separate common-neighbour argument: its two low endpoints need 7 and 6 B
neighbours.  Any B neighbour of either low endpoint has global degree 12 and
its A-column must hit every independent 5-set of A while containing that low
endpoint.  The minimum such hitting-set size is 3 for both endpoints, so the
B neighbour must have d_B<=9.  Each B116 type has exactly 8 such vertices.
Thus the two rows have at least 7+6-8=5 common B neighbours.  Since the low
endpoints are adjacent, their common B-neighbour set is independent (else a
K4), but alpha(B)=4.  Contradiction.
"""
from __future__ import annotations
import argparse, json
from itertools import combinations
from pathlib import Path
import networkx as nx

HERE = Path(__file__).resolve().parent
A_DEFAULT = HERE / "data/m219-r34-A26.g6"
B_DEFAULT = HERE / "data/m219-r34-B116.g6"


def read_g6(path: Path):
    return [nx.from_graph6_bytes(s.encode()) for s in path.read_text().splitlines() if s]


def independent_sets(G, k):
    return [frozenset(S) for S in combinations(G.nodes(), k)
            if G.subgraph(S).number_of_edges() == 0]


def triangle_free(G):
    return all(G.subgraph(S).number_of_edges() < 3 for S in combinations(G.nodes(), 3))


def min_hit_containing(A, u):
    I5 = independent_sets(A, 5)
    for k in range(1, len(A) + 1):
        for S in combinations(A.nodes(), k):
            if u in S and all(set(S) & T for T in I5):
                return k
    raise AssertionError("no hitting set")


def recursive_degree5_profiles(As):
    rows = []
    for ti, T in enumerate(As):
        for p in T:
            if T.degree(p) != 5:
                continue
            Np = set(T.neighbors(p))
            H = [h for h in T if h != p and h not in Np]
            assert len(H) == 5
            needs = sorted(1 + sum(T.has_edge(h, q) for q in Np) for h in H)
            rows.append({"A26_type": ti, "distinguished_vertex": p,
                         "nonneighbor_cross_needs": needs,
                         "max_required_cross_degree": max(needs)})
    assert rows
    assert min(r["max_required_cross_degree"] for r in rows) >= 5
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--A26", type=Path, default=A_DEFAULT)
    ap.add_argument("--B116", type=Path, default=B_DEFAULT)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    As = read_g6(args.A26)
    Bs = read_g6(args.B116)
    assert (len(As), len(Bs)) == (2, 9)
    assert all(len(A) == 11 and A.number_of_edges() == 26 and triangle_free(A)
               and independent_sets(A, 5) and not independent_sets(A, 6) for A in As)
    assert all(len(B) == 24 and B.number_of_edges() == 116
               and independent_sets(B, 4) and not independent_sets(B, 5) for B in Bs)

    profiles = recursive_degree5_profiles(As)
    bstats = []
    for bi, B in enumerate(Bs):
        ds = [B.degree(v) for v in B]
        alpha4 = bool(independent_sets(B, 4)) and not independent_sets(B, 5)
        assert min(ds) >= 8 and alpha4
        bstats.append({"B116_type": bi, "min_degree": min(ds),
                       "degree_le9_count": sum(d <= 9 for d in ds), "alpha": 4})

    exceptional = []
    killed_by_degree5 = 0
    killed_by_type = [0, 0]
    edge_degree_pairs = {}
    for ai, A in enumerate(As):
        for u, v in A.edges():
            du, dv = A.degree(u), A.degree(v)
            key = f"{min(du,dv)}-{max(du,dv)}"
            edge_degree_pairs[key] = edge_degree_pairs.get(key, 0) + 1
            if du == 5 or dv == 5:
                killed_by_degree5 += 1
                killed_by_type[ai] += 1
            else:
                exceptional.append((ai, u, v))

    assert sum(A.number_of_edges() for A in As) == 52
    assert killed_by_degree5 == 51
    assert len(exceptional) == 1
    ai, u, v = exceptional[0]
    A = As[ai]
    assert sorted((A.degree(u), A.degree(v))) == [3, 4]
    ru, rv = 10 - A.degree(u), 10 - A.degree(v)
    hu, hv = min_hit_containing(A, u), min_hit_containing(A, v)
    assert sorted((ru, rv)) == [6, 7]
    assert (hu, hv) == (3, 3)

    exceptional_checks = []
    for bi, B in enumerate(Bs):
        Eu = {b for b in B if 12 - B.degree(b) >= hu}
        Ev = {b for b in B if 12 - B.degree(b) >= hv}
        assert Eu == Ev and len(Eu) == 8
        common_lb = ru + rv - len(Eu | Ev)
        alpha = 4
        assert common_lb >= 5 > alpha
        exceptional_checks.append({"B116_type": bi,
                                   "eligible_B_vertices": len(Eu),
                                   "low_row_sizes": [ru, rv],
                                   "common_neighbor_lower_bound": common_lb,
                                   "independence_upper_bound": alpha})

    exceptional_detail = {"A26_type": ai, "edge": [u, v],
                          "endpoint_degrees": [A.degree(u), A.degree(v)],
                          "method": "common_neighbour_alpha4",
                          "row_sizes": [ru, rv],
                          "min_hitting_column_sizes": [hu, hv],
                          "B_checks": exceptional_checks}

    out = {
        "campaign": "m220-n11-3-recursive-a26-post-audit",
        "edges": 220,
        "n11": 3,
        "catalog_counts": {"A26": len(As), "B116": len(Bs)},
        "recursive_degree5_profiles": profiles,
        "B116_stats": bstats,
        "A26_edge_count": 52,
        "edge_degree_pair_histogram": dict(sorted(edge_degree_pairs.items())),
        "edges_killed_by_recursive_degree5_capacity": killed_by_degree5,
        "degree5_killed_edges_by_A26_type": killed_by_type,
        "exceptional_edges_without_degree5_endpoint": 1,
        "exceptional_edge_proof": exceptional_detail,
        "soundness": (
            "Uses only complete A26/B116 catalogues, exact degree-11 neighbour "
            "structure from m220_structure, independent-set hitting necessities, "
            "and recursive A26 neighbourhood consistency. It does not call the "
            "withdrawn row-domain triangle-free predicate."
        ),
        "conclusion": "No 220-edge R(4,6,36) graph can have exactly three degree-11 vertices.",
        "all_unsat": True,
    }
    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)


if __name__ == "__main__":
    main()
