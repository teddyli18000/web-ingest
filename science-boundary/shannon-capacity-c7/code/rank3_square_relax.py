#!/usr/bin/env python3
import argparse
import json
from itertools import product
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import IDPool, WCNF

import generalized9 as g
import neutral2_sweep as ns

BASELINE = 134_753
STATE_INDEX = 18
RANK3_K9 = (60, 160, 231, 244, 250, 267, 330, 344, 364)
EXPECTED_REMOVE = (267, 294)
EXPECTED_ADD = (15083, 16388)


def bit_indices(mask):
    out = []
    while mask:
        bit = mask & -mask
        out.append(bit.bit_length() - 1)
        mask ^= bit
    return out


def neighborhood(v, digits):
    d = digits[v]
    for delta in product((-1, 0, 1), repeat=g.D):
        yield g.enc5(tuple((d[i] + delta[i]) % g.BASE for i in range(g.D)))


def load_rank3_state(r0, digits):
    supports0, _ = g.support_masks(r0, digits)
    states = ns.enumerate_states(r0, digits, supports0)
    if len(states) < STATE_INDEX:
        raise RuntimeError(f"only {len(states)} neutral2 states")
    r, rem, add = states[STATE_INDEX - 1]
    if tuple(rem) != EXPECTED_REMOVE or tuple(add) != EXPECTED_ADD:
        raise RuntimeError(f"state-18 drift: rem={rem} add={add}")
    return r


