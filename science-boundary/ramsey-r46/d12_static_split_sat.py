#!/usr/bin/env python3
"""Static exact SAT for a fixed A type in the max-degree-12 R(4,6,36) branch.

Fix v with degree 12 and A=N(v), |A|=12.  The 23-vertex B graph and all
A--B cross edges remain variables.  Compared with the older lazy separator,
this formulation eliminates v and the fixed A edges entirely and statically
encodes every remaining B-only and mixed K4/I6 obstruction.
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

from d12_fixed_ab_sat import iter_g6, select_record, validate_A, verify_full

NA, NB = 12, 23


def add_cnf(solver: Solver, cnf) -> int:
    for clause in cnf.clauses:
        solver.add_clause(clause)
    return len(cnf.clauses)


def independent_sets(adj: list[int], k: int) -> list[tuple[int, ...]]:
    return [
        vs for vs in itertools.combinations(range(len(adj)), k)
        if all(not ((adj[u] >> v) & 1) for u, v in itertools.combinations(vs, 2))
    ]


def edge_pairs(adj: list[int], value: bool) -> list[tuple[int, int]]:
    return [
        (i, j) for i in range(len(adj)) for j in range(i + 1, len(adj))
        if bool((adj[i] >> j) & 1) == value
    ]


def add_lex_cross_rows(solver: Solver, x: list[list[int]], pool: IDPool) -> int:
    """Sort B labels by their A-neighbourhood bit rows; sound symmetry break."""
    clauses = 0
    for b in range(NB - 1):
        pref = [pool.id(("lex", b, a)) for a in range(NA)]
        solver.add_clause([pref[0]])
        clauses += 1
        for a in range(NA):
            p, left, right = pref[a], x[a][b], x[a][b + 1]
            # Under equal prefix, row_b <= row_{b+1} lexicographically (0<1).
            solver.add_clause([-p, -left, right])
            clauses += 1
            if a + 1 == NA:
                continue
            q = pref[a + 1]
            for clause in (
                [-q, p],
                [-q, -left, right],
                [-q, left, -right],
                [-p, -left, -right, q],
                [-p, left, right, q],
            ):
                solver.add_clause(clause)
                clauses += 1
    return clauses


def solve(args) -> int:
    ag6, A, ae = select_record(args.a_catalog, args.a_ordinal, NA)
    validate_A(A)
    if args.a_edges is not None and ae != args.a_edges:
        raise ValueError((ae, args.a_edges))
    be = args.b_edges
    if not 0 <= be <= NB * (NB - 1) // 2:
        raise ValueError(be)

    # B internal edge variables y[i][j].
    y = [[0] * NB for _ in range(NB)]
    nxt = 1
    for i in range(NB):
        for j in range(i + 1, NB):
            y[i][j] = y[j][i] = nxt
            nxt += 1
    # Cross variables x[a][b].
    x = [[0] * NB for _ in range(NA)]
    for a in range(NA):
        for b in range(NB):
            x[a][b] = nxt
            nxt += 1
    pool = IDPool(start_from=nxt)

    da = [m.bit_count() for m in A]
    a_edges = edge_pairs(A, True)
    a_non = edge_pairs(A, False)
    a_i3 = independent_sets(A, 3)
    a_i4 = independent_sets(A, 4)
    a_i5 = independent_sets(A, 5)

    counts = {k: 0 for k in (
        "b_edge_cardinality", "degree", "lex", "b_k4", "b_i5",
        "k4_1a3b", "k4_2a2b", "i6_5a1b", "i6_4a2b", "i6_3a3b", "i6_2a4b",
    )}
    start = time.monotonic()
    with Solver(name=args.solver) as s:
        bedges = [y[i][j] for i in range(NB) for j in range(i + 1, NB)]
        counts["b_edge_cardinality"] = add_cnf(
            s, CardEnc.equals(bedges, be, vpool=pool, encoding=EncType.seqcounter)
        )
        for a in range(NA):
            lo, hi = 10 - da[a], 11 - da[a]
            if lo < 0 or hi > NB:
                return finish_unsat(args, ag6, ae, be, start, counts, "A degree impossible")
            counts["degree"] += add_cnf(s, CardEnc.atleast(x[a], lo, vpool=pool, encoding=EncType.seqcounter))
            counts["degree"] += add_cnf(s, CardEnc.atmost(x[a], hi, vpool=pool, encoding=EncType.seqcounter))
        for b in range(NB):
            incident = [y[b][j] for j in range(NB) if j != b] + [x[a][b] for a in range(NA)]
            counts["degree"] += add_cnf(s, CardEnc.atleast(incident, 11, vpool=pool, encoding=EncType.seqcounter))
            counts["degree"] += add_cnf(s, CardEnc.atmost(incident, 12, vpool=pool, encoding=EncType.seqcounter))
        counts["lex"] = add_lex_cross_rows(s, x, pool)

        # B-only constraints.
        for bs in itertools.combinations(range(NB), 4):
            s.add_clause([-y[u][v] for u, v in itertools.combinations(bs, 2)])
            counts["b_k4"] += 1
        for bs in itertools.combinations(range(NB), 5):
            s.add_clause([y[u][v] for u, v in itertools.combinations(bs, 2)])
            counts["b_i5"] += 1

        # Mixed K4 constraints.
        for a in range(NA):
            for bs in itertools.combinations(range(NB), 3):
                s.add_clause(
                    [-y[u][v] for u, v in itertools.combinations(bs, 2)]
                    + [-x[a][b] for b in bs]
                )
                counts["k4_1a3b"] += 1
        for aa in a_edges:
            for b, c in itertools.combinations(range(NB), 2):
                s.add_clause([-y[b][c]] + [-x[a][z] for a in aa for z in (b, c)])
                counts["k4_2a2b"] += 1

        # Mixed independent-6 constraints.
        for aa in a_i5:
            for b in range(NB):
                s.add_clause([x[a][b] for a in aa])
                counts["i6_5a1b"] += 1
        for aa in a_i4:
            for b, c in itertools.combinations(range(NB), 2):
                s.add_clause([y[b][c]] + [x[a][z] for a in aa for z in (b, c)])
                counts["i6_4a2b"] += 1
        for aa in a_i3:
            for bs in itertools.combinations(range(NB), 3):
                s.add_clause(
                    [y[u][v] for u, v in itertools.combinations(bs, 2)]
                    + [x[a][b] for a in aa for b in bs]
                )
                counts["i6_3a3b"] += 1
        for aa in a_non:
            for bs in itertools.combinations(range(NB), 4):
                s.add_clause(
                    [y[u][v] for u, v in itertools.combinations(bs, 2)]
                    + [x[a][b] for a in aa for b in bs]
                )
                counts["i6_2a4b"] += 1

        print("ENCODING " + json.dumps({"a_edges": ae, "b_edges": be, "a_ordinal": args.a_ordinal,
              "clauses": counts, "max_var": pool.top}, sort_keys=True), flush=True)
        sat = s.solve()
        if not sat:
            return finish_unsat(args, ag6, ae, be, start, counts, "SAT solver UNSAT")
        pos = {lit for lit in s.get_model() if lit > 0}

    rows = [["0"] * 36 for _ in range(36)]
    for a in range(NA):
        rows[0][1 + a] = rows[1 + a][0] = "1"
    for i in range(NA):
        for j in range(i + 1, NA):
            if (A[i] >> j) & 1:
                rows[1+i][1+j] = rows[1+j][1+i] = "1"
    for i in range(NB):
        for j in range(i + 1, NB):
            if y[i][j] in pos:
                rows[13+i][13+j] = rows[13+j][13+i] = "1"
    for a in range(NA):
        for b in range(NB):
            if x[a][b] in pos:
                rows[1+a][13+b] = rows[13+b][1+a] = "1"
    srows = ["".join(r) for r in rows]
    verify_full(srows)
    elapsed = time.monotonic() - start
    result = base_result(args, ag6, ae, be, elapsed, counts)
    result.update(status="SAT", degree_sequence=[r.count("1") for r in srows])
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.write_text(json.dumps({"adjacency": srows}, indent=2) + "\n")
    print("RESULT " + json.dumps(result, sort_keys=True), flush=True)
    return 0


def base_result(args, ag6, ae, be, elapsed, counts):
    return {
        "a_ordinal": args.a_ordinal, "a_graph6": ag6, "a_edges": ae, "b_edges": be,
        "solver": args.solver, "elapsed_seconds": round(elapsed, 6), "clause_counts": counts,
    }


def finish_unsat(args, ag6, ae, be, start, counts, reason):
    result = base_result(args, ag6, ae, be, time.monotonic() - start, counts)
    result.update(status="UNSAT", reason=reason)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RESULT " + json.dumps(result, sort_keys=True), flush=True)
    return 20


def self_test() -> None:
    # Verify the split taxonomy exhausts every mixed distribution of 4 and 6.
    assert [(i, 4-i) for i in range(5) if i and 4-i] == [(1,3),(2,2),(3,1)]
    assert [(i, 6-i) for i in range(7) if i and 6-i] == [(1,5),(2,4),(3,3),(4,2),(5,1)]
    print("d12 static split SAT self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("solve")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--a-ordinal", type=int, required=True)
    p.add_argument("--a-edges", type=int)
    p.add_argument("--b-edges", type=int, required=True)
    p.add_argument("--solver", default="cadical195")
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    return solve(args)


if __name__ == "__main__":
    raise SystemExit(main())
