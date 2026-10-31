#!/usr/bin/env python3
"""Exact product-level clique-fiber injection for the first BPZ support-3 family.

The support<=2 factors admit a certified factor-level owner map f(z) in S(z)
whose owner fibers are confusability cliques.  The first obstruction to extending
that *factor-level* map consists of four support-3 factors.  A factor-level map is
stronger than needed for the ten-dimensional product: it is enough to assign each
product point (u,v) to one touched core cell (a,b) in S(u)xS(v), with every cell
fiber a clique in the product conflict graph.

We freeze every regular x regular point to (f(u),f(v)).  Only the 3416 product
points with at least one exception coordinate are variable.  A variable point may
use a core cell only when it conflicts with every frozen regular x regular point
already assigned to that cell.  SAT then chooses exactly one allowed cell per
variable point and forbids two mutually compatible variable product points from
sharing a cell.

SAT gives a replayable injection certificate proving raw core gain <= 0 for the
entire 429x429 family.  UNSAT returns an assumption core of variable product
points, isolating a genuine product-level obstruction for focused prize search.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from pysat.solvers import Glucose4

import bpz_joint_row_defects_maxsat as J
from bpz_support3_first_mus_residual_prize import (
    EXCEPTIONS,
    build_support2_assignment,
)


def product_conflict(ring, p: tuple[int, int], q: tuple[int, int]) -> bool:
    return q[0] in ring.NB[p[0]] and q[1] in ring.NB[p[1]]


def build_instance(root: Path):
    _base, ring, B, _fam = J.load_geometry(root)
    B = set(B)
    regular, support, fmap = build_support2_assignment(ring, B)
    regular = list(regular)
    exceptions = tuple(map(int, EXCEPTIONS))
    for z in exceptions:
        S = tuple(sorted(ring.NB[z] & B))
        if len(S) != 3:
            raise RuntimeError(("exception support drift", z, S))
        support[z] = S

    if len(regular) != 425 or len(exceptions) != 4:
        raise RuntimeError(("factor census drift", len(regular), len(exceptions)))

    groups: dict[int, list[int]] = defaultdict(list)
    for z in regular:
        groups[int(fmap[z])].append(z)
    for a, G in groups.items():
        for i, u in enumerate(G):
            for v in G[i + 1 :]:
                if v not in ring.NB[u]:
                    raise RuntimeError(("fixed owner fiber not clique", a, u, v))

    F = regular + list(exceptions)
    E = set(exceptions)
    variable = [(u, v) for u in F for v in F if u in E or v in E]
    if len(variable) != len(F) ** 2 - len(regular) ** 2 or len(variable) != 3416:
        raise RuntimeError(("variable product census drift", len(variable)))

    # Allowed cells: every assigned cell must be genuinely touched by the point.
    # If both frozen owner groups at a cell are nonempty, the variable point must
    # conflict with every member of their Cartesian-product frozen fiber.
    allowed: list[tuple[tuple[int, int], ...]] = []
    no_allowed: list[tuple[int, int]] = []
    for x, y in variable:
        cells = []
        for a in support[x]:
            for b in support[y]:
                Ga = groups.get(a, ())
                Gb = groups.get(b, ())
                ok = True
                if Ga and Gb:
                    ok = all(u in ring.NB[x] for u in Ga) and all(v in ring.NB[y] for v in Gb)
                if ok:
                    cells.append((a, b))
        cells = sorted(set(cells))
        allowed.append(tuple(cells))
        if not cells:
            no_allowed.append((x, y))

    return ring, B, regular, exceptions, support, fmap, groups, variable, allowed, no_allowed


def solve(root: Path, output: Path, core_limit: int = 0):
    t0 = time.time()
    ring, B, regular, exceptions, support, fmap, groups, variable, allowed, no_allowed = build_instance(root)

    solver = Glucose4(with_proof=False)
    next_var = 1
    selector: list[int] = []
    choice: list[dict[tuple[int, int], int]] = []
    by_cell: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    clause_counts = Counter()

    # One assumption selector per variable product point.  This makes an UNSAT
    # core interpretable at the candidate-point level.
    for i, cells in enumerate(allowed):
        s = next_var
        next_var += 1
        selector.append(s)
        cmap: dict[tuple[int, int], int] = {}
        lits = []
        for c in cells:
            x = next_var
            next_var += 1
            cmap[c] = x
            lits.append(x)
            by_cell[c].append((i, x))
            solver.add_clause([-x, s])
            clause_counts["choice_implies_selector"] += 1
        # selector -> at least one choice; if cells is empty this is [-s].
        solver.add_clause([-s, *lits])
        clause_counts["selector_requires_choice"] += 1
        for a in range(len(lits)):
            for b in range(a + 1, len(lits)):
                solver.add_clause([-lits[a], -lits[b]])
                clause_counts["at_most_one"] += 1
        choice.append(cmap)

    # A cell fiber must be a clique.  Only compatible variable-variable pairs
    # need clauses.  Compatibility means they could coexist in an independent set.
    compatible_pair_clauses = 0
    cell_pair_checks = 0
    for c, entries in by_cell.items():
        for a in range(len(entries)):
            i, xi = entries[a]
            p = variable[i]
            for b in range(a + 1, len(entries)):
                j, xj = entries[b]
                cell_pair_checks += 1
                q = variable[j]
                if not product_conflict(ring, p, q):
                    solver.add_clause([-xi, -xj])
                    compatible_pair_clauses += 1
    clause_counts["compatible_same_cell"] = compatible_pair_clauses

    assumptions = selector[:]
    ts = time.time()
    sat = solver.solve(assumptions=assumptions)
    solve_seconds = time.time() - ts

    result = {
        "method": "exact-product-level-support3-clique-fiber-injection-sat",
        "factor_count": len(regular) + len(exceptions),
        "regular_factors": len(regular),
        "exceptions": list(exceptions),
        "fixed_product_points": len(regular) ** 2,
        "variable_product_points": len(variable),
        "core_cells_with_fixed_fiber": sum(1 for a in groups for b in groups if groups[a] and groups[b]),
        "allowed_choice_histogram": {str(k): v for k, v in sorted(Counter(map(len, allowed)).items())},
        "no_allowed_count": len(no_allowed),
        "sat_variables": next_var - 1,
        "sat_clauses": sum(clause_counts.values()),
        "clause_counts": dict(clause_counts),
        "cell_pair_checks": cell_pair_checks,
        "solve_seconds": solve_seconds,
        "build_plus_solve_seconds": time.time() - t0,
        "status": "sat" if sat else "unsat",
    }

    if sat:
        model = set(z for z in solver.get_model() if z > 0)
        assigned: list[tuple[int, int]] = []
        fibers: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        # Frozen regular x regular assignment.
        for u in regular:
            for v in regular:
                fibers[(int(fmap[u]), int(fmap[v]))].append((u, v))
        for i, p in enumerate(variable):
            chosen = [c for c, x in choice[i].items() if x in model]
            if len(chosen) != 1:
                raise RuntimeError(("assignment cardinality", i, p, chosen))
            c = chosen[0]
            if c[0] not in support[p[0]] or c[1] not in support[p[1]]:
                raise RuntimeError(("assignment outside support", p, c))
            assigned.append(c)
            fibers[c].append(p)

        # Independent full replay: every fiber is a product-conflict clique and
        # every point's assigned cell lies in its exact support rectangle.
        bad = None
        replay_pairs = 0
        for c, L in fibers.items():
            for i, p in enumerate(L):
                if c[0] not in support[p[0]] or c[1] not in support[p[1]]:
                    bad = ("support", c, p)
                    break
                for q in L[i + 1 :]:
                    replay_pairs += 1
                    if not product_conflict(ring, p, q):
                        bad = ("nonclique", c, p, q)
                        break
                if bad:
                    break
            if bad:
                break
        if bad:
            raise RuntimeError(("fiber replay failed", bad))
        result.update(
            replay_ok=True,
            replay_same_cell_pairs=replay_pairs,
            used_core_cells=len(fibers),
            max_fiber_size=max(map(len, fibers.values())),
            variable_assignment=[
                [variable[i][0], variable[i][1], assigned[i][0], assigned[i][1]]
                for i in range(len(variable))
            ],
            conclusion="full 429x429 family admits a core-cell clique-fiber injection; raw core gain is nonpositive",
        )
    else:
        core = solver.get_core() or []
        s_to_i = {s: i for i, s in enumerate(selector)}
        core_idx = [s_to_i[s] for s in core if s in s_to_i]
        core_points = [list(variable[i]) for i in core_idx]
        if core_limit > 0:
            core_points = core_points[:core_limit]
        result.update(
            assumption_core_size=len(core_idx),
            assumption_core_points=core_points,
            conclusion="no product-level clique-fiber injection of this form; core points define the next exact obstruction",
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    summary = {k: v for k, v in result.items() if k not in ("variable_assignment", "assumption_core_points")}
    print(json.dumps(summary, sort_keys=True))
    solver.delete()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--core-limit", type=int, default=0)
    args = ap.parse_args()
    solve(args.tan_root.resolve(), args.output, args.core_limit)


if __name__ == "__main__":
    main()
