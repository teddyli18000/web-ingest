#!/usr/bin/env python3
"""Exact SAT for (4,6,36) graphs invariant under the V4 action of Exoo core 37.

The published 35-vertex core with automorphism group of order four has a V4
action.  The two involutions below were independently recovered from the pinned
McKay/Exoo r46_35some.g6 data (SHA256
89a39d9cccb6a538e8d71d8e82abf84030ff9cde400727291b978fbad0003fc3),
using its 37th graph.  Vertex 35 is added as a second global fixed point.

We identify all edges in one V4 orbit and emit every K4-forbidding and
independent-6-forbidding clause, with duplicate clauses removed.  SAT is exactly
existence inside this group-action class; UNSAT is a complete restricted-family
exclusion.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

N = 36
P = [0,1,2,3,4,5,7,6,11,10,9,8,12,16,15,14,13,20,19,18,17,22,21,24,23,26,25,28,27,30,29,34,33,32,31,35]
Q = [1,0,3,2,5,4,6,7,9,8,11,10,12,14,13,16,15,18,17,20,19,24,23,22,21,28,27,26,25,29,30,33,34,31,32,35]


def compose(a: list[int], b: list[int]) -> list[int]:
    return [a[b[i]] for i in range(N)]


def group() -> list[list[int]]:
    ident = list(range(N))
    pq = compose(P, Q)
    out = [ident, P, Q, pq]
    assert len({tuple(x) for x in out}) == 4
    for a in out:
        assert sorted(a) == ident
    assert compose(P, P) == ident
    assert compose(Q, Q) == ident
    assert compose(P, Q) == compose(Q, P)
    return out


def edge_orbits():
    gs = group()
    ev: dict[tuple[int, int], int] = {}
    orbits: list[set[tuple[int, int]]] = []
    for i in range(N):
        for j in range(i + 1, N):
            e = (i, j)
            if e in ev:
                continue
            orbit = {tuple(sorted((g[i], g[j]))) for g in gs}
            v = len(orbits) + 1
            for x in orbit:
                if x in ev and ev[x] != v:
                    raise AssertionError("overlapping edge orbits")
                ev[x] = v
            orbits.append(orbit)
    assert len(ev) == N * (N - 1) // 2
    return ev, orbits


def generate(out: Path) -> dict:
    ev, orbits = edge_orbits()
    neg: set[tuple[int, ...]] = set()
    pos: set[tuple[int, ...]] = set()
    for vs in itertools.combinations(range(N), 4):
        vars_ = {ev[tuple(sorted(e))] for e in itertools.combinations(vs, 2)}
        neg.add(tuple(sorted(-v for v in vars_)))
    for vs in itertools.combinations(range(N), 6):
        vars_ = {ev[tuple(sorted(e))] for e in itertools.combinations(vs, 2)}
        pos.add(tuple(sorted(vars_)))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="ascii") as f:
        f.write(f"p cnf {len(orbits)} {len(neg) + len(pos)}\n")
        for c in sorted(neg):
            f.write(" ".join(map(str, c)) + " 0\n")
        for c in sorted(pos):
            f.write(" ".join(map(str, c)) + " 0\n")
    return {
        "action": "Exoo-core37-V4-plus-fixed-vertex",
        "vertex_orbits": {"4": 6, "2": 5, "1": 2},
        "variables": len(orbits),
        "edge_orbit_sizes": {str(k): sum(len(o) == k for o in orbits) for k in (1, 2, 4)},
        "k4_clauses": len(neg),
        "i6_clauses": len(pos),
        "clauses": len(neg) + len(pos),
    }


def model_true(path: Path) -> set[int]:
    out = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("v "):
            for tok in line[2:].split():
                x = int(tok)
                if x > 0:
                    out.add(x)
    return out


def decode(model: Path, out: Path) -> None:
    _ev, orbits = edge_orbits()
    true = model_true(model)
    rows = [["0"] * N for _ in range(N)]
    for v, orbit in enumerate(orbits, 1):
        if v in true:
            for i, j in orbit:
                rows[i][j] = rows[j][i] = "1"
    out.write_text(json.dumps({"adjacency": ["".join(r) for r in rows]}, separators=(",", ":")) + "\n", encoding="utf-8")


def self_test() -> None:
    gs = group()
    # Vertex action type 4^6 2^5 1^2.
    unseen = set(range(N)); sizes = []
    while unseen:
        v = min(unseen)
        orb = {g[v] for g in gs}
        unseen -= orb
        sizes.append(len(orb))
    assert sorted(sizes) == [1, 1] + [2] * 5 + [4] * 6
    ev, orbits = edge_orbits()
    assert len(orbits) == 180
    assert sum(len(o) for o in orbits) == 630
    assert {k: sum(len(o) == k for o in orbits) for k in (1,2,4)} == {1:6, 2:36, 4:138}
    for e, v in ev.items():
        for g in gs:
            x = tuple(sorted((g[e[0]], g[e[1]])))
            assert ev[x] == v
    print("core37-v4-sat self-test ok")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate"); g.add_argument("--output", type=Path, required=True)
    d = sub.add_parser("decode"); d.add_argument("--model", type=Path, required=True); d.add_argument("--output", type=Path, required=True)
    sub.add_parser("self-test")
    a = ap.parse_args()
    if a.cmd == "self-test": self_test()
    elif a.cmd == "generate": print(json.dumps(generate(a.output), sort_keys=True))
    else: decode(a.model, a.output)


if __name__ == "__main__":
    main()
