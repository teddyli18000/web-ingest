#!/usr/bin/env python3
"""Degree-17 SAT v3: add a sound Aut(A) lex leader to v2.

For a degree-17 branch, A is one of the seven fixed Ramsey(3,6,17)
neighbourhood graphs and B contains the 18 non-neighbours of vertex 0.  The
base encodings already sort the B vertices lexicographically by their 17-bit
A-neighbourhood rows.  Any automorphism of A still acts simultaneously on the
columns of those rows.

Let r be the first (minimum) B row.  We may soundly require r <= g(r) for every
g in Aut(A): choose, among all Aut(A)-images of a solution (with B rows sorted
after each image), the lexicographically smallest row sequence.  Its first row
r is no larger than the first row of every transformed sequence, and that
transformed first row is no larger than g(r).  Thus the chosen representative
satisfies r <= g(r) for all g.

This script appends those lex-leader clauses to degree17_static_sat_v2.py.
The automorphism finder uses only the Python standard library and is complete;
its search is tiny for the seven 17-vertex catalogue graphs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import degree17_static_sat as base
import degree17_static_sat_v2 as v2

A = tuple(range(1, 18))
B0 = 18


def row_adjacency(rows: list[str]) -> list[set[int]]:
    return [{j for j, ch in enumerate(row) if ch == "1"} for row in rows]


def automorphisms(rows: list[str]) -> list[tuple[int, ...]]:
    """Enumerate every automorphism of a small graph by MRV backtracking."""
    n = len(rows)
    adj = row_adjacency(rows)
    deg = [len(x) for x in adj]
    mapping: dict[int, int] = {}
    used: set[int] = set()
    out: list[tuple[int, ...]] = []

    def candidates(u: int) -> list[int]:
        result: list[int] = []
        for v in range(n):
            if v in used or deg[v] != deg[u]:
                continue
            if all(((x in adj[u]) == (mx in adj[v])) for x, mx in mapping.items()):
                result.append(v)
        return result

    def rec() -> None:
        if len(mapping) == n:
            perm = tuple(mapping[i] for i in range(n))
            # Independent final guard against a backtracking implementation bug.
            for i in range(n):
                for j in range(n):
                    if ((j in adj[i]) != (perm[j] in adj[perm[i]])):
                        raise AssertionError("invalid automorphism emitted")
            out.append(perm)
            return
        best_u = -1
        best: list[int] | None = None
        for u in range(n):
            if u in mapping:
                continue
            cs = candidates(u)
            if not cs:
                return
            if best is None or len(cs) < len(best):
                best_u, best = u, cs
                if len(best) == 1:
                    break
        assert best is not None
        for v in best:
            mapping[best_u] = v
            used.add(v)
            rec()
            used.remove(v)
            del mapping[best_u]

    rec()
    return sorted(set(out))


def lex_leq_permuted(
    lits: list[int], perm: tuple[int, ...], next_var: int
) -> tuple[list[list[int]], int]:
    """CNF for bits(lits) <=lex bits(lits[perm[i]])."""
    n = len(lits)
    if len(perm) != n or sorted(perm) != list(range(n)):
        raise ValueError("perm is not a permutation")
    if all(perm[i] == i for i in range(n)):
        return [], next_var

    # p_i says positions < i are equal. p_0 is true.  We need p_i -> x_i<=y_i
    # and p_{i+1} <-> p_i AND (x_i==y_i).
    pref = list(range(next_var, next_var + n))
    next_var += n
    clauses: list[list[int]] = [[pref[0]]]
    for i in range(n):
        p = pref[i]
        x = lits[i]
        y = lits[perm[i]]
        clauses.append([-p, -x, y])
        if i + 1 == n:
            continue
        q = pref[i + 1]
        clauses.extend(
            [
                [-q, p],
                [-q, -x, y],
                [-q, x, -y],
                [-p, -x, -y, q],
                [-p, x, y, q],
            ]
        )
    return clauses, next_var


def append_aut_leader(
    path: Path, neighborhood: list[str]
) -> dict[str, object]:
    edge, _ = base.edge_variables()
    autos = automorphisms(neighborhood)
    row = [edge[a][B0] for a in A]

    with path.open("r", encoding="ascii") as f:
        header = f.readline()
    parts = header.split()
    if len(parts) != 4 or parts[:2] != ["p", "cnf"]:
        raise ValueError("unexpected DIMACS header")
    base_vars, base_clauses = map(int, parts[2:])

    next_var = base_vars + 1
    clauses: list[list[int]] = []
    nontrivial = []
    for perm in autos:
        if all(perm[i] == i for i in range(len(perm))):
            continue
        cs, next_var = lex_leq_permuted(row, perm, next_var)
        clauses.extend(cs)
        nontrivial.append(list(perm))

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
        "variables": final_vars,
        "clauses": final_clauses,
        "automorphism_group_size": len(autos),
        "nontrivial_automorphisms": len(nontrivial),
        "aut_lex_aux_variables": final_vars - base_vars,
        "aut_lex_clauses": len(clauses),
    }


def self_test() -> None:
    # Exhaustively verify the lex CNF after projecting away auxiliary variables.
    # Reuse v2's tiny complete DPLL checker.
    import itertools

    for n in range(1, 6):
        lits = list(range(1, n + 1))
        for perm in itertools.permutations(range(n)):
            clauses, _ = lex_leq_permuted(lits, perm, n + 1)
            for bits in itertools.product((False, True), repeat=n):
                fixed = {i + 1: bits[i] for i in range(n)}
                got = v2._sat_with_fixed(clauses, fixed)
                rhs = tuple(bits[perm[i]] for i in range(n))
                want = tuple(bits) <= rhs
                if got != want:
                    raise AssertionError((n, perm, bits, got, want))
    print("degree17-static-v3 lex self-test ok")


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
    degree_result = v2.append_degree_bounds(args.output, catalog[args.index])
    aut_result = append_aut_leader(args.output, catalog[args.index])
    result = {
        **base_result,
        **degree_result,
        **aut_result,
        "catalog_index": args.index,
        "path": str(args.output),
        "encoding": "static-full-ramsey+lex-B-cross+degree-11-17+AutA-first-row-lex",
    }
    result.pop("degree_info", None)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
