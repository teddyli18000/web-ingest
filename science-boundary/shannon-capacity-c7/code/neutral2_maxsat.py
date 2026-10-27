#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import IDPool, WCNF

import generalized9 as g
import neutral2_sweep as ns

BASELINE = 134_753
K = 9
BASE_SQUARE = (g.R_SIZE - K) ** 2
NEED_EXTRAS = BASELINE + 1 - BASE_SQUARE


def owner_groups(r, supports):
    rset = set(r)
    owners = {}
    for v, sm in enumerate(supports):
        if v in rset or sm.bit_count() != 1:
            continue
        i = (sm & -sm).bit_length() - 1
        owners.setdefault(i, []).append(v)
    return owners


def solve_maxsat(k9, r, xset, digits, supports):
    kmask = sum(1 << i for i in k9)
    safe = g.safe_vertices(kmask, supports)
    pool = IDPool()
    wcnf = WCNF()

    def vh(xi, ei):
        return pool.id(("h", xi, ei))

    def vv(xi, ei):
        return pool.id(("v", xi, ei))

    endpoint_edges = []
    for a, b in combinations(range(len(safe)), 2):
        if g.conflict(safe[a], safe[b], digits):
            endpoint_edges.append((a, b))

    for xi in range(g.R_SIZE):
        for a, b in endpoint_edges:
            wcnf.append([-vh(xi, a), -vh(xi, b)])
            wcnf.append([-vv(xi, a), -vv(xi, b)])

    rel = []
    active = []
    for xi, xv in enumerate(xset):
        rr = [ei for ei, e in enumerate(safe) if g.conflict(e, xv, digits)]
        rel.append(rr)
        if rr:
            active.append(xi)

    cross_clauses = 0
    for i in active:
        ri = rel[i]
        for j in active:
            rj = rel[j]
            for e in rj:
                he = vh(i, e)
                for f in ri:
                    wcnf.append([-he, -vv(j, f)])
                    cross_clauses += 1

    all_vars = []
    for xi in range(g.R_SIZE):
        for ei in range(len(safe)):
            h = vh(xi, ei)
            v = vv(xi, ei)
            all_vars.extend((h, v))
            wcnf.append([h], weight=1)
            wcnf.append([v], weight=1)

    print(
        "MAXSAT instance",
        json.dumps(
            {
                "safe": len(safe),
                "active_x": len(active),
                "endpoint_edges": len(endpoint_edges),
                "cross_clauses": cross_clauses,
                "candidate_vars": len(all_vars),
                "need_extras": NEED_EXTRAS,
                "base_square": BASE_SQUARE,
            },
            sort_keys=True,
        ),
        flush=True,
    )

    with RC2(wcnf, solver="g3", adapt=True, exhaust=True, verbose=1) as rc2:
        model = rc2.compute()
        cost = rc2.cost

    if model is None:
        return None, {
            "safe": len(safe),
            "active_x": len(active),
            "endpoint_edges": len(endpoint_edges),
            "cross_clauses": cross_clauses,
            "candidate_vars": len(all_vars),
            "selected": 0,
            "score": BASE_SQUARE,
            "rc2_cost": None,
        }

    positive = set(x for x in model if x > 0)
    hs = [[] for _ in range(g.R_SIZE)]
    vs = [[] for _ in range(g.R_SIZE)]
    selected = 0
    for xi in range(g.R_SIZE):
        for ei, e in enumerate(safe):
            if vh(xi, ei) in positive:
                hs[xi].append(e)
                selected += 1
            if vv(xi, ei) in positive:
                vs[xi].append(e)
                selected += 1

    stats = {
        "safe": len(safe),
        "active_x": len(active),
        "endpoint_edges": len(endpoint_edges),
        "cross_clauses": cross_clauses,
        "candidate_vars": len(all_vars),
        "selected": selected,
        "score": BASE_SQUARE + selected,
        "rc2_cost": cost,
        "min_h": min(map(len, hs)),
        "max_h": max(map(len, hs)),
        "min_v": min(map(len, vs)),
        "max_v": max(map(len, vs)),
    }
    return (safe, hs, vs), stats


