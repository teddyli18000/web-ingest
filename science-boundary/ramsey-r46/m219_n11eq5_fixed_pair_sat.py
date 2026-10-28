#!/usr/bin/env python3
"""Exact fixed-pair SAT cover for the m=219, n_11=5 strata.

`m219_structure.py` proves that the five degree-11 vertices induce K5 minus a
matching of size two.  Choose one of the four degree-3 vertices x as root.
Its three degree-11 neighbours form a P3 inside A=N(x), while its matched
non-neighbour y lies in B.  The local edge identity forces the extreme pair
(e(A),e(B))=(26,116).

The complete endpoint catalogues contain two A26 types and nine B116 types.
Since y is adjacent to the three A-side degree-11 vertices and has total
degree 11, deg_B(y)=8.  Only two B116 types contain degree-8 vertices, and in
both types all degree-8 vertices form one automorphism orbit.  Quotienting the
P3 triples by Aut(A) gives 11+5=16 A orbits.  Across the three surviving
global degree sequences this yields exactly 3*16*2=96 branches.

For each branch A and B are fixed; only the 11x24 cross edges and the global
degree classes of B\{y} remain variable.  Every degree is imposed exactly and
all mixed K4 / independent-6 obstructions are encoded statically.  A SAT
model is therefore a complete 36-vertex certificate and is fully checked
before being written.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from collections import Counter
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import d12_fixed_ab_sat as base
import d12_fixed_ab_sym_sat as sym

HERE = Path(__file__).resolve().parent
EXTREME_JSON = HERE / "results" / "m219-extreme-catalogs.json"
NA, NB = 11, 24
DEGREE_SEQUENCES = (
    {11: 5, 12: 20, 13: 11},
    {11: 5, 12: 21, 13: 9, 14: 1},
    {11: 5, 12: 22, 13: 7, 14: 2},
)


def load_extremes(path: Path = EXTREME_JSON):
    d = json.loads(path.read_text(encoding="utf-8"))
    a = [(r["graph6"], *base.decode_graph6(r["graph6"])) for r in d["A26"]["target_graphs"]]
    b = [(r["graph6"], *base.decode_graph6(r["graph6"])) for r in d["B116"]["target_graphs"]]
    assert len(a) == 2 and all(e == 26 and len(adj) == NA for _, adj, e in a)
    assert len(b) == 9 and all(e == 116 and len(adj) == NB for _, adj, e in b)
    return a, b


def edge(adj: list[int], u: int, v: int) -> bool:
    return bool((adj[u] >> v) & 1)


def vertex_orbits(n: int, autos: list[tuple[int, ...]], allowed: set[int] | None = None) -> list[list[int]]:
    domain = set(range(n)) if allowed is None else set(allowed)
    unseen = set(domain)
    out = []
    while unseen:
        v = min(unseen)
        orb = {p[v] for p in autos} & domain
        assert orb
        out.append(sorted(orb))
        unseen -= orb
    return out


def subset_orbits(items: list[tuple[int, ...]], autos: list[tuple[int, ...]]) -> list[dict]:
    remaining = {tuple(sorted(x)) for x in items}
    out = []
    while remaining:
        rep = min(remaining)
        orb = {tuple(sorted(p[v] for v in rep)) for p in autos}
        if not orb <= set(items):
            raise AssertionError((rep, orb - set(items)))
        out.append({"rep": rep, "orbit": sorted(orb), "size": len(orb)})
        remaining -= orb
    return out


def p3_triples(A: list[int]) -> list[tuple[int, int, int]]:
    out = []
    for t in itertools.combinations(range(NA), 3):
        ec = sum(edge(A, u, v) for u, v in itertools.combinations(t, 2))
        if ec == 2:
            out.append(t)
    return out


def p3_center(A: list[int], triple: tuple[int, int, int]) -> tuple[int, tuple[int, int]]:
    ds = {v: sum(edge(A, v, u) for u in triple if u != v) for v in triple}
    center = [v for v, d in ds.items() if d == 2]
    ends = tuple(sorted(v for v, d in ds.items() if d == 1))
    assert len(center) == 1 and len(ends) == 2
    return center[0], ends


def manifest(extreme_json: Path = EXTREME_JSON) -> dict:
    As, Bs = load_extremes(extreme_json)
    a_rows = []
    total_a_orbits = 0
    for ai, (g6, A, _) in enumerate(As):
        autos = sym.automorphisms(A)
        triples = p3_triples(A)
        orbs = subset_orbits(triples, autos)
        total_a_orbits += len(orbs)
        a_rows.append({
            "a_index": ai,
            "graph6": g6,
            "aut_order": len(autos),
            "p3_labelled_count": len(triples),
            "p3_orbits": [{"rep": list(o["rep"]), "size": o["size"]} for o in orbs],
        })
    assert [r["aut_order"] for r in a_rows] == [288, 1152]
    assert [len(r["p3_orbits"]) for r in a_rows] == [11, 5]
    assert total_a_orbits == 16

    b_rows = []
    surviving_b = []
    for bi, (g6, B, _) in enumerate(Bs):
        deg = base.degrees(B)
        d8 = {v for v, d in enumerate(deg) if d == 8}
        autos = sym.automorphisms(B)
        orbs = vertex_orbits(NB, autos, d8) if d8 else []
        row = {
            "b_index": bi,
            "graph6": g6,
            "aut_order": len(autos),
            "degree8_vertices": sorted(d8),
            "degree8_orbits": orbs,
        }
        b_rows.append(row)
        if d8:
            assert len(orbs) == 1
            surviving_b.append(row)
    assert [r["b_index"] for r in surviving_b] == [1, 4]
    assert [r["aut_order"] for r in surviving_b] == [1, 8]

    branches = []
    for si, seq in enumerate(DEGREE_SEQUENCES):
        for ar in a_rows:
            for oi, orb in enumerate(ar["p3_orbits"]):
                for br in surviving_b:
                    branches.append({
                        "sequence_index": si,
                        "degree_sequence": {str(k): v for k, v in seq.items()},
                        "a_index": ar["a_index"],
                        "a_triple_orbit_index": oi,
                        "a_triple": orb["rep"],
                        "a_triple_orbit_size": orb["size"],
                        "b_index": br["b_index"],
                        "y": br["degree8_orbits"][0][0],
                        "y_orbit": br["degree8_orbits"][0],
                    })
    assert len(branches) == 96
    return {"A": a_rows, "B": b_rows, "branches": branches, "branch_count": 96}


def add_cnf(s: Solver, cnf, gate: int | None = None) -> int:
    for clause in cnf.clauses:
        s.add_clause(([-gate] if gate is not None else []) + list(clause))
    return len(cnf.clauses)


def add_ramsey(s: Solver, x: list[list[int]], A: list[int], B: list[int]) -> dict:
    counts = {k: 0 for k in (
        "k4_1a3b", "k4_2a2b", "i6_5a1b", "i6_4a2b", "i6_3a3b", "i6_2a4b",
    )}
    b_tri = base.subsets(B, 3, True)
    a_edges = base.subsets(A, 2, True)
    b_edges = base.subsets(B, 2, True)
    a_i5 = base.subsets(A, 5, False)
    a_i4 = base.subsets(A, 4, False)
    b_non = base.subsets(B, 2, False)
    a_i3 = base.subsets(A, 3, False)
    b_i3 = base.subsets(B, 3, False)
    a_non = base.subsets(A, 2, False)
    b_i4 = base.subsets(B, 4, False)
    for a in range(NA):
        for bs in b_tri:
            s.add_clause([-x[a][b] for b in bs]); counts["k4_1a3b"] += 1
    for aa in a_edges:
        for bb in b_edges:
            s.add_clause([-x[a][b] for a in aa for b in bb]); counts["k4_2a2b"] += 1
    for aa in a_i5:
        for b in range(NB):
            s.add_clause([x[a][b] for a in aa]); counts["i6_5a1b"] += 1
    for aa in a_i4:
        for bb in b_non:
            s.add_clause([x[a][b] for a in aa for b in bb]); counts["i6_4a2b"] += 1
    for aa in a_i3:
        for bb in b_i3:
            s.add_clause([x[a][b] for a in aa for b in bb]); counts["i6_3a3b"] += 1
    for aa in a_non:
        for bb in b_i4:
            s.add_clause([x[a][b] for a in aa for b in bb]); counts["i6_2a4b"] += 1
    return counts


def rows_from_model(A: list[int], B: list[int], x: list[list[int]], model: list[int]) -> list[str]:
    pos = {z for z in model if z > 0}
    rows = [["0"] * 36 for _ in range(36)]
    for a in range(NA):
        rows[0][1 + a] = rows[1 + a][0] = "1"
    for i in range(NA):
        for j in range(i + 1, NA):
            if edge(A, i, j):
                rows[1 + i][1 + j] = rows[1 + j][1 + i] = "1"
    b0 = 1 + NA
    for i in range(NB):
        for j in range(i + 1, NB):
            if edge(B, i, j):
                rows[b0 + i][b0 + j] = rows[b0 + j][b0 + i] = "1"
    for a in range(NA):
        for b in range(NB):
            if x[a][b] in pos:
                rows[1 + a][b0 + b] = rows[b0 + b][1 + a] = "1"
    return ["".join(r) for r in rows]


def exact_verify(rows: list[str], seq: dict[int, int]) -> None:
    assert len(rows) == 36 and all(len(r) == 36 for r in rows)
    for i in range(36):
        assert rows[i][i] == "0"
        for j in range(i + 1, 36):
            assert rows[i][j] == rows[j][i]
    deg = [r.count("1") for r in rows]
    expected = Counter({d: n for d, n in seq.items()})
    assert Counter(deg) == expected, (Counter(deg), expected)
    assert sum(deg) // 2 == 219
    masks = []
    for r in rows:
        m = 0
        for j, z in enumerate(r):
            if z == "1": m |= 1 << j
        masks.append(m)
    for q in itertools.combinations(range(36), 4):
        if all((masks[u] >> v) & 1 for u, v in itertools.combinations(q, 2)):
            raise AssertionError(("K4", q))
    for q in itertools.combinations(range(36), 6):
        if all(not ((masks[u] >> v) & 1) for u, v in itertools.combinations(q, 2)):
            raise AssertionError(("I6", q))


def solve(args) -> int:
    mani = manifest(args.extreme_json)
    if not 0 <= args.ordinal < len(mani["branches"]):
        raise IndexError((args.ordinal, len(mani["branches"])))
    br = mani["branches"][args.ordinal]
    As, Bs = load_extremes(args.extreme_json)
    ag6, A, _ = As[br["a_index"]]
    bg6, B, _ = Bs[br["b_index"]]
    triple = tuple(br["a_triple"])
    center, endpoints = p3_center(A, triple)
    y = br["y"]
    seq = DEGREE_SEQUENCES[br["sequence_index"]]
    da, db = base.degrees(A), base.degrees(B)
    assert db[y] == 8

    # A-side global degrees are fixed: the P3 triple are the other d11
    # neighbours of the root; the other eight A vertices are d12.
    row_targets = [(10 if a in triple else 11) - da[a] for a in range(NA)]
    assert all(0 <= z <= NB for z in row_targets)
    assert sum(row_targets) == 66

    # B\{y} class counts after accounting for root+triple+y as the five d11
    # vertices and the eight d12 vertices in A\triple.
    class_counts = {d: seq.get(d, 0) for d in (12, 13, 14)}
    class_counts[12] -= 8
    assert sum(class_counts.values()) == NB - 1
    assert all(v >= 0 for v in class_counts.values())

    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    cls = {(b, d): pool.id(("class", b, d)) for b in range(NB) if b != y for d in (12, 13, 14)}
    counts = Counter()
    started = time.monotonic()
    with Solver(name=args.solver) as s:
        # Exact A row degrees.
        for a, target in enumerate(row_targets):
            counts["degree_equals"] += add_cnf(s, CardEnc.equals(x[a], target, vpool=pool, encoding=EncType.seqcounter))

        # y is the matched d11 partner of the root: exactly the P3 triple are
        # its A-neighbours.  Its B degree is 8, so total degree is exactly 11.
        for a in range(NA):
            s.add_clause([x[a][y] if a in triple else -x[a][y]])
            counts["fixed_y_cross"] += 1

        # Every other B vertex receives exactly one global degree class, with
        # exact class multiplicities from the selected degree sequence.
        for b in range(NB):
            if b == y: continue
            lits = [cls[b, d] for d in (12, 13, 14)]
            counts["class_onehot"] += add_cnf(s, CardEnc.equals(lits, 1, vpool=pool, encoding=EncType.seqcounter))
        for d in (12, 13, 14):
            lits = [cls[b, d] for b in range(NB) if b != y]
            counts["class_counts"] += add_cnf(s, CardEnc.equals(lits, class_counts[d], vpool=pool, encoding=EncType.seqcounter))

        # Conditional exact B column degrees.
        for b in range(NB):
            if b == y: continue
            col = [x[a][b] for a in range(NA)]
            for d in (12, 13, 14):
                target = d - db[b]
                if not 0 <= target <= NA:
                    s.add_clause([-cls[b, d]])
                    counts["impossible_class"] += 1
                else:
                    enc = CardEnc.equals(col, target, vpool=pool, encoding=EncType.seqcounter)
                    counts["conditional_degree_equals"] += add_cnf(s, enc, gate=cls[b, d])

        # y is an L-degree3 vertex, so all eight of its B-internal neighbours
        # are external degree12 vertices (S(y)=129 exactly).
        for b in range(NB):
            if b != y and edge(B, y, b):
                s.add_clause([cls[b, 12]])
                counts["y_neighbor_is_d12"] += 1

        # The two P3 endpoints are also L-degree3: beyond their three d11
        # neighbours all neighbours must be degree12.  Their cross edges to
        # class13/14 vertices are therefore forbidden.
        for a in endpoints:
            for b in range(NB):
                if b == y: continue
                for d in (13, 14):
                    s.add_clause([-x[a][b], -cls[b, d]])
                    counts["endpoint_no_high"] += 1

        # The P3 center is the unique L-degree4 vertex.  It cannot meet d14,
        # and can meet at most one d13 vertex outside L.
        z13 = []
        for b in range(NB):
            if b == y: continue
            s.add_clause([-x[center][b], -cls[b, 14]])
            counts["center_no_d14"] += 1
            z = pool.id(("center13", b))
            # z <-> x(center,b) & class13(b)
            s.add_clause([-z, x[center][b]])
            s.add_clause([-z, cls[b, 13]])
            s.add_clause([-x[center][b], -cls[b, 13], z])
            counts["center13_and"] += 3
            z13.append(z)
        counts["center_atmost1_d13"] += add_cnf(s, CardEnc.atmost(z13, 1, vpool=pool, encoding=EncType.seqcounter))

        counts.update(add_ramsey(s, x, A, B))
        sat = s.solve()
        elapsed = time.monotonic() - started
        result = {
            "campaign": "m219-n11eq5-A26-B116-fixed-pair",
            "branch_ordinal": args.ordinal,
            "branch_count": len(mani["branches"]),
            **br,
            "a_graph6": ag6,
            "b_graph6": bg6,
            "p3_center": center,
            "p3_endpoints": list(endpoints),
            "row_targets": row_targets,
            "class_counts_B_without_y": {str(k): v for k, v in class_counts.items()},
            "solver": args.solver,
            "clauses_by_kind": dict(counts),
            "max_var": pool.top,
            "elapsed_seconds": round(elapsed, 6),
        }
        if not sat:
            result["status"] = "UNSAT"
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print("RESULT " + json.dumps(result, sort_keys=True))
            return 20
        model = s.get_model()

    rows = rows_from_model(A, B, x, model)
    exact_verify(rows, seq)
    result["status"] = "SAT"
    result["degree_sequence_verified"] = {str(k): v for k, v in seq.items()}
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.write_text(json.dumps({"adjacency": rows}, indent=2) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps(result, sort_keys=True))
    return 0


def self_test(extreme_json: Path) -> None:
    m = manifest(extreme_json)
    assert m["branch_count"] == 96
    assert sum(len(r["p3_orbits"]) for r in m["A"]) == 16
    survivors = [r for r in m["B"] if r["degree8_vertices"]]
    assert len(survivors) == 2
    print(json.dumps({
        "branches": 96,
        "A_p3_orbits": [len(r["p3_orbits"]) for r in m["A"]],
        "surviving_B_indices": [r["b_index"] for r in survivors],
        "B_degree8_orbit_sizes": [len(r["degree8_orbits"][0]) for r in survivors],
    }, sort_keys=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("self-test")
    p.add_argument("--extreme-json", type=Path, default=EXTREME_JSON)
    p = sub.add_parser("manifest")
    p.add_argument("--extreme-json", type=Path, default=EXTREME_JSON)
    p.add_argument("--output", type=Path)
    p = sub.add_parser("solve")
    p.add_argument("--extreme-json", type=Path, default=EXTREME_JSON)
    p.add_argument("--ordinal", type=int, required=True)
    p.add_argument("--solver", default="cadical195")
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(args.extreme_json); return 0
    if args.cmd == "manifest":
        d = manifest(args.extreme_json)
        text = json.dumps(d, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        print(json.dumps({"branch_count": d["branch_count"]}, sort_keys=True)); return 0
    return solve(args)


if __name__ == "__main__":
    raise SystemExit(main())
