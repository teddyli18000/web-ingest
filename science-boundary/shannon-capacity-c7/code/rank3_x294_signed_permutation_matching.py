#!/usr/bin/env python3
"""Scan all 5! * 2^5 signed coordinate permutations of 367-point fibers.

Coordinate permutations and independent sign reversals are automorphisms of
C7^5.  This expands the previously tested translation-only orbit in a direction
that changes the fiber's incidence with the fixed 366 positive-weight X nodes.
"""

import argparse
import itertools
import json
from pathlib import Path

import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs
import rank3_x294_two_swap_matching as tw

SPECIAL = 294
BASELINE = 134753


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--family", choices=("r0", "rank3", "x"), required=True)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = rs.load_rank3_state(r0, digits)
    supports, _ = g.support_masks(r, digits)
    model, bst = nm.solve_maxsat(rs.RANK3_K9, r, xset, digits, supports)
    if model is None or bst["score"] != BASELINE:
        raise RuntimeError(f"base drift {bst}")
    _, hs, vs = model

    x0 = xset[SPECIAL]
    weights = [sum(1 for f in arr if g.conflict(x0, f, digits)) for arr in vs]
    positive = [j for j, w in enumerate(weights) if w]
    if len(positive) != 366 or any(weights[j] != 1 for j in positive):
        raise RuntimeError("weight drift")
    ridx = {j: k for k, j in enumerate(positive)}
    hits = [[] for _ in range(g.U)]
    for j in positive:
        k = ridx[j]
        for v in rs.neighborhood(xset[j], digits):
            hits[v].append(k)

    base = tuple(r0 if args.family == "r0" else r if args.family == "rank3" else xset)
    bd = [digits[v] for v in base]

    best_m = 367
    best = []
    hist = {}
    seen = set()
    tested = 0
    for perm in itertools.permutations(range(5)):
        for negmask in range(32):
            G = tuple(sorted(
                g.enc5(tuple(
                    ((-a[perm[q]]) if ((negmask >> q) & 1) else a[perm[q]]) % 7
                    for q in range(5)
                ))
                for a in bd
            ))
            if G in seen:
                continue
            seen.add(G)
            tested += 1
            m = tw.hk([hits[v] for v in G], 366)
            hist[m] = hist.get(m, 0) + 1
            rec = (perm, negmask, G)
            if m < best_m:
                best_m = m
                best = [rec]
            elif m == best_m and len(best) < 100:
                best.append(rec)

    status = {
        "candidate": False,
        "family": args.family,
        "method": "signed-coordinate-permutation-hall-orbit",
        "raw_group_size": 120 * 32,
        "distinct_fibers_tested": tested,
        "matching_histogram": {str(k): v for k, v in sorted(hist.items())},
        "min_matching": best_m,
        "max_closure_objective": 367 - best_m,
        "best_transforms": [
            {"perm": list(p), "negmask": n} for p, n, _ in best
        ],
        "base_maxsat": bst,
    }

    if best_m <= 365:
        perm, negmask, G = best[0]
        bidx = [i for i in range(367) if i not in set(rs.RANK3_K9)]
        baseids = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
        obj, cert, nsel, pen, cost, rm, ad = tw.closure(
            list(G), weights, xset, digits, hs, vs, r, bidx, baseids
        )
        score = BASELINE + (obj - len(hs[SPECIAL]))
        if len(cert) != score or score <= BASELINE:
            raise RuntimeError(f"closure replay score={score} cert={len(cert)} obj={obj}")
        status.update({
            "candidate": True,
            "score": score,
            "winning_perm": list(perm),
            "winning_negmask": negmask,
            "closure_objective": obj,
            "selected_endpoints": nsel,
            "penalty_old_v_ports": pen,
            "rc2_cost": cost,
            "removed_vs_baseline": rm,
            "added_vs_baseline": ad,
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(z) for z in sorted(cert)]}, separators=(",", ":")) + "\n"
        )

    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(("FOUND" if status["candidate"] else "NONE"), json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
