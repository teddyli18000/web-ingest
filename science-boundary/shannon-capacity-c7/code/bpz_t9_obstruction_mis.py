#!/usr/bin/env python3
"""Solve the remaining BPZ t=9 obstruction as an unrestricted C7^5 MIS.

For the strongest exact t=9 witness found in the complete BPZ I private-swap
component, Definition 2 fails only because the published auxiliary 367-set X
contains one point in D = N(P^H) cap N(P^V), where |D|=1098.

Instead of repairing that X locally, this program asks the full question:

    does C7^5 \ D contain an independent set of size at least 367?

The SAT model is exact and compact.  For each a in Z_7^5, the 32 vertices
    a + {0,1}^5
form a clique in the C7^5 confusability graph.  Conversely every confusable
pair is contained in at least one such cube.  Therefore at-most-one over all
7^5 cubes is exactly the independent-set constraint.  One native global
cardinality constraint asks for at least 367 selected allowed vertices.

A SAT solution is replayed directly and then used as the auxiliary X in Gao's
t=9 product, yielding 367^2 + 9^2 = 134770 vertices for Few Shots p004.
"""

import argparse
import json
import sys
from itertools import combinations, product
from pathlib import Path

from pysat.solvers import Minicard

Q = 7
D = 5
U = Q ** D
N = 367
T = 9
TARGET = N * N + T * T

# Best exact witness from the 243-state I component / 160 obstruction masks.
I_SWAPS = ((6110, 3716), (13677, 14027))
PRIVATE_PAIRS = (
    (1553, 15910),
    (3716, 6110),
    (8888, 6494),
    (10708, 13158),
    (13065, 13358),
    (14027, 13677),
    (14329, 12277),
    (15075, 14733),
    (15384, 15685),
)
ORIENTATION = (0, 0, 1, 1, 0, 1, 1, 0, 0)


def conflict(a, b, digits):
    return all((x - y) % Q in (0, 1, Q - 1) for x, y in zip(digits[a], digits[b]))


def independent(vals, digits):
    vals = list(vals)
    return all(not conflict(a, b, digits) for a, b in combinations(vals, 2))


def enc(word):
    v = 0
    mul = 1
    for x in word:
        v += x * mul
        mul *= Q
    return v


def cube(anchor_digits):
    for bits in product((0, 1), repeat=D):
        yield enc(tuple((anchor_digits[j] + bits[j]) % Q for j in range(D)))


def build(I, X, pairs, PH, PV, ring):
    R = {a for a, _ in pairs}
    B = set(I) - R
    NH = ring.nbhd(set(PH))
    NV = ring.nbhd(set(PV))
    X = set(X)
    if X & NH & NV:
        raise RuntimeError("SAT auxiliary set still hits obstruction")
    X0 = X - (NH | NV)
    XH = X & NH
    XV = X & NV
    P = set()
    for A, C in (
        (B, B), (R, X0), (set(PH), XH), (set(PV), XV),
        (X0, R), (XH, set(PV)), (XV, set(PH)),
    ):
        for a in A:
            for c in C:
                P.add((a, c))
    if len(P) != TARGET:
        raise RuntimeError(f"Gao score drift {len(P)} != {TARGET}")
    points = sorted("".join(map(str, ring.decode(a) + ring.decode(b))) for a, b in P)
    return points, (len(X0), len(XH), len(XV))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import Ring  # type: ignore

    raw = json.loads((root / "data" / "base_c7.json").read_text())
    I = set(map(int, raw["I0"]))
    published_X = set(map(int, raw["X"]))
    ring = Ring(D)
    digits = tuple(ring.decode(v) for v in range(U))
    for a, b in I_SWAPS:
        if a not in I or b in I:
            raise RuntimeError("I witness swap drift")
        I.remove(a)
        I.add(b)
    pairs = list(PRIVATE_PAIRS)
    PH = [q if s else a for (a, q), s in zip(pairs, ORIENTATION)]
    PV = [a if s else q for (a, q), s in zip(pairs, ORIENTATION)]
    if len(I) != N or not independent(I, digits):
        raise RuntimeError("I witness is not independent")
    if len({a for a, _ in pairs}) != T or not independent(PH, digits) or not independent(PV, digits):
        raise RuntimeError("private-pair witness drift")
    obstruction = ring.nbhd(set(PH)) & ring.nbhd(set(PV))
    published_hits = sorted(published_X & obstruction)
    if len(obstruction) != 1098 or published_hits != [10665]:
        raise RuntimeError(f"obstruction drift size={len(obstruction)} hits={published_hits}")

    allowed = [v for v in range(U) if v not in obstruction]
    allowed_set = set(allowed)
    var = {v: i + 1 for i, v in enumerate(allowed)}

    solver = Minicard()
    nontrivial_cubes = 0
    max_cube = 0
    cube_literal_total = 0
    # Exact clique cover of all C7^5 conflict edges.
    for a in range(U):
        lits = [var[v] for v in cube(digits[a]) if v in allowed_set]
        if len(lits) >= 2:
            solver.add_atmost(lits, 1)
            nontrivial_cubes += 1
            max_cube = max(max_cube, len(lits))
            cube_literal_total += len(lits)

    variables = len(allowed)
    # At least N selected <=> at most variables-N negative literals selected.
    solver.add_atmost([-var[v] for v in allowed], variables - N)

    setup = {
        "ambient_vertices": U,
        "obstruction_size": len(obstruction),
        "allowed_vertices": variables,
        "target_auxiliary_size": N,
        "nontrivial_cube_constraints": nontrivial_cubes,
        "cube_literal_total": cube_literal_total,
        "max_allowed_vertices_per_cube": max_cube,
        "published_X_hits": published_hits,
        "target_10d_score": TARGET,
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    sat = solver.solve()
    model = solver.get_model() if sat else None
    solver.delete()

    args.status.parent.mkdir(parents=True, exist_ok=True)
    if not sat:
        status = {
            "candidate": False,
            "sat": False,
            "method": "bpz-t9-obstruction-avoiding-C7^5-MIS-exact-cube-cover",
            "score": 134753,
            "setup": setup,
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("UNSAT", json.dumps(status, sort_keys=True), flush=True)
        return

    pos = {z for z in model if z > 0}
    X = [v for v in allowed if var[v] in pos]
    if len(X) < N:
        raise RuntimeError(f"SAT model selected only {len(X)} vertices")
    # Keep any N vertices; every subset of an independent set remains independent.
    X = X[:N]
    if len(set(X)) != N or set(X) & obstruction or not independent(X, digits):
        raise RuntimeError("SAT model replay failed")

    points, xp = build(I, X, pairs, PH, PV, ring)
    status = {
        "candidate": True,
        "sat": True,
        "method": "bpz-t9-obstruction-avoiding-C7^5-MIS-exact-cube-cover",
        "score": len(points),
        "auxiliary_size": len(X),
        "auxiliary_points": X,
        "private_pairs": [list(z) for z in pairs],
        "orientation": list(ORIENTATION),
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
        "setup": setup,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps({k: v for k, v in status.items() if k != "auxiliary_points"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
