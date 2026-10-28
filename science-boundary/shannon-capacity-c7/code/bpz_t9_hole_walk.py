#!/usr/bin/env python3
"""Global obstruction-free 366-set walk for the BPZ t=9 construction.

Each best translated public seed has exactly one point in the obstruction D.
Delete that mandatory bad point first.  This leaves an independent 366-set
T subset C7^5 \ D.  We then walk far through the reconfiguration graph of
366-point independent sets, using exact legal 1-for-1 moves and occasional
2-for-2 jumps.  After every accepted move we maintain the set of ambient
vertices outside D with zero blockers.  Any such free vertex extends T to an
obstruction-free 367-set, which immediately materializes the nominal 134770
C7^10 BPZ construction.

This is a heuristic construction search, not an impossibility proof.  Unlike a
fixed-radius repair, the accepted walk can move arbitrarily far from the start.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("family_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--case", type=int, required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--steps", type=int, default=4_000_000)
    ap.add_argument("--seconds", type=float, default=420.0)
    ap.add_argument("--two-swap-period", type=int, default=17)
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
    D = set(c["D"])
    bads = S0 & D
    if len(S0) != 367 or len(bads) != 1 or not f.independent(S0, digits):
        raise RuntimeError("one-hit start-state drift")
    bad = next(iter(bads))

    T0 = S0 - {bad}
    if len(T0) != 366 or T0 & D or not f.independent(T0, digits):
        raise RuntimeError("366-set start drift")

    NB = ring.NB
    rng = random.Random((args.seed << 16) ^ (args.case << 4) ^ 0xC7A11E)
    zob = [rng.getrandbits(64) for _ in range(U)]
    rng.seed((args.seed << 24) ^ args.case ^ 0x9E3779B97F4A7C15)

    S = set(T0)
    cnt, sm = init_counts(S, NB)
    free = {v for v in range(U) if v not in S and v not in D and cnt[v] == 0}
    if free:
        raise RuntimeError(f"unexpected free start vertices: {len(free)}")

    h = 0
    for p in S:
        h ^= zob[p]
    visited = {h}
    accepted1 = accepted2 = 0
    attempts1 = attempts2 = 0
    rejected_seen = 0
    restarts = 0
    max_radius = 0
    max_one_blockers = 0
    start = time.monotonic()
    found = None

    def refresh(touched):
        for v in touched:
            if v not in S and v not in D and cnt[v] == 0:
                free.add(v)
            else:
                free.discard(v)

    def mutate(rem, add):
        touched = set()
        for r in rem:
            if r not in S:
                raise RuntimeError("remove point absent")
            S.remove(r)
            touched.add(r)
            for q in NB[r]:
                cnt[q] -= 1
                sm[q] -= r
                touched.add(q)
        for a in add:
            if a in S or a in D or cnt[a] != 0:
                raise RuntimeError("addition is not legal")
            S.add(a)
            touched.add(a)
            for q in NB[a]:
                cnt[q] += 1
                sm[q] += a
                touched.add(q)
        refresh(touched)

    def accept(rem, add, kind):
        nonlocal h, accepted1, accepted2, rejected_seen, max_radius, found
        nh = h
        for r in rem:
            nh ^= zob[r]
        for a in add:
            nh ^= zob[a]
        if nh in visited:
            rejected_seen += 1
            return False
        mutate(rem, add)
        if len(S) != 366 or S & D:
            raise RuntimeError("walk left obstruction-free 366-set space")
        h = nh
        visited.add(h)
        if kind == 1:
            accepted1 += 1
        else:
            accepted2 += 1
        if (accepted1 + accepted2) % 250 == 0:
            max_radius = max(max_radius, len(T0 - S))
        if free:
            y = next(iter(free))
            W = set(S)
            W.add(y)
            if len(W) != 367 or W & D or not f.independent(W, digits):
                raise RuntimeError("free extension replay failed")
            found = W
        return True

    for step in range(args.steps):
        if found is not None or time.monotonic() - start >= args.seconds:
            break
        moved = False
        use_two = args.two_swap_period > 0 and step % args.two_swap_period == 0

        if not use_two:
            for _ in range(180):
                attempts1 += 1
                y = rng.randrange(U)
                if y in S or y in D or cnt[y] != 1:
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
            for _ in range(500):
                attempts2 += 1
                a = rng.randrange(U)
                if a in S or a in D or not (1 <= cnt[a] <= 2):
                    continue
                A = blockers(a, S, NB)
                b = rng.randrange(U)
                if b == a or b in S or b in D or not (1 <= cnt[b] <= 2) or b in NB[a]:
                    continue
                B = blockers(b, S, NB)
                R = set(A) | set(B)
                if len(R) > 2:
                    continue
                if len(R) < 2:
                    for _pad in range(32):
                        q = rng.choice(tuple(S))
                        if q not in R:
                            R.add(q)
                            break
                if len(R) != 2:
                    continue
                rem = sorted(R)
                mutate(rem, [])
                ok = cnt[a] == 0 and cnt[b] == 0 and b not in NB[a]
                mutate([], rem)
                if not ok:
                    raise RuntimeError("two-swap blocker replay failed")
                if accept(rem, [a, b], 2):
                    moved = True
                    break

        if not moved:
            restarts += 1
            S = set(T0)
            cnt, sm = init_counts(S, NB)
            free = {v for v in range(U) if v not in S and v not in D and cnt[v] == 0}
            h = 0
            for p in S:
                h ^= zob[p]
            rng.random()

        if step % 4096 == 0:
            one = sum(1 for v in range(U) if v not in S and v not in D and cnt[v] == 1)
            max_one_blockers = max(max_one_blockers, one)

    elapsed = time.monotonic() - start
    max_radius = max(max_radius, len(T0 - S))
    status = {
        "method": "bpz-t9-obstruction-free-366-hole-walk",
        "candidate": found is not None,
        "case_index": args.case,
        "seed": args.seed,
        "source_seed": c["seed"],
        "obstruction_index": c["obstruction_index"],
        "deleted_bad": bad,
        "steps_requested": args.steps,
        "seconds_requested": args.seconds,
        "elapsed_seconds": elapsed,
        "accepted_one_swaps": accepted1,
        "accepted_two_swaps": accepted2,
        "one_swap_attempts": attempts1,
        "two_swap_attempts": attempts2,
        "rejected_seen": rejected_seen,
        "restarts": restarts,
        "visited_states": len(visited),
        "max_radius_from_start": max_radius,
        "max_sampled_one_blocker_frontier": max_one_blockers,
        "final_free_vertices": len(free),
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
