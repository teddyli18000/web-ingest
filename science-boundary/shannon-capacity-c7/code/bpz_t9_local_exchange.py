#!/usr/bin/env python3
"""Exact local-exchange search around the canonical BPZ t=9 366-set.

The strongest t=9 obstruction D has |D|=1098 and the published 367-point
auxiliary X meets D only at 10665.  Removing that point gives an allowed
366-point independent set L.  For every allowed v outside L, define its owner
support S(v) as the L-points confusable with v.  Replacing k old points can only
use candidates whose supports are contained in those k owners.

This script exhausts improving exchanges through 5->6 without enumerating all
owner k-subsets.  Relevant owner sets are generated from unions of actual
candidate supports.  For k=5, the only owner sets whose minimal support cover
can require four support groups (rather than <=3) are a common-center star of
size-2 supports, optionally with one or two singleton supports; those cases are
added explicitly.  The published instance has only two singleton-support
groups.
"""

import argparse
import json
from collections import Counter, defaultdict
from itertools import combinations, product
from pathlib import Path

Q = 7
D = 5
U = Q ** D
BAD = 10665
PRIVATE_PAIRS = (
    (1553, 15910), (3716, 6110), (8888, 6494),
    (10708, 13158), (13065, 13358), (14027, 13677),
    (14329, 12277), (15075, 14733), (15384, 15685),
)
ORIENTATION = (0, 0, 1, 1, 0, 1, 1, 0, 0)


def dec(v):
    out = []
    for _ in range(D):
        out.append(v % Q)
        v //= Q
    return tuple(out)


def enc(w):
    return sum(x * (Q ** i) for i, x in enumerate(w))


def conflict(a, b, digits):
    if a == b:
        return True
    return all((x - y) % Q in (0, 1, Q - 1)
               for x, y in zip(digits[a], digits[b]))


def neighborhood(v, digits):
    a = digits[v]
    return {
        enc(tuple((a[i] + d[i]) % Q for i in range(D)))
        for d in product((-1, 0, 1), repeat=D)
    }


def independent(vals, digits):
    return all(not conflict(a, b, digits) for a, b in combinations(vals, 2))


def find_independent(pool, need, digits):
    pool = list(pool)
    chosen = []

    def dfs(start):
        if len(chosen) == need:
            return tuple(chosen)
        if len(pool) - start < need - len(chosen):
            return None
        for i in range(start, len(pool)):
            v = pool[i]
            if all(not conflict(v, u, digits) for u in chosen):
                chosen.append(v)
                ans = dfs(i + 1)
                if ans is not None:
                    return ans
                chosen.pop()
        return None

    return dfs(0)


def pool_for_mask(T, groups):
    out = []
    sub = T
    while sub:
        out.extend(groups.get(sub, ()))
        sub = (sub - 1) & T
    return list(dict.fromkeys(out))


def search_masks(owner_masks, need, groups, digits):
    eligible = 0
    max_pool = 0
    for T in owner_masks:
        pool = pool_for_mask(T, groups)
        max_pool = max(max_pool, len(pool))
        if len(pool) < need:
            continue
        eligible += 1
        sol = find_independent(pool, need, digits)
        if sol is not None:
            return {"found": True, "owner_mask": T, "add": list(sol),
                    "eligible_pools": eligible, "max_candidate_pool": max_pool}
    return {"found": False, "eligible_pools": eligible,
            "max_candidate_pool": max_pool}


