#!/usr/bin/env python3
"""Symmetry-reduced exact SAT for the unique lucky degree-12 A29/B101 pair.

This is the same complete 276-cross-edge problem as d12_fixed_ab_sat.py, but
adds sound lex-leader constraints under Aut(A) and optionally Aut(B).  The
unique A29 graph has automorphism group order 576; the unique B101 graph has
order 2.  A lexicographically least member of every orbit survives these
constraints, so UNSAT remains a proof for the original fixed-pair problem.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

import networkx as nx
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import d12_fixed_ab_sat as base

NA, NB = 12, 23


def graph_from_adj(adj: list[int]) -> nx.Graph:
    g = nx.Graph()
    g.add_nodes_from(range(len(adj)))
    for i in range(len(adj)):
        for j in range(i + 1, len(adj)):
            if (adj[i] >> j) & 1:
                g.add_edge(i, j)
    return g


def automorphisms(adj: list[int]) -> list[tuple[int, ...]]:
    g = graph_from_adj(adj)
    out = []
    for m in nx.algorithms.isomorphism.GraphMatcher(g, g).isomorphisms_iter():
        p = tuple(m[i] for i in range(len(adj)))
        if sorted(p) != list(range(len(adj))):
            raise AssertionError("bad automorphism permutation")
        for i in range(len(adj)):
            for j in range(i + 1, len(adj)):
                if bool((adj[i] >> j) & 1) != bool((adj[p[i]] >> p[j]) & 1):
                    raise AssertionError("GraphMatcher returned non-automorphism")
        out.append(p)
    out = sorted(set(out))
    return out


def compose(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    """Permutation p after q: i -> p[q[i]]."""
    return tuple(p[q[i]] for i in range(len(p)))


def generated_subgroup(gens: list[tuple[int, ...]], n: int) -> set[tuple[int, ...]]:
    ident = tuple(range(n))
    seen = {ident}
    stack = [ident]
    while stack:
        h = stack.pop()
        for g in gens:
            for z in (compose(g, h), compose(h, g)):
                if z not in seen:
                    seen.add(z)
                    stack.append(z)
    return seen


def greedy_generators(group: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
    if not group:
        return []
    n = len(group[0])
    ident = tuple(range(n))
    gens: list[tuple[int, ...]] = []
    closure = {ident}
    for p in group:
        if p in closure:
            continue
        gens.append(p)
        closure = generated_subgroup(gens, n)
        if len(closure) == len(group):
            break
    if closure != set(group):
        raise AssertionError((len(closure), len(group)))
    return gens


def add_lex_leader(solver: Solver, pool: IDPool, left: list[int], right: list[int]) -> tuple[int, int]:
    """Add left <=lex right. Return (aux variables, clauses)."""
    if len(left) != len(right):
        raise ValueError("lex vectors differ in length")
    # Prefix variable p means all earlier coordinates are equal. p0 is true.
    p = pool.id()
    solver.add_clause([p])
    aux = 1
    clauses = 1
    for i, (x, y) in enumerate(zip(left, right)):
        solver.add_clause([-p, -x, y])
        clauses += 1
        if i + 1 == len(left):
            break
        q = pool.id()
        aux += 1
        # q <-> p & (x == y)
        for clause in (
            [-q, p],
            [-q, -x, y],
            [-q, x, -y],
            [-p, -x, -y, q],
            [-p, x, y, q],
        ):
            solver.add_clause(list(clause))
            clauses += 1
        p = q
    return aux, clauses


def symmetry_permutations(A: list[int], B: list[int], mode: str) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]], dict]:
    aa = automorphisms(A)
    bb = automorphisms(B)
    if len(aa) != 576:
        raise AssertionError(f"expected |Aut(A29)|=576, got {len(aa)}")
    if len(bb) != 2:
        raise AssertionError(f"expected |Aut(B101)|=2, got {len(bb)}")
    ident_a = tuple(range(NA))
    ident_b = tuple(range(NB))
    if mode == "all-a":
        use_a = [p for p in aa if p != ident_a]
        use_b = []
    elif mode == "all-ab":
        use_a = [p for p in aa if p != ident_a]
        use_b = [p for p in bb if p != ident_b]
    elif mode == "generators":
        use_a = greedy_generators(aa)
        use_b = greedy_generators(bb)
    else:
        raise ValueError(mode)
    return use_a, use_b, {
        "aut_a_order": len(aa),
        "aut_b_order": len(bb),
        "a_generators": len(greedy_generators(aa)),
        "b_generators": len(greedy_generators(bb)),
        "lex_a_permutations": len(use_a),
        "lex_b_permutations": len(use_b),
    }


def add_all_constraints(s: Solver, pool: IDPool, x: list[list[int]], A: list[int], B: list[int], min_degree: int, max_degree: int) -> dict:
    counts = {k: 0 for k in (
        "degree", "k4_1a3b", "k4_2a2b", "i6_5a1b", "i6_4a2b", "i6_3a3b", "i6_2a4b",
    )}
    da, db = base.degrees(A), base.degrees(B)
    for a in range(NA):
        bounds = base.cross_bounds(1 + da[a], NB, min_degree, max_degree)
        if bounds is None:
            s.add_clause([])
            return counts
        lo, hi = bounds
        if lo:
            counts["degree"] += base.add_cnf(s, CardEnc.atleast(x[a], lo, vpool=pool, encoding=EncType.seqcounter))
        if hi < NB:
            counts["degree"] += base.add_cnf(s, CardEnc.atmost(x[a], hi, vpool=pool, encoding=EncType.seqcounter))
    for b in range(NB):
        bounds = base.cross_bounds(db[b], NA, min_degree, max_degree)
        if bounds is None:
            s.add_clause([])
            return counts
        lo, hi = bounds
        col = [x[a][b] for a in range(NA)]
        if lo:
            counts["degree"] += base.add_cnf(s, CardEnc.atleast(col, lo, vpool=pool, encoding=EncType.seqcounter))
        if hi < NA:
            counts["degree"] += base.add_cnf(s, CardEnc.atmost(col, hi, vpool=pool, encoding=EncType.seqcounter))

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


def solve(args) -> int:
    ag6, A, ae = base.select_record(args.a_catalog, 0, NA)
    bg6, B, be = base.select_record(args.b_catalog, 0, NB)
    base.validate_A(A); base.validate_B(B)
    if ae != 29 or be != 101:
        raise ValueError((ae, be))
    use_a, use_b, sym_info = symmetry_permutations(A, B, args.symmetry)

    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    started = time.monotonic()
    with Solver(name=args.solver) as s:
        counts = add_all_constraints(s, pool, x, A, B, args.min_degree, args.max_degree)
        flat = [x[a][b] for a in range(NA) for b in range(NB)]
        lex_aux = lex_clauses = 0
        for p in use_a:
            right = [x[p[a]][b] for a in range(NA) for b in range(NB)]
            a, c = add_lex_leader(s, pool, flat, right); lex_aux += a; lex_clauses += c
        for p in use_b:
            right = [x[a][p[b]] for a in range(NA) for b in range(NB)]
            a, c = add_lex_leader(s, pool, flat, right); lex_aux += a; lex_clauses += c
        sym_info.update(lex_aux_variables=lex_aux, lex_clauses=lex_clauses)
        print("ENCODING " + json.dumps({"solver": args.solver, "symmetry": args.symmetry, **sym_info, "ramsey_counts": counts, "max_var": pool.top}, sort_keys=True), flush=True)
        sat = s.solve()
        elapsed = time.monotonic() - started
        if not sat:
            result = {
                "status": "UNSAT", "solver": args.solver, "symmetry": args.symmetry,
                "elapsed_seconds": round(elapsed, 6), "a_graph6": ag6, "b_graph6": bg6,
                "a_edges": ae, "b_edges": be, "min_degree": args.min_degree, "max_degree": args.max_degree,
                "symmetry_info": sym_info, "ramsey_counts": counts,
            }
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print("RESULT " + json.dumps(result, sort_keys=True), flush=True)
            return 20
        pos = {lit for lit in s.get_model() if lit > 0}

    rows = [["0"] * 36 for _ in range(36)]
    for a in range(NA): rows[0][1+a] = rows[1+a][0] = "1"
    for i in range(NA):
        for j in range(i+1, NA):
            if (A[i] >> j) & 1: rows[1+i][1+j] = rows[1+j][1+i] = "1"
    for i in range(NB):
        for j in range(i+1, NB):
            if (B[i] >> j) & 1: rows[13+i][13+j] = rows[13+j][13+i] = "1"
    for a in range(NA):
        for b in range(NB):
            if x[a][b] in pos: rows[1+a][13+b] = rows[13+b][1+a] = "1"
    srows = ["".join(r) for r in rows]
    base.verify_full(srows, args.min_degree, args.max_degree)
    result = {
        "status": "SAT", "solver": args.solver, "symmetry": args.symmetry,
        "elapsed_seconds": round(elapsed, 6), "a_graph6": ag6, "b_graph6": bg6,
        "a_edges": ae, "b_edges": be, "min_degree": args.min_degree, "max_degree": args.max_degree,
        "degree_sequence": [r.count("1") for r in srows], "symmetry_info": sym_info, "ramsey_counts": counts,
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True); args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    args.output.write_text(json.dumps({"adjacency": srows}, indent=2) + "\n")
    print("RESULT " + json.dumps(result, sort_keys=True), flush=True)
    return 0


def lex_holds(bits: tuple[bool, ...], p: tuple[int, ...]) -> bool:
    right = tuple(bits[p[i]] for i in range(len(bits)))
    return bits <= right


def self_test() -> None:
    # Exhaustively compare the CNF lex encoder with direct Python lex order.
    for n in range(1, 6):
        p = tuple(reversed(range(n)))
        for bits in itertools.product((False, True), repeat=n):
            with Solver(name="cadical195") as s:
                pool = IDPool(start_from=n + 1)
                add_lex_leader(s, pool, list(range(1, n+1)), [p[i]+1 for i in range(n)])
                for i, bit in enumerate(bits, 1): s.add_clause([i if bit else -i])
                assert s.solve() == lex_holds(bits, p), (n, bits, p)
    # Every orbit has at least one lex-min representative under all group elements.
    group = [(0,1,2), (1,0,2)]
    for bits in itertools.product((False, True), repeat=3):
        orbit = {tuple(bits[p[i]] for i in range(3)) for p in group}
        minimum = min(orbit)
        assert all(lex_holds(minimum, p) for p in group)
    assert len(generated_subgroup([(1,0,2)], 3)) == 2
    print("d12 fixed-pair symmetry SAT self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("solve")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--min-degree", type=int, default=11)
    p.add_argument("--max-degree", type=int, default=17)
    p.add_argument("--solver", default="cadical195")
    p.add_argument("--symmetry", choices=("generators","all-a","all-ab"), default="all-ab")
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test": self_test(); return 0
    return solve(args)


if __name__ == "__main__":
    raise SystemExit(main())
