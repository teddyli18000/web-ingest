#!/usr/bin/env python3
"""Exact prize closure for complete products of the five irreducible raw +1 defects.

The pinned BPZ core is BxB.  We have exactly five irreducible 5D support
replacements used here: one 5->6 and four 6->7.  For defects (C,Y) and (D,Z),
the complete Cartesian product YxZ is independent in C7^10 and is supported on
the core rectangle CxD.  Its raw margin over that rectangle is large:
11, 12, or 13 points depending on the pair.

For each of the 18 public terminal peripheries and each ordered defect pair we
solve the *true baseline-relative* local exchange exactly.  Candidate vertices
already present in the baseline are free and omitted from the reward set.  Each
external candidate has reward +1 and implies deletion of every baseline point
(core or terminal periphery) that conflicts with it.  Because the full product
candidate family is independent, the exact objective

    #selected external candidates - #distinct deleted baseline blockers

is a maximum-weight closure / s-t min cut.  A positive optimum is materialized
as a full 10D certificate and independently checked by the Few Shots verifier.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from bpz_amplify_row_defects import Dinic, PINNED_DEFECTS
from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery, validate_defects


def maximum_closure(losses: list[set[int]], blocker_count: int):
    nc = len(losses)
    s = nc + blocker_count
    t = s + 1
    d = Dinic(t + 1)
    inf = nc + blocker_count + 10
    for i, L in enumerate(losses):
        d.add(s, i, 1)
        for j in L:
            d.add(i, nc + j, inf)
    for j in range(blocker_count):
        d.add(nc + j, t, 1)
    cut = d.flow(s, t)
    side = d.source_side(s)
    selected = [i for i in range(nc) if i in side]
    lost = set()
    for i in selected:
        lost.update(losses[i])
    delta = len(selected) - len(lost)
    if delta != nc - cut:
        raise RuntimeError(("closure mismatch", delta, nc - cut))
    return delta, selected, lost


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("certificate", type=Path)
    args = ap.parse_args()
    root = args.tan_root.resolve()
    _base, ring, B, fam = load_geometry(root)
    defects = validate_defects(ring, B)
    if len(defects) != 5:
        raise RuntimeError(("irreducible defect count drift", len(defects)))

    # Independent audit of each pinned Y and irreducibility relative to its C.
    for d in defects:
        C, Y = set(d["C"]), list(d["Y"])
        if C & set(Y):
            raise RuntimeError(("pinned defect not irreducible", d["name"], sorted(C & set(Y))))
        for i, y in enumerate(Y):
            for z in Y[i+1:]:
                if z in ring.NB[y]:
                    raise RuntimeError(("Y not independent", d["name"], y, z))

    Bcore = {(a, b) for a in B for b in B}
    results = []
    best_full = None

    for q in ("O", "H", "V"):
        for r in ("O", "H", "V"):
            for torient in (0, 1):
                P = terminal_periphery(fam, q, r, torient)
                baseline = Bcore | P
                if len(baseline) != 134753:
                    raise RuntimeError(("baseline size drift", q, r, torient, len(baseline)))
                # Only blockers in the small supported core rectangle plus P can
                # be touched, but indexing the full baseline keeps the replay simple.
                bvec = sorted(baseline)
                bidx = {p: i for i, p in enumerate(bvec)}

                for ia, da in enumerate(defects):
                    for ib, db in enumerate(defects):
                        raw = [(x, y) for x in da["Y"] for y in db["Y"]]
                        # Cartesian product of two independent 5D sets is independent.
                        for u, p in enumerate(raw):
                            for z in raw[u+1:]:
                                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                                    raise RuntimeError(("product not independent", da["name"], db["name"], p, z))
                        cand = sorted(set(raw) - baseline)
                        losses = []
                        touched = set()
                        for x, y in cand:
                            L = set()
                            # Core blockers: support is automatically inside CxD.
                            for a in ring.NB[x] & B:
                                for b in ring.NB[y] & B:
                                    j = bidx.get((a, b))
                                    if j is None:
                                        raise RuntimeError(("missing core blocker", (x, y), (a, b)))
                                    L.add(j)
                            # Terminal periphery blockers.
                            for p in P:
                                if p[0] in ring.NB[x] and p[1] in ring.NB[y]:
                                    L.add(bidx[p])
                            losses.append(L)
                            touched.update(L)
                        delta, sel_idx, lost_idx = maximum_closure(losses, len(bvec))
                        selected = [cand[i] for i in sel_idx]
                        entry = {
                            "q": q,
                            "r": r,
                            "terminal_orientation": torient,
                            "left": da["name"],
                            "right": db["name"],
                            "left_k": len(da["C"]),
                            "right_k": len(db["C"]),
                            "raw_product": len(raw),
                            "external_candidates": len(cand),
                            "baseline_product_overlap": len(set(raw) & baseline),
                            "touched_blockers": len(touched),
                            "selected": len(selected),
                            "deleted": len(lost_idx),
                            "delta": delta,
                            "score": 134753 + delta,
                        }
                        results.append(entry)
                        rank = (delta, len(selected), -len(lost_idx), len(cand))
                        if best_full is None or rank > best_full[0]:
                            best_full = (rank, entry, baseline, bvec, selected, lost_idx)

    assert best_full is not None
    _rank, best, baseline, bvec, selected, lost_idx = best_full
    candidate_score = None
    if best["delta"] > 0:
        lost = {bvec[j] for j in lost_idx}
        cand = (baseline - lost) | set(selected)
        candidate_score = len(cand)
        if candidate_score != 134753 + best["delta"]:
            raise RuntimeError(("candidate size mismatch", candidate_score, best))
        # Independent full replay on the changed local object.
        sv = list(selected)
        for i, p in enumerate(sv):
            for z in sv[i+1:]:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                    raise RuntimeError(("selected-selected conflict", p, z))
            for z in baseline - lost:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:
                    raise RuntimeError(("selected-retained conflict", p, z))
        def enc(p):
            return "".join(str(d) for d in (ring.decode(p[0]) + ring.decode(p[1])))
        pts = sorted(enc(p) for p in cand)
        if len(pts) != len(set(pts)):
            raise RuntimeError("duplicate encoded points")
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")

    results.sort(key=lambda e: (e["delta"], e["selected"], -e["deleted"]), reverse=True)
    out = {
        "method": "exact-irreducible-rawdefect-product-maximum-closure",
        "defect_count": len(defects),
        "scenario_count": len(results),
        "best": best,
        "top20": results[:20],
        "candidate_materialized": best["delta"] > 0,
        "candidate_score": candidate_score,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
