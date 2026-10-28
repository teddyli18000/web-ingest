#!/usr/bin/env python3
"""Exact radius<=2 neutral neighborhood search for an orientation-valid t=11 parent.

The frozen U2-derived depth-2 parent has 11 distinct private-neighbour owners,
but its 11 private pairs admit no H/V orientation with both endpoint sets
independent.  This program searches the parent itself, every exact neutral
1-for-1 neighbor, and every exact neutral 2-for-2 neighbor.  For each 367-point
state it recomputes all private pairs and directly backtracks over distinct
owners, private-neighbour choices, and orientations.  A witness consists of 11
pairs (a,q) with distinct owners such that choosing q/a on the H side and a/q
on the V side produces two independent 11-sets.

This is the actual t=11 parent criterion, not merely a private-owner count.
"""
import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t10_aux_translation_fft as base

T = 11


def orientation_witness(points, ring, digits, nb):
    bits = sum(1 << z for z in points)
    pp = base.private(bits, nb)
    by_owner = {}
    for a, q in pp:
        by_owner.setdefault(a, []).append(q)
    owners = sorted(by_owner, key=lambda a: (len(by_owner[a]), a))
    if len(owners) < T:
        return None, len(pp), len(owners)

    H = []
    V = []
    chosen = []

    def ok(v, arr):
        return all(not base.conflict(v, u, digits) for u in arr)

    def dfs(pos):
        if len(chosen) == T:
            return list(chosen)
        need = T - len(chosen)
        if len(owners) - pos < need:
            return None
        for oi in range(pos, len(owners)):
            if len(owners) - oi < need:
                break
            a = owners[oi]
            for q in sorted(by_owner[a]):
                # orientation bit 1: H gets q, V gets owner a
                if ok(q, H) and ok(a, V):
                    H.append(q); V.append(a); chosen.append((a, q, 1))
                    z = dfs(oi + 1)
                    if z is not None: return z
                    chosen.pop(); V.pop(); H.pop()
                # orientation bit 0: H gets owner a, V gets q
                if ok(a, H) and ok(q, V):
                    H.append(a); V.append(q); chosen.append((a, q, 0))
                    z = dfs(oi + 1)
                    if z is not None: return z
                    chosen.pop(); V.pop(); H.pop()
        return None

    return dfs(0), len(pp), len(owners)


def supports(points, ring):
    out = [0] * base.U
    for i, u in enumerate(points):
        bit = 1 << i
        for v in ring.NB[u]:
            out[v] |= bit
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("parent_json", type=Path)
    ap.add_argument("output_parent", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring  # type: ignore

    ring = Ring(base.D)
    digits = tuple(ring.decode(v) for v in range(base.U))
    nb = [sum(1 << z for z in ring.NB[v]) for v in range(base.U)]
    frozen = json.loads(args.parent_json.read_text())
    P = sorted(map(int, frozen["points"]))
    if len(P) != 367 or len(set(P)) != 367 or not base.independent(P, digits):
        raise RuntimeError("frozen U2 parent invalid")
    pset = set(P)

    supp = supports(P, ring)
    one = {}
    two = {}
    for v, sm in enumerate(supp):
        if v in pset:
            continue
        bc = sm.bit_count()
        if bc == 1:
            i = (sm & -sm).bit_length() - 1
            one.setdefault(i, []).append(v)
        elif bc == 2:
            ids = [i for i in range(len(P)) if (sm >> i) & 1]
            two.setdefault((ids[0], ids[1]), []).append(v)

    tested = 0
    distinct = set()
    owner_hist = {}
    pair_hist = {}
    best_owners = 0
    best_pairs = 0
    witness_rec = None

    def test_state(Y, move):
        nonlocal tested, best_owners, best_pairs, witness_rec
        key = tuple(sorted(Y))
        if key in distinct:
            return False
        distinct.add(key)
        if len(key) != 367 or not base.independent(key, digits):
            raise RuntimeError(f"neighbor replay failed move={move}")
        tested += 1
        wit, npairs, nowners = orientation_witness(key, ring, digits, nb)
        owner_hist[str(nowners)] = owner_hist.get(str(nowners), 0) + 1
        pair_hist[str(npairs)] = pair_hist.get(str(npairs), 0) + 1
        best_owners = max(best_owners, nowners)
        best_pairs = max(best_pairs, npairs)
        if wit is None:
            return False
        pairs = [(a, q) for a, q, s in wit]
        orient = [s for a, q, s in wit]
        PH = [q if s else a for (a, q), s in zip(pairs, orient)]
        PV = [a if s else q for (a, q), s in zip(pairs, orient)]
        if len(set(a for a, q in pairs)) != T:
            raise RuntimeError("orientation owner replay failed")
        if not base.independent(PH, digits) or not base.independent(PV, digits):
            raise RuntimeError("orientation independence replay failed")
        witness_rec = {
            "points": list(key),
            "private_pairs": [list(z) for z in pairs],
            "orientation": orient,
            "PH": PH,
            "PV": PV,
            "move": move,
            "private_pair_count": npairs,
            "private_owner_count": nowners,
        }
        return True

    # parent itself (known orientation-invalid, kept as a drift check)
    test_state(P, {"radius": 0})

    # Exact neutral 1-for-1 states.
    if witness_rec is None:
        for a in sorted(one):
            for u in sorted(one[a]):
                Y = list(P); Y[a] = u
                if test_state(Y, {"radius": 1, "remove_indices": [a], "add": [u]}):
                    break
            if witness_rec is not None:
                break

    # Exact neutral 2-for-2 states.  Any non-degenerate 2-swap uses two outside
    # vertices whose support union is contained in the two removed owners.
    owner_pairs = set(two)
    for a, b in combinations(sorted(one), 2):
        owner_pairs.add((a, b))
    candidate_pair_trials = 0
    max_pool = 0
    if witness_rec is None:
        for a, b in sorted(owner_pairs):
            pool = sorted(set(one.get(a, []) + one.get(b, []) + two.get((a, b), [])))
            max_pool = max(max_pool, len(pool))
            for u, v in combinations(pool, 2):
                candidate_pair_trials += 1
                if base.conflict(u, v, digits):
                    continue
                Y = list(P); Y[a] = u; Y[b] = v
                if len(set(Y)) != 367:
                    continue
                if test_state(Y, {"radius": 2, "remove_indices": [a, b], "add": [u, v]}):
                    break
            if witness_rec is not None:
                break

    status = {
        "method": "u2-t11-orientation-valid-neutral-radius2-exact",
        "candidate": witness_rec is not None,
        "states_tested": tested,
        "distinct_states": len(distinct),
        "support1_owner_groups": len(one),
        "support2_owner_pairs": len(two),
        "owner_pairs_generated": len(owner_pairs),
        "candidate_pair_trials": candidate_pair_trials,
        "max_radius2_pool": max_pool,
        "private_owner_histogram": owner_hist,
        "private_pair_histogram": pair_hist,
        "max_private_owners": best_owners,
        "max_private_pairs": best_pairs,
        "source_parent": str(args.parent_json),
        "witness": witness_rec,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    if witness_rec is None:
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    out = {
        "source": "orientation-valid radius<=2 neighbor of frozen U2 depth-2 parent",
        "points": witness_rec["points"],
        "private_pairs": witness_rec["private_pairs"],
        "orientation_hint": witness_rec["orientation"],
        "move": witness_rec["move"],
    }
    args.output_parent.parent.mkdir(parents=True, exist_ok=True)
    args.output_parent.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
