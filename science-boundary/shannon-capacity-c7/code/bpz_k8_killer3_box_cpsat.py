#!/usr/bin/env python3
"""Exact global k<=8 positive support defect with <=3 killer colors.

This is a compact CP-SAT replacement for the cancelled 1.56M-variable CNF.
Candidates are every five-dimensional point outside the pinned 359-point core B
whose support N[z]∩B is nonempty and has size at most eight.  We ask for at
least nine pairwise nonconfusable candidates whose union of touched core owners
has size at most eight and whose union of killed BPZ private-pair colors has
size at most three.

Pairwise conflicts are encoded exactly by the 16807 product cliques of C7^5:
each candidate belongs to 2^5 boxes formed by choosing, in every coordinate,
one of the two cycle edges containing its symbol.  This replaces ~1.9M pairwise
conflict clauses.  Owner and killer cardinalities are native CP-SAT linear
constraints rather than cardinality networks.

SAT gives a globally valid <=8-owner / >=9-addition defect with <=3 killer
colors.  UNSAT, together with the independently replayed known defects killing
four colors, proves the global minimum killer count is exactly four.
"""
from __future__ import annotations

import argparse
import itertools
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from ortools.sat.python import cp_model

from bpz_irreducible_support_sat import dec, load_geometry, conflict5

BITS = tuple(itertools.product((0, 1), repeat=5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tan_root', type=Path)
    ap.add_argument('output', type=Path)
    ap.add_argument('--seconds', type=float, default=19800.0)
    ap.add_argument('--workers', type=int, default=4)
    a = ap.parse_args()

    ring, raw, B, owners, cands, supports, kmasks = load_geometry(a.tan_root.resolve(), 8, False)
    n = len(cands)
    if len(B) != 359 or len(raw['private_pairs']) != 8:
        raise RuntimeError(('geometry', len(B), len(raw['private_pairs'])))
    if n != 16229:
        raise RuntimeError(('candidate-count', n))

    model = cp_model.CpModel()
    x = [model.new_bool_var(f'x_{i}') for i in range(n)]
    y = [model.new_bool_var(f'y_{i}') for i in range(len(owners))]
    kc = [model.new_bool_var(f'k_{j}') for j in range(8)]

    # Exact C7^5 conflict encoding.  A candidate z belongs to 32 boxes; box
    # start coordinate is either z_i or z_i-1 depending on which incident edge
    # of C7 is chosen in that coordinate.
    boxes = defaultdict(list)
    for i, z in enumerate(cands):
        d = dec(z)
        for bits in BITS:
            start = tuple((d[q] - bits[q]) % 7 for q in range(5))
            boxes[start].append(i)
    if len(boxes) != 7**5:
        raise RuntimeError(('box-count', len(boxes)))
    memberships = sum(map(len, boxes.values()))
    if memberships != n * 32:
        raise RuntimeError(('box-memberships', memberships, n * 32))
    box_constraints = 0
    for ids in boxes.values():
        if len(ids) > 1:
            model.add_at_most_one([x[i] for i in ids])
            box_constraints += 1

    support_implications = 0
    killer_implications = 0
    for i, S in enumerate(supports):
        for oi in S:
            model.add_implication(x[i], y[oi])
            support_implications += 1
        km = int(kmasks[i])
        for j in range(8):
            if (km >> j) & 1:
                model.add_implication(x[i], kc[j])
                killer_implications += 1

    model.add(sum(x) >= 9)
    model.add(sum(y) <= 8)
    model.add(sum(kc) <= 3)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = a.seconds
    solver.parameters.num_search_workers = a.workers
    solver.parameters.cp_model_presolve = True
    solver.parameters.linearization_level = 2
    solver.parameters.random_seed = 20261102
    solver.parameters.log_search_progress = True
    t = time.time()
    st = solver.solve(model)
    wall = time.time() - t
    status = solver.status_name(st)

    witness = []
    owner_union = set()
    killer_union = 0
    if st in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        chosen_idx = [i for i in range(n) if solver.boolean_value(x[i])]
        if len(chosen_idx) < 9:
            raise RuntimeError(('cardinality', len(chosen_idx)))
        chosen_idx = chosen_idx[:9]
        witness = [int(cands[i]) for i in chosen_idx]
        for ii, u in enumerate(witness):
            for v in witness[ii + 1:]:
                if conflict5(u, v):
                    raise RuntimeError(('conflict', u, v))
        for i in chosen_idx:
            owner_union.update(int(q) for q in supports[i])
            killer_union |= int(kmasks[i])
        if len(owner_union) > 8 or killer_union.bit_count() > 3:
            raise RuntimeError(('replay', len(owner_union), killer_union.bit_count()))

    out = {
        'method': 'exact-box-cpsat-k8-positive-defect-killer3',
        'B_size': len(B),
        'candidate_count': n,
        'candidate_support_histogram': dict(sorted(Counter(map(len, supports)).items())),
        'box_cliques': len(boxes),
        'box_constraints': box_constraints,
        'box_memberships': memberships,
        'support_implications': support_implications,
        'killer_implications': killer_implications,
        'target_selected': 9,
        'max_support_union': 8,
        'max_killer_colors': 3,
        'solver_status': status,
        'wall_seconds': wall,
        'conflicts': solver.num_conflicts,
        'branches': solver.num_branches,
        'candidate': bool(witness),
        'witness': sorted(witness),
        'support_union_owner_indices': sorted(owner_union),
        'support_union_owner_words': [int(owners[i]) for i in sorted(owner_union)],
        'support_union_size': len(owner_union),
        'killer_mask': killer_union,
        'killed_private_pair_colors': [j for j in range(8) if (killer_union >> j) & 1],
        'killed_private_pair_count': killer_union.bit_count(),
        'exact_min_killer_at_least_four': status == 'INFEASIBLE',
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
