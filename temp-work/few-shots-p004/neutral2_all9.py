#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from pathlib import Path

import generalized9 as g

TARGET = 134_770
MODS = {267: 15083, 294: 16388}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline_certificate", type=Path)
    ap.add_argument("output_certificate", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    original = g.load_r(args.r367)
    xset = g.make_x(original, digits)
    r = list(original)
    for i, v in MODS.items():
        r[i] = v

    if len(set(r)) != g.R_SIZE:
        raise RuntimeError("neutral2 state has duplicates")
    for i, j in combinations(range(g.R_SIZE), 2):
        if g.conflict(r[i], r[j], digits):
            raise RuntimeError(f"neutral2 state is not independent: {i},{j}")

    supports, support_sizes = g.support_masks(r, digits)
    rset = set(r)
    owner_private = {}
    for v, sm in enumerate(supports):
        if v in rset or sm.bit_count() != 1:
            continue
        owner = (sm & -sm).bit_length() - 1
        owner_private.setdefault(owner, []).append(v)
    owners = sorted(owner_private)
    if len(owners) < 9:
        raise RuntimeError(f"only {len(owners)} private centers")

    combos = []
    for k9 in combinations(owners, 9):
        kmask = sum(1 << i for i in k9)
        safe_count = sum(1 for sm in supports if sm & ~kmask == 0)
        combos.append((safe_count, k9))
    combos.sort(reverse=True)

    tested = 0
    best = None
    for safe_count, k9 in combos:
        tested += 1
        print(
            "try",
            json.dumps({"test": tested, "safe": safe_count, "k9": k9}, sort_keys=True),
            flush=True,
        )
        model, stats = g.solve_structure(k9, 9, r, xset, digits, supports, want_model=True)
        record = {"safe_count": safe_count, "k9": list(k9), "stats": stats}
        if best is None or stats["active_x"] < best["stats"]["active_x"]:
            best = record
        if model is None:
            continue

        candidate = g.build_candidate(k9, model, r, xset, digits)
        if len(candidate) != TARGET:
            raise RuntimeError(f"wrong candidate score {len(candidate)}")
        baseline = json.loads(args.baseline_certificate.read_text(encoding="utf-8"))["points"]
        baseline_ids = {int(p, 7) for p in baseline}
        removed = len(baseline_ids - candidate)
        added = len(candidate - baseline_ids)
        args.output_certificate.parent.mkdir(parents=True, exist_ok=True)
        args.output_certificate.write_text(
            json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        status = {
            "candidate": True,
            "score": len(candidate),
            "method": "neutral2-all-nine-center-generalized-sat",
            "private_center_count": len(owners),
            "private_centers": [{"index": i, "word": r[i], "alternatives": owner_private[i]} for i in owners],
            "tested": tested,
            "selected_indices": list(k9),
            "selected_centers": [r[i] for i in k9],
            "neutral2_modifications": MODS,
            "removed_vs_baseline": removed,
            "added_vs_baseline": added,
            "sat_stats": stats,
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
        return

    status = {
        "candidate": False,
        "score": 134753,
        "method": "neutral2-all-nine-center-generalized-sat",
        "private_center_count": len(owners),
        "private_centers": [{"index": i, "word": r[i], "alternatives": owner_private[i]} for i in owners],
        "tested": tested,
        "best_unsat": best,
        "neutral2_modifications": MODS,
    }
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("NONE", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