def owner_sets_through_three_supports(k, masks):
    exact = {m for m in masks if m.bit_count() == k}
    small_pair = set()
    for i, a in enumerate(masks):
        for b in masks[i + 1:]:
            u = a | b
            bc = u.bit_count()
            if bc == k:
                exact.add(u)
            elif bc < k:
                small_pair.add(u)
    if k <= 4:
        for u in small_pair:
            for m in masks:
                z = u | m
                if z.bit_count() == k:
                    exact.add(z)
    return exact, small_pair


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base_c7", type=Path,
                    help="Pinned Tan/BPZ data/base_c7.json")
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    raw = json.loads(args.base_c7.read_text())
    X = list(map(int, raw["X"]))
    if len(X) != 367 or len(set(X)) != 367:
        raise RuntimeError("published X drift")

    digits = tuple(dec(v) for v in range(U))
    PH = [q if s else a for (a, q), s in zip(PRIVATE_PAIRS, ORIENTATION)]
    PV = [a if s else q for (a, q), s in zip(PRIVATE_PAIRS, ORIENTATION)]
    NH = set().union(*(neighborhood(v, digits) for v in PH))
    NV = set().union(*(neighborhood(v, digits) for v in PV))
    obstruction = NH & NV
    hits = sorted(set(X) & obstruction)
    if len(obstruction) != 1098 or hits != [BAD]:
        raise RuntimeError(f"obstruction drift {len(obstruction)} {hits}")

    lower = [v for v in X if v != BAD]
    lower_set = set(lower)
    if len(lower) != 366 or not independent(lower, digits):
        raise RuntimeError("lower-set drift")
    allowed = [v for v in range(U) if v not in obstruction]

    support = {}
    histogram = Counter()
    for v in allowed:
        if v in lower_set:
            continue
        s = tuple(i for i, u in enumerate(lower) if conflict(v, u, digits))
        support[v] = s
        histogram[len(s)] += 1

    direct = [v for v, s in support.items() if not s]
    if direct:
        raise RuntimeError(f"direct 367th point unexpectedly found: {direct[0]}")

    groups_by_k = {}
    for k in range(1, 6):
        g = defaultdict(list)
        for v, s in support.items():
            if 1 <= len(s) <= k:
                mask = sum(1 << i for i in s)
                g[mask].append(v)
        groups_by_k[k] = g

    result = {
        "obstruction_size": len(obstruction),
        "published_hits": hits,
        "allowed_vertices": len(allowed),
        "starting_size": len(lower),
        "support_histogram": {str(k): v for k, v in sorted(histogram.items())},
        "support_group_counts": {
            str(k): sum(1 for s in set(tuple(x) for x in support.values()) if len(s) == k)
            for k in range(1, 6)
        },
        "search": {"direct_add": {"found": False}},
    }

    # k=1..4: every relevant owner set is a union of <=3 actual support groups
    # here.  For k=1/2 the loops naturally degenerate to smaller unions.
    for k in range(1, 5):
        g = groups_by_k[k]
        masks = list(g)
        owners, _ = owner_sets_through_three_supports(k, masks)
        rec = search_masks(owners, k + 1, g, digits)
        rec["relevant_owner_sets"] = len(owners)
        result["search"][f"remove_{k}_add_{k+1}"] = rec
        if rec["found"]:
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(json.dumps(result, sort_keys=True))
            return

    # k=5.  First cover all owner quints that are unions of one/two supports.
    g = groups_by_k[5]
    masks = list(g)
    pair_quints, small_pair = owner_sets_through_three_supports(5, masks)
    base_rec = search_masks(pair_quints, 6, g, digits)
    if base_rec["found"]:
        result["search"]["remove_5_add_6"] = base_rec
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))
        return

    # Add all potentially useful three-support unions not already covered.
    extra = set()
    for u in small_pair:
        bc = u.bit_count()
        if bc == 4:
            for c in range(len(lower)):
                bit = 1 << c
                if u & bit:
                    continue
                T = u | bit
                if T in pair_quints:
                    continue
                if len(pool_for_mask(T, g)) >= 6:
                    extra.add(T)
        else:
            for m in masks:
                T = u | m
                if T.bit_count() == 5 and T not in pair_quints:
                    if len(pool_for_mask(T, g)) >= 6:
                        extra.add(T)
    extra_rec = search_masks(extra, 6, g, digits)
    if extra_rec["found"]:
        result["search"]["remove_5_add_6"] = extra_rec
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, sort_keys=True))
        return

    # A minimal four-support cover of a 5-owner universe must give each of the
    # four supports a private owner.  Hence each support is either a singleton
    # or an edge from its private owner to the fifth common owner.  Since this
    # instance has only two singleton support groups, enumerate these stars.
    singles = [m.bit_length() - 1 for m in masks if m.bit_count() == 1]
    pairs = [m for m in masks if m.bit_count() == 2]
    inc = defaultdict(set)
    for m in pairs:
        a = (m & -m).bit_length() - 1
        b = (m ^ (1 << a)).bit_length() - 1
        inc[a].add(b)
        inc[b].add(a)
    minimal4 = set()
    for center, leaves in inc.items():
        leaves = sorted(leaves)
        for ls in combinations(leaves, 4):
            T = 1 << center
            for x in ls: T |= 1 << x
            minimal4.add(T)
    for s in singles:
        for center, leaves0 in inc.items():
            if center == s: continue
            leaves = sorted(x for x in leaves0 if x != s)
            for ls in combinations(leaves, 3):
                T = (1 << s) | (1 << center)
                for x in ls: T |= 1 << x
                if T.bit_count() == 5: minimal4.add(T)
    for sa, sb in combinations(singles, 2):
        for center, leaves0 in inc.items():
            if center in (sa, sb): continue
            leaves = sorted(x for x in leaves0 if x not in (sa, sb))
            for ls in combinations(leaves, 2):
                T = (1 << sa) | (1 << sb) | (1 << center)
                for x in ls: T |= 1 << x
                if T.bit_count() == 5: minimal4.add(T)

    minimal4 = {T for T in minimal4 if T not in pair_quints and T not in extra
                and len(pool_for_mask(T, g)) >= 6}
    min4_rec = search_masks(minimal4, 6, g, digits)
    rec5 = {
        "found": False,
        "pair_union_owner_quints": len(pair_quints),
        "pair_union_eligible_pools": base_rec["eligible_pools"],
        "additional_three_support_union_eligible_quints": len(extra),
        "additional_minimal_four_support_cover_eligible_quints": len(minimal4),
        "max_candidate_pool": max(base_rec["max_candidate_pool"],
                                  extra_rec["max_candidate_pool"],
                                  min4_rec["max_candidate_pool"]),
    }
    result["search"]["remove_5_add_6"] = rec5
    result["conclusion"] = (
        "No improving local exchange through remove-5/add-6 from the canonical "
        "obstruction-free 366-set."
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
