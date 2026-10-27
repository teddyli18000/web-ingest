#!/usr/bin/env python3
"""Exact lazy-SAT search for R(4,6,36) graphs having a degree-17 vertex.

If vertex 0 has degree 17, its neighborhood is a Ramsey(3,6,17) graph.  McKay's
complete catalogue contains exactly seven such graphs.  By relabelling, fix the
neighbors to vertices 1..17 and fix their induced graph to one selected catalog
representative.  Vertices 18..35 are the non-neighbors of 0 and must induce a
Ramsey(4,5,18) graph.  Cross edges remain free.  Ramsey constraints are then
separated lazily.  UNSAT for all seven representatives proves that no
R(4,6,36) graph can contain a degree-17 vertex.

Requires python-sat.
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

N = 36


def decode_graph6(line: str) -> list[str]:
    s = line.strip()
    if not s or s.startswith(">>"):
        raise ValueError("expected one short graph6 record")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 records are supported")
    bits = []
    for ch in s[1:]:
        v = ord(ch) - 63
        if not 0 <= v < 64:
            raise ValueError("invalid graph6 character")
        bits.extend((v >> shift) & 1 for shift in range(5, -1, -1))
    need = n * (n - 1) // 2
    if len(bits) < need:
        raise ValueError("truncated graph6 record")
    rows = [["0"] * n for _ in range(n)]
    p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]:
                rows[i][j] = rows[j][i] = "1"
            p += 1
    return ["".join(r) for r in rows]


def load_catalog(path: Path) -> list[list[str]]:
    records = [decode_graph6(line) for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    if len(records) != 7 or any(len(rows) != 17 for rows in records):
        raise ValueError("expected the complete seven-graph R(3,6,17) catalogue")
    for idx, rows in enumerate(records):
        tri = any(all(rows[a][b] == "1" for a, b in itertools.combinations(vs, 2)) for vs in itertools.combinations(range(17), 3))
        i6 = any(all(rows[a][b] == "0" for a, b in itertools.combinations(vs, 2)) for vs in itertools.combinations(range(17), 6))
        if tri or i6:
            raise ValueError(f"catalog record {idx} is not a (3,6,17)-graph")
    return records


def edge_variables() -> tuple[list[list[int]], int]:
    edge = [[0] * N for _ in range(N)]
    nxt = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = nxt
            nxt += 1
    return edge, nxt - 1


def add_degree_bounds(solver: Solver, edge: list[list[int]], start: int) -> int:
    pool = IDPool(start_from=start)
    for v in range(N):
        inc = [edge[v][u] for u in range(N) if u != v]
        for cnf in (
            CardEnc.atleast(inc, 11, vpool=pool, encoding=EncType.seqcounter),
            CardEnc.atmost(inc, 17, vpool=pool, encoding=EncType.seqcounter),
        ):
            for clause in cnf.clauses:
                solver.add_clause(clause)
    return pool.top


def add_fixed_branch(solver: Solver, edge: list[list[int]], neighborhood: list[str]) -> None:
    for v in range(1, N):
        solver.add_clause([edge[0][v] if v <= 17 else -edge[0][v]])
    for i in range(17):
        for j in range(i + 1, 17):
            var = edge[i + 1][j + 1]
            solver.add_clause([var if neighborhood[i][j] == "1" else -var])
    # Non-neighbors B=18..35 must be a (4,5)-graph, because adding vertex 0
    # to an independent 5-set in B would create an independent 6-set.
    b = range(18, 36)
    for vs in itertools.combinations(b, 4):
        solver.add_clause([-edge[a][c] for a, c in itertools.combinations(vs, 2)])
    for vs in itertools.combinations(b, 5):
        solver.add_clause([edge[a][c] for a, c in itertools.combinations(vs, 2)])


def phases(edge: list[list[int]], neighborhood: list[str], seed: int) -> list[int]:
    rng = random.Random(seed)
    out = []
    for i in range(N):
        for j in range(i + 1, N):
            var = edge[i][j]
            if i == 0:
                value = j <= 17
            elif 1 <= i < j <= 17:
                value = neighborhood[i - 1][j - 1] == "1"
            else:
                value = rng.random() < 0.43
            out.append(var if value else -var)
    return out


def rows_from_model(model: list[int], edge: list[list[int]]) -> list[str]:
    positive = {x for x in model if 0 < x <= N * (N - 1) // 2}
    return ["".join("1" if i != j and edge[i][j] in positive else "0" for j in range(N)) for i in range(N)]


def violations(rows: list[str]) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    k4 = [vs for vs in itertools.combinations(range(N), 4) if all(rows[a][b] == "1" for a, b in itertools.combinations(vs, 2))]
    i6 = [vs for vs in itertools.combinations(range(N), 6) if all(rows[a][b] == "0" for a, b in itertools.combinations(vs, 2))]
    return k4, i6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--max-iterations", type=int, default=200_000)
    ap.add_argument("--output", type=Path, default=Path("candidate.json"))
    ap.add_argument("--summary", type=Path)
    args = ap.parse_args()
    catalog = load_catalog(args.catalog)
    if not 0 <= args.index < len(catalog):
        ap.error("--index must be 0..6")
    fixed = catalog[args.index]
    edge, edge_vars = edge_variables()
    start = time.monotonic()
    learned: set[tuple[int, tuple[int, ...]]] = set()
    total = 0
    result: dict[str, object] = {"catalog_index": args.index, "solver": args.solver, "seed": args.seed}

    def finish(status: str, rc: int, **extra: object) -> int:
        result.update(status=status, elapsed_seconds=round(time.monotonic() - start, 6), learned_ramsey_clauses=total, **extra)
        print("RESULT " + json.dumps(result, sort_keys=True), flush=True)
        if args.summary:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return rc

    with Solver(name=args.solver, bootstrap_with=[]) as solver:
        add_degree_bounds(solver, edge, edge_vars + 1)
        add_fixed_branch(solver, edge, fixed)
        solver.set_phases(phases(edge, fixed, args.seed))
        for iteration in range(1, args.max_iterations + 1):
            if not solver.solve():
                return finish("UNSAT", 20, iterations=iteration - 1)
            rows = rows_from_model(solver.get_model(), edge)
            k4, i6 = violations(rows)
            if not k4 and not i6:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps({"adjacency": rows}, indent=2) + "\n")
                return finish("SAT", 0, iterations=iteration, output=str(args.output))
            added = 0
            for kind, bad in ((4, k4), (6, i6)):
                for vs in bad:
                    key = (kind, vs)
                    if key in learned:
                        continue
                    learned.add(key)
                    lits = [edge[a][b] for a, b in itertools.combinations(vs, 2)]
                    solver.add_clause(lits if kind == 6 else [-x for x in lits])
                    total += 1
                    added += 1
            if iteration <= 20 or iteration % 100 == 0:
                print(f"iter={iteration} k4={len(k4)} ind6={len(i6)} added={added} total={total} elapsed={time.monotonic()-start:.3f}s", flush=True)
            if added == 0:
                raise RuntimeError("violating model produced no new separator")
    return finish("ITERATION_LIMIT", 30, iterations=args.max_iterations)


if __name__ == "__main__":
    sys.exit(main())
