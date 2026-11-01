#!/usr/bin/env python3
"""Exact raw-core prize for the full 429-factor support<=3 outside×outside family.

The factor conflict graph has 429 vertices and 3541 open edges.  Its ordered
square has 184041 candidate ten-dimensional additions and 28115540 pairwise
new-new conflicts, too many to encode naively in Python.

This program first enumerates maximal cliques of the factor graph, greedily
covers every factor conflict edge by cliques, and checks that the resulting
clique family covers the entire closed conflict relation (loops included).
For factor cliques C,D, C×D is a clique in the strong-product conflict graph.
Thus AddAtMostOne(C×D) over every ordered clique pair is an exact compressed
encoding of all product conflicts.

The CP-SAT objective is

    selected outside×outside points - activated B×B core cells.

Terminal/periphery losses are deliberately omitted, so this is an upper bound
for every pinned 134753 terminal scenario.  If the exact optimum is zero, the
entire support<=3 outside×outside family is closed at raw-core level.  A positive
optimum is saved as a structural witness for a later exact terminal-prize replay.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

from ortools.sat.python import cp_model

import bpz_joint_row_defects_maxsat as J
from bpz_support3_first_mus_residual_prize import EXCEPTIONS, build_support2_assignment


def bits(mask: int):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1
        mask ^= b


def maximal_cliques(adj: list[int]) -> list[tuple[int, ...]]:
    """Bron-Kerbosch with pivoting on a small sparse graph, using Python bitsets."""
    n = len(adj)
    out: list[tuple[int, ...]] = []

    def rec(r: tuple[int, ...], p: int, x: int):
        if not (p | x):
            out.append(r)
            return
        ux = p | x
        pivot = -1
        best = -1
        for u in bits(ux):
            score = (p & adj[u]).bit_count()
            if score > best:
                best = score
                pivot = u
        cand = p if pivot < 0 else p & ~adj[pivot]
        while cand:
            vb = cand & -cand
            v = vb.bit_length() - 1
            rec(r + (v,), p & adj[v], x & adj[v])
            p ^= vb
            x |= vb
            cand ^= vb

    rec((), (1 << n) - 1, 0)
    return out


def greedy_edge_clique_cover(adj_sets: list[set[int]], maximal: list[tuple[int, ...]]):
    edges = [(i, j) for i, a in enumerate(adj_sets) for j in a if i < j]
    eid = {e: k for k, e in enumerate(edges)}
    full = (1 << len(edges)) - 1
    masks: list[int] = []
    cliques: list[tuple[int, ...]] = []
    for c in maximal:
        if len(c) < 2:
            continue
        m = 0
        for ii, u in enumerate(c):
            for v in c[ii + 1 :]:
                a, b = (u, v) if u < v else (v, u)
                k = eid.get((a, b))
                if k is None:
                    raise RuntimeError(("nonclique", c, u, v))
                m |= 1 << k
        if m:
            cliques.append(tuple(sorted(c)))
            masks.append(m)

    uncovered = full
    chosen: list[tuple[int, ...]] = []
    while uncovered:
        best_i = -1
        best_n = 0
        for i, m in enumerate(masks):
            z = (m & uncovered).bit_count()
            if z > best_n:
                best_n = z
                best_i = i
        if best_n <= 0:
            # Every remaining relation is itself a size-two clique.
            k = (uncovered & -uncovered).bit_length() - 1
            chosen.append(edges[k])
            uncovered ^= 1 << k
            continue
        chosen.append(cliques[best_i])
        uncovered &= ~masks[best_i]

    covered_vertices = set().union(*(set(c) for c in chosen)) if chosen else set()
    for v in range(len(adj_sets)):
        if v not in covered_vertices:
            chosen.append((v,))

    # Exact replay: every loop and every factor conflict edge must be contained
    # in at least one chosen clique.
    pair_cover = set()
    for c in chosen:
        for u in c:
            pair_cover.add((u, u))
        for ii, u in enumerate(c):
            for v in c[ii + 1 :]:
                pair_cover.add((min(u, v), max(u, v)))
    for u in range(len(adj_sets)):
        if (u, u) not in pair_cover:
            raise RuntimeError(("uncovered-loop", u))
        for v in adj_sets[u]:
            if u < v and (u, v) not in pair_cover:
                raise RuntimeError(("uncovered-edge", u, v))
    return chosen, edges


def build_geometry(root: Path):
    _base, ring, B0, _fam = J.load_geometry(root.resolve())
    B = set(B0)
    regular, support, _fmap = build_support2_assignment(ring, B)
    for z in EXCEPTIONS:
        support[z] = tuple(sorted(ring.NB[z] & B))
        if len(support[z]) != 3:
            raise RuntimeError(("exception-support", z, support[z]))
    F = sorted(regular + list(EXCEPTIONS))
    if len(F) != 429 or len(set(F)) != 429:
        raise RuntimeError(("factor-count", len(F)))
    pos = {z: i for i, z in enumerate(F)}
    adj_sets = [set() for _ in F]
    for i, u in enumerate(F):
        for v in ring.NB[u]:
            j = pos.get(v)
            if j is not None and j != i:
                adj_sets[i].add(j)
    for i, a in enumerate(adj_sets):
        for j in a:
            if i not in adj_sets[j]:
                raise RuntimeError(("asymmetry", i, j))
    return ring, B, F, support, adj_sets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--time-limit", type=float, default=18000.0)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    t0 = time.time()
    ring, B, F, support, adj_sets = build_geometry(a.tan_root)
    adj_bits = []
    for s in adj_sets:
        m = 0
        for v in s:
            m |= 1 << v
        adj_bits.append(m)

    t = time.time()
    maximal = maximal_cliques(adj_bits)
    maximal_seconds = time.time() - t
    t = time.time()
    cover, edges = greedy_edge_clique_cover(adj_sets, maximal)
    cover_seconds = time.time() - t
    cover_sizes = [len(c) for c in cover]
    sum_cover_sizes = sum(cover_sizes)

    n = len(F)
    model = cp_model.CpModel()
    x = [model.new_bool_var(f"x_{i}_{j}") for i in range(n) for j in range(n)]

    # Exact product-conflict encoding by products of factor cliques.
    product_clique_constraints = 0
    product_clique_memberships = 0
    for C in cover:
        for D in cover:
            lits = [x[i * n + j] for i in C for j in D]
            if len(lits) > 1:
                model.add_at_most_one(lits)
                product_clique_constraints += 1
                product_clique_memberships += len(lits)

    # Exact core-cell activation costs.
    cell_to_y = {}
    activation_implications = 0
    for i, u in enumerate(F):
        Su = support[u]
        for j, v in enumerate(F):
            Sv = support[v]
            xv = x[i * n + j]
            for aa in Su:
                for bb in Sv:
                    cell = (aa, bb)
                    y = cell_to_y.get(cell)
                    if y is None:
                        y = model.new_bool_var(f"y_{aa}_{bb}")
                        cell_to_y[cell] = y
                    model.add_implication(xv, y)
                    activation_implications += 1

    model.maximize(sum(x) - sum(cell_to_y.values()))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = a.time_limit
    solver.parameters.num_search_workers = a.workers
    solver.parameters.log_search_progress = True
    tsolve = time.time()
    status = solver.solve(model)
    solve_seconds = time.time() - tsolve
    status_name = solver.status_name(status)
    objective = solver.objective_value if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
    best_bound = solver.best_objective_bound if status in (cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.UNKNOWN) else None

    selected = []
    activated = []
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i, u in enumerate(F):
            for j, v in enumerate(F):
                if solver.boolean_value(x[i * n + j]):
                    selected.append((u, v))
        activated = [c for c, y in cell_to_y.items() if solver.boolean_value(y)]
        replay = set()
        for u, v in selected:
            replay.update((aa, bb) for aa in support[u] for bb in support[v])
        if replay != set(activated):
            raise RuntimeError(("activation-replay", len(replay), len(activated)))
        # Independent replay under the exact factor relation.
        pos = {z: i for i, z in enumerate(F)}
        for k, (u, v) in enumerate(selected):
            iu = pos[u]
            iv = pos[v]
            for x2, y2 in selected[k + 1 :]:
                jx = pos[x2]
                jy = pos[y2]
                if (jx == iu or jx in adj_sets[iu]) and (jy == iv or jy in adj_sets[iv]):
                    raise RuntimeError(("selected-conflict", (u, v), (x2, y2)))
        if len(selected) - len(activated) != round(objective):
            raise RuntimeError(("objective-replay", len(selected), len(activated), objective))

    exact_nonpositive = bool(
        (status == cp_model.OPTIMAL and objective is not None and objective <= 0.0)
        or (best_bound is not None and best_bound <= 0.0)
    )
    out = {
        "method": "exact-support3-full-product-clique-compressed-raw-core-prize",
        "factor_count": n,
        "support_size_histogram": dict(sorted(Counter(len(support[z]) for z in F).items())),
        "factor_open_edges": len(edges),
        "maximal_clique_count": len(maximal),
        "maximal_clique_size_histogram": dict(sorted(Counter(map(len, maximal)).items())),
        "maximal_clique_seconds": maximal_seconds,
        "edge_clique_cover_count": len(cover),
        "edge_clique_cover_size_histogram": dict(sorted(Counter(cover_sizes).items())),
        "edge_clique_cover_sum_sizes": sum_cover_sizes,
        "edge_clique_cover_max_size": max(cover_sizes),
        "product_vertices": n * n,
        "product_clique_constraints": product_clique_constraints,
        "product_clique_memberships": product_clique_memberships,
        "activated_core_cell_variables": len(cell_to_y),
        "activation_implications": activation_implications,
        "cover_seconds": cover_seconds,
        "solve_status": status_name,
        "solve_seconds": solve_seconds,
        "objective": objective,
        "best_objective_bound": best_bound,
        "exact_nonpositive": exact_nonpositive,
        "selected_count": len(selected),
        "activated_core_cells": len(activated),
        "selected_points": [list(p) for p in selected] if objective is not None and objective > 0 else [],
        "activated_cells": [list(p) for p in sorted(activated)] if objective is not None and objective > 0 else [],
        "total_seconds": time.time() - t0,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("selected_points", "activated_cells")}, sort_keys=True))


if __name__ == "__main__":
    main()
