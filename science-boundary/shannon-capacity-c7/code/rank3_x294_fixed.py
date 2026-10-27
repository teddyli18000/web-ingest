#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.solvers import Minicard
from pysat.formula import IDPool

import generalized9 as g
import rank3_square_relax as rs

BASE_SQUARE = 358 ** 2
TARGET = 134_754
NEED_PORTS = TARGET - BASE_SQUARE
SPECIAL = 294


def independent(vals, digits):
    return all(not g.conflict(a, b, digits) for a, b in combinations(vals, 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--fixed-set", choices=("r0", "rank3", "x"), required=True)
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
    x_bcount = [(supports[xv] & bmask).bit_count() for xv in xset]
    if x_bcount[SPECIAL] != 0:
        raise RuntimeError(f"X_{SPECIAL} is not zero-conflict: {x_bcount[SPECIAL]}")

    safe = tuple(
        v for v in range(g.U)
        if v not in bvals and (supports[v] & bmask) == 0
    )
    if len(safe) != 18:
        raise RuntimeError(f"safe endpoint drift: {len(safe)}")

    if args.fixed_set == "r0":
        fixed = tuple(r0)
    elif args.fixed_set == "rank3":
        fixed = tuple(r)
    else:
        fixed = tuple(xset)
    if len(fixed) != 367 or len(set(fixed)) != 367 or not independent(fixed, digits):
        raise RuntimeError("fixed endpoint set is not a 367-point independent set")

    # H(SPECIAL,e) is square-safe for every e because X_SPECIAL conflicts with no B point.
    # All other variable fibers use the 18 globally safe endpoints.
    pool = IDPool()
    def vh(i, e): return pool.id(("h", i, e))
    def vv(i, e): return pool.id(("v", i, e))

    vars_ = []
    clauses = []
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            vars_.extend(vh(i, e) for e in safe)
        vars_.extend(vv(i, e) for e in safe)

    # Same-orientation conflicts within each variable fiber.
    same_edges = [(a, b) for a, b in combinations(safe, 2) if g.conflict(a, b, digits)]
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for a, b in same_edges:
                clauses.append([-vh(i, a), -vh(i, b)])
        for a, b in same_edges:
            clauses.append([-vv(i, a), -vv(i, b)])

    # Variable H/V cross conflicts.
    cross = 0
    for i in range(g.R_SIZE):
        if i == SPECIAL:
            continue
        for e in safe:
            h = vh(i, e)
            for j in range(g.R_SIZE):
                if not g.conflict(e, xset[j], digits):
                    continue
                for f in safe:
                    if g.conflict(xset[i], f, digits):
                        clauses.append([-h, -vv(j, f)])
                        cross += 1

    # Fixed H_SPECIAL versus variable V fibers becomes unary bans.
    fixed_hits = [any(g.conflict(e, xset[j], digits) for e in fixed) for j in range(g.R_SIZE)]
    x_special_neighbors = [f for f in safe if g.conflict(xset[SPECIAL], f, digits)]
    banned = 0
    for j, hit in enumerate(fixed_hits):
        if not hit:
            continue
        for f in x_special_neighbors:
            clauses.append([-vv(j, f)])
            banned += 1

    need_variable = NEED_PORTS - len(fixed)
    setup = {
        "fixed_set": args.fixed_set,
        "special_x_index": SPECIAL,
        "fixed_h_ports": len(fixed),
        "safe_endpoints": len(safe),
        "need_total_ports": NEED_PORTS,
        "need_variable_ports": need_variable,
        "candidate_variable_ports": len(vars_),
        "same_endpoint_edges": len(same_edges),
        "cross_clauses": cross,
        "fixed_hit_x_count": sum(fixed_hits),
        "x_special_safe_neighbors": len(x_special_neighbors),
        "unary_bans": banned,
        "variables": pool.top,
        "clauses": len(clauses),
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    with Minicard(bootstrap_with=clauses) as solver:
        solver.add_atmost([-v for v in vars_], len(vars_) - need_variable)
        sat = solver.solve()
        model = solver.get_model() if sat else None

    if not sat:
        status = {"candidate": False, "sat": False, "score": 134753, "setup": setup}
        args.status.parent.mkdir(parents=True, exist_ok=True)
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("UNSAT", json.dumps(status, sort_keys=True), flush=True)
        return

    pos = {v for v in model if v > 0}
    hs = [[] for _ in range(g.R_SIZE)]
    vs = [[] for _ in range(g.R_SIZE)]
    hs[SPECIAL] = list(fixed)
    selected = len(fixed)
    for i in range(g.R_SIZE):
        if i != SPECIAL:
            for e in safe:
                if vh(i, e) in pos:
                    hs[i].append(e); selected += 1
        for e in safe:
            if vv(i, e) in pos:
                vs[i].append(e); selected += 1

    candidate = rs.build_candidate(r, xset, bidx, hs, vs, [])
    score = len(candidate)
    if score < TARGET or score != BASE_SQUARE + selected:
        raise RuntimeError(f"bad SAT candidate score {score}, selected={selected}")

    baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n"
    )
    status = {
        "candidate": True,
        "sat": True,
        "score": score,
        "selected_ports": selected,
        "setup": setup,
        "removed_vs_baseline": len(baseline - candidate),
        "added_vs_baseline": len(candidate - baseline),
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
