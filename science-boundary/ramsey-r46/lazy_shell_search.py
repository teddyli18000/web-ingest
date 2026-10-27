#!/usr/bin/env python3
"""Lazy SAT search for a 36-vertex (4,6) graph near a known 35-vertex seed.

The old 35-vertex induced graph is allowed to change on at most ``radius`` edges.
Rather than materialising all ~2M Ramsey clauses up front, solve a relaxation,
find every forbidden K4 / independent-6 in the model, add just those globally
valid clauses, and repeat.  If the incremental solver returns UNSAT, the whole
Hamming shell is rigorously ruled out because every learned clause is a genuine
Ramsey constraint.

Requires python-sat.  The default seed is the Few Shots p003 baseline.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
import sys
import time
import urllib.request
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

N_OLD = 35
N = 36
DEFAULT_BASELINE = (
    "https://raw.githubusercontent.com/few-shots/few-shots/main/"
    "problems/p003-ramsey-r46/baseline/certificate.json"
)


def load_baseline(source: str) -> list[str]:
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "science-boundary-r46/1"})
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    else:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
    rows = payload["adjacency"]
    if len(rows) != N_OLD or any(len(row) != N_OLD for row in rows):
        raise ValueError("baseline must have 35 adjacency rows of length 35")
    return rows


def edge_variables() -> tuple[list[list[int]], int]:
    edge = [[0] * N for _ in range(N)]
    nxt = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = nxt
            nxt += 1
    return edge, nxt - 1


def add_degree_bounds(solver: Solver, edge: list[list[int]], first_aux: int) -> int:
    pool = IDPool(start_from=first_aux)
    for v in range(N):
        incident = [edge[v][u] for u in range(N) if u != v]
        for cnf in (
            CardEnc.atleast(lits=incident, bound=11, vpool=pool, encoding=EncType.seqcounter),
            CardEnc.atmost(lits=incident, bound=17, vpool=pool, encoding=EncType.seqcounter),
        ):
            for clause in cnf.clauses:
                solver.add_clause(clause)
    return pool.top


def add_hamming_bound(
    solver: Solver,
    edge: list[list[int]],
    baseline: list[str],
    radius: int,
    first_aux: int,
) -> int:
    pool = IDPool(start_from=first_aux)
    flip_literals = []
    for i in range(N_OLD):
        for j in range(i + 1, N_OLD):
            var = edge[i][j]
            # Literal is true exactly when the candidate differs from baseline.
            flip_literals.append(-var if baseline[i][j] == "1" else var)
    cnf = CardEnc.atmost(
        lits=flip_literals,
        bound=radius,
        vpool=pool,
        encoding=EncType.seqcounter,
    )
    for clause in cnf.clauses:
        solver.add_clause(clause)
    print(
        f"hamming_bound radius={radius} old_edges={len(flip_literals)} "
        f"clauses={len(cnf.clauses)} max_var={pool.top}",
        flush=True,
    )
    return pool.top


def initial_phases(
    edge: list[list[int]], baseline: list[str], seed: int, new_degree: int
) -> list[int]:
    rng = random.Random(seed)
    new_neighbors = set(rng.sample(range(N_OLD), new_degree))
    phases = []
    for i in range(N):
        for j in range(i + 1, N):
            var = edge[i][j]
            if j < N_OLD:
                value = baseline[i][j] == "1"
            elif i < N_OLD and j == N_OLD:
                value = i in new_neighbors
            else:
                value = False
            phases.append(var if value else -var)
    return phases


def rows_from_model(model: list[int], edge: list[list[int]]) -> list[str]:
    positive = {lit for lit in model if 0 < lit <= N * (N - 1) // 2}
    return [
        "".join(
            "1" if i != j and edge[i][j] in positive else "0"
            for j in range(N)
        )
        for i in range(N)
    ]


def find_violations(rows: list[str]) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    k4 = []
    for vertices in itertools.combinations(range(N), 4):
        if all(rows[a][b] == "1" for a, b in itertools.combinations(vertices, 2)):
            k4.append(vertices)
    ind6 = []
    for vertices in itertools.combinations(range(N), 6):
        if all(rows[a][b] == "0" for a, b in itertools.combinations(vertices, 2)):
            ind6.append(vertices)
    return k4, ind6


def clause_for_k4(vertices: tuple[int, ...], edge: list[list[int]]) -> list[int]:
    return [-edge[a][b] for a, b in itertools.combinations(vertices, 2)]


def clause_for_ind6(vertices: tuple[int, ...], edge: list[list[int]]) -> list[int]:
    return [edge[a][b] for a, b in itertools.combinations(vertices, 2)]


def old_edge_distance(rows: list[str], baseline: list[str]) -> int:
    return sum(
        rows[i][j] != baseline[i][j]
        for i in range(N_OLD)
        for j in range(i + 1, N_OLD)
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--radius", type=int, required=True)
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--new-degree", type=int, default=14)
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--max-iterations", type=int, default=200_000)
    ap.add_argument("--output", type=Path, default=Path("candidate.json"))
    args = ap.parse_args()
    if not 0 <= args.radius <= N_OLD * (N_OLD - 1) // 2:
        ap.error("invalid radius")
    if not 11 <= args.new_degree <= 17:
        ap.error("--new-degree should respect the safe degree bounds 11..17")

    baseline = load_baseline(args.baseline)
    edge, edge_vars = edge_variables()
    started = time.monotonic()
    seen_clause_keys: set[tuple[int, tuple[int, ...]]] = set()
    total_added = 0

    with Solver(name=args.solver, bootstrap_with=[]) as solver:
        top = add_degree_bounds(solver, edge, edge_vars + 1)
        add_hamming_bound(solver, edge, baseline, args.radius, top + 1)
        solver.set_phases(initial_phases(edge, baseline, args.seed, args.new_degree))

        for iteration in range(1, args.max_iterations + 1):
            if not solver.solve():
                print(
                    f"RESULT UNSAT radius={args.radius} iterations={iteration-1} "
                    f"learned_ramsey_clauses={total_added} elapsed={time.monotonic()-started:.3f}s",
                    flush=True,
                )
                return 20

            rows = rows_from_model(solver.get_model(), edge)
            k4, ind6 = find_violations(rows)
            if not k4 and not ind6:
                distance = old_edge_distance(rows, baseline)
                payload = {"adjacency": rows}
                args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                print(
                    f"RESULT SAT radius={args.radius} distance={distance} "
                    f"iterations={iteration} learned_ramsey_clauses={total_added} "
                    f"elapsed={time.monotonic()-started:.3f}s output={args.output}",
                    flush=True,
                )
                return 0

            added_now = 0
            for kind, violations in ((4, k4), (6, ind6)):
                for vertices in violations:
                    key = (kind, vertices)
                    if key in seen_clause_keys:
                        continue
                    seen_clause_keys.add(key)
                    clause = (
                        clause_for_k4(vertices, edge)
                        if kind == 4
                        else clause_for_ind6(vertices, edge)
                    )
                    solver.add_clause(clause)
                    added_now += 1
            total_added += added_now
            if iteration <= 20 or iteration % 100 == 0:
                print(
                    f"iter={iteration} k4={len(k4)} ind6={len(ind6)} "
                    f"added={added_now} total_added={total_added} "
                    f"distance={old_edge_distance(rows, baseline)} "
                    f"elapsed={time.monotonic()-started:.3f}s",
                    flush=True,
                )
            if added_now == 0:
                raise RuntimeError("violating model produced no new separator clause")

    print("RESULT ITERATION_LIMIT", flush=True)
    return 30


if __name__ == "__main__":
    sys.exit(main())
