#!/usr/bin/env python3
"""Rigorous cross-edge relaxation for the lucky degree-16 branch of R(4,6,36).

Fix a lucky vertex v of degree 16 and one complete R(3,6,16) neighbourhood
A.  Let B be the 19 antineighbours.  We deliberately DO NOT construct B.
Instead we keep only necessary consequences that every R(4,5,19) B and every
valid A--B gluing must satisfy.  If this relaxation is UNSAT, the fixed A type
is rigorously impossible; SAT merely means that A survives this cheap filter.

Variables x[a,b] are the 16*19 cross edges.  Necessary constraints:

* every B column hits every independent 5-set of A (otherwise I6);
* for every independent 4-set P of A, at most 3 B columns miss P.  Those
  columns would have to form a clique in B, and B is K4-free;
* for every independent 3-set P of A, at most 8 B columns miss P.  Their
  induced B graph has alpha <= 2 and omega <= 3, hence has at most 8 vertices
  because R(3,4)=9;
* for every edge uv of A, at most 4 B columns are adjacent to both u and v.
  Those B vertices must form an independent set in B, and alpha(B) <= 4;
* every A vertex has full degree 11..17, giving exact row cardinality bounds.

The encoding contains no assumptions about an unpublished complete B
catalogue and no heuristic constraints.  It is therefore a sound prefilter
before the much more expensive full lucky-d16 SAT gluing.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

NA, NB = 16, 19


def decode_graph6(line: str) -> tuple[list[int], int]:
    s = line.strip()
    if s.startswith(">>graph6<<"):
        s = s[len(">>graph6<<") :]
    if not s:
        raise ValueError("empty graph6 record")
    if ord(s[0]) == 126:
        raise ValueError("only short graph6 records are supported")
    n = ord(s[0]) - 63
    need = n * (n - 1) // 2
    bits: list[int] = []
    for ch in s[1:]:
        z = ord(ch) - 63
        if not 0 <= z < 64:
            raise ValueError("invalid graph6 character")
        bits.extend((z >> k) & 1 for k in range(5, -1, -1))
        if len(bits) >= need:
            break
    if len(bits) < need:
        raise ValueError("truncated graph6")
    adj = [0] * n
    p = 0
    edges = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
                edges += 1
            p += 1
    return adj, edges


def iter_catalog(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as f:
        ordinal = 0
        for raw_index, line in enumerate(f):
            s = line.strip()
            if not s or (s.startswith(">>") and not s.startswith(">>graph6<<")):
                continue
            adj, edges = decode_graph6(s)
            if len(adj) != NA:
                continue
            yield ordinal, raw_index, s, adj, edges
            ordinal += 1


def independent_sets(adj: list[int], k: int) -> list[tuple[int, ...]]:
    out = []
    for vs in itertools.combinations(range(len(adj)), k):
        if all(not ((adj[u] >> v) & 1) for u, v in itertools.combinations(vs, 2)):
            out.append(vs)
    return out


def validate_A(adj: list[int]) -> None:
    if len(adj) != NA:
        raise ValueError(f"expected {NA} vertices")
    for i in range(NA):
        for j in range(i + 1, NA):
            if not ((adj[i] >> j) & 1):
                continue
            if adj[i] & adj[j]:
                raise ValueError("catalogue A contains a triangle")
    if independent_sets(adj, 6):
        raise ValueError("catalogue A contains an independent 6-set")


def add_cnf(solver: Solver, cnf) -> int:
    for clause in cnf.clauses:
        solver.add_clause(clause)
    return len(cnf.clauses)


def add_and_indicator(solver: Solver, pool: IDPool, literals: list[int]) -> int:
    """Return z with z <-> AND(literals), adding a propagation-complete encoding."""
    z = pool.id()
    for lit in literals:
        solver.add_clause([-z, lit])
    solver.add_clause([z] + [-lit for lit in literals])
    return z


def solve_relaxation(adj: list[int], edges: int, solver_name: str) -> tuple[bool, dict]:
    validate_A(adj)
    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    i3 = independent_sets(adj, 3)
    i4 = independent_sets(adj, 4)
    i5 = independent_sets(adj, 5)
    aedges = [(u, v) for u in range(NA) for v in range(u + 1, NA) if (adj[u] >> v) & 1]
    counts = {
        "row_cardinality": 0,
        "hit_i5": 0,
        "miss_i4_indicators": 0,
        "miss_i4_cardinality": 0,
        "miss_i3_indicators": 0,
        "miss_i3_cardinality": 0,
        "common_edge_indicators": 0,
        "common_edge_cardinality": 0,
    }
    started = time.monotonic()
    with Solver(name=solver_name) as s:
        # For a in A, deg_G(a)=1+deg_A(a)+deg_cross(a) lies in 11..17.
        for a in range(NA):
            da = adj[a].bit_count()
            lo = max(0, 10 - da)
            hi = min(NB, 16 - da)
            if lo > hi:
                return False, {"reason": "row degree range impossible", "elapsed_seconds": 0.0, "counts": counts}
            if lo:
                counts["row_cardinality"] += add_cnf(
                    s, CardEnc.atleast(x[a], lo, vpool=pool, encoding=EncType.seqcounter)
                )
            if hi < NB:
                counts["row_cardinality"] += add_cnf(
                    s, CardEnc.atmost(x[a], hi, vpool=pool, encoding=EncType.seqcounter)
                )

        # Every B vertex must meet every independent 5-set of A.
        for p in i5:
            for b in range(NB):
                s.add_clause([x[a][b] for a in p])
                counts["hit_i5"] += 1

        # Missing an independent 4-set forces a clique in B, hence <= 3.
        for p in i4:
            zs = []
            for b in range(NB):
                zs.append(add_and_indicator(s, pool, [-x[a][b] for a in p]))
                counts["miss_i4_indicators"] += len(p) + 1
            counts["miss_i4_cardinality"] += add_cnf(
                s, CardEnc.atmost(zs, 3, vpool=pool, encoding=EncType.seqcounter)
            )

        # Missing an independent 3-set leaves alpha(B[S])<=2 and omega<=3;
        # R(3,4)=9 therefore gives |S|<=8.
        for p in i3:
            zs = []
            for b in range(NB):
                zs.append(add_and_indicator(s, pool, [-x[a][b] for a in p]))
                counts["miss_i3_indicators"] += len(p) + 1
            counts["miss_i3_cardinality"] += add_cnf(
                s, CardEnc.atmost(zs, 8, vpool=pool, encoding=EncType.seqcounter)
            )

        # Common B neighbours of an A-edge must be independent in B, hence <=4.
        for u, v in aedges:
            zs = []
            for b in range(NB):
                zs.append(add_and_indicator(s, pool, [x[u][b], x[v][b]]))
                counts["common_edge_indicators"] += 3
            counts["common_edge_cardinality"] += add_cnf(
                s, CardEnc.atmost(zs, 4, vpool=pool, encoding=EncType.seqcounter)
            )

        sat = s.solve()
    return sat, {
        "reason": "survives cross relaxation" if sat else "cross relaxation UNSAT",
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "variables": pool.top,
        "counts": counts,
        "i3": len(i3),
        "i4": len(i4),
        "i5": len(i5),
        "a_edges": edges,
    }


def self_test() -> None:
    # Test graph6 decoder on the empty 5-vertex graph.
    adj, e = decode_graph6("D??")
    assert len(adj) == 5 and e == 0

    # Exhaustively validate AND indicator semantics with PySAT itself.
    for n in range(1, 5):
        for bits in itertools.product((False, True), repeat=n):
            with Solver(name="cadical195") as s:
                pool = IDPool(start_from=n + 1)
                z = add_and_indicator(s, pool, list(range(1, n + 1)))
                for i, bit in enumerate(bits, 1):
                    s.add_clause([i if bit else -i])
                s.add_clause([z if all(bits) else -z])
                assert s.solve(), (n, bits)
                s.add_clause([-z if all(bits) else z])
                assert not s.solve(), (n, bits, "wrong z remained possible")
    print("d16 cross-capacity SAT self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("run")
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--shards", type=int, required=True)
    p.add_argument("--solver", default="cadical195")
    p.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    if not 0 <= args.shard < args.shards:
        ap.error("invalid shard")

    rows = []
    for ordinal, raw_index, g6, adj, edges in iter_catalog(args.catalog):
        if ordinal % args.shards != args.shard:
            continue
        sat, detail = solve_relaxation(adj, edges, args.solver)
        row = {
            "ordinal": ordinal,
            "raw_index": raw_index,
            "graph6": g6,
            "status": "SURVIVES" if sat else "UNSAT",
            **detail,
        }
        rows.append(row)
        print("RESULT " + json.dumps({k: v for k, v in row.items() if k not in {"graph6", "counts"}}, sort_keys=True), flush=True)

    result = {
        "method": "lucky-d16 cross-edge necessary-condition SAT relaxation",
        "logical_scope": "fixed complete R(3,6,16) neighbourhood A; B existence relaxed",
        "shard": args.shard,
        "shards": args.shards,
        "tested": len(rows),
        "unsat": sum(r["status"] == "UNSAT" for r in rows),
        "survivors": sum(r["status"] == "SURVIVES" for r in rows),
        "survivor_ordinals": [r["ordinal"] for r in rows if r["status"] == "SURVIVES"],
        "rows": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("SUMMARY " + json.dumps({k: v for k, v in result.items() if k not in {"rows", "survivor_ordinals"}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
