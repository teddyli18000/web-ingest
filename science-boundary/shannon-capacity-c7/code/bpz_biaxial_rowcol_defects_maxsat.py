#!/usr/bin/env python3
"""Exact simultaneous row+column amplification of the five BPZ raw +1 defects.

This strictly extends the one-axis mixed-mode model.  Each B row may choose at
most one defect C_m->Y_m, and independently each B column may choose at most one.
Same-axis choices are automatically mutually nonconfusable because B is an
independent set.

A row choice (a,m) and column choice (b,n) have one extra *core overlap bonus*
when b in C_m and a in C_n: the core point (a,b) is deleted by both operations,
so the union of deleted core points costs one less than the sum of the two
individual costs.  If their newly introduced points conflict, the two choices
are instead hard-incompatible.  Otherwise an AND variable records the +1 bonus.

For each of the 18 public terminal peripheries we solve exactly

  max  (#row choices + #column choices + #core overlaps) - #periphery losses

with weighted MaxSAT.  A positive optimum is reconstructed as a full 10D
certificate and independently verified by the Few Shots verifier in CI.
"""
from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from bpz_joint_row_defects_maxsat import (
    PINNED_COMMIT,
    load_geometry,
    terminal_periphery,
    validate_defects,
)


def solve_scenario(args):
    root_s, q, r, torient = args
    root = Path(root_s)
    _base, ring, B, fam = load_geometry(root)
    defects = validate_defects(ring, B)
    P = terminal_periphery(fam, q, r, torient)
    pv = sorted(P)
    Bv = sorted(B)
    bix = {a: i for i, a in enumerate(Bv)}
    M = len(defects)
    nside = len(Bv) * M

    by_first = {}
    for j, (u, v) in enumerate(pv):
        by_first.setdefault(u, []).append((v, j))
    first_keys = set(by_first)

    def blockers(n):
        u, v = n
        hit = set()
        for x in ring.NB[u] & first_keys:
            for y, j in by_first[x]:
                if y in ring.NB[v]:
                    hit.add(j)
        return hit

    def rv(i, m):
        return 1 + i * M + m

    def cv(i, m):
        return 1 + nside + i * M + m

    zbase = 2 * nside

    def zv(j):
        return 1 + zbase + j

    w = WCNF()
    # At most one mode per physical row / per physical column.
    for i in range(len(Bv)):
        for m in range(M):
            for n in range(m + 1, M):
                w.append([-rv(i, m), -rv(i, n)])
                w.append([-cv(i, m), -cv(i, n)])

    row_loss = [[set() for _ in range(M)] for _ in Bv]
    col_loss = [[set() for _ in range(M)] for _ in Bv]
    implications = 0
    for i, a in enumerate(Bv):
        for m, d in enumerate(defects):
            lr = set()
            lc = set()
            for y in d["Y"]:
                lr.update(blockers((a, y)))
                lc.update(blockers((y, a)))
            row_loss[i][m] = lr
            col_loss[i][m] = lc
            for j in lr:
                w.append([-rv(i, m), zv(j)])
                implications += 1
            for j in lc:
                w.append([-cv(i, m), zv(j)])
                implications += 1

    # Selection profits.
    for i in range(len(Bv)):
        for m in range(M):
            w.append([rv(i, m)], weight=1)
            w.append([cv(i, m)], weight=1)

    # Cross-axis interactions occur only at potential core-overlap coordinates.
    nextvar = zbase + len(pv) + 1
    overlap_vars = {}
    cross_incompat = 0
    for m, dm in enumerate(defects):
        for n, dn in enumerate(defects):
            for a in dn["C"]:  # row label belongs to column-mode owner set
                ia = bix[a]
                for b in dm["C"]:  # column label belongs to row-mode owner set
                    ib = bix[b]
                    # Exact new-new conflict test between {a}xY_m and Y_nx{b}.
                    bad = any(
                        z in ring.NB[a] and b in ring.NB[y]
                        for y in dm["Y"]
                        for z in dn["Y"]
                    )
                    x, yv = rv(ia, m), cv(ib, n)
                    if bad:
                        w.append([-x, -yv])
                        cross_incompat += 1
                    else:
                        o = nextvar
                        nextvar += 1
                        overlap_vars[(ia, m, ib, n)] = o
                        # o <-> (x and yv)
                        w.append([-o, x])
                        w.append([-o, yv])
                        w.append([-x, -yv, o])
                        w.append([o], weight=1)

    # Periphery losses cost one each.
    for j in range(len(pv)):
        w.append([-zv(j)], weight=1)

    soft_selection = 2 * nside + len(overlap_vars)
    with RC2(w, solver="g3", adapt=True, exhaust=True, incr=True, verbose=0) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError("RC2 returned no model")
    pos = {z for z in model if z > 0}

    rows = []
    cols = []
    loss_union = set()
    for i, a in enumerate(Bv):
        rm = [m for m in range(M) if rv(i, m) in pos]
        cm = [m for m in range(M) if cv(i, m) in pos]
        if len(rm) > 1 or len(cm) > 1:
            raise RuntimeError(("partition violation", a, rm, cm))
        if rm:
            m = rm[0]
            rows.append((a, m))
            loss_union.update(row_loss[i][m])
        if cm:
            m = cm[0]
            cols.append((a, m))
            loss_union.update(col_loss[i][m])
    zchosen = {j for j in range(len(pv)) if zv(j) in pos}
    if zchosen != loss_union:
        raise RuntimeError(("loss model mismatch", len(zchosen), len(loss_union)))

    expected_overlap = 0
    selected_r = {(bix[a], m) for a, m in rows}
    selected_c = {(bix[a], m) for a, m in cols}
    chosen_overlap = 0
    for key, o in overlap_vars.items():
        ia, m, ib, n = key
        both = (ia, m) in selected_r and (ib, n) in selected_c
        if (o in pos) != both:
            raise RuntimeError(("overlap AND mismatch", key, o in pos, both))
        if both:
            chosen_overlap += 1
    # Any selected cross pair excluded from overlap_vars must not be a potential
    # overlap unless it was hard-incompatible (which an optimum cannot select).
    for a, m in rows:
        for b, n in cols:
            if a in defects[n]["C"] and b in defects[m]["C"]:
                expected_overlap += 1
    if expected_overlap != chosen_overlap:
        raise RuntimeError(("overlap count mismatch", expected_overlap, chosen_overlap))

    delta = len(rows) + len(cols) + chosen_overlap - len(loss_union)
    if delta != soft_selection - cost:
        raise RuntimeError(("objective mismatch", delta, soft_selection - cost))
    return {
        "q": q,
        "r": r,
        "terminal_orientation": torient,
        "delta": delta,
        "row_choices": [[a, defects[m]["name"]] for a, m in rows],
        "column_choices": [[a, defects[m]["name"]] for a, m in cols],
        "row_count": len(rows),
        "column_count": len(cols),
        "core_overlap_bonus": chosen_overlap,
        "loss_count": len(loss_union),
        "loss_indices": sorted(loss_union),
        "overlap_vars": len(overlap_vars),
        "cross_incompatibilities": cross_incompat,
        "implications": implications,
        "hard": len(w.hard),
        "soft": len(w.soft),
    }


