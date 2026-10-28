#!/usr/bin/env python3
"""Exact SAT for 36-vertex (4,6)-graphs with a semiregular cyclic automorphism.

For order m|36, fix the permutation consisting of 36/m disjoint m-cycles.
All edges in one orbit of this permutation share a Boolean variable. Every
4-set contributes a negative clause forbidding K4; every 6-set contributes a
positive clause forbidding an independent 6-set. Duplicate clauses are removed.
Thus SAT is exactly existence in this symmetry class, not a heuristic restriction
beyond the stated automorphism.
"""
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path

N = 36


def permutation(order: int) -> list[int]:
    if order <= 1 or N % order:
        raise ValueError("order must divide 36 and exceed 1")
    p = list(range(N))
    for b in range(N // order):
        base = b * order
        for i in range(order):
            p[base + i] = base + (i + 1) % order
    return p


def edge_orbits(order: int):
    p = permutation(order)
    edge_var = {}
    orbits = []
    for i in range(N):
        for j in range(i + 1, N):
            e = (i, j)
            if e in edge_var:
                continue
            idx = len(orbits) + 1
            orb = []
            x, y = e
            while True:
                ee = (x, y) if x < y else (y, x)
                if ee in edge_var:
                    break
                edge_var[ee] = idx
                orb.append(ee)
                x, y = p[x], p[y]
            orbits.append(orb)
    assert len(edge_var) == N * (N - 1) // 2
    return edge_var, orbits


def clauses(order: int):
    ev, orbits = edge_orbits(order)
    neg = set()
    pos = set()
    for vertices in itertools.combinations(range(N), 4):
        vs = tuple(sorted({ev[(i, j)] for i, j in itertools.combinations(vertices, 2)}))
        neg.add(tuple(-v for v in vs))
    for vertices in itertools.combinations(range(N), 6):
        vs = tuple(sorted({ev[(i, j)] for i, j in itertools.combinations(vertices, 2)}))
        pos.add(vs)
    return ev, orbits, sorted(neg), sorted(pos)


def generate(order: int, out: Path) -> dict:
    _ev, orbits, neg, pos = clauses(order)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="ascii") as f:
        f.write(f"p cnf {len(orbits)} {len(neg) + len(pos)}\n")
        for clause in neg:
            f.write(" ".join(map(str, clause)) + " 0\n")
        for clause in pos:
            f.write(" ".join(map(str, clause)) + " 0\n")
    return {
        "order": order,
        "cycles": N // order,
        "variables": len(orbits),
        "k4_clauses": len(neg),
        "i6_clauses": len(pos),
        "clauses": len(neg) + len(pos),
        "edge_orbit_sizes": {
            str(k): sum(len(o) == k for o in orbits)
            for k in sorted({len(o) for o in orbits})
        },
    }


def model_vars(path: Path) -> set[int]:
    true = set()
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if raw.startswith("v "):
            for tok in raw[2:].split():
                x = int(tok)
                if x > 0:
                    true.add(x)
    return true


def decode(order: int, model: Path, out: Path) -> None:
    _ev, orbits = edge_orbits(order)
    true = model_vars(model)
    rows = [["0"] * N for _ in range(N)]
    for idx, orb in enumerate(orbits, 1):
        if idx in true:
            for i, j in orb:
                rows[i][j] = rows[j][i] = "1"
    obj = {"adjacency": ["".join(r) for r in rows]}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, separators=(",", ":")) + "\n", encoding="utf-8")


def self_test() -> None:
    for order in (2, 3, 4, 6, 9, 12, 18, 36):
        ev, orbits = edge_orbits(order)
        assert sum(map(len, orbits)) == 630 and len(ev) == 630
        p = permutation(order)
        for idx, orb in enumerate(orbits, 1):
            orbit_set = set(orb)
            for i, j in orb:
                a, b = p[i], p[j]
                e = (a, b) if a < b else (b, a)
                assert e in orbit_set and ev[e] == idx
        assert len({ev[e] for e in itertools.combinations(range(4), 2)}) >= 1
        assert len({ev[e] for e in itertools.combinations(range(6), 2)}) >= 1
    print("semiregular-sat self-test ok")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--order", type=int, required=True)
    gen.add_argument("--output", type=Path, required=True)
    dec = sub.add_parser("decode")
    dec.add_argument("--order", type=int, required=True)
    dec.add_argument("--model", type=Path, required=True)
    dec.add_argument("--output", type=Path, required=True)
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "self-test":
        self_test()
    elif args.cmd == "generate":
        print(json.dumps(generate(args.order, args.output), sort_keys=True))
    else:
        decode(args.order, args.model, args.output)


if __name__ == "__main__":
    main()
