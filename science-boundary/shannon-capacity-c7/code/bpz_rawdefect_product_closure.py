#!/usr/bin/env python3
"""Exact prize closure for complete products of the five irreducible raw +1 defects.

For irreducible 5D defects C->Y and D->Z, YxZ is an independent 10D family.
Its raw margin over CxD is 11, 12, or 13 points.  For each public 134753 BPZ
terminal construction we optimize the *actual* exchange: every external product
candidate has reward +1 and forces deletion of every baseline point it conflicts
with.  Since all product candidates are mutually independent, the exact objective

    #selected external candidates - #distinct deleted baseline blockers

is a maximum-weight closure / s-t min cut.

The implementation groups work by the 18 terminal configurations.  Each worker
reuses one terminal-periphery index across all 25 ordered defect pairs, and each
min-cut contains only blockers actually touched by that pair.  A positive optimum
is structurally replayed, materialized as a full 10D certificate, and checked by
the upstream Few Shots verifier in CI.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
from pathlib import Path

from bpz_amplify_row_defects import Dinic
from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery, validate_defects

G = {}


def maximum_closure(losses: list[set[tuple[int, int]]]):
    touched = sorted(set().union(*losses) if losses else set())
    loc = {p: i for i, p in enumerate(touched)}
    ll = [{loc[p] for p in L} for L in losses]
    nc, nb = len(ll), len(touched)
    s, t = nc + nb, nc + nb + 1
    d = Dinic(t + 1)
    inf = nc + nb + 10
    for i, L in enumerate(ll):
        d.add(s, i, 1)
        for j in L:
            d.add(i, nc + j, inf)
    for j in range(nb):
        d.add(nc + j, t, 1)
    cut = d.flow(s, t)
    side = d.source_side(s)
    selected = [i for i in range(nc) if i in side]
    lost_local = set()
    for i in selected:
        lost_local.update(ll[i])
    delta = len(selected) - len(lost_local)
    if delta != nc - cut:
        raise RuntimeError(("closure mismatch", delta, nc - cut))
    return delta, selected, {touched[j] for j in lost_local}, len(touched)


def init_worker(state):
    global G
    G = state


def terminal_task(task):
    q, r, torient = task
    ring, B, fam, defects, Bcore = G["ring"], G["B"], G["fam"], G["defects"], G["Bcore"]
    P = terminal_periphery(fam, q, r, torient)
    baseline = Bcore | P
    if len(baseline) != 134753:
        raise RuntimeError(("baseline size drift", q, r, torient, len(baseline)))

    # Exact periphery blocker index by first coordinate.
    by_first: dict[int, list[tuple[int, tuple[int, int]]]] = {}
    for p in P:
        by_first.setdefault(p[0], []).append((p[1], p))
    first_keys = set(by_first)

    def blockers(x: int, y: int):
        L: set[tuple[int, int]] = set()
        # Core blockers.
        for a in ring.NB[x] & B:
            for b in ring.NB[y] & B:
                L.add((a, b))
        # Terminal-periphery blockers.
        for a in ring.NB[x] & first_keys:
            for b, p in by_first[a]:
                if b in ring.NB[y]:
                    L.add(p)
        return L

    results = []
    best = None
    for da in defects:
        for db in defects:
            raw = sorted({(x, y) for x in da["Y"] for y in db["Y"]})
            # Product of two independent 5D sets must be independent; replay it.
            for i, p in enumerate(raw):
                for z in raw[i + 1:]:
                    if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                        raise RuntimeError(("product not independent", da["name"], db["name"], p, z))
            cand = [p for p in raw if p not in baseline]
            losses = [blockers(x, y) for x, y in cand]
            delta, sel_idx, lost, touched = maximum_closure(losses)
            selected = [cand[i] for i in sel_idx]
            entry = {
                "q": q,
                "r": r,
                "terminal_orientation": torient,
                "left": da["name"],
                "right": db["name"],
                "left_k": len(da["C"]),
                "right_k": len(db["C"]),
                "raw_product": len(raw),
                "external_candidates": len(cand),
                "baseline_product_overlap": len(raw) - len(cand),
                "touched_blockers": touched,
                "selected": len(selected),
                "deleted": len(lost),
                "delta": delta,
                "score": 134753 + delta,
            }
            results.append(entry)
            rank = (delta, len(selected), -len(lost), len(cand))
            if best is None or rank > best[0]:
                best = (rank, entry, selected, lost)
    assert best is not None
    _rank, entry, selected, lost = best
    return {"results": results, "best": entry, "best_selected": selected, "best_lost": sorted(lost)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()
    root = args.tan_root.resolve()
    _base, ring, B, fam = load_geometry(root)
    defects = validate_defects(ring, B)
    if len(defects) != 5:
        raise RuntimeError(("irreducible defect count drift", len(defects)))

    # Recheck that these are genuinely irreducible independent 5D witnesses.
    for d in defects:
        C, Y = set(d["C"]), list(d["Y"])
        if C & set(Y):
            raise RuntimeError(("pinned defect reducible", d["name"], sorted(C & set(Y))))
        for i, y in enumerate(Y):
            for z in Y[i + 1:]:
                if z in ring.NB[y]:
                    raise RuntimeError(("Y not independent", d["name"], y, z))

    Bcore = {(a, b) for a in B for b in B}
    state = {"ring": ring, "B": B, "fam": fam, "defects": defects, "Bcore": Bcore}
    tasks = [(q, r, o) for q in ("O", "H", "V") for r in ("O", "H", "V") for o in (0, 1)]
    workers = max(1, min(args.workers, 4, len(tasks)))
    ctx = mp.get_context("fork")
    if workers == 1:
        init_worker(state)
        packs = [terminal_task(t) for t in tasks]
    else:
        with ctx.Pool(workers, initializer=init_worker, initargs=(state,)) as pool:
            packs = list(pool.imap_unordered(terminal_task, tasks, chunksize=1))

    results = [e for pack in packs for e in pack["results"]]
    best_pack = max(
        packs,
        key=lambda p: (p["best"]["delta"], p["best"]["selected"], -p["best"]["deleted"], p["best"]["external_candidates"]),
    )
    best = best_pack["best"]
    selected = {tuple(p) for p in best_pack["best_selected"]}
    lost = {tuple(p) for p in best_pack["best_lost"]}

    candidate_score = None
    if best["delta"] > 0:
        P = terminal_periphery(fam, best["q"], best["r"], best["terminal_orientation"])
        baseline = Bcore | P
        cand = (baseline - lost) | selected
        candidate_score = len(cand)
        if candidate_score != 134753 + best["delta"]:
            raise RuntimeError(("candidate size mismatch", candidate_score, best))
        # Independent local replay.
        sv = list(selected)
        for i, p in enumerate(sv):
            for z in sv[i + 1:]:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                    raise RuntimeError(("selected-selected conflict", p, z))
            for z in baseline - lost:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                    raise RuntimeError(("selected-retained conflict", p, z))

        def enc(p):
            return "".join(str(d) for d in (ring.decode(p[0]) + ring.decode(p[1])))

        pts = sorted(enc(p) for p in cand)
        if len(pts) != len(set(pts)):
            raise RuntimeError("duplicate encoded points")
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")

    results.sort(key=lambda e: (e["delta"], e["selected"], -e["deleted"], e["external_candidates"]), reverse=True)
    out = {
        "method": "exact-irreducible-rawdefect-product-maximum-closure",
        "defect_count": len(defects),
        "terminal_count": len(tasks),
        "scenario_count": len(results),
        "workers": workers,
        "best": best,
        "top20": results[:20],
        "candidate_materialized": best["delta"] > 0,
        "candidate_score": candidate_score,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
