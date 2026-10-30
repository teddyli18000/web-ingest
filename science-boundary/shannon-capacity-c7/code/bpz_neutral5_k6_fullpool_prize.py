#!/usr/bin/env python3
"""Exact full-support-pool neutral5 x k6 prize optimization.

The audited neutral-k5 witness sweeps only tested maximum 5-sets from each
factor.  This model uses every point in the complete support pools of all 30
outside-only neutral k5 owner sets and all four irreducible k6 defects.

For each of the 18 public terminal baselines, candidate ten-dimensional points
are the global union

    (U5 x U6) union (U6 x U5)

minus the baseline.  Selecting a candidate pays exactly for every baseline point
(core or terminal) that it conflicts with.  New-new conflicts are hard clauses.
Thus no fixed rectangle, fixed maximum witness, or predeclared core deletion is
assumed.

The lexicographic objective is:
  1. maximize true score gain = selected_new - distinct_deleted_baseline;
  2. among equal gain, maximize selected_new.

With n candidates, M=n+1 and soft weights M+1 on candidate selection and M on
keeping each touched baseline point make one unit of primary gain dominate every
possible secondary difference.  A positive gain is materialized for upstream
verification; a nonempty zero-gain optimum is a new equal-score mother basin.
"""
from __future__ import annotations

import argparse
import itertools
import json
import multiprocessing as mp
import os
from collections import defaultdict
from pathlib import Path

G = {}


def init_worker(state):
    global G
    G = state


def solve_terminal(task):
    from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    from bpz_joint_row_defects_maxsat import terminal_periphery

    q, r, orient = task
    ring, B, fam, U5, U6, core, cand_all = (
        G["ring"], G["B"], G["fam"], G["U5"], G["U6"], G["core"], G["cand_all"]
    )
    P = terminal_periphery(fam, q, r, orient)
    baseline = core | P
    if len(baseline) != 134753:
        raise RuntimeError(("baseline", q, r, orient, len(baseline)))

    cand = [p for p in cand_all if p not in baseline]
    n = len(cand)
    idx = {p: i for i, p in enumerate(cand)}
    byfirst = defaultdict(list)
    for p in P:
        byfirst[p[0]].append(p)
    first = set(byfirst)

    # Exact baseline losses. Core footprint is a support product; terminal
    # blockers are enumerated only through realized first-coordinate buckets.
    losses = []
    touched = set()
    for x, y in cand:
        L = {(a, b) for a in (ring.NB[x] & B) for b in (ring.NB[y] & B)}
        for a in ring.NB[x] & first:
            for p in byfirst[a]:
                if p[1] in ring.NB[y]:
                    L.add(p)
        if not L <= baseline:
            raise RuntimeError(("loss outside baseline", (x, y), len(L - baseline)))
        losses.append(L)
        touched.update(L)

    touched = sorted(touched)
    bidx = {p: i for i, p in enumerate(touched)}
    M = n + 1
    w = WCNF()
    implications = 0
    for i, L in enumerate(losses):
        for p in L:
            w.append([-(i + 1), n + bidx[p] + 1])
            implications += 1

    # Exact conflict graph among candidates. Iterate realized product
    # neighborhoods using a lookup table rather than all O(n^2) pairs.
    first_c = {x for x, _ in cand}
    second_c = {y for _, y in cand}
    nfirst = {x: ring.NB[x] & first_c for x in first_c}
    nsecond = {y: ring.NB[y] & second_c for y in second_c}
    conflicts = 0
    for i, (x, y) in enumerate(cand):
        for a in nfirst[x]:
            for b in nsecond[y]:
                j = idx.get((a, b))
                if j is not None and j > i:
                    w.append([-(i + 1), -(j + 1)])
                    conflicts += 1

    # Lexicographic true-gain, then exchange-size objective.
    for i in range(n):
        w.append([i + 1], weight=M + 1)
    for j in range(len(touched)):
        w.append([-(n + j + 1)], weight=M)

    with RC2(w, solver="g4", adapt=True, exhaust=True, incr=True, verbose=0) as rc2:
        model = rc2.compute()
    if model is None:
        raise RuntimeError(("RC2 no model", task))
    pos = {z for z in model if z > 0}
    chosen_idx = [i for i in range(n) if i + 1 in pos]
    selected = [cand[i] for i in chosen_idx]
    deleted = {touched[j] for j in range(len(touched)) if n + j + 1 in pos}
    forced = set()
    for i in chosen_idx:
        forced.update(losses[i])
    if deleted != forced:
        raise RuntimeError(("blocker drift", task, len(deleted), len(forced)))

    # Independent replay of the returned exchange.
    for i, p in enumerate(selected):
        nx, ny = ring.NB[p[0]], ring.NB[p[1]]
        for z in selected[i + 1:]:
            if z[0] in nx and z[1] in ny:
                raise RuntimeError(("new-new conflict", task, p, z))
        for z in baseline - deleted:
            if z[0] in nx and z[1] in ny:
                raise RuntimeError(("new-retained conflict", task, p, z))

    gain = len(selected) - len(deleted)
    return {
        "q": q,
        "r": r,
        "terminal_orientation": orient,
        "U5": len(U5),
        "U6": len(U6),
        "candidate_count": n,
        "touched_baseline": len(touched),
        "implications": implications,
        "conflict_clauses": conflicts,
        "selected": len(selected),
        "deleted": len(deleted),
        "gain": gain,
        "score": 134753 + gain,
        "selected_points": [list(p) for p in selected],
        "deleted_points": [list(p) for p in sorted(deleted)],
    }


