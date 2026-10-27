#!/usr/bin/env python3
"""Feasibility search for the one-sided X_294 relaxation across neutral2 ranks.

For a selected state-18 rank, keep the 358x358 BxB core, allow the unique
zero-conflict companion fiber X_294 to use an arbitrary independent 5D H-fiber,
keep all other H fibers and every V fiber on the 18 ordinary safe endpoints,
and ask only whether at least 6590 ports can coexist.  This is a pure CP-SAT
feasibility model: SAT yields a Few Shots candidate; INFEASIBLE closes this
subspace for that rank; UNKNOWN is inconclusive.
"""

import argparse
import json
import os
from itertools import combinations, product
from pathlib import Path

from ortools.sat.python import cp_model

import generalized9 as g
import rank3_square_relax as rs

STATE_INDEX = 18
SPECIAL = 294
BASE_SQUARE = 358 ** 2
TARGET = 134_754
NEED = TARGET - BASE_SQUARE


def owner_groups(r, supports):
    rset = set(r)
    owners = {}
    for v, sm in enumerate(supports):
        if v in rset or sm.bit_count() != 1:
            continue
        i = (sm & -sm).bit_length() - 1
        owners.setdefault(i, []).append(v)
    return owners


def rank_rows(r, xset, supports):
    owners = owner_groups(r, supports)
    rows = []
    for k9 in combinations(sorted(owners), 9):
        kset = set(k9)
        bidx = [i for i in range(g.R_SIZE) if i not in kset]
        bmask = sum(1 << i for i in bidx)
        bvals = {r[i] for i in bidx}
        zeros = [i for i, x in enumerate(xset) if (supports[x] & bmask) == 0]
        safe = tuple(
            v for v in range(g.U)
            if v not in bvals and (supports[v] & bmask) == 0
        )
        rows.append((len(safe), tuple(k9), tuple(bidx), bmask, bvals, zeros, safe))
    rows.sort(key=lambda z: (-z[0], z[1]))
    return rows


def clique(anchor, digits):
    a = digits[anchor]
    return [
        g.enc5(tuple((a[d] + bit[d]) % 7 for d in range(5)))
        for bit in product((0, 1), repeat=5)
    ]


def write_status(path, status):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("RESULT", json.dumps(status, sort_keys=True), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--rank", type=int, required=True)
    ap.add_argument("--time-limit", type=float, default=900.0)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = rs.load_rank3_state(r0, digits)
    supports, _ = g.support_masks(r, digits)
    rows = rank_rows(r, xset, supports)
    if not 0 <= args.rank < len(rows):
        raise RuntimeError(f"rank {args.rank} outside 0..{len(rows)-1}")

    safe_count, k9, bidx, bmask, bvals, zeros, safe = rows[args.rank]
    base_meta = {
        "state": STATE_INDEX,
        "rank": args.rank,
        "k9": list(k9),
        "zero_x_indices": zeros,
        "safe_endpoints": safe_count,
        "base_square": BASE_SQUARE,
        "need_ports": NEED,
        "target": TARGET,
    }
    if zeros != [SPECIAL]:
        write_status(args.status, {
            "candidate": False,
            "solver_status": "SKIPPED_NO_UNIQUE_X294",
            "setup": base_meta,
        })
        return
    if safe_count != 18:
        raise RuntimeError(f"safe endpoint drift for rank {args.rank}: {safe_count}")

    hcand = [tuple(range(g.U)) if i == SPECIAL else safe for i in range(g.R_SIZE)]
    vcand = [safe for _ in range(g.R_SIZE)]
    vsets = [set(v) for v in vcand]

    model = cp_model.CpModel()
    hmaps, vmaps, allvars = [], [], []
    for i in range(g.R_SIZE):
        hm = {e: model.NewBoolVar(f"h_{i}_{e}") for e in hcand[i]}
        vm = {e: model.NewBoolVar(f"v_{i}_{e}") for e in vcand[i]}
        hmaps.append(hm)
        vmaps.append(vm)
        allvars.extend(hm.values())
        allvars.extend(vm.values())

    same = [
        (a, b)
        for ai, a in enumerate(safe)
        for b in safe[ai + 1:]
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

    model.Add(sum(allvars) >= NEED)
    setup = dict(base_meta)
    setup.update({
        "candidate_port_variables": len(allvars),
        "ordinary_same_pair_clauses": ordinary_same,
        "special_clique_constraints": special_cliques,
        "cross_clauses": cross,
        "solver": "ortools-cp-sat-feasibility",
    })
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.time_limit
    solver.parameters.num_search_workers = max(1, os.cpu_count() or 1)
    result = solver.Solve(model)
    name = solver.StatusName(result)
    has_solution = result in (cp_model.OPTIMAL, cp_model.FEASIBLE)
    selected = None
    if has_solution:
        selected = sum(solver.Value(v) for v in allvars)

    status = {
        "candidate": False,
        "solver_status": name,
        "selected_ports": selected,
        "score": BASE_SQUARE + selected if selected is not None else None,
        "setup": setup,
    }

    if has_solution:
        if selected is None or selected < NEED:
            raise RuntimeError(f"solver violated target: selected={selected}")
        hs = [[] for _ in range(g.R_SIZE)]
        vs = [[] for _ in range(g.R_SIZE)]
        for i in range(g.R_SIZE):
            hs[i] = [e for e, var in hmaps[i].items() if solver.Value(var)]
            vs[i] = [e for e, var in vmaps[i].items() if solver.Value(var)]
        cert = rs.build_candidate(r, xset, list(bidx), hs, vs, [])
        score = len(cert)
        if score != BASE_SQUARE + selected or score < TARGET:
            raise RuntimeError(f"candidate score mismatch: {score} vs {selected}")
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

    write_status(args.status, status)


if __name__ == "__main__":
    main()
