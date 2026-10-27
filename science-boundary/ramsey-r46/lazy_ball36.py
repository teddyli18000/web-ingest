#!/usr/bin/env python3
"""Exact lazy-SAT search inside a Hamming ball around a 36-vertex near-miss.

All 630 graph edges are variables.  The candidate is constrained to differ from
an input 36-vertex graph on at most ``radius`` edges.  Safe degree bounds
11..17 are imposed.  Ramsey clauses are separated lazily: every K4 and every
independent 6-set found in a SAT model yields a globally valid blocking clause.
Thus SAT yields an explicit R(4,6,36) witness and UNSAT rigorously excludes the
entire labelled Hamming ball.

Requires python-sat.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

N = 36


def load_seed(path: Path) -> list[str]:
    rows = json.loads(path.read_text(encoding="utf-8"))["adjacency"]
    if len(rows) != N or any(len(r) != N or set(r) - {"0", "1"} for r in rows):
        raise ValueError("seed must contain 36 binary adjacency rows")
    for i in range(N):
        if rows[i][i] != "0":
            raise ValueError("seed has a loop")
        for j in range(i + 1, N):
            if rows[i][j] != rows[j][i]:
                raise ValueError("seed is asymmetric")
    return rows


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


def add_hamming_bound(
    solver: Solver, edge: list[list[int]], seed: list[str], radius: int, start: int
) -> int:
    pool = IDPool(start_from=start)
    flips = []
    for i in range(N):
        for j in range(i + 1, N):
            var = edge[i][j]
            flips.append(-var if seed[i][j] == "1" else var)
    cnf = CardEnc.atmost(flips, radius, vpool=pool, encoding=EncType.seqcounter)
    for clause in cnf.clauses:
        solver.add_clause(clause)
    print(
        f"hamming_ball radius={radius} edges={len(flips)} "
        f"clauses={len(cnf.clauses)} max_var={pool.top}",
        flush=True,
    )
    return pool.top


def seed_phases(edge: list[list[int]], seed: list[str]) -> list[int]:
    return [
        edge[i][j] if seed[i][j] == "1" else -edge[i][j]
        for i in range(N)
        for j in range(i + 1, N)
    ]


def rows_from_model(model: list[int], edge: list[list[int]]) -> list[str]:
    positive = {x for x in model if 0 < x <= N * (N - 1) // 2}
    return [
        "".join("1" if i != j and edge[i][j] in positive else "0" for j in range(N))
        for i in range(N)
    ]


def find_violations(rows: list[str]) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    k4 = [
        vs
        for vs in itertools.combinations(range(N), 4)
        if all(rows[a][b] == "1" for a, b in itertools.combinations(vs, 2))
    ]
    ind6 = [
        vs
        for vs in itertools.combinations(range(N), 6)
        if all(rows[a][b] == "0" for a, b in itertools.combinations(vs, 2))
    ]
    return k4, ind6


def block(vertices: tuple[int, ...], edge: list[list[int]], want_edge: bool) -> list[int]:
    lits = [edge[a][b] for a, b in itertools.combinations(vertices, 2)]
    return lits if want_edge else [-x for x in lits]


def distance(rows: list[str], seed: list[str]) -> int:
    return sum(
        rows[i][j] != seed[i][j]
        for i in range(N)
        for j in range(i + 1, N)
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-graph", type=Path, required=True)
    ap.add_argument("--radius", type=int, required=True)
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--max-iterations", type=int, default=200_000)
    ap.add_argument("--output", type=Path, default=Path("candidate.json"))
    ap.add_argument("--summary", type=Path)
    args = ap.parse_args()
    if not 0 <= args.radius <= N * (N - 1) // 2:
        ap.error("invalid radius")

    seed = load_seed(args.seed_graph)
    edge, edge_vars = edge_variables()
    started = time.monotonic()
    learned: set[tuple[int, tuple[int, ...]]] = set()
    total_added = 0
    result: dict[str, object] = {
        "radius": args.radius,
        "solver": args.solver,
        "seed_graph": str(args.seed_graph),
    }

    def finish(status: str, rc: int, **extra: object) -> int:
        result.update(
            status=status,
            elapsed_seconds=round(time.monotonic() - started, 6),
            learned_ramsey_clauses=total_added,
            **extra,
        )
        print("RESULT " + json.dumps(result, sort_keys=True), flush=True)
        if args.summary:
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return rc

    with Solver(name=args.solver, bootstrap_with=[]) as solver:
        top = add_degree_bounds(solver, edge, edge_vars + 1)
        add_hamming_bound(solver, edge, seed, args.radius, top + 1)
        solver.set_phases(seed_phases(edge, seed))

        # Seed with the known near-miss conflicts so the first SAT call need not rediscover them.
        k4, ind6 = find_violations(seed)
        print(f"seed_conflicts k4={len(k4)} ind6={len(ind6)}", flush=True)
        for kind, violations in ((4, k4), (6, ind6)):
            for vs in violations:
                key = (kind, vs)
                learned.add(key)
                solver.add_clause(block(vs, edge, want_edge=(kind == 6)))
                total_added += 1

        for iteration in range(1, args.max_iterations + 1):
            if not solver.solve():
                return finish("UNSAT", 20, iterations=iteration - 1)
            rows = rows_from_model(solver.get_model(), edge)
            k4, ind6 = find_violations(rows)
            if not k4 and not ind6:
                d = distance(rows, seed)
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps({"adjacency": rows}, indent=2) + "\n")
                return finish("SAT", 0, iterations=iteration, distance=d, output=str(args.output))

            added_now = 0
            for kind, violations in ((4, k4), (6, ind6)):
                for vs in violations:
                    key = (kind, vs)
                    if key in learned:
                        continue
                    learned.add(key)
                    solver.add_clause(block(vs, edge, want_edge=(kind == 6)))
                    added_now += 1
            total_added += added_now
            if iteration <= 20 or iteration % 100 == 0:
                print(
                    f"iter={iteration} k4={len(k4)} ind6={len(ind6)} added={added_now} "
                    f"total={total_added} distance={distance(rows, seed)} "
                    f"elapsed={time.monotonic()-started:.3f}s",
                    flush=True,
                )
            if added_now == 0:
                raise RuntimeError("violating model produced no new separator")

    return finish("ITERATION_LIMIT", 30, iterations=args.max_iterations)


if __name__ == "__main__":
    sys.exit(main())
