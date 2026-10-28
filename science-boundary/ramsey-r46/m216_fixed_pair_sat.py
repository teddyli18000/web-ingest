#!/usr/bin/env python3
"""Exact fixed-pair SAT for the only possible 216-edge degree sequence.

The endpoint edge-sum relaxation forces every hypothetical 216-edge
Ramsey(4,6,36) graph to be 12-regular.  For any vertex x,
S(x)=12*12=144, hence the local edge identity gives

    e(B)-e(A)=216-144=72.

The exact extrema e(A)<=29 and e(B)>=101 force the unique A29/B101 pair.
All remaining freedom is the 12x23 cross-edge matrix.  Total degree 12 fixes
every row/column sum exactly, leaving a single complete SAT instance.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import d12_fixed_ab_sat as base
import m217_fixed_pair_sat as fixed

NA, NB = 12, 23


def add_cnf(s: Solver, cnf) -> int:
    for clause in cnf.clauses:
        s.add_clause(clause)
    return len(cnf.clauses)


def solve(args) -> int:
    ag6, A, bg6, B = fixed.load_pair(args.a_catalog, args.b_catalog)
    da, db = base.degrees(A), base.degrees(B)
    row_targets = [12 - 1 - da[a] for a in range(NA)]
    col_targets = [12 - db[b] for b in range(NB)]
    assert sum(row_targets) == sum(col_targets) == 74

    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    counts = {"degree_equals": 0}
    started = time.monotonic()
    with Solver(name=args.solver) as s:
        for a, target in enumerate(row_targets):
            counts["degree_equals"] += add_cnf(
                s, CardEnc.equals(x[a], target, vpool=pool, encoding=EncType.seqcounter)
            )
        for b, target in enumerate(col_targets):
            counts["degree_equals"] += add_cnf(
                s, CardEnc.equals([x[a][b] for a in range(NA)], target, vpool=pool, encoding=EncType.seqcounter)
            )
        counts.update(fixed.add_ramsey(s, x, A, B))
        sat = s.solve()
        elapsed = time.monotonic() - started
        result = {
            "campaign": "m216-fixed-A29-B101-12-regular",
            "solver": args.solver,
            "a_graph6": ag6,
            "b_graph6": bg6,
            "row_targets": row_targets,
            "col_targets": col_targets,
            "cross_edges": sum(row_targets),
            "clauses_by_kind": counts,
            "max_var": pool.top,
            "elapsed_seconds": round(elapsed, 6),
        }
        if not sat:
            result["status"] = "UNSAT"
            args.summary.parent.mkdir(parents=True, exist_ok=True)
            args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print("RESULT " + json.dumps(result, sort_keys=True))
            return 20
        model = s.get_model()

    rows = fixed.rows_from_model(A, B, x, model)
    base.verify_full(rows, 12, 12)
    deg = [r.count("1") for r in rows]
    assert deg == [12] * 36, deg
    assert sum(deg) // 2 == 216
    result.update(status="SAT", degree_sequence=deg)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.output.write_text(json.dumps({"adjacency": rows}, indent=2) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps(result, sort_keys=True))
    return 0


def self_test() -> None:
    # The exact arithmetic that identifies the unique local pair at m=216.
    assert 216 - 12 * 12 == 72
    assert 101 - 29 == 72
    print("m216 fixed-pair SAT self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("solve")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
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
