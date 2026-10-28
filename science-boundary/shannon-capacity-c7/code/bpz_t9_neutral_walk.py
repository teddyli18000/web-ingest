#!/usr/bin/env python3
"""Neutral-walk construction search for an obstruction-free 367-set in C7^5.

Exact radius searches show the public one-hit BPZ t=9 near states are locally
rigid.  This search deliberately leaves a fixed-radius ball while preserving a
367-point independent set and at most one obstruction hit.  It mixes exact
legal 1-for-1 swaps with legal 2-for-2 jumps, rejects revisited states, and
checks every accepted state for zero obstruction hits.  A zero-hit state is
replayed and materialized as the 134770-point C7^10 BPZ construction.

This is a heuristic construction search, not an impossibility proof.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

import bpz_t9_aux_translation_fft as f
import bpz_t9_exchange_repair as er

U = 7 ** 5
TARGET = 367 * 367 + 9 * 9


def blockers(v, S, NB):
    return [q for q in NB[v] if q in S]


def init_counts(S, NB):
    cnt = [0] * U
    sm = [0] * U
    for p in S:
        for q in NB[p]:
            cnt[q] += 1
            sm[q] += p
    return cnt, sm


def apply_move(S, cnt, sm, NB, rem, add):
    for r in rem:
        if r not in S:
            raise RuntimeError("remove point absent")
        S.remove(r)
        for q in NB[r]:
            cnt[q] -= 1
            sm[q] -= r
    for a in add:
        if a in S or cnt[a] != 0:
            raise RuntimeError("addition is not free after removals")
        S.add(a)
        for q in NB[a]:
            cnt[q] += 1
            sm[q] += a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("family_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--case", type=int, required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--steps", type=int, default=2_000_000)
    ap.add_argument("--seconds", type=float, default=420.0)
    ap.add_argument("--two-swap-period", type=int, default=13)
    args = ap.parse_args()
    if not 0 <= args.case < 20:
        raise SystemExit("case must be 0..19")

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import Ring

    raw = json.loads((root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    X0 = set(map(int, raw["X"]))
    ring = Ring(5)
    digits = tuple(ring.decode(v) for v in range(U))
    nbmask = [sum(1 << z for z in ring.NB[v]) for v in range(U)]
    cases = er.one_hit_cases(I0, X0, ring, digits, nbmask, args.family_root)
    c = cases[args.case]
    S0 = set(c["S"])
    Dset = set(c["D"])
    if len(S0) != 367 or len(S0 & Dset) != 1 or not f.independent(S0, digits):
        raise RuntimeError("start-state drift")

    NB = ring.NB
    rng = random.Random((args.seed << 8) ^ args.case ^ 0xC7F1A5)
    zob = [rng.getrandbits(64) for _ in range(U)]
    # Decouple move randomness from Zobrist initialization.
    rng.seed((args.seed << 16) ^ args.case ^ 0x9E3779B9)

    S = set(S0)
    cnt, sm = init_counts(S, NB)
    h = 0
    for p in S:
        h ^= zob[p]
    visited = {h}
    accepted1 = accepted2 = rejected_seen = rejected_hits = 0
    attempts1 = attempts2 = restarts = 0
    max_radius = 0
    max_visited = 1
    start = time.monotonic()
    found = None

    def hit_count_after(rem, add):
        return len(S & Dset) - sum(r in Dset for r in rem) + sum(a in Dset for a in add)

    def accept(rem, add, kind):
        nonlocal h, accepted1, accepted2, rejected_seen, rejected_hits, max_radius, max_visited, found
        nh = h
        for r in rem: nh ^= zob[r]
        for a in add: nh ^= zob[a]
        if nh in visited:
            rejected_seen += 1
            return False
        hits = hit_count_after(rem, add)
        if hits > 1:
            rejected_hits += 1
            return False
        apply_move(S, cnt, sm, NB, rem, add)
        h = nh
        visited.add(h)
        max_visited = max(max_visited, len(visited))
        if kind == 1: accepted1 += 1
        else: accepted2 += 1
        if hits == 0:
            if S & Dset or len(S) != 367 or not f.independent(S, digits):
                raise RuntimeError("zero-hit state replay failed")
            found = set(S)
            return True
        if (accepted1 + accepted2) % 1000 == 0:
            rad = len(S0 - S)
            max_radius = max(max_radius, rad)
        return True

    for step in range(args.steps):
        if found is not None or time.monotonic() - start >= args.seconds:
            break
        moved = False
        use_two = args.two_swap_period > 0 and step % args.two_swap_period == 0
        if not use_two:
            # Rejection sampling from the 16807 ambient points is cheap because
            # one-blocker vertices are plentiful near these maximal sets.
            for _ in range(200):
                attempts1 += 1
                y = rng.randrange(U)
                if y in S or cnt[y] != 1:
                    continue
                r = sm[y]
                if r not in S:
                    bs = blockers(y, S, NB)
                    if len(bs) != 1:
                        continue
                    r = bs[0]
                if accept([r], [y], 1):
                    moved = True
                    break
        if not moved:
            # Random exact 2-for-2 jump. Supports are measured against the
            # current independent set; union <=2 is sufficient and necessary.
            for _ in range(400):
                attempts2 += 1
                a = rng.randrange(U)
                if a in S or not (1 <= cnt[a] <= 2):
                    continue
                A = blockers(a, S, NB)
                if len(A) != cnt[a]:
                    raise RuntimeError("count/support drift")
                b = rng.randrange(U)
                if b == a or b in S or not (1 <= cnt[b] <= 2) or b in NB[a]:
                    continue
                B = blockers(b, S, NB)
                R = set(A) | set(B)
                if len(R) > 2:
                    continue
                if len(R) < 2:
                    # Pad with an unrelated non-obstruction point so hit count
                    # cannot accidentally improve by deletion alone.
                    pads = [q for q in S if q not in R and q not in Dset]
                    if not pads:
                        continue
                    R.add(pads[rng.randrange(len(pads))])
                rem = sorted(R)
                if hit_count_after(rem, [a, b]) > 1:
                    continue
                # After removing the exact blocker union both additions must be free.
                apply_move(S, cnt, sm, NB, rem, [])
                free = cnt[a] == 0 and cnt[b] == 0 and b not in NB[a]
                apply_move(S, cnt, sm, NB, [], rem)
                if not free:
                    raise RuntimeError("two-swap blocker replay failed")
                if accept(rem, [a, b], 2):
                    moved = True
                    break
        if not moved:
            # The walk can become trapped by the visited-state filter. Restart
            # from the exact one-hit state with a different RNG phase.
            restarts += 1
            S = set(S0)
            cnt, sm = init_counts(S, NB)
            h = 0
            for p in S: h ^= zob[p]
            rng.random()

    elapsed = time.monotonic() - start
    max_radius = max(max_radius, len(S0 - S))
    status = {
        "method": "bpz-t9-neutral-one-two-swap-walk",
        "candidate": found is not None,
        "case_index": args.case,
        "seed": args.seed,
        "source_seed": c["seed"],
        "obstruction_index": c["obstruction_index"],
        "start_bad": c["bad"],
        "steps_requested": args.steps,
        "seconds_requested": args.seconds,
        "elapsed_seconds": elapsed,
        "accepted_one_swaps": accepted1,
        "accepted_two_swaps": accepted2,
        "one_swap_attempts": attempts1,
        "two_swap_attempts": attempts2,
        "rejected_visited": rejected_seen,
        "rejected_hits": rejected_hits,
        "restarts": restarts,
        "visited_states": len(visited),
        "max_radius_from_start": max_radius,
        "final_hits": len(S & Dset),
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    if found is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    Ibits, pairs, orient, PH, PV = c["witness"]
    points, xp = f.build(Ibits, sum(1 << q for q in found), pairs, PH, PV, ring)
    if len(points) != TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    status.update({
        "score": len(points),
        "private_pairs": [list(q) for q in pairs],
        "orientation": list(orient),
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
