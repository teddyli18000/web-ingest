#!/usr/bin/env python3
"""Exact 10-for-10 t=9 repair sweep for owner nonets containing support 8/9.

Start from the canonical obstruction-free 366-set L.  A successful radius-10
repair selects ten pairwise nonconfusable outside vertices whose union of
blockers against L has size at most nine.  For every nine-owner set T that
contains a realized support of size eight or nine, this program builds the
*entire* candidate pool {v : nonempty S(v) subset T} and exhaustively asks for
an independent 10-set.  Thus all shards together are exact for this stated
high-support stratum.

Sharding is by T modulo --shard-count.  Generation may reach the same T from
several size-8 supports; a per-shard seen set deduplicates it without changing
coverage.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpz_t9_obstruction_mis as mis
import bpz_t9_kamis as bridge
from bpz_t9_radius7_support6 import find_independent, pool_for

RADIUS = 9
NEED = 10
BASELINE = 134753


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--shard-index", type=int, default=0)
    ap.add_argument("--shard-count", type=int, default=1)
    args = ap.parse_args()
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise SystemExit("bad shard")

    I, published_X, pairs, PH, PV, ring, digits, obstruction, lower = bridge.reconstruct(args.tan_root)
    if len(lower) != 366 or len(obstruction) != 1098:
        raise RuntimeError("instance drift")
    lower = list(lower)
    lower_set = set(lower)

    groups: dict[int, list[int]] = {}
    support_hist: dict[int, int] = {}
    free = []
    for v in range(mis.U):
        if v in obstruction or v in lower_set:
            continue
        mask = 0
        for i, u in enumerate(lower):
            if mis.conflict(v, u, digits):
                mask |= 1 << i
        bc = mask.bit_count()
        support_hist[bc] = support_hist.get(bc, 0) + 1
        if bc == 0:
            free.append(v)
        elif bc <= RADIUS:
            groups.setdefault(mask, []).append(v)

    # A support-zero vertex is already a stronger/easier witness: L + v has 367.
    if free:
        X = lower + [free[0]]
        if set(X) & obstruction or len(X) != 367 or not mis.independent(X, digits):
            raise RuntimeError("support-zero replay failed")
        points, xp = mis.build(I, X, pairs, PH, PV, ring)
        if len(points) != mis.TARGET:
            raise RuntimeError(f"10D score drift {len(points)}")
        status = {
            "candidate": True,
            "exact_for_stratum": True,
            "method": "bpz-t9-radius10-support8-exact",
            "score": len(points),
            "direct_free_vertex": free[0],
            "shard_index": args.shard_index,
            "shard_count": args.shard_count,
            "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
        args.status.parent.mkdir(parents=True, exist_ok=True)
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
        return

    s8 = [m for m in groups if m.bit_count() == 8]
    s9 = [m for m in groups if m.bit_count() == 9]
    all_owner_mask = (1 << len(lower)) - 1

    seen: set[int] = set()
    generated = assigned = scanned = eligible = 0
    max_pool = 0
    winner = None
    winT = None

    def test(T: int):
        nonlocal generated, assigned, scanned, eligible, max_pool, winner, winT
        generated += 1
        if T in seen:
            return False
        seen.add(T)
        if T % args.shard_count != args.shard_index:
            return False
        assigned += 1
        pool = pool_for(T, groups)
        scanned += 1
        max_pool = max(max_pool, len(pool))
        if len(pool) < NEED:
            return False
        eligible += 1
        add = find_independent(pool, digits, NEED)
        if add is not None:
            winner, winT = add, T
            return True
        return False

    # A realized support-9 fixes its owner nonet exactly.
    for T in s9:
        if test(T):
            break

    # Every owner nonet containing a realized support-8 is S plus one owner.
    if winner is None:
        for S in s8:
            outside = all_owner_mask ^ S
            while outside:
                b = outside & -outside
                outside ^= b
                if test(S | b):
                    break
            if winner is not None:
                break

    setup = {
        "starting_size": len(lower),
        "obstruction_size": len(obstruction),
        "support_histogram": {str(k): v for k, v in sorted(support_hist.items())},
        "support_groups": {str(k): sum(m.bit_count() == k for m in groups) for k in range(1, RADIUS + 1)},
        "size8_support_groups": len(s8),
        "size9_support_groups": len(s9),
        "generated_nonets_with_duplicates": generated,
        "unique_nonets_seen_before_shard_filter": len(seen),
        "assigned_nonets": assigned,
        "scanned_nonets": scanned,
        "eligible_pools_at_least_10": eligible,
        "max_candidate_pool": max_pool,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
    }

    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        status = {
            "candidate": False,
            "exact_for_shard": True,
            "exact_for_stratum_when_all_shards_complete": True,
            "method": "bpz-t9-radius10-support8-exact",
            "score": BASELINE,
            "setup": setup,
            "conclusion": "No 10-point repair in this shard whose owner nonet contains a realized size-8 or size-9 support.",
        }
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    owners = [i for i in range(len(lower)) if (winT >> i) & 1]
    actual_owners = sorted({i for v in winner for i, u in enumerate(lower) if mis.conflict(v, u, digits)})
    if not set(actual_owners) <= set(owners) or len(actual_owners) > RADIUS:
        raise RuntimeError("owner replay failed")
    owner_set = set(actual_owners)
    repaired = [v for i, v in enumerate(lower) if i not in owner_set] + winner
    if len(repaired) < 367 or set(repaired) & obstruction or not mis.independent(repaired, digits):
        raise RuntimeError(f"repair replay failed size={len(repaired)} owners={len(actual_owners)}")

    X = repaired[:367]
    points, xp = mis.build(I, X, pairs, PH, PV, ring)
    if len(points) != mis.TARGET:
        raise RuntimeError(f"10D score drift {len(points)}")

    status = {
        "candidate": True,
        "exact_for_shard": True,
        "method": "bpz-t9-radius10-support8-exact",
        "score": len(points),
        "owner_nonet": owners,
        "actual_removed_owners": actual_owners,
        "added_auxiliary": winner,
        "raw_repaired_auxiliary_size": len(repaired),
        "setup": setup,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
