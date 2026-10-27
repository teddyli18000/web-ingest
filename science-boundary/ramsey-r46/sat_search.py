#!/usr/bin/env python3
"""Direct SAT search for a 36-vertex (4,6)-Ramsey graph.

Requires python-sat.  The durable mathematical encoding is simple:
- one Boolean variable per undirected edge of K_36;
- every 4-set gets a clause saying at least one of its six edges is absent;
- every 6-set gets a clause saying at least one of its fifteen edges is present.

We additionally add safe degree bounds 11 <= deg(v) <= 17.  They follow from
R(4,5)=25 and R(3,6)=18: the non-neighborhood of v is a (4,5)-graph and the
neighborhood of v is a (3,6)-graph.
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


def build_edge_variables() -> tuple[list[list[int]], int]:
    edge = [[0] * N for _ in range(N)]
    nxt = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = nxt
            nxt += 1
    return edge, nxt - 1


def phase_literals(edge: list[list[int]], mode: str, seed: int) -> list[int]:
    rng = random.Random(seed)
    out: list[int] = []
    cyclic_mask = 11459  # best n=36 circulant in our exhaustive simple-violation scan
    for i in range(N):
        for j in range(i + 1, N):
            var = edge[i][j]
            if mode == "cyclic":
                d = min(j - i, N - (j - i))
                value = bool((cyclic_mask >> (d - 1)) & 1)
            elif mode == "random":
                # Valid (4,6) graphs are fairly dense; 0.40 is only a phase bias.
                value = rng.random() < 0.40
            elif mode == "mixed":
                d = min(j - i, N - (j - i))
                value = bool((cyclic_mask >> (d - 1)) & 1)
                if rng.random() < 0.10:
                    value = not value
            else:
                raise ValueError(mode)
            out.append(var if value else -var)
    return out


def add_problem_clauses(solver: Solver, edge: list[list[int]]) -> None:
    started = time.monotonic()
    k4_count = 0
    for vertices in itertools.combinations(range(N), 4):
        clause = [-edge[a][b] for a, b in itertools.combinations(vertices, 2)]
        solver.add_clause(clause)
        k4_count += 1
    print(f"added_k4_clauses={k4_count} elapsed={time.monotonic()-started:.2f}s", flush=True)

    i6_count = 0
    for vertices in itertools.combinations(range(N), 6):
        clause = [edge[a][b] for a, b in itertools.combinations(vertices, 2)]
        solver.add_clause(clause)
        i6_count += 1
        if i6_count % 250_000 == 0:
            print(
                f"added_independent6_clauses={i6_count} elapsed={time.monotonic()-started:.2f}s",
                flush=True,
            )
    print(
        f"added_independent6_clauses={i6_count} elapsed={time.monotonic()-started:.2f}s",
        flush=True,
    )


def add_degree_bounds(
    solver: Solver, edge: list[list[int]], first_aux: int
) -> int:
    pool = IDPool(start_from=first_aux)
    clauses = 0
    for v in range(N):
        incident = [edge[v][u] for u in range(N) if u != v]
        lo = CardEnc.atleast(
            lits=incident, bound=11, vpool=pool, encoding=EncType.seqcounter
        )
        hi = CardEnc.atmost(
            lits=incident, bound=17, vpool=pool, encoding=EncType.seqcounter
        )
        for clause in itertools.chain(lo.clauses, hi.clauses):
            solver.add_clause(clause)
            clauses += 1
    print(f"added_degree_bound_clauses={clauses} max_var={pool.top}", flush=True)
    return pool.top


def model_to_rows(model: list[int], edge: list[list[int]]) -> list[str]:
    positive = {lit for lit in model if lit > 0}
    rows = []
    for i in range(N):
        rows.append("".join("1" if i != j and edge[i][j] in positive else "0" for j in range(N)))
    return rows


def exact_check(rows: list[str]) -> None:
    for vertices in itertools.combinations(range(N), 4):
        if all(rows[a][b] == "1" for a, b in itertools.combinations(vertices, 2)):
            raise RuntimeError(f"internal check found K4 {vertices}")
    for vertices in itertools.combinations(range(N), 6):
        if all(rows[a][b] == "0" for a, b in itertools.combinations(vertices, 2)):
            raise RuntimeError(f"internal check found independent-6 {vertices}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--phase", choices=["cyclic", "random", "mixed"], default="mixed")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("candidate.json"))
    parser.add_argument("--no-degree-bounds", action="store_true")
    args = parser.parse_args()

    edge, edge_vars = build_edge_variables()
    print(
        f"n={N} edge_vars={edge_vars} solver={args.solver} phase={args.phase} seed={args.seed}",
        flush=True,
    )
    started = time.monotonic()
    with Solver(name=args.solver, bootstrap_with=[]) as solver:
        # Safe symmetry break: every valid graph has an edge, so relabel one edge as {0,1}.
        solver.add_clause([edge[0][1]])
        if not args.no_degree_bounds:
            add_degree_bounds(solver, edge, edge_vars + 1)
        add_problem_clauses(solver, edge)
        solver.set_phases(phase_literals(edge, args.phase, args.seed))
        print(f"encoding_complete elapsed={time.monotonic()-started:.2f}s", flush=True)
        sat = solver.solve()
        print(f"solver_result={'SAT' if sat else 'UNSAT'} elapsed={time.monotonic()-started:.2f}s", flush=True)
        if not sat:
            # UNSAT here would prove there is no 36-vertex (4,6)-graph at all, because
            # the degree bounds and x_01 symmetry break are logically lossless.
            return 20
        rows = model_to_rows(solver.get_model(), edge)

    exact_check(rows)
    payload = {"adjacency": rows}
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    edges = sum(row.count("1") for row in rows) // 2
    degrees = [row.count("1") for row in rows]
    print(f"candidate={args.output} edges={edges} degree_min={min(degrees)} degree_max={max(degrees)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
