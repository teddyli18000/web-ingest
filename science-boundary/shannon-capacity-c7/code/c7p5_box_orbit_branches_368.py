#!/usr/bin/env python3
"""Complete 50-branch symmetry decomposition of global C7^5 target 368.

After translation we may assume 00000 belongs to a putative independent set.
The automorphism stabilizer of 00000 contains arbitrary coordinate permutations
and independent coordinate reflections x -> -x.  Therefore every other vertex
is classified, up to this stabilizer, by the sorted multiset of its five cyclic
distances from zero, each in {0,1,2,3}.  There are C(8,5)=56 multisets; the six
using only {0,1} are confusable with 00000 and cannot occur.  Hence exactly 50
nonconfusable orbit types remain.

Every independent set of size at least two containing 00000 has a second point
of one of these types, and a stabilizer automorphism maps that point to the
canonical representative used here.  Thus solving all 50 branches with both
00000 and the representative fixed is a complete target-368 decision.

Each branch uses the exact 16807 product-clique constraints from
c7p5_box_cpsat_368.py.  The intended runner packs several single-worker CP-SAT
branches concurrently instead of consuming one hosted runner per orbit.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from ortools.sat.python import cp_model

from c7p5_box_cpsat_368 import N, TARGET, BITS, dec, enc, independent, word


def orbit_representatives():
    reps = []
    for ds in itertools.combinations_with_replacement(range(4), 5):
        if max(ds) <= 1:
            continue
        v = enc(ds)
        reps.append((ds, v))
    if len(reps) != 50 or len({v for _, v in reps}) != 50:
        raise RuntimeError(('orbit-count', len(reps)))
    return reps


def solve_branch(payload):
    idx, ds, rep, seconds, seed = payload
    model = cp_model.CpModel()
    x = [model.new_bool_var(f'x_{v}') for v in range(N)]
    for start in itertools.product(range(7), repeat=5):
        vids = [enc(tuple((start[i] + bits[i]) % 7 for i in range(5))) for bits in BITS]
        if len(set(vids)) != 32:
            raise RuntimeError(('box', start))
        model.add_at_most_one([x[v] for v in vids])
    model.add(x[0] == 1)
    model.add(x[rep] == 1)
    model.add(sum(x) >= TARGET)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(seconds)
    solver.parameters.num_search_workers = 1
    solver.parameters.cp_model_presolve = True
    solver.parameters.linearization_level = 2
    solver.parameters.random_seed = int(seed + idx * 1009)
    solver.parameters.log_search_progress = False
    t = time.time()
    st = solver.solve(model)
    wall = time.time() - t
    status = solver.status_name(st)
    chosen = []
    if st in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        chosen = [v for v in range(N) if solver.boolean_value(x[v])]
        if len(chosen) < TARGET or 0 not in chosen or rep not in chosen or not independent(chosen):
            raise RuntimeError(('branch-witness', idx, len(chosen)))
        if len(chosen) > TARGET:
            keep = [0, rep] + [v for v in chosen if v not in (0, rep)][: TARGET - 2]
            chosen = sorted(keep)
            if len(chosen) != TARGET or not independent(chosen):
                raise RuntimeError(('trim', idx))
    return {
        'branch': idx,
        'distance_multiset': list(ds),
        'representative': rep,
        'representative_word': word(rep),
        'status': status,
        'wall_seconds': wall,
        'conflicts': solver.num_conflicts,
        'branches': solver.num_branches,
        'candidate': bool(chosen),
        'chosen': chosen,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('output', type=Path)
    ap.add_argument('witness5', type=Path)
    ap.add_argument('certificate10', type=Path)
    ap.add_argument('--seconds-per-branch', type=float, default=1200.0)
    ap.add_argument('--processes', type=int, default=4)
    ap.add_argument('--seed', type=int, default=20261102)
    a = ap.parse_args()

    reps = orbit_representatives()
    tasks = [(i, ds, rep, a.seconds_per_branch, a.seed) for i, (ds, rep) in enumerate(reps)]
    rows = []
    witness = None
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.processes) as ex:
        fs = [ex.submit(solve_branch, t) for t in tasks]
        for f in as_completed(fs):
            r = f.result()
            rows.append(r)
            print(json.dumps({k: v for k, v in r.items() if k != 'chosen'}, sort_keys=True), flush=True)
            if r['candidate'] and witness is None:
                witness = r
                for q in fs:
                    q.cancel()
                break

    rows.sort(key=lambda r: r['branch'])
    candidate = witness is not None
    if candidate:
        chosen = witness['chosen']
        a.witness5.parent.mkdir(parents=True, exist_ok=True)
        a.witness5.write_text(json.dumps({'points': [word(v) for v in chosen]}, separators=(',', ':')) + '\n')
        words = [word(v) for v in chosen]
        pts10 = sorted(u + v for u in words for v in words)
        a.certificate10.parent.mkdir(parents=True, exist_ok=True)
        a.certificate10.write_text(json.dumps({'points': pts10}, separators=(',', ':')) + '\n')

    complete = len(rows) == 50 and all(r['status'] == 'INFEASIBLE' for r in rows)
    out = {
        'method': 'complete-c7p5-stabilizer-orbit-box-cpsat-target368',
        'orbit_branches': 50,
        'completed_rows': len(rows),
        'infeasible_rows': sum(r['status'] == 'INFEASIBLE' for r in rows),
        'unknown_rows': sum(r['status'] == 'UNKNOWN' for r in rows),
        'candidate_368': candidate,
        'exact_alpha_367': complete,
        'seconds_per_branch': a.seconds_per_branch,
        'processes': a.processes,
        'wall_seconds': time.time() - t0,
        'rows': [{k: v for k, v in r.items() if k != 'chosen'} for r in rows],
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k != 'rows'}, sort_keys=True))


if __name__ == '__main__':
    main()
