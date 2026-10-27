#!/usr/bin/env python3
"""Exact live-port MaxSAT with H(X_294) free over all 7^5 endpoints.

The rank-3 square block and all ordinary safe H/V fibers remain fixed as a
structural scaffold.  The special H fiber is no longer chosen from a known
367-set: every 5D point is a variable, with the full C7^5 conflict graph
encoded exactly.  This removes the last preselected 5D-fiber assumption in the
X_294 route while keeping the problem small enough for a sparse MaxSAT model.
"""

import argparse
import json
from itertools import combinations, product
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import IDPool, WCNF

import generalized9 as g
import rank3_square_relax as rs

SPECIAL = 294
BASELINE = 134753
BASE_SQUARE = 358 ** 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
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
        raise RuntimeError(f"safe drift: {len(safe)}")

    pool = IDPool()
    def H(i, ei): return pool.id(("h", i, ei))
    def V(i, ei): return pool.id(("v", i, ei))
    def E(v): return pool.id(("e", v))

    w = WCNF()
    endpoint_edges = [(a, b) for a, b in combinations(range(len(safe)), 2)
                      if g.conflict(safe[a], safe[b], digits)]
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
            for ei in rel[j]:
                h = H(i, ei)
                for fi in ri:
                    w.append([-h, -V(j, fi)])
                    ordinary_cross += 1

    # Full exact C7^5 conflict graph on the special endpoint variables.
    # Every nonzero delta in {-1,0,1}^5 gives one confusable neighbor;
    # v<u keeps each undirected edge exactly once.
    deltas = tuple(d for d in product((-1, 0, 1), repeat=5) if any(d))
    special_edges = 0
    for v in range(g.U):
        a = digits[v]
        for d in deltas:
            u = g.enc5(tuple((a[k] + d[k]) % 7 for k in range(5)))
            if u <= v:
                continue
            w.append([-E(v), -E(u)])
            special_edges += 1
    expected_edges = g.U * (3 ** 5 - 1) // 2
    if special_edges != expected_edges:
        raise RuntimeError(f"special edge drift {special_edges} != {expected_edges}")

    # Build inverse neighborhoods of X.  Cross-conflict with V(j,e) occurs iff
    # z~X_j and X_294~e.
    xhits = [[] for _ in range(g.U)]
    for j, x in enumerate(xset):
        for v in rs.neighborhood(x, digits):
            xhits[v].append(j)
    special_rel = rel[SPECIAL]
    special_cross = 0
    for v in range(g.U):
        ev = E(v)
        for j in xhits[v]:
            for ei in special_rel:
                w.append([-ev, -V(j, ei)])
                special_cross += 1

    soft = []
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for ei in range(len(safe)):
                z = H(i, ei); soft.append(z); w.append([z], weight=1)
        for ei in range(len(safe)):
            z = V(i, ei); soft.append(z); w.append([z], weight=1)
    for v in range(g.U):
        z = E(v); soft.append(z); w.append([z], weight=1)

    setup = {
        "safe": len(safe),
        "special": SPECIAL,
        "special_rel": len(special_rel),
        "endpoint_edges": len(endpoint_edges),
        "ordinary_cross_clauses": ordinary_cross,
        "special_independence_edges": special_edges,
        "special_cross_clauses": special_cross,
        "soft_variables": len(soft),
        "variables": pool.top,
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    with RC2(w, solver="g3", adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError("ambient joint MaxSAT unexpectedly UNSAT")
    pos = {z for z in model if z > 0}

    hs = [[] for _ in range(g.R_SIZE)]
    vs = [[] for _ in range(g.R_SIZE)]
    selected = 0
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for ei, e in enumerate(safe):
                if H(i, ei) in pos:
                    hs[i].append(e); selected += 1
        for ei, e in enumerate(safe):
            if V(i, ei) in pos:
                vs[i].append(e); selected += 1
    hs[SPECIAL] = [v for v in range(g.U) if E(v) in pos]
    selected += len(hs[SPECIAL])

    # Replay special-fiber independence independently of the SAT encoding.
    for a, b in combinations(hs[SPECIAL], 2):
        if g.conflict(a, b, digits):
            raise RuntimeError("special H solution is not independent")

    score = BASE_SQUARE + selected
    cert = rs.build_candidate(r, xset, bidx, hs, vs, [])
    if len(cert) != score:
        raise RuntimeError(f"candidate score mismatch: {len(cert)} != {score}")

    status = {
        "candidate": score > BASELINE,
        "method": "rank3-x294-full-ambient-live-port-maxsat",
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

    if score > BASELINE:
        baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
        status["removed_vs_baseline"] = len(baseline - cert)
        status["added_vs_baseline"] = len(cert - baseline)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(z) for z in sorted(cert)]}, separators=(",", ":")) + "\n"
        )

    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(("FOUND" if status["candidate"] else "NONE"), json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
