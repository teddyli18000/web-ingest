#!/usr/bin/env python3
import argparse
import json
from itertools import product
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import IDPool, WCNF

import generalized9 as g
import neutral2_maxsat as nm
import neutral2_sweep as ns

BASELINE = 134_753
STATE_INDEX = 18
K9 = (60, 160, 231, 244, 250, 267, 330, 344, 364)
XZERO = 294
EXPECTED_REMOVE = (267, 294)
EXPECTED_ADD = (15083, 16388)


def neighborhood(v, digits):
    d = digits[v]
    for delta in product((-1, 0, 1), repeat=g.D):
        yield g.enc5(tuple((d[i] + delta[i]) % g.BASE for i in range(g.D)))


def load_state(r0, digits):
    supports0, _ = g.support_masks(r0, digits)
    states = ns.enumerate_states(r0, digits, supports0)
    r, rem, add = states[STATE_INDEX - 1]
    if tuple(rem) != EXPECTED_REMOVE or tuple(add) != EXPECTED_ADD:
        raise RuntimeError(f"state-18 drift: rem={rem} add={add}")
    return r


def port_conflict(a, b, xset, digits):
    oa, ia, ea = a
    ob, ib, eb = b
    if oa == "H" and ob == "H":
        return g.conflict(ea, eb, digits) and g.conflict(xset[ia], xset[ib], digits)
    if oa == "V" and ob == "V":
        return g.conflict(xset[ia], xset[ib], digits) and g.conflict(ea, eb, digits)
    if oa == "H":
        return g.conflict(ea, xset[ib], digits) and g.conflict(xset[ia], eb, digits)
    return g.conflict(xset[ib], ea, digits) and g.conflict(eb, xset[ia], digits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("model_output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--max-old-conflicts", type=int, default=3)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = load_state(r0, digits)
    supports, _ = g.support_masks(r, digits)

    base_model, base_stats = nm.solve_maxsat(K9, r, xset, digits, supports)
    if base_model is None or base_stats["score"] != BASELINE:
        raise RuntimeError(f"expected rank3 tie, got {base_stats}")
    _, hs, vs = base_model

    kset = set(K9)
    bidx = [i for i in range(g.R_SIZE) if i not in kset]
    bvals = {r[i] for i in bidx}
    if any(g.conflict(xset[XZERO], b, digits) for b in bvals):
        raise RuntimeError("x294 is not square-zero-conflict")

    selected = []
    selected_set = set()
    for i, arr in enumerate(hs):
        for e in arr:
            p = ("H", i, e)
            selected_set.add(p)
            selected.append(p)
    for i, arr in enumerate(vs):
        for e in arr:
            p = ("V", i, e)
            selected_set.add(p)
            selected.append(p)
    if len(selected) != base_stats["selected"]:
        raise RuntimeError("selected-port count mismatch")

    # Only new ports in the unique square-zero-conflict companion fiber x_294.
    raw = []
    conflict_sets = []
    hist = {}
    for ori in ("H", "V"):
        for e in range(g.U):
            if e in bvals:
                continue
            p = (ori, XZERO, e)
            if p in selected_set:
                continue
            conflicts = [idx for idx, q in enumerate(selected) if port_conflict(p, q, xset, digits)]
            n = len(conflicts)
            hist[n] = hist.get(n, 0) + 1
            if n <= args.max_old_conflicts:
                raw.append(p)
                conflict_sets.append(tuple(conflicts))

    pool = IDPool()
    wcnf = WCNF()

    def vp(i):
        return pool.id(("new", i))

    def vd(old_idx):
        return pool.id(("drop-old", old_idx))

    touched_old = set()
    for i, conflicts in enumerate(conflict_sets):
        wcnf.append([vp(i)], weight=1)
        for old_idx in conflicts:
            touched_old.add(old_idx)
            wcnf.append([-vp(i), vd(old_idx)])
    for old_idx in sorted(touched_old):
        wcnf.append([-vd(old_idx)], weight=1)

    # Same-orientation conflicts can be emitted from 5D neighborhoods.
    by_key = {(p[0], p[2]): i for i, p in enumerate(raw)}
    pair_clauses = 0
    for i, (ori, _, e) in enumerate(raw):
        for f in neighborhood(e, digits):
            j = by_key.get((ori, f))
            if j is not None and i < j:
                wcnf.append([-vp(i), -vp(j)])
                pair_clauses += 1

    # H_294(e) conflicts V_294(f) iff e~x294 and x294~f.
    x0 = xset[XZERO]
    hnear = [i for i, p in enumerate(raw) if p[0] == "H" and g.conflict(p[2], x0, digits)]
    vnear = [i for i, p in enumerate(raw) if p[0] == "V" and g.conflict(x0, p[2], digits)]
    for i in hnear:
        for j in vnear:
            wcnf.append([-vp(i), -vp(j)])
            pair_clauses += 1

    setup = {
        "state": STATE_INDEX,
        "k9": list(K9),
        "xzero": XZERO,
        "base_score": base_stats["score"],
        "base_selected": base_stats["selected"],
        "max_old_conflicts": args.max_old_conflicts,
        "all_new_conflict_histogram": hist,
        "candidate_new_ports": len(raw),
        "touched_old_ports": len(touched_old),
        "new_pair_conflict_clauses": pair_clauses,
        "variables": pool.top,
        "hard_clauses": len(wcnf.hard),
        "soft_clauses": len(wcnf.soft),
    }
    print("SETUP", json.dumps(setup, sort_keys=True), flush=True)

    with RC2(wcnf, solver="g3", adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    if model is None:
        raise RuntimeError("local MaxSAT returned no model")
    positive = {v for v in model if v > 0}
    add_idx = [i for i in range(len(raw)) if vp(i) in positive]
    drop_idx = [i for i in sorted(touched_old) if vd(i) in positive]
    gain = len(add_idx) - len(drop_idx)
    score = BASELINE + gain

    # Rebuild a full candidate directly from the concrete base tie assignment.
    keep_ports = [p for i, p in enumerate(selected) if i not in set(drop_idx)]
    add_ports = [raw[i] for i in add_idx]
    all_ports = keep_ports + add_ports
    cand = {r[a] * g.U + r[b] for a in bidx for b in bidx}
    for ori, i, e in all_ports:
        xv = xset[i]
        cand.add(e * g.U + xv if ori == "H" else xv * g.U + e)
    expected = len(bidx) ** 2 + len(all_ports)
    if len(cand) != expected:
        raise RuntimeError(f"duplicate candidate vertices: {len(cand)} != {expected}")

    # Independent replay of every port against square and every other port.
    for ori, i, e in all_ports:
        xv = xset[i]
        if ori == "H":
            if any(g.conflict(e, r[a], digits) and g.conflict(xv, r[b], digits) for a in bidx for b in bidx):
                raise RuntimeError("H port conflicts square")
        else:
            if any(g.conflict(xv, r[a], digits) and g.conflict(e, r[b], digits) for a in bidx for b in bidx):
                raise RuntimeError("V port conflicts square")
    for a in range(len(all_ports)):
        for b in range(a + 1, len(all_ports)):
            if port_conflict(all_ports[a], all_ports[b], xset, digits):
                raise RuntimeError(f"port replay conflict {a},{b}")

    stats = dict(setup)
    stats.update({
        "selected_new_ports": len(add_idx),
        "deleted_old_ports": len(drop_idx),
        "net_gain": gain,
        "score": score,
        "rc2_cost": cost,
    })
    model_data = {
        "method": "rank3-x294-local-augmentation-maxsat",
        "stats": stats,
        "deleted_old_port_indices": drop_idx,
        "deleted_old_ports": [selected[i] for i in drop_idx],
        "added_ports": add_ports,
    }
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.model_output.write_text(json.dumps(model_data, separators=(",", ":")) + "\n")

    baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
    status = {
        "candidate": score > BASELINE,
        "score": score,
        "method": "rank3-x294-local-augmentation-maxsat",
        "stats": stats,
        "removed_vs_baseline": len(baseline - cand),
        "added_vs_baseline": len(cand - baseline),
    }
    if score > BASELINE:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"points": [g.dec10(v) for v in sorted(cand)]}, separators=(",", ":")) + "\n")
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
    else:
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
