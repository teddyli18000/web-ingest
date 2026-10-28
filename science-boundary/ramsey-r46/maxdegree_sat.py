#!/usr/bin/env python3
"""Exact SAT branches by the maximum degree of a hypothetical (4,6,36)-graph.

For a branch D, relabel a maximum-degree vertex as 0 and its neighbours as
1..D.  Then fix N(0)={1,...,D}, require 11 <= deg(v) <= D for every vertex,
and add every K4- and independent-6-forbidding clause.  The branches D=11..17
therefore cover every (4,6,36)-graph without loss; unlike the older sat_r46.py,
D is the *global maximum degree*, not merely deg(0).
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

N = 36
MIN_DEG = 11


def edge_variables():
    edge = [[0] * N for _ in range(N)]
    v = 1
    for i in range(N):
        for j in range(i + 1, N):
            edge[i][j] = edge[j][i] = v
            v += 1
    return edge, v - 1


def atmost_seq(lits: list[int], k: int, next_var: int):
    n = len(lits)
    if k < 0:
        return [[]], next_var
    if k >= n:
        return [], next_var
    if k == 0:
        return [[-x] for x in lits], next_var
    s = []
    for _ in range(n - 1):
        row = list(range(next_var, next_var + k))
        next_var += k
        s.append(row)
    out = [[-lits[0], s[0][0]]]
    for j in range(1, k):
        out.append([-s[0][j]])
    for i in range(1, n - 1):
        out.append([-lits[i], s[i][0]])
        out.append([-s[i - 1][0], s[i][0]])
        for j in range(1, k):
            out.append([-lits[i], -s[i - 1][j - 1], s[i][j]])
            out.append([-s[i - 1][j], s[i][j]])
    for i in range(1, n):
        out.append([-lits[i], -s[i - 1][k - 1]])
    return out, next_var


def degree_constraints(edge, D: int, start_var: int):
    fixed = {edge[0][j]: (j <= D) for j in range(1, N)}
    clauses = []
    next_var = start_var
    info = []
    for v in range(N):
        free = []
        fixed_true = 0
        for u in range(N):
            if u == v:
                continue
            x = edge[v][u]
            if x in fixed:
                fixed_true += int(fixed[x])
            else:
                free.append(x)
        lo = max(0, MIN_DEG - fixed_true)
        hi = min(len(free), D - fixed_true)
        if lo > hi:
            return [[]], next_var, fixed, [{"vertex": v, "infeasible": True}]
        up, next_var = atmost_seq(free, hi, next_var)
        low, next_var = atmost_seq([-x for x in free], len(free) - lo, next_var)
        clauses.extend(up)
        clauses.extend(low)
        info.append({"vertex": v, "fixed_true": fixed_true, "free": len(free),
                     "residual_min": lo, "residual_max": hi,
                     "clauses": len(up) + len(low)})
    return clauses, next_var, fixed, info


def generate(D: int, path: Path):
    if not 11 <= D <= 17:
        raise ValueError("D must be 11..17")
    edge, edge_vars = edge_variables()
    deg_clauses, next_var, fixed, info = degree_constraints(edge, D, edge_vars + 1)
    variables = next_var - 1
    k4 = math.comb(N, 4)
    i6 = math.comb(N, 6)
    units = len(fixed)
    total = k4 + i6 + units + len(deg_clauses)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="ascii", buffering=1024 * 1024) as out:
        out.write(f"p cnf {variables} {total}\n")
        for x, val in sorted(fixed.items()):
            out.write(f"{x if val else -x} 0\n")
        for vs in itertools.combinations(range(N), 4):
            out.write(" ".join(str(-edge[a][b]) for a, b in itertools.combinations(vs, 2)) + " 0\n")
        for vs in itertools.combinations(range(N), 6):
            out.write(" ".join(str(edge[a][b]) for a, b in itertools.combinations(vs, 2)) + " 0\n")
        for c in deg_clauses:
            out.write(" ".join(map(str, c)) + " 0\n")
    return {"max_degree": D, "variables": variables, "edge_variables": edge_vars,
            "clauses": total, "k4_clauses": k4, "i6_clauses": i6,
            "fixed_edge_units": units, "degree_clauses": len(deg_clauses),
            "encoding": "full-Ramsey+fixed-max-degree-vertex+global-degree-11-D"}


def model_true(path: Path):
    out = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("v "):
            for tok in line[2:].split():
                x = int(tok)
                if x > 0:
                    out.add(x)
    return out


def decode(model: Path, out: Path):
    edge, _ = edge_variables()
    true = model_true(model)
    rows = []
    for i in range(N):
        rows.append("".join("1" if i != j and edge[i][j] in true else "0" for j in range(N)))
    out.write_text(json.dumps({"adjacency": rows}, separators=(",", ":")) + "\n", encoding="utf-8")


def tiny_sat(clauses, fixed):
    def rec(a):
        while True:
            changed = False
            for c in clauses:
                if any(abs(l) in a and a[abs(l)] == (l > 0) for l in c):
                    continue
                u = [l for l in c if abs(l) not in a]
                if not u:
                    return False
                if len(u) == 1:
                    l = u[0]; a[abs(l)] = l > 0; changed = True
            if not changed:
                break
        v = next((abs(l) for c in clauses for l in c if abs(l) not in a), None)
        if v is None:
            return True
        for val in (False, True):
            b = dict(a); b[v] = val
            if rec(b): return True
        return False
    return rec(dict(fixed))


def self_test():
    for n in range(1, 7):
        lits = list(range(1, n + 1))
        for k in range(n + 1):
            clauses, _ = atmost_seq(lits, k, n + 1)
            for bits in itertools.product((False, True), repeat=n):
                got = tiny_sat(clauses, {i + 1: bits[i] for i in range(n)})
                assert got == (sum(bits) <= k), (n, k, bits, got)
    edge, _ = edge_variables()
    for D in range(11, 18):
        _c, _n, fixed, info = degree_constraints(edge, D, 631)
        assert all(not x.get("infeasible") for x in info)
        assert sum(fixed.values()) == D
    print("maxdegree-sat self-test ok")


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate"); g.add_argument("--max-degree", type=int, required=True); g.add_argument("--output", type=Path, required=True)
    d = sub.add_parser("decode"); d.add_argument("--model", type=Path, required=True); d.add_argument("--output", type=Path, required=True)
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test()
    elif a.cmd == "generate": print(json.dumps(generate(a.max_degree, a.output), sort_keys=True))
    else: decode(a.model, a.output)


if __name__ == "__main__": main()
