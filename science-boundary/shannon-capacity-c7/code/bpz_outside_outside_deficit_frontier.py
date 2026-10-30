#!/usr/bin/env python3
"""Terminal-aware outside-outside frontier for the pinned BPZ C7 construction.

The row/column reduction proves that a breakthrough not already implying
alpha(C7^5)>=368 must contain at least one new point (x,y) with x,y outside B.
This program searches such genuinely two-sided points without enumerating the
entire ~2.7e8 pair universe.

For a five-dimensional outsider z and terminal transversal q in {O,H,V}, define

    deficit_q(z) = |N[z] cap B| + |N[z] cap q| - 1.

This is the singleton version of the exact single-row 368 reduction.  Small
values identify factor vertices closest to row-wise neutrality.  For a chosen
cap d, scenario (q,r,o) uses

    Fq(d) x Fr(d)

as its outside-outside candidate universe, excluding baseline points.  Every
candidate's complete conflict set against the 134753-point baseline is priced
exactly.  We first solve maximum closure ignoring new-new conflicts.  If that
upper-bound relaxation is positive and the candidate set is small enough, we
solve the exact weighted MaxSAT with all strong-product conflicts.

This is an exact result only for the reported deficit-capped universes; it is a
frontier probe, not a proof for arbitrary outside-outside points.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from bpz_amplify_row_defects import Dinic
from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery

PINNED_COMMIT = "c753408492dde92a239708986d16c15dbf6c3235"


def max_closure(losses: list[set[tuple[int, int]]]):
    touched = sorted(set().union(*losses)) if losses else []
    bi = {p: i for i, p in enumerate(touched)}
    n, m = len(losses), len(touched)
    s, t = n + m, n + m + 1
    g = Dinic(t + 1)
    inf = n + m + 10
    for i, ls in enumerate(losses):
        g.add(s, i, 1)
        for p in ls:
            g.add(i, n + bi[p], inf)
    for j in range(m):
        g.add(n + j, t, 1)
    cut = g.flow(s, t)
    side = g.source_side(s)
    chosen = [i for i in range(n) if i in side]
    lost = set()
    for i in chosen:
        lost.update(losses[i])
    gain = len(chosen) - len(lost)
    if gain != n - cut:
        raise RuntimeError(("closure mismatch", gain, n - cut))
    return gain, chosen, lost


def factor_census(root: Path):
    _base, ring, B, fam = load_geometry(root)
    B = set(B)
    trans = {q: set(fam[q]) for q in ("O", "H", "V")}
    hist = {}
    counts = {q: {} for q in trans}
    factors = {q: {} for q in trans}
    sigs = set()
    for z in range(ring.n):
        if z in B:
            continue
        sb = frozenset(ring.NB[z] & B)
        hits = tuple(len(ring.NB[z] & trans[q]) for q in ("O", "H", "V"))
        key = (len(sb),) + hits
        hist[str(key)] = hist.get(str(key), 0) + 1
        sigs.add((sb, tuple(frozenset(ring.NB[z] & trans[q]) for q in ("O", "H", "V"))))
        for qi, q in enumerate(("O", "H", "V")):
            d = len(sb) + hits[qi] - 1
            counts[q][d] = counts[q].get(d, 0) + 1
            factors[q][z] = d
    return ring, B, fam, {
        "outsiders": ring.n - len(B),
        "unique_factor_signatures": len(sigs),
        "support_hit_histogram": hist,
        "deficit_histograms": {q: {str(k): v for k, v in sorted(h.items())} for q, h in counts.items()},
    }, factors


def solve_scenario(task):
    root_s, cap, q, r, orient, closure_limit, exact_limit = task
    root = Path(root_s)
    _base, ring, B, fam = load_geometry(root)
    B = set(B)
    P = terminal_periphery(fam, q, r, orient)
    core = {(a, b) for a in B for b in B}
    baseline = core | P
    if len(baseline) != 134753:
        raise RuntimeError(("baseline", len(baseline)))

    fq = [z for z in range(ring.n) if z not in B and len(ring.NB[z] & B) + len(ring.NB[z] & fam[q]) - 1 <= cap]
    fr = [z for z in range(ring.n) if z not in B and len(ring.NB[z] & B) + len(ring.NB[z] & fam[r]) - 1 <= cap]
    candidates = [(x, y) for x in fq for y in fr if (x, y) not in baseline]
    row = {
        "cap": cap, "q": q, "r": r, "terminal_orientation": orient,
        "left_factors": len(fq), "right_factors": len(fr), "candidates": len(candidates),
        "closure_gain": None, "closure_selected": None, "closure_deleted": None,
        "exact_gain": None, "selected": 0, "deleted": 0, "status": "counted",
    }
    if not candidates:
        row["closure_gain"] = 0
        row["status"] = "empty"
        return row
    if len(candidates) > closure_limit:
        row["status"] = "closure-skipped-size"
        return row

    by_first = {}
    for p in P:
        by_first.setdefault(p[0], []).append(p)
    first_keys = set(by_first)
    losses = []
    for x, y in candidates:
        hit = {(a, b) for a in (ring.NB[x] & B) for b in (ring.NB[y] & B)}
        for a in ring.NB[x] & first_keys:
            for p in by_first[a]:
                if p[1] in ring.NB[y]:
                    hit.add(p)
        if not hit <= baseline:
            raise RuntimeError(("loss outside baseline", x, y, len(hit - baseline)))
        losses.append(hit)

    t0 = time.time()
    cg, cs, cd = max_closure(losses)
    row.update({"closure_gain": cg, "closure_selected": len(cs), "closure_deleted": len(cd), "closure_seconds": time.time() - t0})
    if cg <= 0:
        row["status"] = "closure-closed"
        return row
    if len(candidates) > exact_limit:
        row["status"] = "closure-positive-exact-skipped-size"
        return row

    touched = sorted(set().union(*losses)); bi = {p: i for i, p in enumerate(touched)}
    ci = {p: i for i, p in enumerate(candidates)}
    nc = len(candidates)
    def xv(i): return i + 1
    def zv(j): return nc + j + 1
    w = WCNF(); implications = 0; conflicts = 0
    for i, ls in enumerate(losses):
        for p in ls:
            w.append([-xv(i), zv(bi[p])]); implications += 1
    fqs, frs = set(fq), set(fr)
    for i, (x, y) in enumerate(candidates):
        for a in ring.NB[x] & fqs:
            for b in ring.NB[y] & frs:
                j = ci.get((a, b))
                if j is not None and j > i:
                    w.append([-xv(i), -xv(j)]); conflicts += 1
    for i in range(nc): w.append([xv(i)], weight=1)
    for j in range(len(touched)): w.append([-zv(j)], weight=1)
    t1 = time.time()
    with RC2(w, solver="g4", adapt=True, exhaust=True, incr=True, verbose=0) as rc2:
        model = rc2.compute(); cost = rc2.cost
    if model is None:
        raise RuntimeError("RC2 no model")
    pos = {z for z in model if z > 0}
    sel = [i for i in range(nc) if xv(i) in pos]
    lost = {touched[j] for j in range(len(touched)) if zv(j) in pos}
    forced = set()
    for i in sel: forced.update(losses[i])
    if lost != forced:
        raise RuntimeError(("loss mismatch", len(lost), len(forced)))
    gain = len(sel) - len(lost)
    if gain != nc - cost:
        raise RuntimeError(("objective mismatch", gain, nc - cost))
    selected = [candidates[i] for i in sel]
    for i, p in enumerate(selected):
        for z in selected[i+1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                raise RuntimeError(("selected conflict", p, z))
    row.update({
        "status": "exact-rc2", "exact_gain": gain, "selected": len(sel), "deleted": len(lost),
        "touched_blockers": len(touched), "conflict_clauses": conflicts,
        "implications": implications, "exact_seconds": time.time() - t1,
    })
    if gain > 0:
        row["selected_points"] = [list(p) for p in selected]
        row["deleted_points"] = [list(p) for p in sorted(lost)]
    return row


def materialize(root: Path, best, out: Path):
    _base, ring, B, fam = load_geometry(root)
    P = terminal_periphery(fam, best["q"], best["r"], best["terminal_orientation"])
    baseline = {(a, b) for a in B for b in B} | P
    sel = {tuple(map(int, p)) for p in best["selected_points"]}
    dele = {tuple(map(int, p)) for p in best["deleted_points"]}
    cand = (baseline - dele) | sel
    score = len(cand)
    if score != 134753 + int(best["exact_gain"]):
        raise RuntimeError(("score", score, best["exact_gain"]))
    def enc(p): return "".join(str(z) for z in (ring.decode(p[0]) + ring.decode(p[1])))
    pts = sorted(enc(p) for p in cand)
    if len(pts) != len(set(pts)):
        raise RuntimeError("duplicates")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")
    return score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("--caps", default="0,1,2")
    ap.add_argument("--closure-limit", type=int, default=120000)
    ap.add_argument("--exact-limit", type=int, default=60000)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    a = ap.parse_args()
    root = a.tan_root.resolve()
    _ring, _B, _fam, census, _factors = factor_census(root)
    caps = [int(x) for x in a.caps.split(",") if x.strip()]
    tasks = [(str(root), cap, q, r, o, a.closure_limit, a.exact_limit)
             for cap in caps for q in ("O", "H", "V") for r in ("O", "H", "V") for o in (0, 1)]
    workers = max(1, min(a.workers, 4, len(tasks)))
    rows = []
    if workers == 1:
        rows = [solve_scenario(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs = [ex.submit(solve_scenario, t) for t in tasks]
            for f in as_completed(fs): rows.append(f.result())
    rows.sort(key=lambda x: ((x["exact_gain"] if x["exact_gain"] is not None else -10**9), (x["closure_gain"] if x["closure_gain"] is not None else -10**9)), reverse=True)
    exact_pos = [r for r in rows if (r.get("exact_gain") or 0) > 0]
    score = None
    best = exact_pos[0] if exact_pos else (rows[0] if rows else None)
    if exact_pos:
        score = materialize(root, best, a.certificate)
    out = {
        "method": "outside-outside-deficit-frontier",
        "source_commit": PINNED_COMMIT,
        "caps": caps,
        "closure_limit": a.closure_limit,
        "exact_limit": a.exact_limit,
        "workers": workers,
        "census": census,
        "scenario_count": len(rows),
        "positive_exact": len(exact_pos),
        "best": best,
        "candidate_materialized": bool(exact_pos),
        "candidate_score": score,
        "rows": rows,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k:v for k,v in out.items() if k not in ("rows","census")}, sort_keys=True))
    print(json.dumps({"deficit_histograms": census["deficit_histograms"], "unique_factor_signatures": census["unique_factor_signatures"]}, sort_keys=True))

if __name__ == "__main__":
    main()
