#!/usr/bin/env python3
"""Degree-17 SAT v4: add the lucky-vertex B-edge window to v3.

A hypothetical R(4,6,36) graph has a lucky vertex v satisfying the
McKay--Radziszowski inequality

    2 e(B) <= d(v) (36 - 2 d(v)) + 2 e(A),

where A=G[N(v)] and B=G[V \ (N(v) union {v})].  In the d(v)=17 branch this is

    e(B) <= e(A) + 17.

Moreover B is an R(4,5,18) graph, whose exact minimum edge count is 50.
The seven complete R(3,6,17) catalogue representatives have e(A)=40..42,
so the lucky branch forces only 50 <= e(B) <= 57..59.

This wrapper appends that exact cardinality window to the existing v3 static
encoding (full Ramsey clauses, 11..17 degree bounds, B-row lex ordering, and
the sound Aut(A) first-row lex leader).  The new constraint is the substantive
change from the earlier degree-17 campaigns, which did not exploit lucky-edge
information and timed out on hard branches.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import degree17_static_sat as base
import degree17_static_sat_v2 as v2
import degree17_static_sat_v3 as v3

B = tuple(range(18, 36))
B_EDGE_MIN = 50


def edge_count(rows: list[str]) -> int:
    return sum(row.count("1") for row in rows) // 2


def append_b_edge_window(path: Path, neighborhood: list[str]) -> dict[str, int]:
    edge, _ = base.edge_variables()
    a_edges = edge_count(neighborhood)
    b_edge_max = a_edges + 17
    bedges = [edge[u][v] for u, v in itertools.combinations(B, 2)]

    with path.open("r", encoding="ascii") as f:
        header = f.readline()
    parts = header.split()
    if len(parts) != 4 or parts[:2] != ["p", "cnf"]:
        raise ValueError("unexpected DIMACS header")
    base_vars, base_clauses = map(int, parts[2:])
    next_var = base_vars + 1

    upper, next_var = v2.atmost_seq(bedges, b_edge_max, next_var)
    # sum(bedges) >= B_EDGE_MIN iff sum(not bedges) <= |E(K18)|-B_EDGE_MIN.
    lower, next_var = v2.atmost_seq(
        [-x for x in bedges], len(bedges) - B_EDGE_MIN, next_var
    )
    clauses = upper + lower
    final_vars = next_var - 1
    final_clauses = base_clauses + len(clauses)

    with path.open("a", encoding="ascii", buffering=1024 * 1024) as out:
        for clause in clauses:
            out.write(" ".join(map(str, clause)) + " 0\n")

    header_fmt = "p cnf {vars:10d} {clauses:12d}\n"
    final_header = header_fmt.format(vars=final_vars, clauses=final_clauses)
    if len(final_header) != len(header):
        raise RuntimeError("DIMACS header width changed")
    with path.open("r+", encoding="ascii") as out:
        out.seek(0)
        out.write(final_header)

    return {
        "a_edges": a_edges,
        "b_edge_min": B_EDGE_MIN,
        "b_edge_max": b_edge_max,
        "lucky_edge_aux_variables": final_vars - base_vars,
        "lucky_edge_clauses": len(clauses),
        "variables": final_vars,
        "clauses": final_clauses,
    }


def _range_cnf(lits: list[int], lo: int, hi: int) -> list[list[int]]:
    next_var = max((abs(x) for x in lits), default=0) + 1
    upper, next_var = v2.atmost_seq(lits, hi, next_var)
    lower, _ = v2.atmost_seq([-x for x in lits], len(lits) - lo, next_var)
    return upper + lower


def self_test() -> None:
    # Exhaustively verify projection of the range encoding on small inputs.
    for n in range(1, 7):
        lits = list(range(1, n + 1))
        for lo in range(n + 1):
            for hi in range(lo, n + 1):
                clauses = _range_cnf(lits, lo, hi)
                for bits in itertools.product((False, True), repeat=n):
                    fixed = {i + 1: bits[i] for i in range(n)}
                    got = v2._sat_with_fixed(clauses, fixed)
                    want = lo <= sum(bits) <= hi
                    if got != want:
                        raise AssertionError((n, lo, hi, bits, got, want))
    print("degree17-static-v4 lucky-edge self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path)
    ap.add_argument("--index", type=int)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.catalog is None or args.index is None or args.output is None:
        ap.error("--catalog, --index and --output are required unless --self-test")

    catalog = base.load_catalog(args.catalog)
    if not 0 <= args.index < len(catalog):
        ap.error("--index must be 0..6")
    neighborhood = catalog[args.index]
    base_result = base.generate(args.output, neighborhood, args.index)
    degree_result = v2.append_degree_bounds(args.output, neighborhood)
    aut_result = v3.append_aut_leader(args.output, neighborhood)
    lucky_result = append_b_edge_window(args.output, neighborhood)
    result = {
        **base_result,
        **degree_result,
        **aut_result,
        **lucky_result,
        "catalog_index": args.index,
        "path": str(args.output),
        "encoding": "degree17-v4-full-ramsey+degree11-17+lex+AutA+lucky-B-edge-window",
        "lucky_identity": "e(B) <= e(A)+17",
        "b_edge_min_source": "exact R(4,5,18) minimum = 50",
    }
    result.pop("degree_info", None)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
