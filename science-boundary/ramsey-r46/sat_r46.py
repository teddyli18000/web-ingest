#!/usr/bin/env python3
"""Direct SAT encoding for a 36-vertex (4,6)-graph.

Variables are graph edges. Clauses forbid K4s and independent 6-sets. For a
branch degree d, graph relabelling lets us fix vertex 0 adjacent to 1..d and
nonadjacent to d+1..35. Across d=11..17 these branches cover every possible
(4,6,36)-graph by the standard neighborhood Ramsey bounds R(4,5)=25 and
R(3,6)=18.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

N = 36


def var_map(n: int = N) -> tuple[list[list[int]], int]:
    matrix = [[0] * n for _ in range(n)]
    var = 1
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j] = matrix[j][i] = var
            var += 1
    return matrix, var - 1


def generate(path: Path, degree: int) -> tuple[int, int]:
    if not 11 <= degree <= 17:
        raise ValueError("degree must be 11..17")
    vm, nvars = var_map()
    nclauses = math.comb(N, 4) + math.comb(N, 6) + (N - 1)
    with path.open("w", encoding="ascii", buffering=1024 * 1024) as out:
        out.write(f"p cnf {nvars} {nclauses}\n")
        for vertices in itertools.combinations(range(N), 4):
            literals = [-vm[a][b] for a, b in itertools.combinations(vertices, 2)]
            out.write(" ".join(map(str, literals)) + " 0\n")
        for vertices in itertools.combinations(range(N), 6):
            literals = [vm[a][b] for a, b in itertools.combinations(vertices, 2)]
            out.write(" ".join(map(str, literals)) + " 0\n")
        for j in range(1, N):
            edge = vm[0][j]
            out.write(f"{edge if j <= degree else -edge} 0\n")
    return nvars, nclauses


def parse_model(path: Path) -> tuple[bool, set[int]]:
    sat = False
    true_vars: set[int] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("s ") and "SATISFIABLE" in line and "UNSATISFIABLE" not in line:
            sat = True
        if line.startswith("v "):
            for token in line.split()[1:]:
                try:
                    value = int(token)
                except ValueError:
                    continue
                if value > 0:
                    true_vars.add(value)
    return sat, true_vars


def certificate(model: Path, out: Path) -> bool:
    sat, true_vars = parse_model(model)
    if not sat:
        return False
    vm, _ = var_map()
    rows = []
    for i in range(N):
        row = []
        for j in range(N):
            row.append("1" if i != j and vm[i][j] in true_vars else "0")
        rows.append("".join(row))
    out.write_text(json.dumps({"adjacency": rows}, indent=2) + "\n", encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("degree", type=int)
    gen.add_argument("out", type=Path)
    dec = sub.add_parser("decode")
    dec.add_argument("model", type=Path)
    dec.add_argument("out", type=Path)
    args = parser.parse_args()

    if args.cmd == "generate":
        nvars, nclauses = generate(args.out, args.degree)
        print(
            json.dumps(
                {
                    "n": N,
                    "degree": args.degree,
                    "variables": nvars,
                    "clauses": nclauses,
                    "path": str(args.out),
                }
            )
        )
        return 0

    sat = certificate(args.model, args.out)
    print(json.dumps({"sat": sat, "certificate": str(args.out) if sat else None}))
    return 0 if sat else 1


if __name__ == "__main__":
    raise SystemExit(main())
