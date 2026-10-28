#!/usr/bin/env python3
"""DIMACS backend for the exact symmetry-reduced lucky-d12 fixed pair.

The logical encoding is shared with d12_fixed_ab_sym_sat.py.  This module only
changes the backend: clauses are materialized as DIMACS so an independent
standalone solver (Kissat) can attack the same exact problem.  SAT models are
decoded from the first 276 cross-edge variables and independently verified as
full 36-vertex Ramsey(4,6) certificates before being written.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pysat.formula import IDPool

import d12_fixed_ab_sat as base
import d12_fixed_ab_sym_sat as sym

NA, NB = 12, 23


class ClauseSink:
    def __init__(self) -> None:
        self.clauses: list[list[int]] = []

    def add_clause(self, clause) -> None:
        self.clauses.append(list(clause))


def generate(a_catalog: Path, b_catalog: Path, mode: str, out: Path, meta: Path) -> dict:
    ag6, A, ae = base.select_record(a_catalog, 0, NA)
    bg6, B, be = base.select_record(b_catalog, 0, NB)
    base.validate_A(A); base.validate_B(B)
    if (ae, be) != (29, 101):
        raise ValueError((ae, be))

    use_a, use_b, sym_info = sym.symmetry_permutations(A, B, mode)
    x = [[a * NB + b + 1 for b in range(NB)] for a in range(NA)]
    pool = IDPool(start_from=NA * NB + 1)
    sink = ClauseSink()
    ramsey_counts = sym.add_all_constraints(sink, pool, x, A, B, 11, 17)
    flat = [x[a][b] for a in range(NA) for b in range(NB)]
    lex_aux = lex_clauses = 0
    for p in use_a:
        right = [x[p[a]][b] for a in range(NA) for b in range(NB)]
        a, c = sym.add_lex_leader(sink, pool, flat, right)
        lex_aux += a; lex_clauses += c
    for p in use_b:
        right = [x[a][p[b]] for a in range(NA) for b in range(NB)]
        a, c = sym.add_lex_leader(sink, pool, flat, right)
        lex_aux += a; lex_clauses += c
    sym_info.update(lex_aux_variables=lex_aux, lex_clauses=lex_clauses)

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="ascii", buffering=1024 * 1024) as f:
        f.write(f"p cnf {pool.top} {len(sink.clauses)}\n")
        for clause in sink.clauses:
            f.write(" ".join(map(str, clause)) + " 0\n")
    result = {
        "encoding": "fixed A29/B101 exact mixed Ramsey + degree11..17 + automorphism lex leaders",
        "backend": "DIMACS",
        "symmetry": mode,
        "variables": pool.top,
        "clauses": len(sink.clauses),
        "cross_variables": NA * NB,
        "a_graph6": ag6,
        "b_graph6": bg6,
        "a_edges": ae,
        "b_edges": be,
        "symmetry_info": sym_info,
        "ramsey_counts": ramsey_counts,
        "path": str(out),
    }
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return result


def parse_model(path: Path) -> set[int]:
    positive: set[int] = set()
    status = None
    for raw in path.read_text(encoding="ascii", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("s "):
            status = line
        if not line.startswith("v "):
            continue
        for tok in line.split()[1:]:
            try:
                lit = int(tok)
            except ValueError:
                continue
            if lit > 0:
                positive.add(lit)
    if status is None or "SATISFIABLE" not in status or "UNSATISFIABLE" in status:
        raise ValueError(f"model file does not contain SATISFIABLE status: {status}")
    return positive


def decode(a_catalog: Path, b_catalog: Path, solver_log: Path, output: Path) -> dict:
    _, A, ae = base.select_record(a_catalog, 0, NA)
    _, B, be = base.select_record(b_catalog, 0, NB)
    if (ae, be) != (29, 101):
        raise ValueError((ae, be))
    pos = parse_model(solver_log)
    rows = [["0"] * 36 for _ in range(36)]
    for a in range(NA):
        rows[0][1+a] = rows[1+a][0] = "1"
    for i in range(NA):
        for j in range(i+1, NA):
            if (A[i] >> j) & 1:
                rows[1+i][1+j] = rows[1+j][1+i] = "1"
    for i in range(NB):
        for j in range(i+1, NB):
            if (B[i] >> j) & 1:
                rows[13+i][13+j] = rows[13+j][13+i] = "1"
    for a in range(NA):
        for b in range(NB):
            var = a * NB + b + 1
            if var in pos:
                rows[1+a][13+b] = rows[13+b][1+a] = "1"
    srows = ["".join(r) for r in rows]
    base.verify_full(srows, 11, 17)
    result = {"adjacency": srows}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"valid": True, "degree_sequence": [r.count('1') for r in srows]}))
    return result


def self_test() -> None:
    sym.self_test()
    # Kissat-style model parser sanity, including auxiliary literals.
    p = Path("/tmp/d12-model-selftest.log")
    p.write_text("s SATISFIABLE\nv 1 -2 3 0\nv -4 5 0\n", encoding="ascii")
    assert parse_model(p) == {1, 3, 5}
    p.unlink(missing_ok=True)
    print("d12 symmetric DIMACS self-test ok")


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    p = sub.add_parser("generate")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--symmetry", choices=("generators", "all-a", "all-ab"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--meta", type=Path, required=True)
    p = sub.add_parser("decode")
    p.add_argument("--a-catalog", type=Path, required=True)
    p.add_argument("--b-catalog", type=Path, required=True)
    p.add_argument("--solver-log", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test(); return 0
    if args.cmd == "generate":
        generate(args.a_catalog, args.b_catalog, args.symmetry, args.output, args.meta); return 0
    decode(args.a_catalog, args.b_catalog, args.solver_log, args.output); return 0


if __name__ == "__main__":
    raise SystemExit(main())
