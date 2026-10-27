#!/usr/bin/env python3
"""Optimize the rank-3 one-sided zero-conflict-fiber model with OR-Tools CP-SAT.

This is the same combinatorial subspace as rank3_xzero_one_side_sat.py, but the
large global cardinality objective is kept native instead of being handed to
MiniCard's int32-backed allocator.
"""

import argparse
import json
import os
from itertools import product
from pathlib import Path

from ortools.sat.python import cp_model

import generalized9 as g
import rank3_square_relax as rs

SPECIAL = 294
BASE_SQUARE = 358 ** 2
TARGET = 134_754
NEED = TARGET - BASE_SQUARE


def clique(anchor: int, digits):
    a = digits[anchor]
    return [
        g.enc5(tuple((a[d] + bit[d]) % 7 for d in range(5)))
        for bit in product((0, 1), repeat=5)
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--time-limit", type=float, default=1200.0)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = rs.load_rank3_state(r0, digits)
    supports, _ = g.support_masks(r, digits)

    kset = set(rs.RANK3_K9)
    bidx = [i for i in range(g.R_SIZE) if i not in kset]
    bmask = sum(1 << i for i in bidx)
    bvals = {r[i] for i in bidx}
    zero = [i for i, x in enumerate(xset) if (supports[x] & bmask) == 0]
    if zero != [SPECIAL]:
        raise RuntimeError(f"zero fiber drift: {zero}")
    safe = tuple(
        v for v in range(g.U)
        if v not in bvals and (supports[v] & bmask) == 0
    )
    if len(safe) != 18:
        raise RuntimeError(f"safe endpoint drift: {len(safe)}")

    hcand = [tuple(range(g.U)) if i == SPECIAL else safe for i in range(g.R_SIZE)]
    vcand = [safe for _ in range(g.R_SIZE)]
    vsets = [set(v) for v in vcand]

    model = cp_model.CpModel()
    hvars = []
    hmaps = []
    vvars = []
    vmaps = []
    allvars = []
    for i in range(g.R_SIZE):
        hv = [model.NewBoolVar(f"h_{i}_{e}") for e in hcand[i]]
        vv = [model.NewBoolVar(f"v_{i}_{e}") for e in vcand[i]]
        hvars.append(hv)
        hmaps.append(dict(zip(hcand[i], hv)))
        vvars.append(vv)
        vmaps.append(dict(zip(vcand[i], vv)))
        allvars.extend(hv)
        allvars.extend(vv)

    same = [
        (a, b)
        for ai, a in enumerate(safe)
        for b in safe[ai + 1 :]
        if g.conflict(a, b, digits)
    ]
    ordinary_same = 0
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for a, b in same:
                model.AddBoolOr([hmaps[i][a].Not(), hmaps[i][b].Not()])
                ordinary_same += 1
        for a, b in same:
            model.AddBoolOr([vmaps[i][a].Not(), vmaps[i][b].Not()])
            ordinary_same += 1

    special_cliques = 0
    for a in range(g.U):
        model.AddAtMostOne([hmaps[SPECIAL][e] for e in clique(a, digits)])
        special_cliques += 1

    xhits = [[] for _ in range(g.U)]
    xneigh = []
    for i, x in enumerate(xset):
        n = tuple(rs.neighborhood(x, digits))
        xneigh.append(set(n))
        for e in n:
            xhits[e].append(i)

    cross = 0
    for i in range(g.R_SIZE):
        ni = xneigh[i]
        for e in hcand[i]:
            h = hmaps[i][e]
            for j in xhits[e]:
                for f in ni.intersection(vsets[j]):
                    model.AddBoolOr([h.Not(), vmaps[j][f].Not()])
                    cross += 1

    model.Maximize(sum(allvars))
    setup = {
        "state": rs.STATE_INDEX,
        "special": SPECIAL,
        "safe_endpoints": len(safe),
        "candidate_port_variables": len(allvars),
        "ordinary_same_pair_clauses": ordinary_same,
        "special_clique_constraints": special_cliques,
        "cross_clauses": cross,
        "need_ports": NEED,
        "target": TARGET,
        "solver": "ortools-cp-sat",
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.time_limit
    solver.parameters.num_search_workers = max(1, os.cpu_count() or 1)
    solver.parameters.log_search_progress = True
    result = solver.Solve(model)
    name = solver.StatusName(result)
    has_solution = result in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    selected = int(round(solver.ObjectiveValue())) if has_solution else None
    bound = float(solver.BestObjectiveBound()) if has_solution or result == cp_model.UNKNOWN else None

    status = {
        "candidate": False,
        "solver_status": name,
        "selected_ports": selected,
        "best_bound": bound,
        "score": BASE_SQUARE + selected if selected is not None else None,
        "setup": setup,
    }

    if has_solution and selected is not None and selected >= NEED:
        hs = [[] for _ in range(g.R_SIZE)]
        vs = [[] for _ in range(g.R_SIZE)]
        for i in range(g.R_SIZE):
            hs[i] = [e for e, var in hmaps[i].items() if solver.Value(var)]
            vs[i] = [e for e, var in vmaps[i].items() if solver.Value(var)]
        cert = rs.build_candidate(r, xset, bidx, hs, vs, [])
        score = len(cert)
        if score != BASE_SQUARE + selected or score < TARGET:
            raise RuntimeError(f"bad CP-SAT candidate score={score}, selected={selected}")
        baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(v) for v in sorted(cert)]}, separators=(",", ":")) + "\n"
        )
        status.update({
            "candidate": True,
            "score": score,
            "removed_vs_baseline": len(baseline - cert),
            "added_vs_baseline": len(cert - baseline),
        })

    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("RESULT", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
