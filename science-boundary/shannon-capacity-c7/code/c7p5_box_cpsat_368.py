#!/usr/bin/env python3
"""Global exact C7^5 target-368 CP-SAT using 32-point product cliques.

For each a in Z_7, {a,a+1} is a clique of C7.  Choosing one such edge in each
of five coordinates gives a 32-word clique in C7^5.  There are exactly 7^5
such boxes.  Conversely any two confusable five-letter words lie together in
at least one such box, because in every coordinate their symbols are equal or
adjacent on C7.  Therefore 16807 AtMostOne constraints on these boxes encode
the full C7^5 conflict graph exactly, replacing 2,033,647 pairwise edge clauses.

The graph is vertex-transitive, so any nonempty independent set can be translated
to contain 00000.  We impose x_00000=1 as an exact symmetry break.  A translated
public 367-set is supplied as a hint only.  FEASIBLE gives a 368 witness and its
135424-point square; INFEASIBLE proves alpha(C7^5)=367.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from pathlib import Path

from ortools.sat.python import cp_model

N = 7**5
TARGET = 368
OFFSETS = tuple(itertools.product((-1, 0, 1), repeat=5))
BITS = tuple(itertools.product((0, 1), repeat=5))


def dec(v: int):
    d = [0] * 5
    for i in range(4, -1, -1):
        d[i] = v % 7
        v //= 7
    return tuple(d)


def enc(d):
    v = 0
    for x in d:
        v = 7 * v + x
    return v


def word(v: int):
    return ''.join(map(str, dec(v)))


def independent(S):
    ss = set(S)
    if len(ss) != len(S):
        return False
    for v in S:
        d = dec(v)
        for off in OFFSETS:
            if off == (0, 0, 0, 0, 0):
                continue
            w = enc(tuple((d[i] + off[i]) % 7 for i in range(5)))
            if w in ss and w > v:
                return False
    return True


def translate_to_zero(S):
    p = min(S)
    shift = dec(p)
    T = sorted(enc(tuple((x - shift[i]) % 7 for i, x in enumerate(dec(v)))) for v in S)
    if 0 not in T or len(T) != len(set(T)) or not independent(T):
        raise RuntimeError('translation replay')
    return T, p, shift


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tan_root', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('witness5', type=Path)
    ap.add_argument('certificate10', type=Path)
    ap.add_argument('--seconds', type=float, default=19800.0)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()

    raw = json.loads((a.tan_root / 'data' / 'base_c7.json').read_text())
    seed = sorted(map(int, raw['I0']))
    if len(seed) != 367 or not independent(seed):
        raise RuntimeError(('bad-I0', len(seed)))
    hint, source_point, shift = translate_to_zero(seed)

    model = cp_model.CpModel()
    x = [model.new_bool_var(f'x_{v}') for v in range(N)]
    box_count = 0
    membership_count = 0
    for start in itertools.product(range(7), repeat=5):
        box = []
        for bits in BITS:
            d = tuple((start[i] + bits[i]) % 7 for i in range(5))
            box.append(x[enc(d)])
        if len(set(box)) != 32:
            raise RuntimeError(('box-duplicate', start))
        model.add_at_most_one(box)
        box_count += 1
        membership_count += len(box)
    if box_count != N or membership_count != N * 32:
        raise RuntimeError(('box-census', box_count, membership_count))

    model.add(x[0] == 1)
    model.add(sum(x) >= TARGET)
    hs = set(hint)
    for v in hs:
        model.add_hint(x[v], 1)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = a.seconds
    solver.parameters.num_search_workers = a.workers
    solver.parameters.cp_model_presolve = True
    solver.parameters.linearization_level = 2
    solver.parameters.random_seed = 20261101
    solver.parameters.log_search_progress = True
    t = time.time()
    st = solver.solve(model)
    wall = time.time() - t
    status = solver.status_name(st)

    chosen = []
    if st in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        chosen = [v for v in range(N) if solver.boolean_value(x[v])]
        if len(chosen) < TARGET or 0 not in chosen or not independent(chosen):
            raise RuntimeError(('bad-witness', len(chosen), 0 in chosen))
        if len(chosen) > TARGET:
            chosen = sorted(chosen)[:TARGET]
            if not independent(chosen):
                raise RuntimeError('trim-failed')
        a.witness5.parent.mkdir(parents=True, exist_ok=True)
        a.witness5.write_text(json.dumps({'points': [word(v) for v in chosen]}, separators=(',', ':')) + '\n')
        words = [word(v) for v in chosen]
        pts10 = sorted(u + v for u in words for v in words)
        if len(pts10) != TARGET * TARGET:
            raise RuntimeError(('square-size', len(pts10)))
        a.certificate10.parent.mkdir(parents=True, exist_ok=True)
        a.certificate10.write_text(json.dumps({'points': pts10}, separators=(',', ':')) + '\n')

    out = {
        'method': 'global-c7p5-box-clique-cpsat-target368',
        'vertices': N,
        'target': TARGET,
        'box_cliques': box_count,
        'box_size': 32,
        'box_memberships': membership_count,
        'symmetry_break_contains_zero': True,
        'hint_size': len(hint),
        'hint_source_point': source_point,
        'hint_translation': list(shift),
        'solver_status': status,
        'wall_seconds': wall,
        'conflicts': solver.num_conflicts,
        'branches': solver.num_branches,
        'candidate_368': bool(chosen),
        'exact_alpha_367': status == 'INFEASIBLE',
        'score10': TARGET * TARGET if chosen else None,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
