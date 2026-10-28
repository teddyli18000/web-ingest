#!/usr/bin/env python3
"""Static SAT encoding for R(4,6,36) graphs with a degree-17 vertex.

Fix vertex 0 to degree 17 and its neighborhood A={1,...,17} to one of the
seven complete Ramsey(3,6,17) catalogue representatives. The remaining
vertices B={18,...,35} are unlabeled, so their 17-bit A-neighborhood rows are
sorted lexicographically as a sound symmetry break. All K4 / independent-6
clauses are generated once and simplified against the fixed branch before a
standalone SAT solver is invoked.

The first 630 DIMACS variables are graph-edge variables in the same ordering
as sat_r46.py, so a SAT model can be decoded by that script. Extra variables
encode only the lexicographic symmetry break.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

N = 36
A = tuple(range(1, 18))
B = tuple(range(18, 36))


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


def load_catalog(path: Path) -> list[list[str]]:
    graphs = [
        decode_graph6(line)
        for line in path.read_text(encoding="ascii").splitlines()
        if line.strip()
    ]
    if len(graphs) != 7 or any(len(g) != 17 for g in graphs):
        raise ValueError("expected the complete seven-graph R(3,6,17) catalogue")
    return graphs


def edge_variables() -> tuple[list[list[int]], int]:
    edge = [[0] * N for _ in range(N)]
    nxt = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = nxt
            nxt += 1
    return edge, nxt - 1


def fixed_edges(edge: list[list[int]], neighborhood: list[str]) -> dict[int, bool]:
    fixed: dict[int, bool] = {}
    for v in range(1, N):
        fixed[edge[0][v]] = v <= 17
    for i in range(17):
        for j in range(i + 1, 17):
            fixed[edge[i + 1][j + 1]] = neighborhood[i][j] == "1"
    return fixed


def lex_prefix_variables(edge_vars: int) -> tuple[list[list[int]], int]:
    """prefix[k][i] says the first i cross bits of B-pair k are equal."""
    prefix: list[list[int]] = []
    nxt = edge_vars + 1
    for _ in range(len(B) - 1):
        row = list(range(nxt, nxt + len(A)))
        prefix.append(row)
        nxt += len(A)
    return prefix, nxt - 1


def simplified_ramsey_clause(
    vertices: tuple[int, ...],
    edge: list[list[int]],
    fixed: dict[int, bool],
    positive: bool,
) -> list[int] | None:
    """Return a simplified clause, or None if a fixed edge satisfies it."""
    out: list[int] = []
    for a, b in itertools.combinations(vertices, 2):
        var = edge[a][b]
        value = fixed.get(var)
        if value is None:
            out.append(var if positive else -var)
            continue
        literal_true = value if positive else not value
        if literal_true:
            return None
        # A fixed-false literal contributes nothing to the residual clause.
    if not out:
        raise ValueError("fixed branch already violates a Ramsey constraint")
    return out


def emit_clause(out, clause: list[int]) -> None:
    out.write(" ".join(map(str, clause)) + " 0\n")


def generate(path: Path, neighborhood: list[str], index: int) -> dict[str, int]:
    edge, edge_vars = edge_variables()
    fixed = fixed_edges(edge, neighborhood)
    prefix, nvars = lex_prefix_variables(edge_vars)
    counts = {"fixed_units": 0, "lex": 0, "k4": 0, "ind6": 0}

    # Reserve a fixed-width DIMACS header, then patch the final clause count.
    header_fmt = "p cnf {vars:10d} {clauses:12d}\n"
    header = header_fmt.format(vars=nvars, clauses=0)
    with path.open("w+", encoding="ascii", buffering=1024 * 1024) as out:
        out.write(header)

        for var, value in sorted(fixed.items()):
            emit_clause(out, [var if value else -var])
            counts["fixed_units"] += 1

        # B labels are arbitrary. Sort each B vertex by its 17-bit adjacency
        # row into A. Every solution has a relabeling satisfying this order.
        for k, (b, c) in enumerate(zip(B, B[1:])):
            pref = prefix[k]
            emit_clause(out, [pref[0]])
            counts["lex"] += 1
            for i, a in enumerate(A):
                p = pref[i]
                x = edge[a][b]
                y = edge[a][c]
                # Equal prefix implies x <= y at the first differing bit.
                emit_clause(out, [-p, -x, y])
                counts["lex"] += 1
                if i + 1 == len(A):
                    continue
                q = pref[i + 1]
                # q <-> p AND (x == y).
                for clause in (
                    [-q, p],
                    [-q, -x, y],
                    [-q, x, -y],
                    [-p, -x, -y, q],
                    [-p, x, y, q],
                ):
                    emit_clause(out, clause)
                    counts["lex"] += 1

        for vertices in itertools.combinations(range(N), 4):
            clause = simplified_ramsey_clause(
                vertices, edge, fixed, positive=False
            )
            if clause is not None:
                emit_clause(out, clause)
                counts["k4"] += 1

        for vertices in itertools.combinations(range(N), 6):
            clause = simplified_ramsey_clause(
                vertices, edge, fixed, positive=True
            )
            if clause is not None:
                emit_clause(out, clause)
                counts["ind6"] += 1

        nclauses = sum(counts.values())
        final_header = header_fmt.format(vars=nvars, clauses=nclauses)
        if len(final_header) != len(header):
            raise RuntimeError("DIMACS header width changed")
        out.seek(0)
        out.write(final_header)

    return {
        "catalog_index": index,
        "variables": nvars,
        "edge_variables": edge_vars,
        "clauses": nclauses,
        **counts,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    catalog = load_catalog(args.catalog)
    if not 0 <= args.index < len(catalog):
        ap.error("--index must be 0..6")
    result = generate(args.output, catalog[args.index], args.index)
    result["path"] = str(args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
