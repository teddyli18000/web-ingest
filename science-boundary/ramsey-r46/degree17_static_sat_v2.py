#!/usr/bin/env python3
"""Strengthen degree17_static_sat.py with exact safe degree bounds 11..17.

The base encoder fixes a degree-17 vertex and one of the seven complete
(3,6,17) neighbourhood catalogue representatives, adds all residual Ramsey
clauses, and lexicographically orders the 18 unlabeled non-neighbours.

This wrapper adds propagation-friendly Sinz sequential-counter CNF for the
necessary global degree bounds 11 <= deg(v) <= 17.  Fixed edge values are
eliminated before the counters are built, so the counters are branch-specific.
The degree bounds are mathematical consequences of R(3,6)=18 and R(4,5)=25;
they do not remove any (4,6,36) solution.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import degree17_static_sat as base

N = 36
MIN_DEG = 11
MAX_DEG = 17


def atmost_seq(lits: list[int], k: int, next_var: int) -> tuple[list[list[int]], int]:
    """Sinz sequential-counter encoding of sum(lits) <= k.

    ``lits`` may contain positive or negative literals.  Auxiliary variables
    are existential, and the encoding is projection-equivalent to the stated
    cardinality constraint.
    """
    n = len(lits)
    if k < 0:
        return [[]], next_var
    if k >= n:
        return [], next_var
    if k == 0:
        return [[-lit] for lit in lits], next_var

    # s[i][j] for i=0..n-2 and j=0..k-1.
    s: list[list[int]] = []
    for _ in range(n - 1):
        row = list(range(next_var, next_var + k))
        next_var += k
        s.append(row)

    clauses: list[list[int]] = []
    clauses.append([-lits[0], s[0][0]])
    # These units are redundant but strengthen propagation and make the
    # intended prefix-count semantics explicit.
    for j in range(1, k):
        clauses.append([-s[0][j]])

    for i in range(1, n - 1):
        clauses.append([-lits[i], s[i][0]])
        clauses.append([-s[i - 1][0], s[i][0]])
        for j in range(1, k):
            clauses.append([-lits[i], -s[i - 1][j - 1], s[i][j]])
            clauses.append([-s[i - 1][j], s[i][j]])

    for i in range(1, n):
        clauses.append([-lits[i], -s[i - 1][k - 1]])
    return clauses, next_var


def degree_clauses(
    edge: list[list[int]], fixed: dict[int, bool], start_var: int
) -> tuple[list[list[int]], int, list[dict[str, int]]]:
    clauses: list[list[int]] = []
    next_var = start_var
    info: list[dict[str, int]] = []
    for v in range(N):
        free: list[int] = []
        fixed_true = 0
        for u in range(N):
            if u == v:
                continue
            var = edge[v][u]
            val = fixed.get(var)
            if val is None:
                free.append(var)
            elif val:
                fixed_true += 1

        lo = MIN_DEG - fixed_true
        hi = MAX_DEG - fixed_true
        if lo < 0:
            lo = 0
        if hi > len(free):
            hi = len(free)
        if lo > hi:
            raise ValueError(f"fixed branch makes degree bounds impossible at vertex {v}")

        upper, next_var = atmost_seq(free, hi, next_var)
        # sum(free) >= lo  <=>  sum(not free) <= len(free)-lo.
        lower, next_var = atmost_seq([-x for x in free], len(free) - lo, next_var)
        clauses.extend(upper)
        clauses.extend(lower)
        info.append(
            {
                "vertex": v,
                "fixed_true": fixed_true,
                "free": len(free),
                "residual_min": lo,
                "residual_max": hi,
                "clauses": len(upper) + len(lower),
            }
        )
    return clauses, next_var, info


def append_degree_bounds(path: Path, neighborhood: list[str]) -> dict[str, object]:
    edge, _ = base.edge_variables()
    fixed = base.fixed_edges(edge, neighborhood)

    with path.open("r", encoding="ascii") as f:
        header = f.readline()
    parts = header.split()
    if len(parts) != 4 or parts[:2] != ["p", "cnf"]:
        raise ValueError("unexpected DIMACS header")
    base_vars, base_clauses = map(int, parts[2:])

    clauses, next_var, degree_info = degree_clauses(edge, fixed, base_vars + 1)
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
        "base_variables": base_vars,
        "base_clauses": base_clauses,
        "variables": final_vars,
        "clauses": final_clauses,
        "degree_aux_variables": final_vars - base_vars,
        "degree_clauses": len(clauses),
        "degree_info": degree_info,
    }


def _sat_with_fixed(clauses: list[list[int]], fixed: dict[int, bool]) -> bool:
    """Tiny DPLL used only for exhaustive encoder self-tests."""
    def rec(assign: dict[int, bool]) -> bool:
        while True:
            changed = False
            for clause in clauses:
                satisfied = False
                unknown: list[int] = []
                for lit in clause:
                    v = abs(lit)
                    if v in assign:
                        if assign[v] == (lit > 0):
                            satisfied = True
                            break
                    else:
                        unknown.append(lit)
                if satisfied:
                    continue
                if not unknown:
                    return False
                if len(unknown) == 1:
                    lit = unknown[0]
                    v, val = abs(lit), lit > 0
                    old = assign.get(v)
                    if old is not None and old != val:
                        return False
                    if old is None:
                        assign[v] = val
                        changed = True
            if not changed:
                break
        branch = None
        for clause in clauses:
            if any(abs(l) in assign and assign[abs(l)] == (l > 0) for l in clause):
                continue
            branch = next((abs(l) for l in clause if abs(l) not in assign), None)
            if branch is not None:
                break
        if branch is None:
            return True
        for val in (False, True):
            child = dict(assign)
            child[branch] = val
            if rec(child):
                return True
        return False

    return rec(dict(fixed))


def self_test() -> None:
    # Exhaustively project small counters onto their input variables.
    for n in range(1, 7):
        lits = list(range(1, n + 1))
        for k in range(0, n + 1):
            clauses, _ = atmost_seq(lits, k, n + 1)
            for bits in itertools.product((False, True), repeat=n):
                fixed = {i + 1: bits[i] for i in range(n)}
                got = _sat_with_fixed(clauses, fixed)
                want = sum(bits) <= k
                if got != want:
                    raise AssertionError((n, k, bits, got, want))
    print("degree17-static-v2 self-test ok")


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
    base_result = base.generate(args.output, catalog[args.index], args.index)
    degree_result = append_degree_bounds(args.output, catalog[args.index])
    result = {
        **base_result,
        **degree_result,
        "catalog_index": args.index,
        "path": str(args.output),
        "encoding": "static-full-ramsey+lex-B-cross+sequential-degree-11-17",
    }
    # Keep console output compact; per-vertex details remain derivable and are
    # not needed by the campaign collector.
    result.pop("degree_info", None)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