def reconstruct_pool(groups, C, k):
    out = []
    C = tuple(sorted(C))
    for r in range(1, k + 1):
        for s in itertools.combinations(C, r):
            out.extend(groups.get(tuple(s), ()))
    return set(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("audit_json", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1))
    args = ap.parse_args()

    from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery
    from bpz_amplify_row_defects import PINNED_DEFECTS

    _base, ring, B, fam = load_geometry(args.tan_root.resolve())
    B = set(B)
    audit = json.loads(args.audit_json.read_text())
    neutral_rows = [r for r in audit.get("rows", []) if int(r["min_owner_intersection"]) == 0]
    if len(neutral_rows) != 30:
        raise RuntimeError(("expected 30 outside neutral5 owner sets", len(neutral_rows)))
    k6 = [d for d in PINNED_DEFECTS if len(d["owners"]) == 6]
    if len(k6) != 4:
        raise RuntimeError(("k6 count", len(k6)))

    groups = defaultdict(list)
    for z in range(ring.n):
        S = tuple(sorted(ring.NB[z] & B))
        if S and len(S) <= 6:
            groups[S].append(z)

    U5 = set()
    for row in neutral_rows:
        C = tuple(map(int, row["owners"]))
        P = reconstruct_pool(groups, C, 5)
        if len(P) != int(row["pool_size"]):
            raise RuntimeError(("neutral pool drift", C, len(P), row["pool_size"]))
        U5.update(P)
    U6 = set()
    for d in k6:
        C = tuple(map(int, d["owners"]))
        U6.update(reconstruct_pool(groups, C, 6))

    core = {(x, y) for x in B for y in B}
    cand_all = sorted({(x, y) for x in U5 for y in U6} | {(y, x) for x in U5 for y in U6})
    tasks = [(q, r, o) for q in ("O", "H", "V") for r in ("O", "H", "V") for o in (0, 1)]
    state = {"ring": ring, "B": B, "fam": fam, "U5": U5, "U6": U6, "core": core, "cand_all": cand_all}
    workers = max(1, min(args.workers, 4, len(tasks)))
    ctx = mp.get_context("fork")
    if workers == 1:
        init_worker(state)
        rows = [solve_terminal(t) for t in tasks]
    else:
        with ctx.Pool(workers, initializer=init_worker, initargs=(state,)) as proc:
            rows = list(proc.imap_unordered(solve_terminal, tasks, chunksize=1))
    rows.sort(key=lambda x: (x["gain"], x["selected"], -x["deleted"]), reverse=True)
    best = rows[0]

    materialized = False
    if best["selected"] > 0 and best["gain"] >= 0:
        P = terminal_periphery(fam, best["q"], best["r"], best["terminal_orientation"])
        baseline = core | P
        selected = {tuple(p) for p in best["selected_points"]}
        deleted = {tuple(p) for p in best["deleted_points"]}
        cand = (baseline - deleted) | selected
        if len(cand) != 134753 + best["gain"]:
            raise RuntimeError(("materialized score", len(cand), best["gain"]))
        def enc(p):
            return "".join(str(d) for d in (ring.decode(p[0]) + ring.decode(p[1])))
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps({"points": sorted(enc(p) for p in cand)}, separators=(",", ":")) + "\n")
        materialized = True

    out = {
        "method": "exact-fullpool-neutral5-k6-global-prize",
        "neutral_owner_sets": len(neutral_rows),
        "k6_defects": len(k6),
        "U5": len(U5),
        "U6": len(U6),
        "raw_union_candidates": len(cand_all),
        "scenario_count": len(rows),
        "positive_gain": sum(r["gain"] > 0 for r in rows),
        "nonempty_neutral": sum(r["gain"] == 0 and r["selected"] > 0 for r in rows),
        "best": best,
        "top10": rows[:10],
        "candidate_materialized": materialized,
        "candidate_score": 134753 + best["gain"] if materialized else None,
        "workers": workers,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "top10"}, sort_keys=True))


if __name__ == "__main__":
    main()
