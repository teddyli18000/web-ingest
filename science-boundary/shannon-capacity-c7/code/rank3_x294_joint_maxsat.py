#!/usr/bin/env python3
"""Jointly optimize the free X_294 H fiber with all remaining rank-3 ports.

Unlike the Hall follow-ups, this does not freeze a previously chosen 134753
MaxSAT port model.  H(294,*) is replaced by an optional 367-point independent
fiber F, while every ordinary H/V safe endpoint remains live in the same RC2
optimization.  Thus the objective is the final port count itself.
"""

import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import IDPool, WCNF

import generalized9 as g
import rank3_square_relax as rs

SPECIAL = 294
BASELINE = 134753
BASE_SQUARE = 358 ** 2


def independent(vals, digits):
    return all(not g.conflict(a, b, digits) for a, b in combinations(vals, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--family", choices=("r0", "rank3", "x"), required=True)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = rs.load_rank3_state(r0, digits)
    supports, _ = g.support_masks(r, digits)

    kset = set(rs.RANK3_K9)
    kmask = sum(1 << i for i in rs.RANK3_K9)
    bidx = [i for i in range(g.R_SIZE) if i not in kset]
    bmask = sum(1 << i for i in bidx)
    zero = [i for i, x in enumerate(xset) if (supports[x] & bmask) == 0]
    if zero != [SPECIAL]:
        raise RuntimeError(f"zero-fiber drift: {zero}")

    safe = tuple(g.safe_vertices(kmask, supports))
    if len(safe) != 18:
        raise RuntimeError(f"safe endpoint drift: {len(safe)}")

    F = tuple(r0 if args.family == "r0" else r if args.family == "rank3" else xset)
    if len(F) != 367 or len(set(F)) != 367 or not independent(F, digits):
        raise RuntimeError("special fiber is not a 367-point independent set")

    pool = IDPool()
    def H(i, ei): return pool.id(("h", i, ei))
    def V(i, ei): return pool.id(("v", i, ei))
    def E(fi): return pool.id(("e", fi))

    w = WCNF()
    endpoint_edges = []
    for a, b in combinations(range(len(safe)), 2):
        if g.conflict(safe[a], safe[b], digits):
            endpoint_edges.append((a, b))

    # Ordinary same-orientation fibers.  The special H fiber needs no pair
    # clauses because F itself is independent.
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for a, b in endpoint_edges:
                w.append([-H(i, a), -H(i, b)])
        for a, b in endpoint_edges:
            w.append([-V(i, a), -V(i, b)])

    rel = []
    active = []
    for i, x in enumerate(xset):
        rr = [ei for ei, e in enumerate(safe) if g.conflict(e, x, digits)]
        rel.append(rr)
        if rr:
            active.append(i)

    ordinary_cross = 0
    for i in active:
        if i == SPECIAL:
            continue
        ri = rel[i]
        for j in active:
            rj = rel[j]
            for ei in rj:
                h = H(i, ei)
                for fi in ri:
                    w.append([-h, -V(j, fi)])
                    ordinary_cross += 1

    # Exact cross-conflicts between the arbitrary special H fiber (F_i, X294)
    # and every live V(j,e): both 5D coordinates must be confusable.
    special_rel = rel[SPECIAL]
    special_cross = 0
    hit_hist = []
    for fi, z in enumerate(F):
        hits = [j for j, x in enumerate(xset) if g.conflict(z, x, digits)]
        hit_hist.append(len(hits))
        ez = E(fi)
        for j in hits:
            for ei in special_rel:
                w.append([-ez, -V(j, ei)])
                special_cross += 1

    soft = []
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for ei in range(len(safe)):
                z = H(i, ei)
                soft.append(z)
                w.append([z], weight=1)
        for ei in range(len(safe)):
            z = V(i, ei)
            soft.append(z)
            w.append([z], weight=1)
    for fi in range(len(F)):
        z = E(fi)
        soft.append(z)
        w.append([z], weight=1)

    setup = {
        "family": args.family,
        "safe": len(safe),
        "special": SPECIAL,
        "special_rel": len(special_rel),
        "endpoint_edges": len(endpoint_edges),
        "ordinary_cross_clauses": ordinary_cross,
        "special_cross_clauses": special_cross,
        "soft_variables": len(soft),
        "variables": pool.top,
        "special_hit_min": min(hit_hist),
        "special_hit_max": max(hit_hist),
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    with RC2(w, solver="g3", adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError("joint MaxSAT unexpectedly UNSAT")

    pos = {z for z in model if z > 0}
    hs = [[] for _ in range(g.R_SIZE)]
    vs = [[] for _ in range(g.R_SIZE)]
    selected = 0
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for ei, e in enumerate(safe):
                if H(i, ei) in pos:
                    hs[i].append(e)
                    selected += 1
        for ei, e in enumerate(safe):
            if V(i, ei) in pos:
                vs[i].append(e)
                selected += 1
    hs[SPECIAL] = [F[fi] for fi in range(len(F)) if E(fi) in pos]
    selected += len(hs[SPECIAL])

    score = BASE_SQUARE + selected
    status = {
        "candidate": False,
        "method": "rank3-x294-joint-live-port-maxsat",
        "score": score,
        "selected_ports": selected,
        "selected_special_h": len(hs[SPECIAL]),
        "rc2_cost": cost,
        "setup": setup,
        "min_h": min(map(len, hs)),
        "max_h": max(map(len, hs)),
        "min_v": min(map(len, vs)),
        "max_v": max(map(len, vs)),
    }

    cert = rs.build_candidate(r, xset, bidx, hs, vs, [])
    if len(cert) != score:
        raise RuntimeError(f"candidate score mismatch: set={len(cert)} expected={score}")

    baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
    if score > BASELINE:
        status.update({
            "candidate": True,
            "removed_vs_baseline": len(baseline - cert),
            "added_vs_baseline": len(cert - baseline),
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(z) for z in sorted(cert)]}, separators=(",", ":")) + "\n"
        )

    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(("FOUND" if status["candidate"] else "NONE"), json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
