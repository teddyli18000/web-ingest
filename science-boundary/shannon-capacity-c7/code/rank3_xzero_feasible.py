#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from pysat.formula import IDPool
from pysat.solvers import Minicard

import generalized9 as g
import rank3_square_relax as rs

BASE_SQUARE = 358 ** 2
TARGET_TOTAL = 134_754
NEED_PORTS = TARGET_TOTAL - BASE_SQUARE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--include-b-endpoints-on-zero-conflict-fibers", action="store_true")
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
    outside_count = [(supports[v] & bmask).bit_count() for v in range(g.U)]
    x_bcount = [(supports[xv] & bmask).bit_count() for xv in xset]
    x_zero = [i for i, c in enumerate(x_bcount) if c == 0]

    safe = tuple(v for v in range(g.U) if v not in bvals and outside_count[v] == 0)
    cand = []
    cand_sets = []
    for xi, cc in enumerate(x_bcount):
        if cc == 0:
            if args.include_b_endpoints_on_zero_conflict_fibers:
                arr = tuple(range(g.U))
            else:
                arr = tuple(v for v in range(g.U) if v not in bvals)
        else:
            arr = safe
        cand.append(arr)
        cand_sets.append(set(arr))

    x_hits = [[] for _ in range(g.U)]
    x_neigh = []
    for xi, xv in enumerate(xset):
        nv = tuple(rs.neighborhood(xv, digits))
        x_neigh.append(set(nv))
        for v in nv:
            x_hits[v].append(xi)

    pool = IDPool()
    def vh(xi, e): return pool.id(("h", xi, e))
    def vv(xi, e): return pool.id(("v", xi, e))

    all_vars = []
    clauses = []
    same = 0
    cross = 0

    for xi in range(g.R_SIZE):
        for e in cand[xi]:
            all_vars.append(vh(xi, e))
            all_vars.append(vv(xi, e))

    for xi in range(g.R_SIZE):
        s = cand_sets[xi]
        for e in cand[xi]:
            for f in rs.neighborhood(e, digits):
                if f <= e or f not in s:
                    continue
                clauses.append([-vh(xi, e), -vh(xi, f)])
                clauses.append([-vv(xi, e), -vv(xi, f)])
                same += 2

    for i in range(g.R_SIZE):
        ni = x_neigh[i]
        for e in cand[i]:
            h = vh(i, e)
            for j in x_hits[e]:
                for f in ni.intersection(cand_sets[j]):
                    clauses.append([-h, -vv(j, f)])
                    cross += 1

    setup = {
        "state": rs.STATE_INDEX,
        "k9": list(rs.RANK3_K9),
        "base_square": BASE_SQUARE,
        "target_total": TARGET_TOTAL,
        "need_ports": NEED_PORTS,
        "safe_endpoints": len(safe),
        "x_zero_indices": x_zero,
        "include_b_endpoints_on_zero_conflict_fibers": args.include_b_endpoints_on_zero_conflict_fibers,
        "candidate_port_variables": len(all_vars),
        "same_orientation_clauses": same,
        "cross_orientation_clauses": cross,
        "variables": pool.top,
        "hard_pair_clauses": len(clauses),
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    if NEED_PORTS > len(all_vars):
        raise RuntimeError("not enough port variables even before conflicts")

    with Minicard(bootstrap_with=clauses) as solver:
        # At least NEED_PORTS selected <=> at most N-NEED_PORTS negated literals true.
        solver.add_atmost([-v for v in all_vars], len(all_vars) - NEED_PORTS)
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
    selected = 0
    for xi in range(g.R_SIZE):
        for e in cand[xi]:
            if vh(xi, e) in pos:
                hs[xi].append(e); selected += 1
            if vv(xi, e) in pos:
                vs[xi].append(e); selected += 1

    candidate = rs.build_candidate(r, xset, bidx, hs, vs, [])
    if len(candidate) != BASE_SQUARE + selected:
        raise RuntimeError("candidate score mismatch")
    if len(candidate) < TARGET_TOTAL:
        raise RuntimeError("SAT model missed target")

    baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n"
    )
    status = {
        "candidate": True,
        "sat": True,
        "score": len(candidate),
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
