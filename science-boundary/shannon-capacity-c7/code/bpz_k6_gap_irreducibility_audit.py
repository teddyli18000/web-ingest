#!/usr/bin/env python3
"""Audit k=6 clique-cover-gap cases for genuine irreducible raw defects.

Input is the `k6.json` emitted by `bpz_support_clique_cover_gap_census.py`.
For each reported cover-gap owner set C with candidate pool P, recompute the
maximum independent-set size in P and, among all maximum independent sets,
minimize |Y intersect C|.

If the minimum intersection is zero, C->Y is an irreducible 6->7 support
defect.  If it is one, one deleted owner is immediately re-added and cancels,
so the apparent k=6 defect reduces to a smaller support defect.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def conflict5(a: int, b: int) -> bool:
    if a == b:
        return True
    for _ in range(5):
        x, y = a % 7, b % 7
        a //= 7
        b //= 7
        if (x - y) % 7 not in (0, 1, 6):
            return False
    return True


def best_independent(pool: list[int], owners: set[int]):
    n = len(pool)
    compat = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if not conflict5(pool[i], pool[j]):
                compat[i] |= 1 << j
                compat[j] |= 1 << i

    best_size = -1
    best_intersection = 10**9
    best_witness: list[int] = []

    def rec(mask: int, chosen: list[int], owner_hits: int):
        nonlocal best_size, best_intersection, best_witness
        size = len(chosen)
        if size + mask.bit_count() < best_size:
            return
        if size + mask.bit_count() == best_size and owner_hits >= best_intersection:
            return
        if not mask:
            if size > best_size or (size == best_size and owner_hits < best_intersection):
                best_size = size
                best_intersection = owner_hits
                best_witness = [pool[i] for i in chosen]
            return

        # Branch on a high-conflict vertex within the current candidate set.
        mm = mask
        pick = (mm & -mm).bit_length() - 1
        worst = -1
        while mm:
            bit = mm & -mm
            i = bit.bit_length() - 1
            noncompat = (mask & ~(compat[i] | (1 << i))).bit_count()
            if noncompat > worst:
                worst = noncompat
                pick = i
            mm -= bit

        # Include first: useful because alpha=7 witnesses are small and sparse.
        rec(mask & compat[pick], chosen + [pick], owner_hits + (pool[pick] in owners))
        rec(mask & ~(1 << pick), chosen, owner_hits)

    rec((1 << n) - 1, [], 0)
    return best_size, best_intersection, sorted(best_witness)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("k6_json", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    data = json.loads(args.k6_json.read_text())
    cases = data.get("cover_gap_cases", [])
    if data.get("k") != 6 or len(cases) != data.get("cover_gap_count"):
        raise RuntimeError("unexpected census schema/count")

    audited = []
    hist = Counter()
    for case in cases:
        owners = set(map(int, case["owners"]))
        pool = list(map(int, case["pool"]))
        alpha, inter, witness = best_independent(pool, owners)
        if alpha != int(case["alpha"]):
            raise RuntimeError(("alpha mismatch", sorted(owners), alpha, case["alpha"]))
        hist[inter] += 1
        audited.append({
            "owners": sorted(owners),
            "pool_size": len(pool),
            "alpha": alpha,
            "min_owner_intersection_at_alpha": inter,
            "irreducible": inter == 0,
            "witness": witness,
        })

    irreducible = [x for x in audited if x["irreducible"]]
    out = {
        "method": "exact-k6-gap-max-independent-min-owner-intersection",
        "input_gap_cases": len(cases),
        "intersection_histogram": {str(k): v for k, v in sorted(hist.items())},
        "irreducible_count": len(irreducible),
        "irreducible": irreducible,
        "cases": audited,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "cases"}, sort_keys=True))


if __name__ == "__main__":
    main()
