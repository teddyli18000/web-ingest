#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from pathlib import Path

import generalized9 as g

MODS = {267: 15083, 294: 16388}
PORTS = [
    (11283, 13677, 0), (15083, 14733, 1), (13108, 13158, 0),
    (15953, 15910, 1), (14328, 12277, 0), (16388, 16046, 0),
    (1321, 15685, 1), (8601, 6494, 0), (3660, 6110, 1),
]
TARGET = 134770


def independent(vals, digits):
    return all(not g.conflict(a, b, digits) for a, b in combinations(vals, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("out", type=Path)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    x = g.make_x(r0, digits)
    r = list(r0)
    for i, v in MODS.items():
        r[i] = v

    hs = [a if side == 0 else b for a, b, side in PORTS]
    vs = [b if side == 0 else a for a, b, side in PORTS]

    def forbidden(q):
        return any(g.conflict(q, h, digits) for h in hs) and any(g.conflict(q, v, digits) for v in vs)

    bad = [i for i, q in enumerate(x) if forbidden(q)]
    if len(bad) != 1:
        raise RuntimeError(f"expected exactly one forbidden companion point, got {bad}")
    b = bad[0]
    xset = set(x)

    # Exact support of every outside, port-safe vertex against the current X.
    supports = {}
    support_hist = {}
    for q in range(g.U):
        if q in xset or forbidden(q):
            continue
        s = tuple(i for i, z in enumerate(x) if g.conflict(q, z, digits))
        support_hist[len(s)] = support_hist.get(len(s), 0) + 1
        if 1 <= len(s) <= 3:
            supports[q] = s

    print("bad", b, x[b], "support_hist", json.dumps(support_hist, sort_keys=True), flush=True)

    def emit(remove, add, kind):
        xp = [z for i, z in enumerate(x) if i not in remove] + list(add)
        if len(xp) != g.R_SIZE or len(set(xp)) != g.R_SIZE or not independent(xp, digits):
            raise RuntimeError("constructed companion repair is not an independent 367-set")
        if any(forbidden(q) for q in xp):
            raise RuntimeError("constructed companion repair still meets H/V forbidden intersection")
        result = {
            "kind": "coupled-found",
            "method": kind,
            "score": TARGET,
            "best_overlap_seen": 1,
            "bad_index": b,
            "bad_point": x[b],
            "remove_x_indices": sorted(remove),
            "remove_x_points": [x[i] for i in sorted(remove)],
            "add_x_points": list(add),
            "independent_set": r,
            "companion_set": xp,
            "ports": [{"center": a, "alt": z, "side": s} for a, z, s in PORTS],
            "support_histogram": support_hist,
        }
        args.out.write_text(json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8")
        print("FOUND", json.dumps({k: result[k] for k in ("method", "remove_x_indices", "remove_x_points", "add_x_points")}, sort_keys=True), flush=True)

    # Exact 2->2: bad point plus one other removed X point.
    for j in range(g.R_SIZE):
        if j == b:
            continue
        rem = {b, j}
        cand = [q for q, s in supports.items() if set(s).issubset(rem)]
        for u, v in combinations(cand, 2):
            if not g.conflict(u, v, digits):
                emit(rem, (u, v), "neutral2-companion-exact-2for2")
                return
    print("exact 2-for-2 none", flush=True)

    # Exact 3->3: bad point plus any two other removed X points. Generate only
    # owner triples that can actually support at least three admissible additions.
    owner_pairs = set()
    for s in supports.values():
        if b in s:
            others = [i for i in s if i != b]
            if len(others) == 2:
                owner_pairs.add(tuple(sorted(others)))
            elif len(others) == 1:
                # Pair this mandatory owner with every owner seen in a support-1/2 candidate.
                a = others[0]
                relevant = set()
                for t in supports.values():
                    if len(t) <= 2:
                        relevant.update(t)
                for k in relevant:
                    if k not in (b, a):
                        owner_pairs.add(tuple(sorted((a, k))))
    # Also include pairs formed from owners of low-support vertices involving b or alone.
    relevant = set()
    for s in supports.values():
        if len(s) <= 2 and (b in s or len(s) == 1):
            relevant.update(i for i in s if i != b)
    for j, k in combinations(sorted(relevant), 2):
        owner_pairs.add((j, k))

    tested_triples = 0
    for j, k in sorted(owner_pairs):
        if b in (j, k) or j == k:
            continue
        rem = {b, j, k}
        cand = [q for q, s in supports.items() if set(s).issubset(rem)]
        if len(cand) < 3:
            continue
        tested_triples += 1
        for u, v, w in combinations(cand, 3):
            if (not g.conflict(u, v, digits) and not g.conflict(u, w, digits)
                    and not g.conflict(v, w, digits)):
                emit(rem, (u, v, w), "neutral2-companion-exact-3for3")
                return

    result = {
        "kind": "none",
        "method": "neutral2-companion-exact-2for2-3for3",
        "bad_index": b,
        "bad_point": x[b],
        "support_histogram": support_hist,
        "candidate_vertices_le3": len(supports),
        "tested_3for3_owner_pairs": tested_triples,
    }
    args.out.write_text(json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8")
    print("NONE", json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
