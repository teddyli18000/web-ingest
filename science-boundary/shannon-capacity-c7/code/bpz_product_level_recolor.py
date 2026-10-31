#!/usr/bin/env python3
"""Adaptive local recoloring of the product-level support-3 core-cell injection.

The frozen support<=2 product injection fails only on a tiny product-level SAT
core.  Instead of abandoning the injection proof, release selected regular x
regular points from their frozen owner cells and jointly recolor them together
with all exception-containing product points.

At each round:
  * unreleased regular x regular points remain frozen at (f(u),f(v));
  * all exception-containing points and released regular points must choose one
    core cell in their exact support rectangle;
  * a movable point may choose a cell only if it conflicts with every still-
    frozen point in that cell;
  * two compatible movable points may not choose the same cell.

If UNSAT, an assumption core identifies mandatory movable points responsible for
failure.  We inspect all currently blocked support cells of those core points
and release the cheapest complete blocker set for one such cell, then repeat.
A SAT round is independently replayed over all 429^2 product points and is a
valid full-family clique-fiber injection certificate.  Failure to find SAT is
only a search result, not an impossibility theorem.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from pysat.solvers import Glucose4

from bpz_product_level_injection_sat import build_instance, product_conflict


def solve_round(ring, regular, exceptions, support, fmap, groups, exception_points, release):
    release = set(release)
    # Frozen regular product fibers after removing released RR points.
    fixed_by_cell = defaultdict(list)
    for u in regular:
        a = int(fmap[u])
        for v in regular:
            p = (u, v)
            if p not in release:
                fixed_by_cell[(a, int(fmap[v]))].append(p)

    movable = list(exception_points) + sorted(release)
    domains = []
    blocked = []
    for p in movable:
        x, y = p
        ds = []
        bm = {}
        for a in support[x]:
            for b in support[y]:
                c = (a, b)
                bad = [q for q in fixed_by_cell.get(c, ()) if not product_conflict(ring, p, q)]
                if bad:
                    bm[c] = tuple(bad)
                else:
                    ds.append(c)
        domains.append(tuple(sorted(set(ds))))
        blocked.append(bm)

    solver = Glucose4(with_proof=False)
    nxt = 1
    selectors = []
    choices = []
    by_cell = defaultdict(list)
    clauses = Counter()
    for i, ds in enumerate(domains):
        s = nxt; nxt += 1; selectors.append(s)
        cm = {}; lits = []
        for c in ds:
            x = nxt; nxt += 1
            cm[c] = x; lits.append(x); by_cell[c].append((i, x))
            solver.add_clause([-x, s]); clauses['choice_implies_selector'] += 1
        solver.add_clause([-s, *lits]); clauses['selector_requires_choice'] += 1
        for a in range(len(lits)):
            for b in range(a + 1, len(lits)):
                solver.add_clause([-lits[a], -lits[b]]); clauses['at_most_one'] += 1
        choices.append(cm)

    pair_checks = 0
    for c, es in by_cell.items():
        for a in range(len(es)):
            i, xi = es[a]; p = movable[i]
            for b in range(a + 1, len(es)):
                j, xj = es[b]; q = movable[j]; pair_checks += 1
                if not product_conflict(ring, p, q):
                    solver.add_clause([-xi, -xj]); clauses['compatible_same_cell'] += 1

    ts = time.time(); sat = solver.solve(assumptions=selectors); sec = time.time() - ts
    out = {
        'status': 'sat' if sat else 'unsat',
        'movable_points': len(movable),
        'released_rr': len(release),
        'domain_histogram': {str(k): v for k, v in sorted(Counter(map(len, domains)).items())},
        'sat_variables': nxt - 1,
        'sat_clauses': sum(clauses.values()),
        'clause_counts': dict(clauses),
        'cell_pair_checks': pair_checks,
        'solve_seconds': sec,
    }
    if sat:
        model = {z for z in solver.get_model() if z > 0}
        assignment = {}
        for i, p in enumerate(movable):
            got = [c for c, x in choices[i].items() if x in model]
            if len(got) != 1: raise RuntimeError(('assignment cardinality', p, got))
            assignment[p] = got[0]
        out['assignment'] = assignment
    else:
        core = solver.get_core() or []
        si = {s: i for i, s in enumerate(selectors)}
        idx = [si[s] for s in core if s in si]
        out['core_indices'] = idx
        out['core_points'] = [movable[i] for i in idx]
        out['blocked'] = blocked
    solver.delete()
    return out, movable, fixed_by_cell


def replay_full(ring, regular, exception_points, support, fmap, release, assignment):
    fibers = defaultdict(list)
    release = set(release)
    for u in regular:
        for v in regular:
            p = (u, v)
            if p not in release:
                fibers[(int(fmap[u]), int(fmap[v]))].append(p)
    for p in list(exception_points) + sorted(release):
        c = assignment[p]
        if c[0] not in support[p[0]] or c[1] not in support[p[1]]:
            raise RuntimeError(('assigned outside support', p, c))
        fibers[c].append(p)
    checks = 0
    for c, L in fibers.items():
        for i, p in enumerate(L):
            if c[0] not in support[p[0]] or c[1] not in support[p[1]]:
                raise RuntimeError(('fiber support replay', c, p))
            for q in L[i+1:]:
                checks += 1
                if not product_conflict(ring, p, q):
                    raise RuntimeError(('fiber nonclique', c, p, q))
    if sum(map(len, fibers.values())) != (len(regular) + 4) ** 2:
        raise RuntimeError(('point count replay', sum(map(len, fibers.values()))))
    return {'fiber_count': len(fibers), 'max_fiber_size': max(map(len, fibers.values())), 'same_cell_pair_checks': checks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tan_root', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--max-rounds', type=int, default=100)
    ap.add_argument('--max-release', type=int, default=5000)
    args = ap.parse_args()

    t0 = time.time()
    ring, B, regular, exceptions, support, fmap, groups, exception_points, _allowed, _no = build_instance(args.tan_root.resolve())
    release = set()
    rounds = []
    final = None

    for rnd in range(args.max_rounds):
        rr, movable, fixed = solve_round(ring, regular, exceptions, support, fmap, groups, exception_points, release)
        rec = {k: v for k, v in rr.items() if k not in ('assignment', 'blocked')}
        rec['round'] = rnd
        rounds.append(rec)
        print(json.dumps(rec, sort_keys=True), flush=True)
        if rr['status'] == 'sat':
            replay = replay_full(ring, regular, exception_points, support, fmap, release, rr['assignment'])
            final = {
                'status': 'sat', 'round': rnd, 'released_rr': len(release),
                'release': [list(p) for p in sorted(release)], 'replay': replay,
                'conclusion': 'full 429x429 family has a replayed clique-fiber injection after local RR recoloring; raw core gain is nonpositive',
            }
            break

        # Cheapest complete fixed-blocker release that opens one currently blocked
        # support cell for a point in the UNSAT core.
        actions = []
        for i in rr['core_indices']:
            p = movable[i]
            bm = rr['blocked'][i]
            for c, blockers in bm.items():
                new = tuple(sorted(q for q in blockers if q not in release))
                if new:
                    actions.append((len(new), p, c, new))
        if not actions:
            final = {
                'status': 'stuck-unsat', 'round': rnd, 'released_rr': len(release),
                'core_points': [list(p) for p in rr['core_points']],
                'conclusion': 'UNSAT core has no remaining fixed-cell blockers to release; obstruction is intrinsic to current movable list-coloring',
            }
            break
        actions.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
        cost, p, c, add = actions[0]
        release.update(add)
        rounds[-1]['chosen_release_action'] = {'core_point': list(p), 'cell': list(c), 'new_blockers': [list(q) for q in add], 'new_blocker_count': cost}
        if len(release) > args.max_release:
            final = {
                'status': 'release-cap', 'round': rnd, 'released_rr': len(release),
                'conclusion': 'adaptive recoloring exceeded release cap without a certificate',
            }
            break

    if final is None:
        final = {'status': 'round-cap', 'released_rr': len(release), 'conclusion': 'round cap reached without certificate'}
    out = {
        'method': 'adaptive-product-level-support3-local-recoloring',
        'source_injection_run': 41233022940,
        'exceptions': list(exceptions),
        'regular_factors': len(regular),
        'variable_exception_points': len(exception_points),
        'rounds': rounds,
        'final': final,
        'wall_seconds': time.time() - t0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'final': final, 'round_count': len(rounds), 'wall_seconds': out['wall_seconds']}, sort_keys=True))


if __name__ == '__main__':
    main()
