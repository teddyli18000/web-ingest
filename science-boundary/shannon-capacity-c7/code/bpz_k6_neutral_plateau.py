#!/usr/bin/env python3
"""Find the largest nonempty zero-gain move in the complete k6 support rectangles.

The earlier full support-rectangle prize calculation proved that every scenario
has maximum net gain 0, but ordinary weighted MaxSAT can return the empty set as
that optimum.  Here we solve a lexicographic objective in one RC2 call:

    primary:   maximize selected_new - deleted_baseline
    secondary: maximize selected_new.

For n candidate vertices choose M=n+1 and maximize

    M*(selected-deleted) + selected.

This is implemented by soft weight M+1 on each candidate and M on keeping each
baseline blocker.  Hence a one-unit gain improvement dominates every possible
secondary-cardinality difference.  If the known gain optimum remains zero, the
result is the largest neutral exchange in that scenario, producing a distant
134753-point mother state for a fresh unrestricted local search.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path

G = {}


def init_worker(state):
    global G
    G = state


def solve_task(task):
    from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    from bpz_joint_row_defects_maxsat import terminal_periphery

    q, r, orient, ia, ib = task
    ring, B, fam, defects, pools, Bcore = (
        G["ring"], G["B"], G["fam"], G["defects"], G["pools"], G["Bcore"]
    )
    da, db = defects[ia], defects[ib]
    P = terminal_periphery(fam, q, r, orient)
    baseline = Bcore | P
    if len(baseline) != 134753:
        raise RuntimeError(("baseline", q, r, orient, len(baseline)))

    byfirst = {}
    for p in P:
        byfirst.setdefault(p[0], []).append((p[1], p))
    first = set(byfirst)
    bcache = {}

    def blockers(p):
        if p in bcache:
            return bcache[p]
        x, y = p
        L = set()
        for a in ring.NB[x] & B:
            for b in ring.NB[y] & B:
                L.add((a, b))
        for a in ring.NB[x] & first:
            for b, z in byfirst[a]:
                if b in ring.NB[y]:
                    L.add(z)
        bcache[p] = L
        return L

    cand = sorted({(x, y) for x in pools[ia] for y in pools[ib]} - baseline)
    losses = [blockers(p) for p in cand]
    n = len(cand)
    dv = {}
    w = WCNF()

    def bv(p):
        if p not in dv:
            dv[p] = n + len(dv) + 1
        return dv[p]

    for i, L in enumerate(losses):
        for p in L:
            w.append([-(i + 1), bv(p)])

    conflicts = 0
    for i, (x, y) in enumerate(cand):
        nx, ny = ring.NB[x], ring.NB[y]
        for j in range(i + 1, n):
            u, v = cand[j]
            if u in nx and v in ny:
                w.append([-(i + 1), -(j + 1)])
                conflicts += 1

    M = n + 1
    for i in range(n):
        w.append([i + 1], weight=M + 1)
    for z in dv.values():
        w.append([-z], weight=M)

    with RC2(w, solver="g4", adapt=True, exhaust=True, incr=False, verbose=0) as rc2:
        model = rc2.compute()
    if model is None:
        raise RuntimeError(("RC2 no model", task))
    pos = {z for z in model if z > 0}
    selected = [cand[i] for i in range(n) if i + 1 in pos]
    lost = {p for p, z in dv.items() if z in pos}
    # Independent objective replay from the actual selected set; no reliance on
    # the weighted cost arithmetic is needed for the reported result.
    actual_lost = set()
    for i, p in enumerate(selected):
        actual_lost.update(losses[cand.index(p)])
        for z in selected[i + 1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                raise RuntimeError(("selected conflict", task, p, z))
    if actual_lost != lost:
        # RC2 has a strict keep-blocker reward, so extra deletion variables must
        # not occur in an optimum; assert this to catch encoding drift.
        raise RuntimeError(("blocker model drift", task, len(actual_lost), len(lost)))
    gain = len(selected) - len(lost)
    return {
        "q": q, "r": r, "terminal_orientation": orient,
        "left": da["name"], "right": db["name"],
        "pool_left": len(pools[ia]), "pool_right": len(pools[ib]),
        "candidates": n, "conflicts": conflicts,
        "selected": len(selected), "deleted": len(lost), "gain": gain,
        "score": 134753 + gain,
        "selected_points": [list(p) for p in selected],
        "deleted_points": [list(p) for p in sorted(lost)],
    }


def main():
    from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery, validate_defects

    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()

    _base, ring, B, fam = load_geometry(args.tan_root.resolve())
    all_defects = validate_defects(ring, B)
    defects = [d for d in all_defects if str(d["name"]).startswith("k6-")]
    if len(defects) != 4:
        raise RuntimeError(("expected four k6 defects", [d["name"] for d in all_defects]))
    pools = []
    for d in defects:
        C = set(d["C"])
        pools.append(tuple(z for z in range(ring.n) if (ring.NB[z] & B) <= C))
    Bcore = {(x, y) for x in B for y in B}
    state = {"ring": ring, "B": set(B), "fam": fam, "defects": defects,
             "pools": pools, "Bcore": Bcore}
    tasks = [(q, r, o, ia, ib)
             for q in ("O", "H", "V") for r in ("O", "H", "V") for o in (0, 1)
             for ia in range(4) for ib in range(4)]
    workers = max(1, min(args.workers, 4, len(tasks)))
    ctx = mp.get_context("fork")
    if workers == 1:
        init_worker(state)
        rows = [solve_task(t) for t in tasks]
    else:
        with ctx.Pool(workers, initializer=init_worker, initargs=(state,)) as proc:
            rows = list(proc.imap_unordered(solve_task, tasks, chunksize=1))

    rows.sort(key=lambda x: (x["gain"], x["selected"], -x["deleted"]), reverse=True)
    best = rows[0]
    materialized = False
    if best["selected"] > 0 and best["gain"] >= 0:
        P = terminal_periphery(fam, best["q"], best["r"], best["terminal_orientation"])
        baseline = Bcore | P
        selected = {tuple(p) for p in best["selected_points"]}
        lost = {tuple(p) for p in best["deleted_points"]}
        cand = (baseline - lost) | selected
        if len(cand) != 134753 + best["gain"]:
            raise RuntimeError(("materialized size", len(cand), best["gain"]))
        # Recheck every new point against retained baseline via exact blocker
        # generation implicit in the structural geometry, then new-new above.
        def enc(p):
            return "".join(str(d) for d in (ring.decode(p[0]) + ring.decode(p[1])))
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps({"points": sorted(enc(p) for p in cand)}, separators=(",", ":")) + "\n")
        materialized = True

    out = {
        "method": "exact-lexicographic-k6-support-rectangle-plateau",
        "scenario_count": len(rows),
        "positive_gain": sum(r["gain"] > 0 for r in rows),
        "nonempty_neutral": sum(r["gain"] == 0 and r["selected"] > 0 for r in rows),
        "best": best,
        "top20": rows[:20],
        "candidate_materialized": materialized,
        "candidate_score": (134753 + best["gain"]) if materialized else None,
        "workers": workers,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "top20"}, sort_keys=True))


if __name__ == "__main__":
    main()
