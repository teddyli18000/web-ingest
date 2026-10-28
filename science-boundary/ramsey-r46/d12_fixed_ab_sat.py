#!/usr/bin/env python3
"""Exact cross-edge SAT for a fixed degree-12 neighborhood/antineighborhood pair.

Fix a distinguished vertex v of degree 12, A=N(v) (12 vertices), and B
(the 23 non-neighbours). A and B are supplied as graph6 records. Once A and
B are fixed, the only unknowns are the 12*23=276 A--B cross edges.

The encoding is complete: configurable full-graph degree bounds plus every
mixed K4 and mixed independent-6 obstruction are encoded statically. A SAT
model is therefore a complete 36-vertex Ramsey(4,6) certificate. For the
maximum-degree-12 branch use --min-degree 11 --max-degree 12; for the general
R(4,6,36) structural range use 11..17.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
import tarfile
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

NA, NB = 12, 23


def decode_graph6(s: str) -> tuple[list[int], int]:
    s = s.strip()
    if s.startswith(">>graph6<<"):
        s = s[len(">>graph6<<") :]
    if not s:
        raise ValueError("empty graph6 record")
    if ord(s[0]) == 126:
        raise ValueError("only short graph6 records are supported")
    n = ord(s[0]) - 63
    if not 0 <= n <= 62:
        raise ValueError("invalid graph6 order")
    need = n * (n - 1) // 2
    bits: list[int] = []
    for ch in s[1:]:
        v = ord(ch) - 63
        if not 0 <= v < 64:
            raise ValueError("invalid graph6 character")
        bits.extend((v >> k) & 1 for k in range(5, -1, -1))
        if len(bits) >= need:
            break
    if len(bits) < need:
        raise ValueError("truncated graph6 record")
    adj = [0] * n
    e = 0
    p = 0
    for j in range(1, n):
        for i in range(j):
            if bits[p]:
                adj[i] |= 1 << j
                adj[j] |= 1 << i
                e += 1
            p += 1
    return adj, e


def iter_g6(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="ascii") as f:
        for raw, line in enumerate(f):
            s = line.strip()
            if not s or (s.startswith(">>") and not s.startswith(">>graph6<<")):
                continue
            yield raw, s, *decode_graph6(s)


def extract_tar_stratum(archive: Path, n: int, edges: int, out: Path) -> int:
    found: list[str] = []
    with tarfile.open(archive, "r:gz") as tf:
        for info in tf.getmembers():
            if not info.isfile():
                continue
            f = tf.extractfile(info)
            if f is None:
                continue
            for line_no, raw in enumerate(f, 1):
                try:
                    s = raw.decode("ascii").strip()
                except UnicodeDecodeError as exc:
                    raise ValueError(f"{info.name}:{line_no}: non-ASCII") from exc
                if not s or (s.startswith(">>") and not s.startswith(">>graph6<<")):
                    continue
                adj, e = decode_graph6(s)
                if len(adj) == n and e == edges:
                    found.append(s)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(found) + ("\n" if found else ""), encoding="ascii")
    print(json.dumps({"n": n, "edges": edges, "count": len(found), "out": str(out)}, sort_keys=True))
    return len(found)


def extract_g6_stratum(inp: Path, n: int, edges: int, out: Path) -> int:
    found = []
    for _, s, adj, e in iter_g6(inp):
        if len(adj) == n and e == edges:
            found.append(s)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(found) + ("\n" if found else ""), encoding="ascii")
    print(json.dumps({"n": n, "edges": edges, "count": len(found), "out": str(out)}, sort_keys=True))
    return len(found)


def select_record(path: Path, ordinal: int, expected_n: int) -> tuple[str, list[int], int]:
    seen = 0
    for _, s, adj, e in iter_g6(path):
        if len(adj) != expected_n:
            continue
        if seen == ordinal:
            return s, adj, e
        seen += 1
    raise IndexError(f"ordinal {ordinal} outside {seen} records in {path}")


def is_clique(adj: list[int], vs: tuple[int, ...]) -> bool:
    return all((adj[u] >> v) & 1 for u, v in itertools.combinations(vs, 2))


def is_independent(adj: list[int], vs: tuple[int, ...]) -> bool:
    return all(not ((adj[u] >> v) & 1) for u, v in itertools.combinations(vs, 2))


def subsets(adj: list[int], k: int, edge_value: bool) -> list[tuple[int, ...]]:
    pred = is_clique if edge_value else is_independent
    return [vs for vs in itertools.combinations(range(len(adj)), k) if pred(adj, vs)]


def validate_A(adj: list[int]) -> None:
    if len(adj) != NA:
        raise ValueError(f"A n={len(adj)} != {NA}")
    if subsets(adj, 3, True):
        raise ValueError("A contains a triangle")
    if subsets(adj, 6, False):
        raise ValueError("A contains an independent 6-set")


def validate_B(adj: list[int]) -> None:
    if len(adj) != NB:
        raise ValueError(f"B n={len(adj)} != {NB}")
    if subsets(adj, 4, True):
        raise ValueError("B contains a K4")
    if subsets(adj, 5, False):
        raise ValueError("B contains an independent 5-set")


def degrees(adj: list[int]) -> list[int]:
    return [m.bit_count() for m in adj]


def add_cnf(solver: Solver, cnf) -> int:
    for clause in cnf.clauses:
        solver.add_clause(clause)
    return len(cnf.clauses)


def cross_bounds(base_degree: int, cross_slots: int, min_degree: int, max_degree: int) -> tuple[int, int] | None:
    if base_degree > max_degree or base_degree + cross_slots < min_degree:
        return None
    lo = max(0, min_degree - base_degree)
    hi = min(cross_slots, max_degree - base_degree)
    if lo > hi:
        return None
    return lo, hi


def solve_pair(args) -> int:
    if not 0 <= args.min_degree <= args.max_degree <= 35:
        raise ValueError((args.min_degree, args.max_degree))
    ag6, A, ae = select_record(args.a_catalog, args.a_ordinal, NA)
    bg6, B, be = select_record(args.b_catalog, args.b_ordinal, NB)
    validate_A(A)
    validate_B(B)
    if args.a_edges is not None and ae != args.a_edges:
        raise ValueError((ae, args.a_edges))
    if args.b_edges is not None and be != args.b_edges:
        raise ValueError((be, args.b_edges))

    da, db = degrees(A), degrees(B)
    # v contributes one fixed edge to each A vertex and zero to each B vertex.
    abounds = [cross_bounds(1 + d, NB, args.min_degree, args.max_degree) for d in da]
    bbounds = [cross_bounds(d, NA, args.min_degree, args.max_degree) for d in db]
    if any(z is None for z in abounds):
        return write_unsat(args, ag6, bg6, ae, be, "A degree range impossible", 0, {})
    if any(z is None for z in bbounds):
        return write_unsat(args, ag6, bg6, ae, be, "B degree range impossible", 0, {})

    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    counts = {
        "degree": 0,
        "k4_1a3b": 0,
        "k4_2a2b": 0,
        "i6_5a1b": 0,
        "i6_4a2b": 0,
        "i6_3a3b": 0,
        "i6_2a4b": 0,
    }
    start = time.monotonic()
    with Solver(name=args.solver) as s:
        for a in range(NA):
            lo, hi = abounds[a]
            row = x[a]
            if lo:
                counts["degree"] += add_cnf(s, CardEnc.atleast(row, lo, vpool=pool, encoding=EncType.seqcounter))
            if hi < len(row):
                counts["degree"] += add_cnf(s, CardEnc.atmost(row, hi, vpool=pool, encoding=EncType.seqcounter))
        for b in range(NB):
            lo, hi = bbounds[b]
            col = [x[a][b] for a in range(NA)]
            if lo:
                counts["degree"] += add_cnf(s, CardEnc.atleast(col, lo, vpool=pool, encoding=EncType.seqcounter))
            if hi < len(col):
                counts["degree"] += add_cnf(s, CardEnc.atmost(col, hi, vpool=pool, encoding=EncType.seqcounter))

        b_tri = subsets(B, 3, True)
        a_edges = subsets(A, 2, True)
        b_edges = subsets(B, 2, True)
        a_i5 = subsets(A, 5, False)
        a_i4 = subsets(A, 4, False)
        b_non = subsets(B, 2, False)
        a_i3 = subsets(A, 3, False)
        b_i3 = subsets(B, 3, False)
        a_non = subsets(A, 2, False)
        b_i4 = subsets(B, 4, False)

        for a in range(NA):
            for bs in b_tri:
                s.add_clause([-x[a][b] for b in bs])
                counts["k4_1a3b"] += 1
        for aa in a_edges:
            for bb in b_edges:
                s.add_clause([-x[a][b] for a in aa for b in bb])
                counts["k4_2a2b"] += 1
        for aa in a_i5:
            for b in range(NB):
                s.add_clause([x[a][b] for a in aa])
                counts["i6_5a1b"] += 1
        for aa in a_i4:
            for bb in b_non:
                s.add_clause([x[a][b] for a in aa for b in bb])
                counts["i6_4a2b"] += 1
        for aa in a_i3:
            for bb in b_i3:
                s.add_clause([x[a][b] for a in aa for b in bb])
                counts["i6_3a3b"] += 1
        for aa in a_non:
            for bb in b_i4:
                s.add_clause([x[a][b] for a in aa for b in bb])
                counts["i6_2a4b"] += 1

        sat = s.solve()
        elapsed = time.monotonic() - start
        if not sat:
            return write_unsat(args, ag6, bg6, ae, be, "SAT solver UNSAT", elapsed, counts)
        model = set(l for l in s.get_model() if l > 0)

    rows = [["0"] * 36 for _ in range(36)]
    for a in range(NA):
        u = 1 + a
        rows[0][u] = rows[u][0] = "1"
    for i in range(NA):
        for j in range(i + 1, NA):
            if (A[i] >> j) & 1:
                rows[1 + i][1 + j] = rows[1 + j][1 + i] = "1"
    for i in range(NB):
        for j in range(i + 1, NB):
            if (B[i] >> j) & 1:
                rows[13 + i][13 + j] = rows[13 + j][13 + i] = "1"
    for a in range(NA):
        for b in range(NB):
            if x[a][b] in model:
                rows[1 + a][13 + b] = rows[13 + b][1 + a] = "1"
    srows = ["".join(r) for r in rows]
    verify_full(srows, args.min_degree, args.max_degree)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"adjacency": srows}, indent=2) + "\n")
    result = base_result(args, ag6, bg6, ae, be, elapsed, counts)
    result.update(status="SAT", degree_sequence=[r.count("1") for r in srows])
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RESULT " + json.dumps(result, sort_keys=True))
    return 0


def verify_full(rows: list[str], min_degree: int = 11, max_degree: int = 12) -> None:
    if len(rows) != 36 or any(len(r) != 36 for r in rows):
        raise AssertionError("bad adjacency dimensions")
    for i in range(36):
        if rows[i][i] != "0":
            raise AssertionError("self edge")
        for j in range(i + 1, 36):
            if rows[i][j] != rows[j][i]:
                raise AssertionError("asymmetric adjacency")
    for vs in itertools.combinations(range(36), 4):
        if all(rows[u][v] == "1" for u, v in itertools.combinations(vs, 2)):
            raise AssertionError(f"K4 {vs}")
    for vs in itertools.combinations(range(36), 6):
        if all(rows[u][v] == "0" for u, v in itertools.combinations(vs, 2)):
            raise AssertionError(f"I6 {vs}")
    ds = [r.count("1") for r in rows]
    if min(ds) < min_degree or max(ds) > max_degree:
        raise AssertionError(ds)


def base_result(args, ag6, bg6, ae, be, elapsed, counts):
    return {
        "a_ordinal": args.a_ordinal,
        "b_ordinal": args.b_ordinal,
        "a_graph6": ag6,
        "b_graph6": bg6,
        "a_edges": ae,
        "b_edges": be,
        "min_degree": args.min_degree,
        "max_degree": args.max_degree,
        "solver": args.solver,
        "elapsed_seconds": round(elapsed, 6),
        "clause_counts": counts,
    }


def write_unsat(args, ag6, bg6, ae, be, reason, elapsed, counts) -> int:
    result = base_result(args, ag6, bg6, ae, be, elapsed, counts)
    result.update(status="UNSAT", reason=reason)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("RESULT " + json.dumps(result, sort_keys=True))
    return 20


def self_test() -> None:
    empty5, e0 = decode_graph6("D??")
    assert len(empty5) == 5 and e0 == 0
    adj = [0] * 4
    for u, v in ((0, 1), (1, 2), (2, 3)):
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    assert subsets(adj, 2, True) == [(0, 1), (1, 2), (2, 3)]
    assert (0, 2) in subsets(adj, 2, False)
    assert cross_bounds(5, 12, 11, 17) == (6, 12)
    assert cross_bounds(18, 12, 11, 17) is None
    print("d12 fixed-A/B SAT self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("extract-tar")
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--edges", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("extract-g6")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--n", type=int, required=True)
    p.add_argument("--edges", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("solve")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--a-ordinal", type=int, required=True)
    p.add_argument("--b-ordinal", type=int, required=True)
    p.add_argument("--a-edges", type=int)
    p.add_argument("--b-edges", type=int)
    p.add_argument("--min-degree", type=int, default=11)
    p.add_argument("--max-degree", type=int, default=12)
    p.add_argument("--solver", default="cadical195")
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
        return 0
    if args.cmd == "extract-tar":
        extract_tar_stratum(args.archive, args.n, args.edges, args.out)
        return 0
    if args.cmd == "extract-g6":
        extract_g6_stratum(args.input, args.n, args.edges, args.out)
        return 0
    return solve_pair(args)


if __name__ == "__main__":
    raise SystemExit(main())
