#!/usr/bin/env python3
"""Exact lazy SAT for the max-degree-12 branch of R(4,6,36).

Relabel a maximum-degree vertex as 0, set A=N(0)={1,...,12}, and fix
G[A] to one representative from McKay's complete R(3,6,12) catalogue.
The other 23 vertices B are non-neighbours of 0. Every vertex is constrained
to degree 11 or 12. B itself is a (4,5,23)-graph, so all B-only K4 and
independent-5 constraints are present from the start. Mixed Ramsey constraints
are separated lazily from exact models.

For a=e(A), degree counting gives b=e(B) in [a+61,a+78]. McKay's exact
extreme catalogue gives b>=101 for every (4,5,23)-graph. Thus a>=23; the
first campaign targets a=27..29, only 50 complete A-catalogue types.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import random
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

N = 36
A = tuple(range(1, 13))
B = tuple(range(13, 36))
EDGE_VARS = N * (N - 1) // 2


def decode_graph6(line: str) -> list[str]:
    s = line.strip()
    if not s or s.startswith(">>"):
        raise ValueError("expected one short graph6 record")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("only short graph6 records are supported")
    bits: list[int] = []
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


def edge_count(rows: list[str]) -> int:
    return sum(row.count("1") for row in rows) // 2


def edge_variables() -> tuple[list[list[int]], int]:
    edge = [[0] * N for _ in range(N)]
    nxt = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = nxt
            nxt += 1
    return edge, nxt - 1


def iter_catalog(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as f:
        for raw_index, line in enumerate(f):
            s = line.strip()
            if not s or s.startswith(">>"):
                continue
            rows = decode_graph6(s)
            if len(rows) != 12:
                raise ValueError(f"catalog record {raw_index} has n={len(rows)}, expected 12")
            yield raw_index, s, rows


def select_catalog(path: Path, wanted_edges: int, ordinal: int):
    seen = 0
    for raw_index, g6, rows in iter_catalog(path):
        if edge_count(rows) != wanted_edges:
            continue
        if seen == ordinal:
            return raw_index, g6, rows
        seen += 1
    raise IndexError(f"no edge_count={wanted_edges} ordinal={ordinal}; stratum size={seen}")


def masks_from_rows(rows: list[str]) -> list[int]:
    out = []
    for i, row in enumerate(rows):
        m = 0
        for j, c in enumerate(row):
            if c == "1":
                m |= 1 << j
        out.append(m & ~(1 << i))
    return out


def enumerate_cliques(adj: list[int], k: int, cap: int | None = None) -> list[tuple[int, ...]]:
    n = len(adj)
    out: list[tuple[int, ...]] = []

    def rec(cand: int, chosen: tuple[int, ...]) -> None:
        if cap is not None and len(out) >= cap:
            return
        if len(chosen) == k:
            out.append(chosen)
            return
        need = k - len(chosen)
        while cand.bit_count() >= need:
            bit = cand & -cand
            v = bit.bit_length() - 1
            cand ^= bit
            rec(cand & adj[v], chosen + (v,))
            if cap is not None and len(out) >= cap:
                return

    rec((1 << n) - 1, ())
    return out


def complement_masks(adj: list[int]) -> list[int]:
    n = len(adj)
    full = (1 << n) - 1
    return [full & ~adj[i] & ~(1 << i) for i in range(n)]


def validate_A(rows: list[str]) -> None:
    adj = masks_from_rows(rows)
    if enumerate_cliques(adj, 3, 1):
        raise ValueError("selected R(3,6,12) record contains a triangle")
    if enumerate_cliques(complement_masks(adj), 6, 1):
        raise ValueError("selected R(3,6,12) record contains an independent 6-set")


def fixed_edges(edge: list[list[int]], arows: list[str]) -> dict[int, bool]:
    fixed: dict[int, bool] = {}
    for v in A:
        fixed[edge[0][v]] = True
    for v in B:
        fixed[edge[0][v]] = False
    for i in range(12):
        for j in range(i + 1, 12):
            fixed[edge[A[i]][A[j]]] = arows[i][j] == "1"
    return fixed


def add_cnf(solver: Solver, cnf) -> int:
    for clause in cnf.clauses:
        solver.add_clause(clause)
    return len(cnf.clauses)


def add_lex_B_cross(solver: Solver, edge: list[list[int]], pool: IDPool) -> int:
    """Soundly sort B labels by their 12-bit cross-neighbourhood rows."""
    clauses = 0
    for k, (b, c) in enumerate(zip(B, B[1:])):
        pref = [pool.id(("lex", k, i)) for i in range(len(A))]
        solver.add_clause([pref[0]])
        clauses += 1
        for i, a in enumerate(A):
            p, x, y = pref[i], edge[a][b], edge[a][c]
            solver.add_clause([-p, -x, y])
            clauses += 1
            if i + 1 == len(A):
                continue
            q = pref[i + 1]
            for clause in (
                [-q, p],
                [-q, -x, y],
                [-q, x, -y],
                [-p, -x, -y, q],
                [-p, x, y, q],
            ):
                solver.add_clause(clause)
                clauses += 1
    return clauses


def rows_from_model(model: list[int], edge: list[list[int]]) -> list[str]:
    positive = {lit for lit in model if 0 < lit <= EDGE_VARS}
    return [
        "".join("1" if i != j and edge[i][j] in positive else "0" for j in range(N))
        for i in range(N)
    ]


def violations(rows: list[str], cap: int):
    adj = masks_from_rows(rows)
    return (
        enumerate_cliques(adj, 4, cap),
        enumerate_cliques(complement_masks(adj), 6, cap),
    )


def clause_k4(vs: tuple[int, ...], edge: list[list[int]]) -> list[int]:
    return [-edge[a][b] for a, b in itertools.combinations(vs, 2)]


def clause_i6(vs: tuple[int, ...], edge: list[list[int]]) -> list[int]:
    return [edge[a][b] for a, b in itertools.combinations(vs, 2)]


def solve_one(args) -> int:
    raw_index, g6, arows = select_catalog(args.catalog, args.edge_count, args.ordinal)
    validate_A(arows)
    a = edge_count(arows)
    if a != args.edge_count:
        raise AssertionError((a, args.edge_count))
    b_lo = max(101, a + 61)
    b_hi = a + 78
    if b_lo > b_hi:
        raise ValueError("branch impossible from edge-count bounds")

    edge, edge_vars = edge_variables()
    fixed = fixed_edges(edge, arows)
    started = time.monotonic()
    summary = {
        "max_degree": 12,
        "a_edges": a,
        "a_ordinal": args.ordinal,
        "a_raw_catalog_index": raw_index,
        "a_graph6": g6,
        "b_edge_lower": b_lo,
        "b_edge_upper": b_hi,
        "solver": args.solver,
        "status": "RUNNING",
    }

    pool = IDPool(start_from=edge_vars + 1)
    seen: set[tuple[int, tuple[int, ...]]] = set()
    learned = 0
    with Solver(name=args.solver, bootstrap_with=[]) as solver:
        for var, value in fixed.items():
            solver.add_clause([var if value else -var])

        degree_clauses = 0
        for v in range(N):
            incident = [edge[v][u] for u in range(N) if u != v]
            degree_clauses += add_cnf(
                solver,
                CardEnc.atleast(lits=incident, bound=11, vpool=pool, encoding=EncType.seqcounter),
            )
            degree_clauses += add_cnf(
                solver,
                CardEnc.atmost(lits=incident, bound=12, vpool=pool, encoding=EncType.seqcounter),
            )

        bedges = [edge[u][v] for u, v in itertools.combinations(B, 2)]
        bcard_clauses = add_cnf(
            solver,
            CardEnc.atleast(lits=bedges, bound=b_lo, vpool=pool, encoding=EncType.seqcounter),
        )
        bcard_clauses += add_cnf(
            solver,
            CardEnc.atmost(lits=bedges, bound=b_hi, vpool=pool, encoding=EncType.seqcounter),
        )

        lex_clauses = add_lex_B_cross(solver, edge, pool)

        b_local = 0
        for vs in itertools.combinations(B, 4):
            solver.add_clause(clause_k4(vs, edge))
            b_local += 1
        for vs in itertools.combinations(B, 5):
            solver.add_clause([edge[x][y] for x, y in itertools.combinations(vs, 2)])
            b_local += 1

        rng = random.Random(args.seed + 1009 * raw_index)
        phases = []
        b_density = ((b_lo + b_hi) / 2) / len(bedges)
        for i in range(N):
            for j in range(i + 1, N):
                x = edge[i][j]
                val = fixed.get(x)
                if val is None:
                    if i in B and j in B:
                        val = rng.random() < b_density
                    elif (i in A and j in B) or (i in B and j in A):
                        val = rng.random() < 0.23
                    else:
                        val = False
                phases.append(x if val else -x)
        solver.set_phases(phases)

        summary.update(
            degree_clauses=degree_clauses,
            b_cardinality_clauses=bcard_clauses,
            b_local_clauses=b_local,
            lex_clauses=lex_clauses,
            max_var=pool.top,
        )
        print("BRANCH " + json.dumps(summary, sort_keys=True), flush=True)

        for iteration in range(1, args.max_iterations + 1):
            if not solver.solve():
                summary.update(
                    status="UNSAT",
                    iterations=iteration - 1,
                    learned_ramsey_clauses=learned,
                    elapsed_seconds=round(time.monotonic() - started, 6),
                )
                args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
                print("RESULT " + json.dumps(summary, sort_keys=True), flush=True)
                return 20

            rows = rows_from_model(solver.get_model(), edge)
            k4, i6 = violations(rows, args.separator_cap)
            if not k4 and not i6:
                deg = [row.count("1") for row in rows]
                if min(deg) < 11 or max(deg) > 12 or deg[0] != 12:
                    raise RuntimeError(f"degree check failed: {deg}")
                args.output.write_text(json.dumps({"adjacency": rows}, indent=2) + "\n")
                summary.update(
                    status="SAT",
                    iterations=iteration,
                    learned_ramsey_clauses=learned,
                    elapsed_seconds=round(time.monotonic() - started, 6),
                    degree_min=min(deg),
                    degree_max=max(deg),
                    b_edges=sum(rows[u][v] == "1" for u, v in itertools.combinations(B, 2)),
                )
                args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
                print("RESULT " + json.dumps(summary, sort_keys=True), flush=True)
                return 0

            added = 0
            for kind, bads in ((4, k4), (6, i6)):
                for vs in bads:
                    key = (kind, vs)
                    if key in seen:
                        continue
                    seen.add(key)
                    solver.add_clause(clause_k4(vs, edge) if kind == 4 else clause_i6(vs, edge))
                    added += 1
            if not added:
                raise RuntimeError("violating model yielded no new Ramsey separator")
            learned += added
            if iteration <= 10 or iteration % 25 == 0:
                print(
                    f"iter={iteration} k4={len(k4)} i6={len(i6)} added={added} "
                    f"learned={learned} elapsed={time.monotonic()-started:.2f}s",
                    flush=True,
                )

    summary.update(
        status="ITERATION_LIMIT",
        iterations=args.max_iterations,
        learned_ramsey_clauses=learned,
        elapsed_seconds=round(time.monotonic() - started, 6),
    )
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return 30


def self_test() -> None:
    rng = random.Random(20261028)
    for n in range(4, 9):
        for _ in range(20):
            rows = [["0"] * n for _ in range(n)]
            for i in range(n):
                for j in range(i + 1, n):
                    if rng.random() < 0.4:
                        rows[i][j] = rows[j][i] = "1"
            srows = ["".join(r) for r in rows]
            adj = masks_from_rows(srows)
            for k in range(2, min(4, n) + 1):
                got = set(enumerate_cliques(adj, k))
                want = {
                    vs for vs in itertools.combinations(range(n), k)
                    if all(srows[a][b] == "1" for a, b in itertools.combinations(vs, 2))
                }
                assert got == want, (n, k, got ^ want)
    print("d12-catalog-lazy self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    s = sub.add_parser("solve")
    s.add_argument("--catalog", type=Path, required=True)
    s.add_argument("--edge-count", type=int, required=True)
    s.add_argument("--ordinal", type=int, required=True)
    s.add_argument("--solver", default="cadical195")
    s.add_argument("--seed", type=int, default=20261028)
    s.add_argument("--max-iterations", type=int, default=100000)
    s.add_argument("--separator-cap", type=int, default=20000)
    s.add_argument("--output", type=Path, default=Path("candidate.json"))
    s.add_argument("--summary", type=Path, default=Path("summary.json"))
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    if not 23 <= args.edge_count <= 29:
        ap.error("--edge-count must be 23..29 for a feasible D=12 branch")
    return solve_one(args)


if __name__ == "__main__":
    raise SystemExit(main())
