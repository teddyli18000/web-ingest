#!/usr/bin/env python3
"""Exact one-new-vertex 368 decision relative to the validated public 367-set union.

Let U be the 1525-vertex union of the 40 validated public C7^5 independent sets
of size 367.  A 368-set using exactly one vertex v outside U exists iff
U \ N[v] contains an independent set of size 367.

Outside vertices with the same closed-neighbourhood signature N[v]∩U are
interchangeable in this one-new problem.  We therefore keep one representative
per distinct signature and solve one CP-SAT instance:

  exactly one outside signature is chosen;
  at least 367 vertices of U are chosen;
  all conflicts inside U and all outside-to-U conflicts are forbidden.

SAT yields an independently replayed 368-word witness and its 135424-point
C7^10 square.  INFEASIBLE proves that every 368-set must use at least two
vertices outside the current public union.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from ortools.sat.python import cp_model

from public367_union_cpsat import dec, enc, graph_from_corpus, independent, word5, OFFSETS


def signature(v: int, uid: dict[int, int]) -> tuple[int, ...]:
    d = dec(v)
    hit = []
    for off in OFFSETS:
        w = enc(tuple((d[k] + off[k]) % 7 for k in range(5)))
        i = uid.get(w)
        if i is not None:
            hit.append(i)
    return tuple(sorted(set(hit)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("witness5", type=Path)
    ap.add_argument("certificate10", type=Path)
    ap.add_argument("--seconds", type=float, default=18000.0)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    rows, seeds, universe, edges = graph_from_corpus(a.corpus)
    U = set(universe)
    uid = {v: i for i, v in enumerate(universe)}

    groups = defaultdict(list)
    t0 = time.time()
    for v in range(7**5):
        if v in U:
            continue
        groups[signature(v, uid)].append(v)
    sigs = sorted(groups, key=lambda s: (len(s), s))
    reps = [min(groups[s]) for s in sigs]

    # Immediate replay against every known 367 seed before invoking CP-SAT.
    seed_sets = [set(s) for s in seeds]
    direct = None
    for sig, rep in zip(sigs, reps):
        hit = {universe[i] for i in sig}
        for si, S in enumerate(seed_sets):
            if S.isdisjoint(hit):
                direct = (rep, si, sorted(S | {rep}))
                break
        if direct:
            break

    model = cp_model.CpModel()
    xu = [model.new_bool_var(f"u_{i}") for i in range(len(universe))]
    xo = [model.new_bool_var(f"o_{j}") for j in range(len(sigs))]
    for i, j in edges:
        model.add_at_most_one(xu[i], xu[j])
    for j, sig in enumerate(sigs):
        oj = xo[j]
        for i in sig:
            model.add_at_most_one(oj, xu[i])
    model.add_exactly_one(xo)
    model.add(sum(xu) >= 367)

    # A known 367 set gives a strong U-side hint.  Hints are not constraints.
    hs = seed_sets[0]
    for i, v in enumerate(universe):
        if v in hs:
            model.add_hint(xu[i], 1)

    chosen = []
    selected_outside_rep = None
    status_name = "DIRECT_SEED_WITNESS" if direct else None
    wall = 0.0
    conflicts = 0
    branches = 0
    if direct:
        chosen = direct[2]
        selected_outside_rep = direct[0]
    else:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = a.seconds
        solver.parameters.num_search_workers = a.workers
        solver.parameters.cp_model_presolve = True
        solver.parameters.linearization_level = 2
        solver.parameters.log_search_progress = True
        t = time.time()
        st = solver.solve(model)
        wall = time.time() - t
        status_name = solver.status_name(st)
        conflicts = solver.num_conflicts
        branches = solver.num_branches
        if st in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            outs = [j for j in range(len(sigs)) if solver.boolean_value(xo[j])]
            if len(outs) != 1:
                raise RuntimeError(("outside-count", outs))
            j = outs[0]
            selected_outside_rep = reps[j]
            chosen = [universe[i] for i in range(len(universe)) if solver.boolean_value(xu[i])]
            chosen.append(selected_outside_rep)

    candidate = bool(chosen)
    if candidate:
        chosen = sorted(chosen)
        if len(chosen) < 368 or not independent(chosen):
            raise RuntimeError(("witness-replay", len(chosen)))
        # Trim any surplus U points while preserving the selected outside point.
        if len(chosen) > 368:
            o = selected_outside_rep
            rest = [v for v in chosen if v != o][:367]
            chosen = sorted(rest + [o])
            if len(chosen) != 368 or not independent(chosen):
                raise RuntimeError("trim-replay")
        a.witness5.parent.mkdir(parents=True, exist_ok=True)
        a.witness5.write_text(json.dumps({"points": [word5(v) for v in chosen]}, separators=(",", ":")) + "\n")
        w = [word5(v) for v in chosen]
        pts10 = sorted(x + y for x in w for y in w)
        if len(pts10) != 368 * 368:
            raise RuntimeError(("square-size", len(pts10)))
        a.certificate10.parent.mkdir(parents=True, exist_ok=True)
        a.certificate10.write_text(json.dumps({"points": pts10}, separators=(",", ":")) + "\n")

    out = {
        "method": "exact-public367-union-one-new-cpsat",
        "distinct_public_sets": len(rows),
        "union_vertices": len(universe),
        "union_conflict_edges": len(edges),
        "outside_vertices": 7**5 - len(universe),
        "distinct_outside_signatures": len(sigs),
        "signature_size_histogram": dict(sorted(Counter(map(len, sigs)).items())),
        "max_signature_multiplicity": max(map(len, groups.values())),
        "census_seconds": time.time() - t0 - wall,
        "solver_status": status_name,
        "solver_wall_seconds": wall,
        "solver_conflicts": conflicts,
        "solver_branches": branches,
        "candidate_368": candidate,
        "selected_outside_representative": selected_outside_rep,
        "score10": 368 * 368 if candidate else None,
        "exact_one_new_excluded": status_name == "INFEASIBLE",
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
