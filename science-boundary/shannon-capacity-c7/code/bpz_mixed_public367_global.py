#!/usr/bin/env python3
"""One-shot exact MaxSAT for mixed public 367-point terminal fibers.

This is the globally encoded replacement for enumerating all left/right maximum
independent 8-sets of the 16-point Q graph.  The pinned BPZ geometry gives eight
private pairs whose union is Q.  On each side, exactly one endpoint+public-367
set choice is selected from every private pair.  Thus each side has eight full
367-point fibers.

For a left fiber q x S and right fiber T x r, complete coexistence is equivalent
to
    T cap N[q] = empty OR S cap N[r] = empty.
Every incompatible pair of choices is a hard clause.  Same-side compatibility
is guaranteed by the exact Q=8K2 structure, which is asserted independently.

All feasible solutions have 16*367=5872 pairwise distinct periphery points and
score 134753 with BB.  Soft weights maximize the exact number of selected
periphery points outside the canonical PH x X union X x PV reference, yielding
a far record-tie mother in a single solver call.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2


def conflict5(a: int, b: int) -> bool:
    if a == b:
        return True
    for _ in range(5):
        x, y = a % 7, b % 7
        a //= 7
        b //= 7
        if (x - y) % 7 not in (0, 1, 6):
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("corpus", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import load_base  # type: ignore

    raw = json.loads((root / "data" / "base_c7.json").read_text())
    base, _t, _e, ax = load_base(root / "data" / "base_c7.json")
    if not all(ax.values()):
        raise RuntimeError({k: v for k, v in ax.items() if not v})
    ring = base.ring
    I = set(map(int, raw["I0"]))
    private_pairs = [tuple(map(int, p)) for p in raw["private_pairs"]]
    owners = {p[0] for p in private_pairs}
    B = I - owners
    Q = {z for z in range(ring.n) if not (ring.NB[z] & B)}
    PH = set(map(int, raw["PH"]))
    PV = set(map(int, raw["PV"]))
    X = frozenset(map(int, raw["X"]))
    if len(B) != 359 or len(Q) != 16 or len(private_pairs) != 8:
        raise RuntimeError((len(B), len(Q), private_pairs))
    if set().union(*(set(p) for p in private_pairs)) != Q:
        raise RuntimeError("private pairs do not partition Q")
    # Exact Q graph must be eight disjoint edges and nothing else.
    for i, p in enumerate(private_pairs):
        if not conflict5(*p):
            raise RuntimeError(("private pair not edge", p))
        for j in range(i + 1, len(private_pairs)):
            for u in p:
                for v in private_pairs[j]:
                    if conflict5(u, v):
                        raise RuntimeError(("cross-pair Q conflict", i, j, u, v))

    corp = json.loads(args.corpus.read_text())
    sets = []
    for row in corp["sets"]:
        S = frozenset(map(int, row["points"]))
        if len(S) != 367:
            raise RuntimeError(("corpus size", row["sha256"], len(S)))
        # Independent replay of every public set.
        vv = sorted(S)
        for i, u in enumerate(vv):
            for v in vv[i + 1:]:
                if conflict5(u, v):
                    raise RuntimeError(("bad corpus independence", row["sha256"], u, v))
        sets.append((row["sha256"], tuple(row["sources"]), S))
    m = len(sets)
    if m == 0:
        raise RuntimeError("empty corpus")
    xidx = [i for i, (_h, _src, S) in enumerate(sets) if S == X]
    if len(xidx) != 1:
        raise RuntimeError(("BPZ-X corpus match", xidx))

    reference = {(q, z) for q in PH for z in X} | {(z, q) for q in PV for z in X}
    if len(reference) != 5872:
        raise RuntimeError(("reference size", len(reference)))

    # choice variable: side 0/1, pair index, endpoint 0/1, corpus-set index.
    choice = {}
    rev = {}
    nv = 0
    for side in (0, 1):
        for pi, pair in enumerate(private_pairs):
            for ei, q in enumerate(pair):
                for si in range(m):
                    nv += 1
                    choice[(side, pi, ei, si)] = nv
                    rev[nv] = (side, pi, ei, si)

    w = WCNF()
    onehot_clauses = 0
    # Exactly one endpoint+set choice per private pair on each side.
    for side in (0, 1):
        for pi in range(8):
            lits = [choice[(side, pi, ei, si)] for ei in (0, 1) for si in range(m)]
            w.append(lits)
            onehot_clauses += 1
            for a in range(len(lits)):
                for b in range(a + 1, len(lits)):
                    w.append([-lits[a], -lits[b]])
                    onehot_clauses += 1

    # Precompute whether a public 367 set avoids N[q].
    safe = {}
    for si, (_h, _src, S) in enumerate(sets):
        for q in Q:
            safe[(si, q)] = not any(z in ring.NB[q] for z in S)

    cross_clauses = 0
    for lpi, lpair in enumerate(private_pairs):
        for lei, q in enumerate(lpair):
            for rpi, rpair in enumerate(private_pairs):
                for rei, r in enumerate(rpair):
                    for si in range(m):
                        # left q x S is safe against right T x r if S avoids N[r]
                        if safe[(si, r)]:
                            continue
                        lv = choice[(0, lpi, lei, si)]
                        for ti in range(m):
                            # or T avoids N[q]
                            if safe[(ti, q)]:
                                continue
                            rv = choice[(1, rpi, rei, ti)]
                            w.append([-lv, -rv])
                            cross_clauses += 1

    # Exact additive outside-reference reward. Feasible left/right full fibers
    # cannot intersect: an intersection (q,r) would make both avoidance tests
    # false. Same-side fibers have distinct first/second Q coordinates.
    rewards = {}
    for side in (0, 1):
        for pi, pair in enumerate(private_pairs):
            for ei, q in enumerate(pair):
                for si, (_h, _src, S) in enumerate(sets):
                    if side == 0:
                        fiber = {(q, z) for z in S}
                    else:
                        fiber = {(z, q) for z in S}
                    reward = len(fiber - reference)
                    rewards[choice[(side, pi, ei, si)]] = reward
                    if reward:
                        w.append([choice[(side, pi, ei, si)]], weight=reward)

    with RC2(w, solver="g4", adapt=True, exhaust=True, incr=True, verbose=0) as rc2:
        model = rc2.compute()
    if model is None:
        raise RuntimeError("mixed-fiber global model UNSAT")
    pos = {z for z in model if z > 0}
    chosen = [rev[v] for v in range(1, nv + 1) if v in pos]
    if len(chosen) != 16:
        raise RuntimeError(("choice count", len(chosen)))

    periphery = set()
    assignments = []
    reward = 0
    for side, pi, ei, si in chosen:
        q = private_pairs[pi][ei]
        h, src, S = sets[si]
        fiber = {(q, z) for z in S} if side == 0 else {(z, q) for z in S}
        periphery.update(fiber)
        reward += rewards[choice[(side, pi, ei, si)]]
        assignments.append({"side": "L" if side == 0 else "R", "private_pair": pi,
                            "endpoint": q, "sha256": h, "sources": list(src),
                            "outside_reference": rewards[choice[(side, pi, ei, si)]]})
    if len(periphery) != 5872:
        raise RuntimeError(("periphery overlap", len(periphery)))
    if len(periphery - reference) != reward:
        raise RuntimeError(("reward drift", reward, len(periphery - reference)))

    # Full structural replay.
    pv = list(periphery)
    for i, p in enumerate(pv):
        nx, ny = ring.NB[p[0]], ring.NB[p[1]]
        for z in pv[i + 1:]:
            if z[0] in nx and z[1] in ny:
                raise RuntimeError(("periphery conflict", p, z))
    core = {(x, y) for x in B for y in B}
    cand = core | periphery
    if len(cand) != 134753:
        raise RuntimeError(("score", len(cand)))
    for p in periphery:
        nx, ny = ring.NB[p[0]], ring.NB[p[1]]
        for z in core:
            if z[0] in nx and z[1] in ny:
                raise RuntimeError(("core conflict", p, z))

    def enc(p):
        return "".join(str(d) for d in (ring.decode(p[0]) + ring.decode(p[1])))
    args.certificate.parent.mkdir(parents=True, exist_ok=True)
    args.certificate.write_text(json.dumps({"points": sorted(enc(p) for p in cand)}, separators=(",", ":")) + "\n")
    out = {
        "method": "exact-global-mixed-public367-full-fibers",
        "corpus_sets": m,
        "variables": nv,
        "onehot_clauses": onehot_clauses,
        "cross_clauses": cross_clauses,
        "score": 134753,
        "outside_reference": reward,
        "symmetric_difference_reference": 2 * reward,
        "assignments": sorted(assignments, key=lambda x: (x["side"], x["private_pair"])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "assignments"}, sort_keys=True))
    print("assignments", json.dumps(out["assignments"], sort_keys=True))


if __name__ == "__main__":
    main()
