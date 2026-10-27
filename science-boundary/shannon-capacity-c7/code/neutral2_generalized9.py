#!/usr/bin/env python3
import argparse
import json
from itertools import combinations
from pathlib import Path

import generalized9 as g

TARGET = 134_770
MODS = {267: 15083, 294: 16388}
PORT_CENTERS = [11283, 15083, 13108, 15953, 14328, 16388, 1321, 8601, 3660]


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

    r_index = {v: i for i, v in enumerate(r)}
    missing = [v for v in PORT_CENTERS if v not in r_index]
    if missing:
        raise RuntimeError(f"neutral2 port centers missing from state: {missing}")
    k9 = tuple(sorted(r_index[v] for v in PORT_CENTERS))
    if len(set(k9)) != 9:
        raise RuntimeError("neutral2 port centers are not distinct")

    supports, support_sizes = g.support_masks(r, digits)
    hist = {}
    for s in support_sizes:
        hist[s] = hist.get(s, 0) + 1

    print(
        "neutral2 generalized SAT",
        json.dumps({"deleted_indices": k9, "deleted_centers": PORT_CENTERS}, sort_keys=True),
        flush=True,
    )
    model, stats = g.solve_structure(k9, 9, r, xset, digits, supports, want_model=True)
    if model is None:
        status = {
            "candidate": False,
            "score": 134753,
            "method": "neutral2-generalized-safe-endpoint-sat",
            "deleted_r_indices": list(k9),
            "deleted_r_centers": PORT_CENTERS,
            "neutral2_modifications": MODS,
            "support_histogram": hist,
            "sat_stats": stats,
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    candidate = g.build_candidate(k9, model, r, xset, digits)
    if len(candidate) != TARGET:
        raise RuntimeError(f"wrong candidate score {len(candidate)} != {TARGET}")

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
        "method": "neutral2-generalized-safe-endpoint-sat",
        "deleted_r_indices": list(k9),
        "deleted_r_centers": PORT_CENTERS,
        "neutral2_modifications": MODS,
        "removed_vs_baseline": removed,
        "added_vs_baseline": added,
        "support_histogram": hist,
        "sat_stats": stats,
    }
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
