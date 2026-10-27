#!/usr/bin/env python3
"""Exact one-swap repair of the auxiliary X set for the BPZ t=9 near misses.

The exact one-swap-I sweep has two 367-point I states with exactly nine private
pairs.  Exhausting all 2^9 orientations shows that each state has orientations
with independent P^H and P^V for which exactly one published X point lies in
N(P^H) cap N(P^V).  For every such orientation, this program removes that sole
bad X point and exhausts every y in C7^5 \ X.  A replacement is valid iff

  * X - {bad} + {y} is still a 367-point independent set; and
  * y is not in N(P^H) cap N(P^V).

A hit repairs all Definition-2 axioms with t=9, so Gao's product has
367^2 + 9^2 = 134770 vertices.  The full 10D certificate is materialized for
the independent Few Shots verifier.
"""

import argparse
import json
import sys
from itertools import combinations, product
from pathlib import Path

Q = 7
D = 5
U = Q ** D
N = 367
T = 9
TARGET = N * N + T * T
I_SWAPS = ((6110, 3716), (13677, 14027))


def conflict(a: int, b: int, digits) -> bool:
    return all((x - y) % Q in (0, 1, Q - 1) for x, y in zip(digits[a], digits[b]))


def independent(vals, digits) -> bool:
    vals = list(vals)
    return all(not conflict(a, b, digits) for a, b in combinations(vals, 2))


def private_pairs(I, ring):
    out = []
    for q in range(U):
        if q in I:
            continue
        hits = [z for z in ring.NB[q] if z in I]
        if len(hits) == 1:
            out.append((hits[0], q))
    return sorted(out)


def build_candidate(I, X, pairs, PH, PV, ring):
    owners = {r for r, _ in pairs}
    B = set(I) - owners
    NH = ring.nbhd(set(PH))
    NV = ring.nbhd(set(PV))
    if set(X) & NH & NV:
        raise RuntimeError("Definition-2 double-hit survived repair")
    X0 = set(X) - (NH | NV)
    XH = set(X) & NH
    XV = set(X) & NV
    if (X0 | XH | XV) != set(X) or X0 & XH or X0 & XV or XH & XV:
        raise RuntimeError("X partition is not disjoint")

    pts = set()
    for A, C in (
        (B, B),
        (owners, X0),
        (set(PH), XH),
        (set(PV), XV),
        (X0, owners),
        (XH, set(PV)),
        (XV, set(PH)),
    ):
        for a in A:
            for c in C:
                pts.add((a, c))
    if len(pts) != TARGET:
        raise RuntimeError(f"Gao product score drift: {len(pts)} != {TARGET}")

    def p10(pair):
        a, b = pair
        return "".join(map(str, ring.decode(a) + ring.decode(b)))

    return sorted(p10(p) for p in pts), (len(X0), len(XH), len(XV))


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
    I0 = set(map(int, raw["I0"]))
    X0 = set(map(int, raw["X"]))
    ring = Ring(D)
    digits = tuple(ring.decode(v) for v in range(U))
    if len(I0) != N or len(X0) != N or not independent(I0, digits) or not independent(X0, digits):
        raise RuntimeError("published base drift")

    # For each y, exact X-neighbour set as a bit mask over the published X.
    xlist = sorted(X0)
    xpos = {x: i for i, x in enumerate(xlist)}
    x_hits = [0] * U
    for x, i in xpos.items():
        bit = 1 << i
        for y in ring.NB[x]:
            x_hits[y] |= bit

    tested_orientations = 0
    repair_trials = 0
    near = []
    winner = None

    for rem, add in I_SWAPS:
        I = set(I0)
        if rem not in I or add in I:
            raise RuntimeError("I-swap drift")
        I.remove(rem)
        I.add(add)
        if len(I) != N or not independent(I, digits):
            raise RuntimeError("one-swap I is not independent")
        pairs = private_pairs(I, ring)
        if len(pairs) != T or len({r for r, _ in pairs}) != T:
            raise RuntimeError(f"expected exactly nine private pairs after {(rem, add)}, got {pairs}")

        for orient in product((0, 1), repeat=T):
            PH = [q if side else r for (r, q), side in zip(pairs, orient)]
            PV = [r if side else q for (r, q), side in zip(pairs, orient)]
            if not independent(PH, digits) or not independent(PV, digits):
                continue
            tested_orientations += 1
            NH = ring.nbhd(set(PH))
            NV = ring.nbhd(set(PV))
            bad = sorted(X0 & NH & NV)
            if len(bad) != 1:
                continue
            badx = bad[0]
            badbit = 1 << xpos[badx]
            best_local = {"I_swap": [rem, add], "orientation": list(orient), "bad_X": badx, "repairs": 0}

            # Exact one-swap neighbourhood of X0 at the required owner badx.
            for y in range(U):
                if y in X0:
                    continue
                repair_trials += 1
                # X0 - {badx} + {y} independent iff y has no X0-neighbour
                # other than possibly badx.
                if x_hits[y] & ~badbit:
                    continue
                if y in NH and y in NV:
                    continue
                X = set(X0)
                X.remove(badx)
                X.add(y)
                if len(X) != N or not independent(X, digits):
                    raise RuntimeError("X repair replay failed independence")
                if X & NH & NV:
                    raise RuntimeError("X repair replay left a double hit")
                best_local["repairs"] += 1
                if winner is None:
                    winner = (I, X, pairs, PH, PV, rem, add, badx, y, orient)
            near.append(best_local)
            print("ORIENTATION", json.dumps(best_local, sort_keys=True), flush=True)

    status = {
        "method": "bpz-t9-exact-one-swap-X-repair",
        "candidate": winner is not None,
        "same_side_valid_orientations_tested": tested_orientations,
        "ambient_repair_trials": repair_trials,
        "one_bad_X_orientations": len(near),
        "near_orientations": near,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    I, X, pairs, PH, PV, rem, add, badx, y, orient = winner
    points, xpart = build_candidate(I, X, pairs, PH, PV, ring)

    # Replay every Definition-2 axiom explicitly.
    if not independent(I, digits) or not independent(X, digits):
        raise RuntimeError("final I/X independence failed")
    if any(r not in I or q in I or {w for w in I if w in ring.NB[q]} != {r} for r, q in pairs):
        raise RuntimeError("final private-pair axiom failed")
    if len({e for p in pairs for e in p}) != 2 * T:
        raise RuntimeError("final endpoint-disjoint axiom failed")
    if not independent(PH, digits) or not independent(PV, digits):
        raise RuntimeError("final transversal independence failed")
    if set(PH) & set(PV) or set(PH) | set(PV) != {e for p in pairs for e in p}:
        raise RuntimeError("final complementary-transversal axiom failed")
    if X & ring.nbhd(set(PH)) & ring.nbhd(set(PV)):
        raise RuntimeError("final X double-hit axiom failed")

    status.update({
        "score": len(points),
        "I_swap": {"remove": rem, "add": add},
        "X_swap": {"remove": badx, "add": y},
        "orientation": list(orient),
        "private_pairs": [list(p) for p in pairs],
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": xpart[0], "XH": xpart[1], "XV": xpart[2]},
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
