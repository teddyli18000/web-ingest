#!/usr/bin/env python3
"""Exact 39-branch SAT cover of the remaining 217-edge R(4,6,36) case.

`m217_structure.py` reduces any hypothetical 217-edge graph to degree sequence
12^34 13^2, with the two degree-13 vertices p,q nonadjacent.  Choose any
12-degree vertex x adjacent to p.  Exact local edge extrema force
A=N(x) to be the unique 29-edge R(3,6,12) graph and B to be the unique
101-edge R(4,5,23) graph.

Inside this fixed A29/B101 pair exactly one A vertex (p) and exactly one B
vertex (q) have total degree 13; every other vertex except x has total degree
12, and p--q is a nonedge.  Aut(A29) has 3 vertex orbits and Aut(B101) has 13,
so 3*13=39 representative placements exactly cover all possibilities.

Each branch has only the 276 A--B cross-edge variables, exact row/column sums,
and every mixed K4 / independent-6 clause.  SAT is therefore a full
36-vertex certificate; 39 UNSAT branches prove there is no 217-edge graph.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import d12_fixed_ab_sat as base
import d12_fixed_ab_sym_sat as sym

NA, NB = 12, 23
EXPECTED_A = "K@G_wzbwuwZ_"
EXPECTED_B = "V?Q?d@cUCLHoH[[cROdaWFrDRqUTTDErGk^A^WQFhJ_?"


def vertex_orbits(n: int, autos: list[tuple[int, ...]]) -> list[list[int]]:
    unseen = set(range(n))
    out = []
    while unseen:
        v = min(unseen)
        orb = {p[v] for p in autos}
        # Closure is automatic because autos is the whole group, but verify it.
        if any({p[u] for p in autos} != orb for u in orb):
            raise AssertionError("inconsistent automorphism orbit")
        out.append(sorted(orb))
        unseen -= orb
    return out


def load_pair(a_catalog: Path, b_catalog: Path):
    ag6, A, ae = base.select_record(a_catalog, 0, NA)
    bg6, B, be = base.select_record(b_catalog, 0, NB)
    base.validate_A(A); base.validate_B(B)
    if (ag6, ae) != (EXPECTED_A, 29):
        raise ValueError((ag6, ae))
    if (bg6, be) != (EXPECTED_B, 101):
        raise ValueError((bg6, be))
    return ag6, A, bg6, B


def orbit_manifest(A: list[int], B: list[int]) -> dict:
    aa = sym.automorphisms(A)
    bb = sym.automorphisms(B)
    if len(aa) != 576 or len(bb) != 2:
        raise AssertionError((len(aa), len(bb)))
    ao = vertex_orbits(NA, aa)
    bo = vertex_orbits(NB, bb)
    if len(ao) != 3 or len(bo) != 13:
        raise AssertionError((ao, bo))
    reps = [(a[0], b[0]) for a in ao for b in bo]
    if len(reps) != 39:
        raise AssertionError(len(reps))
    return {
        "aut_A_order": len(aa),
        "aut_B_order": len(bb),
        "A_vertex_orbits": ao,
        "B_vertex_orbits": bo,
        "representative_pairs": reps,
    }


def add_cnf(s: Solver, cnf) -> int:
    for clause in cnf.clauses:
        s.add_clause(clause)
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
        rows[0][1+a] = rows[1+a][0] = "1"
    for i in range(NA):
        for j in range(i + 1, NA):
            if (A[i] >> j) & 1:
                rows[1+i][1+j] = rows[1+j][1+i] = "1"
    for i in range(NB):
        for j in range(i + 1, NB):
            if (B[i] >> j) & 1:
                rows[13+i][13+j] = rows[13+j][13+i] = "1"
    for a in range(NA):
        for b in range(NB):
            if x[a][b] in pos:
                rows[1+a][13+b] = rows[13+b][1+a] = "1"
    return ["".join(r) for r in rows]


def solve(args) -> int:
    ag6, A, bg6, B = load_pair(args.a_catalog, args.b_catalog)
    manifest = orbit_manifest(A, B)
    reps = manifest["representative_pairs"]
    if not 0 <= args.ordinal < len(reps):
        raise IndexError((args.ordinal, len(reps)))
    high_a, high_b = reps[args.ordinal]
    da, db = base.degrees(A), base.degrees(B)

    row_targets = [((13 if a == high_a else 12) - 1 - da[a]) for a in range(NA)]
    col_targets = [((13 if b == high_b else 12) - db[b]) for b in range(NB)]
    if any(not 0 <= z <= NB for z in row_targets) or any(not 0 <= z <= NA for z in col_targets):
        raise AssertionError((row_targets, col_targets))
    if sum(row_targets) != 75 or sum(col_targets) != 75:
        raise AssertionError((sum(row_targets), sum(col_targets)))

    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    started = time.monotonic()
    counts = {"degree_equals": 0}
    with Solver(name=args.solver) as s:
        for a, target in enumerate(row_targets):
            counts["degree_equals"] += add_cnf(
                s, CardEnc.equals(x[a], target, vpool=pool, encoding=EncType.seqcounter)
            )
        for b, target in enumerate(col_targets):
            col = [x[a][b] for a in range(NA)]
            counts["degree_equals"] += add_cnf(
                s, CardEnc.equals(col, target, vpool=pool, encoding=EncType.seqcounter)
            )
        # The two degree-13 vertices were proved nonadjacent in m217_structure.py.
        s.add_clause([-x[high_a][high_b]])
        counts["high_nonedge"] = 1
        counts.update(add_ramsey(s, x, A, B))
        sat = s.solve()
        elapsed = time.monotonic() - started
        result = {
            "campaign": "m217-fixed-A29-B101-orbit-pair",
            "branch_ordinal": args.ordinal,
            "branch_count": len(reps),
            "high_A": high_a,
            "high_B": high_b,
            "high_A_orbit": next(o for o in manifest["A_vertex_orbits"] if high_a in o),
            "high_B_orbit": next(o for o in manifest["B_vertex_orbits"] if high_b in o),
            "high_A_internal_degree": da[high_a],
            "high_B_internal_degree": db[high_b],
            "row_targets": row_targets,
            "col_targets": col_targets,
            "aut_A_order": manifest["aut_A_order"],
            "aut_B_order": manifest["aut_B_order"],
            "solver": args.solver,
            "clauses_by_kind": counts,
            "max_var": pool.top,
            "elapsed_seconds": round(elapsed, 6),
            "a_graph6": ag6,
            "b_graph6": bg6,
        }
        if not sat:
            result["status"] = "UNSAT"
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print("RESULT " + json.dumps(result, sort_keys=True))
            return 20
        model = s.get_model()

    rows = rows_from_model(A, B, x, model)
    base.verify_full(rows, 12, 13)
    deg = [r.count("1") for r in rows]
    if Counter(deg) != Counter({12: 34, 13: 2}):
        raise AssertionError(deg)
    if rows[1+high_a][13+high_b] != "0":
        raise AssertionError("high vertices adjacent")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"adjacency": rows}, indent=2) + "\n")
    result.update(status="SAT", degree_sequence=deg)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RESULT " + json.dumps(result, sort_keys=True))
    return 0


def manifest_cmd(args) -> None:
    _, A, _, B = load_pair(args.a_catalog, args.b_catalog)
    d = orbit_manifest(A, B)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "A_orbits": len(d["A_vertex_orbits"]),
        "B_orbits": len(d["B_vertex_orbits"]),
        "branches": len(d["representative_pairs"]),
        "A_vertex_orbits": d["A_vertex_orbits"],
        "B_vertex_orbits": d["B_vertex_orbits"],
    }, sort_keys=True))


def self_test() -> None:
    # Exact cardinality targets do not depend on which orbit representatives
    # are selected; only their placement changes.
    print("m217 fixed-pair SAT self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("manifest")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p = sub.add_parser("solve")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--ordinal", type=int, required=True)
    p.add_argument("--solver", default="cadical195")
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    if args.cmd == "manifest":
        manifest_cmd(args); return 0
    return solve(args)


if __name__ == "__main__":
    from collections import Counter
    raise SystemExit(main())
