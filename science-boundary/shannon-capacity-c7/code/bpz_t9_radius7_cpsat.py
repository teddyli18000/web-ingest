#!/usr/bin/env python3
"""Independent exact CP-SAT decision for the BPZ t=9 7-owner / 8-addition repair.

This encodes the same mathematical question as ``bpz_t9_radius7_sat.py`` but
uses OR-Tools CP-SAT rather than PySAT/Minicard.  A feasible solution selects
exactly eight outside vertices whose conflict-owner union has size at most
seven and whose vertices are pairwise nonconfusable.  The latter condition is
encoded exactly by the 7^5 binary cubes of C7^5.

If feasible, replay the 5D repair independently and materialize the full 10D
134770-point t=9 construction for the upstream Few Shots verifier.
"""
import argparse
import json
import sys
from itertools import product
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_obstruction_mis as mis
import bpz_t9_kamis as bridge

RADIUS = 7
NEED = 8


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    I, published_X, pairs, PH, PV, ring, digits, obstruction, lower = bridge.reconstruct(args.tan_root)
    if len(lower) != 366 or len(obstruction) != 1098:
        raise RuntimeError("instance drift")
    lower = list(lower)
    lower_set = set(lower)

    cand = []
    supports = []
    support_hist = {}
    for v in range(mis.U):
        if v in obstruction or v in lower_set:
            continue
        s = [i for i, u in enumerate(lower) if mis.conflict(v, u, digits)]
        if 1 <= len(s) <= RADIUS:
            cand.append(v)
            supports.append(tuple(s))
            support_hist[len(s)] = support_hist.get(len(s), 0) + 1

    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x_{v}") for v in cand]
    y = [model.NewBoolVar(f"y_{i}") for i in range(len(lower))]

    owner_users = [[] for _ in lower]
    implications = 0
    for j, s in enumerate(supports):
        for i in s:
            model.AddImplication(x[j], y[i])
            owner_users[i].append(x[j])
            implications += 1

    # Remove gratuitous owner selections. Together with x -> y this makes y
    # exactly the owner union of the selected outside vertices.
    owner_reverse = 0
    for i, users in enumerate(owner_users):
        if users:
            model.Add(sum(users) >= y[i])
            owner_reverse += 1
        else:
            model.Add(y[i] == 0)

    model.Add(sum(y) <= RADIUS)
    # Any solution with >8 additions contains an 8-subset with the same or
    # smaller owner union, so equality is an exact symmetry/size reduction.
    model.Add(sum(x) == NEED)

    cindex = {v: j for j, v in enumerate(cand)}
    nontrivial = 0
    cube_lits = 0
    max_cube = 0
    for a in range(mis.U):
        ad = digits[a]
        js = []
        for bits in product((0, 1), repeat=mis.D):
            v = mis.enc(tuple((ad[k] + bits[k]) % mis.Q for k in range(mis.D)))
            j = cindex.get(v)
            if j is not None:
                js.append(j)
        if len(js) >= 2:
            model.AddAtMostOne([x[j] for j in js])
            nontrivial += 1
            cube_lits += len(js)
            max_cube = max(max_cube, len(js))

    setup = {
        "starting_size": len(lower),
        "obstruction_size": len(obstruction),
        "candidate_vertices": len(cand),
        "support_histogram": {str(k): v for k, v in sorted(support_hist.items())},
        "owner_variables": len(y),
        "radius": RADIUS,
        "need_additions": NEED,
        "implications": implications,
        "owner_reverse_constraints": owner_reverse,
        "nontrivial_cube_constraints": nontrivial,
        "cube_literal_total": cube_lits,
        "max_candidate_vertices_per_cube": max_cube,
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 4
    solver.parameters.cp_model_presolve = True
    solver.parameters.cp_model_probing_level = 2
    solver.parameters.log_search_progress = True
    status_code = solver.Solve(model)
    status_name = solver.StatusName(status_code)
    print("CP_STATUS", status_name, flush=True)

    args.status.parent.mkdir(parents=True, exist_ok=True)
    if status_code == cp_model.INFEASIBLE:
        status = {
            "candidate": False,
            "sat": False,
            "exact": True,
            "method": "bpz-t9-radius7-cpsat",
            "score": 134753,
            "solver_status": status_name,
            "setup": setup,
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("UNSAT", json.dumps(status, sort_keys=True), flush=True)
        return
    if status_code not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        status = {
            "candidate": False,
            "sat": None,
            "exact": False,
            "method": "bpz-t9-radius7-cpsat",
            "score": 134753,
            "solver_status": status_name,
            "setup": setup,
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("UNKNOWN", json.dumps(status, sort_keys=True), flush=True)
        return

    chosen = [j for j in range(len(cand)) if solver.Value(x[j])]
    if len(chosen) != NEED:
        raise RuntimeError(f"selected {len(chosen)} candidates, expected {NEED}")
    add = [cand[j] for j in chosen]
    owners = sorted({i for j in chosen for i in supports[j]})
    if len(owners) > RADIUS:
        raise RuntimeError("owner-union replay exceeds radius")

    owner_set = set(owners)
    new = [v for i, v in enumerate(lower) if i not in owner_set] + add
    if len(new) < 367 or set(new) & obstruction or not mis.independent(new, digits):
        raise RuntimeError(f"CP-SAT replay failed size={len(new)} owners={len(owners)}")
    X = new[:367]
    if len(X) != 367 or not mis.independent(X, digits):
        raise RuntimeError("367-set replay failed")

    points, xp = mis.build(I, X, pairs, PH, PV, ring)
    if len(points) != mis.TARGET:
        raise RuntimeError(f"10D score drift {len(points)}")

    out_status = {
        "candidate": True,
        "sat": True,
        "exact": True,
        "method": "bpz-t9-radius7-cpsat",
        "score": len(points),
        "solver_status": status_name,
        "removed_owners": owners,
        "added_auxiliary": add,
        "raw_repaired_auxiliary_size": len(new),
        "setup": setup,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(out_status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(out_status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
