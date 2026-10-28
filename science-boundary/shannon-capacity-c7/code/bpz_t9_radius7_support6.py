#!/usr/bin/env python3
"""Exact radius-7 repair sweep for owner septets containing a size-6/7 support.

For the canonical obstruction-free 366-set L, every allowed outside vertex v
has an owner support S(v) subset L.  A 7->8 repair with owner union T can use
only vertices with S(v) subset T.  This program exhausts every |T|=7 that
contains at least one realized support of size 6 or 7 and exactly tests whether
the corresponding candidate pool contains eight pairwise nonconfusable points.

This is a strict subset of the full radius-7 decision, but it is exhaustive for
the stated support-6/7 stratum and is deliberately solver-independent.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_obstruction_mis as mis
import bpz_t9_kamis as bridge

RADIUS = 7
NEED = 8


def pool_for(mask: int, groups: dict[int, list[int]]) -> list[int]:
    out = []
    sub = mask
    while sub:
        g = groups.get(sub)
        if g:
            out.extend(g)
        sub = (sub - 1) & mask
    return out


def find_independent(pool: list[int], digits, need: int = NEED):
    n = len(pool)
    if n < need:
        return None
    comp = [0] * n
    for i in range(n):
        for j in range(i + 1, n):
            if not mis.conflict(pool[i], pool[j], digits):
                comp[i] |= 1 << j
                comp[j] |= 1 << i

    # Reorder by descending compatibility degree. This is only a search-order
    # choice; the recursive branching below remains exhaustive.
    order = sorted(range(n), key=lambda i: comp[i].bit_count(), reverse=True)
    remap = {old: new for new, old in enumerate(order)}
    p2 = [pool[i] for i in order]
    c2 = [0] * n
    for ni, oi in enumerate(order):
        z = comp[oi]
        while z:
            b = z & -z
            oj = b.bit_length() - 1
            c2[ni] |= 1 << remap[oj]
            z ^= b

    def dfs(cands: int, chosen: list[int]):
        want = need - len(chosen)
        if want == 0:
            return chosen
        if cands.bit_count() < want:
            return None
        # Exhaustive include-branch over candidates; after trying v, remove it
        # from the outer candidate set to cover the exclude branch implicitly.
        while cands:
            if cands.bit_count() < want:
                return None
            b = cands & -cands
            v = b.bit_length() - 1
            cands ^= b
            r = dfs(cands & c2[v], chosen + [v])
            if r is not None:
                return r
        return None

    ans = dfs((1 << n) - 1, [])
    return None if ans is None else [p2[i] for i in ans]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    I, published_X, pairs, PH, PV, ring, digits, obstruction, lower = bridge.reconstruct(args.tan_root)
    if len(lower) != 366 or len(obstruction) != 1098:
        raise RuntimeError("instance drift")
    lower = list(lower)
    lower_set = set(lower)

    groups: dict[int, list[int]] = {}
    support_hist = {}
    for v in range(mis.U):
        if v in obstruction or v in lower_set:
            continue
        mask = 0
        for i, u in enumerate(lower):
            if mis.conflict(v, u, digits):
                mask |= 1 << i
        bc = mask.bit_count()
        if 1 <= bc <= RADIUS:
            groups.setdefault(mask, []).append(v)
            support_hist[bc] = support_hist.get(bc, 0) + 1

    s6 = [m for m in groups if m.bit_count() == 6]
    s7 = [m for m in groups if m.bit_count() == 7]
    seen = set()
    scanned = eligible = 0
    max_pool = 0
    best_pool = 0

    def test(T: int):
        nonlocal scanned, eligible, max_pool, best_pool
        if T in seen:
            return None
        seen.add(T)
        scanned += 1
        pool = pool_for(T, groups)
        max_pool = max(max_pool, len(pool))
        if len(pool) < NEED:
            return None
        eligible += 1
        add = find_independent(pool, digits)
        if add is not None:
            best_pool = max(best_pool, len(pool))
            return add
        return None

    # Every realized 7-support fixes its owner septet exactly.
    winner = None
    winT = None
    for T in s7:
        add = test(T)
        if add is not None:
            winner, winT = add, T
            break

    # Every owner septet containing a realized 6-support is obtained by adding
    # one of the other 360 owner indices. Enumerating all such extensions is
    # exact for this stratum; ``seen`` deduplicates septets reached many ways.
    if winner is None:
        all_owner_mask = (1 << len(lower)) - 1
        for S in s6:
            outside = all_owner_mask ^ S
            while outside:
                b = outside & -outside
                outside ^= b
                T = S | b
                add = test(T)
                if add is not None:
                    winner, winT = add, T
                    break
            if winner is not None:
                break

    setup = {
        "starting_size": len(lower),
        "obstruction_size": len(obstruction),
        "support_histogram": {str(k): v for k, v in sorted(support_hist.items())},
        "support_groups": {str(k): sum(m.bit_count() == k for m in groups) for k in range(1, 8)},
        "size6_support_groups": len(s6),
        "size7_support_groups": len(s7),
        "unique_owner_septets_scanned": scanned,
        "eligible_pools_at_least_8": eligible,
        "max_candidate_pool": max_pool,
    }

    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        status = {
            "candidate": False,
            "exact_for_stratum": True,
            "method": "bpz-t9-radius7-support6-exact",
            "score": 134753,
            "setup": setup,
            "conclusion": "No 7->8 repair whose owner union contains a realized size-6 or size-7 support.",
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    owners = [i for i in range(len(lower)) if (winT >> i) & 1]
    actual_owners = sorted({i for v in winner for i, u in enumerate(lower) if mis.conflict(v, u, digits)})
    if not set(actual_owners) <= set(owners) or len(actual_owners) > RADIUS:
        raise RuntimeError("owner replay failed")
    owner_set = set(actual_owners)
    new = [v for i, v in enumerate(lower) if i not in owner_set] + winner
    if len(new) < 367 or set(new) & obstruction or not mis.independent(new, digits):
        raise RuntimeError(f"repair replay failed size={len(new)} owners={len(actual_owners)}")
    X = new[:367]
    points, xp = mis.build(I, X, pairs, PH, PV, ring)
    if len(points) != mis.TARGET:
        raise RuntimeError(f"10D score drift {len(points)}")

    status = {
        "candidate": True,
        "exact_for_stratum": True,
        "method": "bpz-t9-radius7-support6-exact",
        "score": len(points),
        "owner_septet": owners,
        "actual_removed_owners": actual_owners,
        "added_auxiliary": winner,
        "raw_repaired_auxiliary_size": len(new),
        "setup": setup,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
