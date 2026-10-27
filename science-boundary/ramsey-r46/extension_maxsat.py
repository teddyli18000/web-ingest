#!/usr/bin/env python3
"""Exact MaxSAT ranking of the 37 known (4,6,35) graphs for one-vertex extension.

For each 35-vertex seed, choose the new vertex neighborhood that minimizes the
number of forbidden subgraphs involving the new vertex.  Every old triangle
contributes a soft clause forbidding adjacency to all three vertices; every old
independent 5-set contributes a soft clause requiring adjacency to at least one
of the five.  Since the old graph is already valid, the optimum MaxSAT cost is
exactly the minimum number of K4 / independent-6 violations in a frozen-core
36-vertex augmentation.

Requires python-sat.  Uses the source fetching/orientation logic in
extension_check.py and independently recounts the resulting violations.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

import extension_check as ext


def bits(mask: int) -> list[int]:
    out = []
    while mask:
        b = mask & -mask
        out.append(b.bit_length() - 1)
        mask ^= b
    return out


def clause_from_mask(mask: int, positive: bool) -> list[int]:
    return [(v + 1) if positive else -(v + 1) for v in bits(mask)]


def exact_cost(constraints: ext.Constraints, chosen: int) -> tuple[int, int, int]:
    k4 = sum(1 for tri in constraints.tris if tri & chosen == tri)
    ind6 = sum(1 for ind in constraints.ind5 if ind & chosen == 0)
    return k4 + ind6, k4, ind6


def optimize_one(name: str, text: str, sha256: str, solver: str) -> dict:
    started = time.monotonic()
    published = ext.parse_matrix(text)
    graph, orientation = ext.orient_r46(published)
    constraints = ext.build_constraints(graph)

    wcnf = WCNF()
    for tri in constraints.tris:
        wcnf.append(clause_from_mask(tri, positive=False), weight=1)
    for ind in constraints.ind5:
        wcnf.append(clause_from_mask(ind, positive=True), weight=1)

    with RC2(wcnf, solver=solver, adapt=True, exhaust=True, incr=True) as rc2:
        model = rc2.compute()
        optimum = rc2.cost
    if model is None:
        raise RuntimeError(f"MaxSAT unexpectedly returned no model for {name}")
    chosen = 0
    for lit in model:
        if 1 <= lit <= constraints.n:
            chosen |= 1 << (lit - 1)
    recounted, k4, ind6 = exact_cost(constraints, chosen)
    if recounted != optimum:
        raise RuntimeError(
            f"cost mismatch on {name}: rc2={optimum} exact={recounted}"
        )
    if optimum == 0 and not ext.verify_extension(graph, chosen):
        raise RuntimeError(f"zero-cost witness failed exact extension check on {name}")

    return {
        "name": name,
        "sha256": sha256,
        "orientation": orientation,
        "triangles": len(constraints.tris),
        "independent5": len(constraints.ind5),
        "optimum_conflicts": optimum,
        "k4_conflicts": k4,
        "independent6_conflicts": ind6,
        "new_degree": chosen.bit_count(),
        "neighbor_set": bits(chosen),
        "seconds": round(time.monotonic() - started, 6),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", default="g3")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    results = []
    for i in range(1, ext.N_PUBLISHED + 1):
        text, digest = ext.fetch_graph(i, args.timeout)
        row = optimize_one(f"h{i:04d}", text, digest, args.solver)
        results.append(row)
        print(json.dumps(row, sort_keys=True), flush=True)

    results.sort(key=lambda r: (r["optimum_conflicts"], r["k4_conflicts"], r["name"]))
    summary = {
        "graphs": len(results),
        "solver": args.solver,
        "best_optimum_conflicts": results[0]["optimum_conflicts"],
        "best_graphs": [
            r["name"]
            for r in results
            if r["optimum_conflicts"] == results[0]["optimum_conflicts"]
        ],
        "results": results,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(
        "SUMMARY "
        + json.dumps({k: v for k, v in summary.items() if k != "results"}, sort_keys=True),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