def solve(r, xset, digits, supports, max_square_conflicts, include_b_zero=False):
    kset = set(RANK3_K9)
    bidx = [i for i in range(g.R_SIZE) if i not in kset]
    bmask = sum(1 << i for i in bidx)
    bvals = {r[i] for i in bidx}
    base_square = len(bidx) ** 2

    outside = [supports[v] & bmask for v in range(g.U)]
    outside_count = [m.bit_count() for m in outside]
    safe = [v for v in range(g.U) if v not in bvals and outside_count[v] == 0]
    count_hist = {}
    for v in range(g.U):
        if v in bvals:
            continue
        c = outside_count[v]
        count_hist[c] = count_hist.get(c, 0) + 1

    x_bmask = [supports[xv] & bmask for xv in xset]
    x_bcount = [m.bit_count() for m in x_bmask]
    x_hist = {}
    for c in x_bcount:
        x_hist[c] = x_hist.get(c, 0) + 1

    cand = []
    cand_sets = []
    for xi in range(g.R_SIZE):
        cc = x_bcount[xi]
        arr = tuple(
            v for v in range(g.U)
            if (v not in bvals or (include_b_zero and cc == 0))
            and outside_count[v] * cc <= max_square_conflicts
        )
        cand.append(arr)
        cand_sets.append(set(arr))

    # x_hits[v] = companion indices whose 5D vertex conflicts with v.
    x_hits = [[] for _ in range(g.U)]
    x_neigh = []
    for xi, xv in enumerate(xset):
        nv = tuple(neighborhood(xv, digits))
        x_neigh.append(set(nv))
        for v in nv:
            x_hits[v].append(xi)

    pool = IDPool()
    wcnf = WCNF()

    def vh(xi, e):
        return pool.id(("h", xi, e))

    def vv(xi, e):
        return pool.id(("v", xi, e))

    def vd(a, b):
        return pool.id(("delete-square", a, b))

    touched = set()
    port_vars = 0
    extra_ports = 0
    port_cost_hist = {}
    for xi in range(g.R_SIZE):
        cm = x_bmask[xi]
        cbits = bit_indices(cm)
        cc = len(cbits)
        for e in cand[xi]:
            am = outside[e]
            abits = bit_indices(am)
            cost = len(abits) * cc
            if cost > max_square_conflicts:
                raise RuntimeError("candidate exceeds square-conflict radius")
            port_cost_hist[cost] = port_cost_hist.get(cost, 0) + 2
            h = vh(xi, e)
            v = vv(xi, e)
            wcnf.append([h], weight=1)
            wcnf.append([v], weight=1)
            port_vars += 2
            if cost:
                extra_ports += 2
            for a in abits:
                for b in cbits:
                    hp = (a, b)
                    vp = (b, a)
                    touched.add(hp)
                    touched.add(vp)
                    wcnf.append([-h, vd(*hp)])
                    wcnf.append([-v, vd(*vp)])

    for a, b in sorted(touched):
        wcnf.append([-vd(a, b)], weight=1)

    same_edges = 0
    for xi in range(g.R_SIZE):
        s = cand_sets[xi]
        for e in cand[xi]:
            for f in neighborhood(e, digits):
                if f <= e or f not in s:
                    continue
                wcnf.append([-vh(xi, e), -vh(xi, f)])
                wcnf.append([-vv(xi, e), -vv(xi, f)])
                same_edges += 2

    cross_clauses = 0
    for i in range(g.R_SIZE):
        ni = x_neigh[i]
        for e in cand[i]:
            h = vh(i, e)
            for j in x_hits[e]:
                for f in ni.intersection(cand_sets[j]):
                    wcnf.append([-h, -vv(j, f)])
                    cross_clauses += 1

    setup = {
        "state": STATE_INDEX,
        "k9": list(RANK3_K9),
        "max_port_square_conflicts": max_square_conflicts,
        "include_b_endpoints_on_zero_conflict_fibers": include_b_zero,
        "base_square": base_square,
        "safe_endpoints": len(safe),
        "endpoint_outside_conflict_histogram": count_hist,
        "x_conflict_histogram": x_hist,
        "port_square_conflict_histogram": port_cost_hist,
        "candidate_ports": port_vars,
        "new_port_variables": extra_ports,
        "touched_square_vertices": len(touched),
        "same_orientation_clauses": same_edges,
        "cross_orientation_clauses": cross_clauses,
        "variables": pool.top,
        "hard_clauses": len(wcnf.hard),
        "soft_clauses": len(wcnf.soft),
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    with RC2(wcnf, solver="g3", adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError("MaxSAT returned no model")
    positive = {x for x in model if x > 0}

    hs = [[] for _ in range(g.R_SIZE)]
    vs = [[] for _ in range(g.R_SIZE)]
    selected = 0
    for xi in range(g.R_SIZE):
        for e in cand[xi]:
            if vh(xi, e) in positive:
                hs[xi].append(e)
                selected += 1
            if vv(xi, e) in positive:
                vs[xi].append(e)
                selected += 1

    deleted = [(a, b) for a, b in sorted(touched) if vd(a, b) in positive]
    score = base_square - len(deleted) + selected
    stats = dict(setup)
    stats.update({
        "selected_ports": selected,
        "deleted_square_vertices": len(deleted),
        "score": score,
        "rc2_cost": cost,
        "min_h": min(map(len, hs)),
        "max_h": max(map(len, hs)),
        "min_v": min(map(len, vs)),
        "max_v": max(map(len, vs)),
    })
    return bidx, hs, vs, deleted, stats


def build_candidate(r, xset, bidx, hs, vs, deleted):
    deleted_set = set(deleted)
    candidate = set()
    for ai in bidx:
        for bi in bidx:
            if (ai, bi) not in deleted_set:
                candidate.add(r[ai] * g.U + r[bi])
    selected = 0
    for xi, xv in enumerate(xset):
        for e in hs[xi]:
            candidate.add(e * g.U + xv)
            selected += 1
        for e in vs[xi]:
            candidate.add(xv * g.U + e)
            selected += 1
    expected = len(bidx) ** 2 - len(deleted_set) + selected
    if len(candidate) != expected:
        raise RuntimeError(f"candidate duplicate: {len(candidate)} != {expected}")
    return candidate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("model_output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--max-port-square-conflicts", type=int, default=2)
    ap.add_argument("--include-b-endpoints-on-zero-conflict-fibers", action="store_true")
    args = ap.parse_args()
    if args.max_port_square_conflicts < 0:
        raise SystemExit("max-port-square-conflicts must be nonnegative")

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = load_rank3_state(r0, digits)
    supports, _ = g.support_masks(r, digits)

    bidx, hs, vs, deleted, stats = solve(
        r,
        xset,
        digits,
        supports,
        args.max_port_square_conflicts,
        args.include_b_endpoints_on_zero_conflict_fibers,
    )
    candidate = build_candidate(r, xset, bidx, hs, vs, deleted)
    if len(candidate) != stats["score"]:
        raise RuntimeError("score mismatch")

    suffix = "-bzero" if args.include_b_endpoints_on_zero_conflict_fibers else ""
    method = f"rank3-maxsat-square-relax-conflict-le{args.max_port_square_conflicts}{suffix}"
    model_data = {
        "method": method,
        "state_index": STATE_INDEX,
        "k9": list(RANK3_K9),
        "neutral_remove_indices": list(EXPECTED_REMOVE),
        "neutral_add": list(EXPECTED_ADD),
        "deleted_square_index_pairs": [list(x) for x in deleted],
        "selected_h": [[xi, e] for xi, arr in enumerate(hs) for e in arr],
        "selected_v": [[xi, e] for xi, arr in enumerate(vs) for e in arr],
        "stats": stats,
    }
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.model_output.write_text(json.dumps(model_data, separators=(",", ":")) + "\n")

    baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
    status = {
        "candidate": len(candidate) > BASELINE,
        "score": len(candidate),
        "method": method,
        "stats": stats,
        "removed_vs_baseline": len(baseline - candidate),
        "added_vs_baseline": len(candidate - baseline),
    }
    if len(candidate) > BASELINE:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n"
        )
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
    else:
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