def materialize(root: Path, best, out_cert: Path):
    _base, ring, B, fam = load_geometry(root)
    defects0 = validate_defects(ring, B)
    defects = {d["name"]: d for d in defects0}
    P = terminal_periphery(fam, best["q"], best["r"], best["terminal_orientation"])
    pv = sorted(P)
    loss = {pv[j] for j in best["loss_indices"]}
    rows = [(int(a), defects[name]) for a, name in best["row_choices"]]
    cols = [(int(a), defects[name]) for a, name in best["column_choices"]]

    removed = set()
    new = set()
    for a, d in rows:
        removed.update((a, c) for c in d["C"])
        new.update((a, y) for y in d["Y"])
    for b, d in cols:
        removed.update((c, b) for c in d["C"])
        new.update((y, b) for y in d["Y"])
    core = {(a, b) for a in B for b in B}
    if not removed <= core or new & core:
        raise RuntimeError("candidate core partition drift")
    kept_p = P - loss

    def cf10(x, y):
        return y[0] in ring.NB[x[0]] and y[1] in ring.NB[x[1]]

    for n in new:
        sb0 = ring.NB[n[0]] & B
        sb1 = ring.NB[n[1]] & B
        if any((u, v) not in removed for u in sb0 for v in sb1):
            raise RuntimeError(("new hits retained core", n))
        if any(cf10(n, p) for p in kept_p):
            raise RuntimeError(("new hits retained periphery", n))
    nv = list(new)
    for i, x in enumerate(nv):
        for y in nv[i + 1:]:
            if cf10(x, y):
                raise RuntimeError(("new-new conflict", x, y))

    cand = (core - removed) | kept_p | new
    expected = 134753 + int(best["delta"])
    if len(cand) != expected:
        raise RuntimeError(("score mismatch", len(cand), expected, len(removed), len(new), len(loss)))

    def encode(p):
        return "".join(str(z) for z in (ring.decode(p[0]) + ring.decode(p[1])))

    pts = sorted(encode(p) for p in cand)
    if len(pts) != len(set(pts)):
        raise RuntimeError("duplicate certificate points")
    out_cert.parent.mkdir(parents=True, exist_ok=True)
    out_cert.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")
    return len(pts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()
    root = args.tan_root.resolve()
    tasks = [(str(root), q, r, o)
             for q in ("O", "H", "V")
             for r in ("O", "H", "V")
             for o in (0, 1)]
    workers = max(1, min(args.workers, len(tasks), 4))
    results = []
    if workers == 1:
        for t in tasks:
            results.append(solve_scenario(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(solve_scenario, t) for t in tasks]
            for f in as_completed(futs):
                results.append(f.result())
    results.sort(key=lambda x: (x["delta"], x["row_count"] + x["column_count"], x["core_overlap_bonus"]), reverse=True)
    best = results[0]
    score = None
    if best["delta"] > 0:
        score = materialize(root, best, args.certificate)
    out = {
        "method": "exact-biaxial-row-column-defect-weighted-maxsat",
        "source_commit": PINNED_COMMIT,
        "scenario_count": len(results),
        "workers": workers,
        "best": best,
        "top10": results[:10],
        "candidate_materialized": best["delta"] > 0,
        "candidate_score": score,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