def build_candidate(k9, model, r, xset, digits):
    _, hs, vs = model
    kset = set(k9)
    b = [rv for i, rv in enumerate(r) if i not in kset]
    candidate = {a * g.U + c for a in b for c in b}

    selected = 0
    for xi, xv in enumerate(xset):
        for e in hs[xi]:
            candidate.add(e * g.U + xv)
            selected += 1
        for e in vs[xi]:
            candidate.add(xv * g.U + e)
            selected += 1

    expected = len(b) ** 2 + selected
    if len(candidate) != expected:
        raise RuntimeError(f"duplicate 10D vertices: {len(candidate)} != {expected}")

    for xi in range(g.R_SIZE):
        for a, b0 in combinations(hs[xi], 2):
            if g.conflict(a, b0, digits):
                raise RuntimeError("H fiber conflict")
        for a, b0 in combinations(vs[xi], 2):
            if g.conflict(a, b0, digits):
                raise RuntimeError("V fiber conflict")

    for i in range(g.R_SIZE):
        for j in range(g.R_SIZE):
            if any(g.conflict(e, xset[j], digits) for e in hs[i]) and any(
                g.conflict(xset[i], f, digits) for f in vs[j]
            ):
                raise RuntimeError("H/V cross conflict")

    return candidate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--combo-index", type=int, default=-1)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    supports0, _ = g.support_masks(r0, digits)
    states = ns.enumerate_states(r0, digits, supports0)

    eligible = []
    for si, (r, rem, add) in enumerate(states, 1):
        supports, _ = g.support_masks(r, digits)
        owners = owner_groups(r, supports)
        if len(owners) < K:
            continue
        for k9 in combinations(sorted(owners), K):
            kmask = sum(1 << i for i in k9)
            safe_count = sum(1 for sm in supports if sm & ~kmask == 0)
            eligible.append((safe_count, si, r, rem, add, supports, k9, len(owners)))

    eligible.sort(key=lambda z: (-z[0], z[1], z[6]))
    print(
        "eligible",
        json.dumps(
            [
                {
                    "rank": idx,
                    "safe": rec[0],
                    "state": rec[1],
                    "remove": list(rec[3]),
                    "add": list(rec[4]),
                    "k9": list(rec[6]),
                    "centers": rec[7],
                }
                for idx, rec in enumerate(eligible)
            ],
            sort_keys=True,
        ),
        flush=True,
    )

    if args.combo_index >= 0:
        if args.combo_index >= len(eligible):
            status = {
                "candidate": False,
                "skipped": True,
                "combo_index": args.combo_index,
                "eligible": len(eligible),
            }
            args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
            print("SKIP", json.dumps(status, sort_keys=True), flush=True)
            return
        todo = [(args.combo_index, eligible[args.combo_index])]
    else:
        todo = list(enumerate(eligible))

    baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
    best = None
    for rank, rec in todo:
        safe_count, si, r, rem, add, supports, k9, centers = rec
        print(
            "TRY",
            json.dumps(
                {
                    "rank": rank,
                    "state": si,
                    "safe": safe_count,
                    "k9": list(k9),
                    "remove": list(rem),
                    "add": list(add),
                },
                sort_keys=True,
            ),
            flush=True,
        )
        model, stats = solve_maxsat(k9, r, xset, digits, supports)
        record = {
            "rank": rank,
            "state": si,
            "safe": safe_count,
            "k9": list(k9),
            "remove": list(rem),
            "add": list(add),
            "centers": centers,
            "stats": stats,
        }
        if best is None or stats["score"] > best["stats"]["score"]:
            best = record
        print("RESULT", json.dumps(record, sort_keys=True), flush=True)

        if model is None or stats["score"] <= BASELINE:
            continue
        candidate = build_candidate(k9, model, r, xset, digits)
        if len(candidate) != stats["score"]:
            raise RuntimeError("candidate score mismatch")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n"
        )
        status = {
            "candidate": True,
            "score": len(candidate),
            "method": "neutral2-maxsat-partial-nine-port",
            "combo_index": rank,
            "state_index": si,
            "neutral_remove_indices": list(rem),
            "neutral_add": list(add),
            "selected_indices": list(k9),
            "selected_centers": [r[i] for i in k9],
            "maxsat": stats,
            "removed_vs_baseline": len(baseline - candidate),
            "added_vs_baseline": len(candidate - baseline),
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
        return

    status = {
        "candidate": False,
        "score": best["stats"]["score"] if best else BASE_SQUARE,
        "method": "neutral2-maxsat-partial-nine-port",
        "need_score": BASELINE + 1,
        "best": best,
    }
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("NONE", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
