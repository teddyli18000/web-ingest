#!/usr/bin/env python3
"""Exact C7^5 maximum-independent-set reformulation around a certified 315-core.

Let C be the 315-point independent core from molind/c7-five.  For any independent
Y outside C, every vertex of C not conflicting with Y can be added, so the best
extension of Y has size

    |Y| + |C| - |N_C(Y)|.

Hence alpha(C7^5) is exactly

    |C| + max_Y ( |Y| - |N_C(Y)| ),

with Y independent in V\C.  This is a prize-collecting MIS with only 315 blocker
variables.  Soft candidate clauses reward selected outside vertices; soft
negative blocker clauses charge each touched core vertex once.  Hard clauses
encode outside conflicts and candidate -> touched-core implications.

Vertex transitivity gives a lossless symmetry break that the completed solution
contains vertex 0.  If 0 lies in C we force its blocker false; otherwise we force
the outside candidate 0 true.

An exact optimum >=368 is squared to a Few Shots C7^10 certificate of size at
least 135424.  If an exact solver returns 367, the formulation itself is an exact
upper-bound route alpha(C7^5)=367; such a claim should still receive an
independent UNSAT/proof replay before publication.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
from pathlib import Path

from pysat.formula import WCNF
from pysat.examples.rc2 import RC2

Q = 7
D = 5
U = Q ** D
CORE_EXPECT = 315
TARGET = 368
POW = tuple(Q ** i for i in range(D))


def dec(v: int) -> tuple[int, ...]:
    return tuple((v // POW[i]) % Q for i in range(D))


def enc(w) -> int:
    return sum(int(w[i]) * POW[i] for i in range(D))


def neighbors(v: int):
    d = dec(v)
    for delta in itertools.product((-1, 0, 1), repeat=D):
        if all(x == 0 for x in delta):
            continue
        yield enc(tuple((d[i] + delta[i]) % Q for i in range(D)))


def conflict(a: int, b: int) -> bool:
    if a == b:
        return True
    da, db = dec(a), dec(b)
    return all((x - y) % Q in (0, 1, Q - 1) for x, y in zip(da, db))


def independent(s) -> bool:
    s = set(s)
    for v in s:
        for u in neighbors(v):
            if u in s:
                return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("c7five_root", type=Path)
    ap.add_argument("certificate", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--solver", default="g4")
    a = ap.parse_args()

    with gzip.open(a.c7five_root / "data" / "core-overlap.json.gz", "rt") as f:
        bundle = json.load(f)
    core = tuple(sorted(map(int, bundle["core"])))
    if len(core) != CORE_EXPECT or len(set(core)) != CORE_EXPECT or not independent(core):
        raise RuntimeError(("bad certified core", len(core), len(set(core))))
    core_set = set(core)
    outside = tuple(v for v in range(U) if v not in core_set)
    oi = {v: i for i, v in enumerate(outside)}
    ci = {v: i for i, v in enumerate(core)}

    # Candidate variables first, then one blocker variable per core point.
    cvar = {v: i + 1 for i, v in enumerate(outside)}
    block_base = len(outside) + 1
    bvar = {v: block_base + i for i, v in enumerate(core)}

    w = WCNF()
    outside_edges = 0
    support_implications = 0
    support_hist = {}

    for v in outside:
        sv = []
        for u in neighbors(v):
            if u in core_set:
                sv.append(u)
            elif u in oi and u > v:
                w.append([-cvar[v], -cvar[u]])
                outside_edges += 1
        support_hist[len(sv)] = support_hist.get(len(sv), 0) + 1
        for c in sv:
            w.append([-cvar[v], bvar[c]])
            support_implications += 1

    # Reward each chosen outside point, and reward each untouched core point.
    for v in outside:
        w.append([cvar[v]], weight=1)
    for c in core:
        w.append([-bvar[c]], weight=1)

    # Lossless graph-transitivity symmetry break: completed solution contains 0.
    if 0 in core_set:
        w.append([-bvar[0]])
        symmetry = {"kind": "core-zero-unblocked", "vertex": 0}
    else:
        w.append([cvar[0]])
        symmetry = {"kind": "outside-zero-selected", "vertex": 0}

    setup = {
        "method": "exact-c7p5-315core-prize-maxsat",
        "ambient_vertices": U,
        "core_size": len(core),
        "outside_vertices": len(outside),
        "outside_conflict_edges": outside_edges,
        "support_implications": support_implications,
        "support_size_histogram": {str(k): v for k, v in sorted(support_hist.items())},
        "soft_clauses": len(outside) + len(core),
        "target": TARGET,
        "solver": a.solver,
        "symmetry_break": symmetry,
        "core_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    with RC2(w, solver=a.solver, adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = int(rc2.cost)
    if model is None:
        raise RuntimeError("RC2 unexpectedly returned no model")
    pos = {x for x in model if x > 0}
    selected = {v for v in outside if cvar[v] in pos}

    # Independently reconstruct the true touched-core set from selected Y rather
    # than trusting blocker assignments in the MaxSAT model.
    blocked = set()
    for v in selected:
        blocked.update(u for u in neighbors(v) if u in core_set)
    completed = selected | (core_set - blocked)
    soft_total = len(outside) + len(core)
    maxsat_score = soft_total - cost
    if not independent(selected) or not independent(completed):
        raise RuntimeError("independence replay failed")
    if len(completed) != maxsat_score:
        raise RuntimeError(("objective replay mismatch", len(completed), maxsat_score, len(selected), len(blocked)))
    if 0 not in completed:
        raise RuntimeError("symmetry replay failed")

    st = {
        "candidate": len(completed) >= TARGET,
        "exact_optimum": len(completed),
        "prize": len(selected) - len(blocked),
        "selected_outside": len(selected),
        "activated_core_blockers": len(blocked),
        "rc2_cost": cost,
        "setup": setup,
        "points5": sorted(completed),
    }

    a.status.parent.mkdir(parents=True, exist_ok=True)
    a.status.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    print("RESULT", json.dumps({k: v for k, v in st.items() if k != "points5"}, sort_keys=True), flush=True)

    if len(completed) >= TARGET:
        S = sorted(completed)[:TARGET]
        if not independent(S):
            raise RuntimeError("target subset replay failed")
        pts = []
        digits = {v: dec(v) for v in S}
        for x in S:
            sx = "".join(map(str, digits[x]))
            for y in S:
                pts.append(sx + "".join(map(str, digits[y])))
        if len(pts) != TARGET * TARGET or len(set(pts)) != TARGET * TARGET:
            raise RuntimeError("squared certificate size")
        a.certificate.parent.mkdir(parents=True, exist_ok=True)
        a.certificate.write_text(json.dumps({"points": sorted(pts)}, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
