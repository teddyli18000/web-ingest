#!/usr/bin/env python3
"""Exact simultaneous 2-for-2 bridge search on the BPZ auxiliary X set.

The complete one-point private-swap components of the published I and X each
have 243 states.  Across the I component there are 640 t=9 transversal
orientations with independent P^H and P^V, but every X state in its 243-state
component hits N(P^H) cap N(P^V) at least once.

This program freezes every such obstruction mask, then exhausts all simultaneous
2-for-2 replacements of the published X whose two additions have conflict
support contained in the two removed X owners.  States already in the 243-state
X component are skipped.  Any genuinely new X state avoiding any frozen
obstruction mask yields a Definition-2 t=9 gadget and therefore a 134770-point
independent set in C7^10.
"""

import argparse
import json
import sys
from itertools import combinations, product
from pathlib import Path

Q = 7
D = 5
U = Q ** D
N = 367
T = 9
TARGET = N * N + T * T


def conflict(a, b, digits):
    return all((x - y) % Q in (0, 1, Q - 1) for x, y in zip(digits[a], digits[b]))


def independent(vals, digits):
    vals = list(vals)
    return all(not conflict(a, b, digits) for a, b in combinations(vals, 2))


def values(bits):
    while bits:
        z = bits & -bits
        yield z.bit_length() - 1
        bits ^= z


def private(bits, nbmask):
    out = []
    zero = []
    for q in range(U):
        if (bits >> q) & 1:
            continue
        h = nbmask[q] & bits
        bc = h.bit_count()
        if bc == 0:
            zero.append(q)
        elif bc == 1:
            out.append((h.bit_length() - 1, q))
    return sorted(out), zero


def component(start, nbmask):
    seen = {start}
    front = [start]
    priv = {}
    while front:
        nxt = []
        for bits in front:
            pp, _ = private(bits, nbmask)
            priv[bits] = pp
            for r, q in pp:
                b = bits ^ (1 << r) ^ (1 << q)
                if b not in seen:
                    seen.add(b)
                    nxt.append(b)
        front = nxt
    return seen, priv


def build(Ibits, Xbits, pairs, PH, PV, ring):
    I = set(values(Ibits))
    X = set(values(Xbits))
    R = {r for r, _ in pairs}
    B = I - R
    NH = ring.nbhd(set(PH))
    NV = ring.nbhd(set(PV))
    if X & NH & NV:
        raise RuntimeError("winning X still has a double hit")
    X0 = X - (NH | NV)
    XH = X & NH
    XV = X & NV
    P = set()
    for A, C in (
        (B, B), (R, X0), (set(PH), XH), (set(PV), XV),
        (X0, R), (XH, set(PV)), (XV, set(PH)),
    ):
        for a in A:
            for c in C:
                P.add((a, c))
    if len(P) != TARGET:
        raise RuntimeError(f"score drift {len(P)}")
    pts = sorted("".join(map(str, ring.decode(a) + ring.decode(b))) for a, b in P)
    return pts, (len(X0), len(XH), len(XV))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    root = args.tan_root.resolve()
    sys.path.insert(0, str(root))
    from shannon.certificates import Ring  # type: ignore

    raw = json.loads((root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    X0 = set(map(int, raw["X"]))
    ring = Ring(D)
    digits = tuple(ring.decode(v) for v in range(U))
    if len(I0) != N or len(X0) != N or not independent(I0, digits) or not independent(X0, digits):
        raise RuntimeError("base drift")

    nbmask = [sum(1 << z for z in ring.NB[v]) for v in range(U)]
    Istart = sum(1 << z for z in I0)
    Xstart = sum(1 << z for z in X0)
    Icomp, Ipriv = component(Istart, nbmask)
    Xcomp, _ = component(Xstart, nbmask)
    if len(Icomp) != 243 or len(Xcomp) != 243:
        raise RuntimeError(f"component drift I={len(Icomp)} X={len(Xcomp)}")

    # Freeze all same-side-valid t=9 obstruction masks from the entire I component.
    obstructions = {}
    eligible_I = 0
    subset_count = 0
    orientation_count = 0
    same_side = 0
    for Ibits in Icomp:
        pp = Ipriv[Ibits]
        if len({r for r, _ in pp}) < T:
            continue
        eligible_I += 1
        for pairs in combinations(pp, T):
            if len({r for r, _ in pairs}) < T:
                continue
            subset_count += 1
            for orient in product((0, 1), repeat=T):
                orientation_count += 1
                PH = [q if s else r for (r, q), s in zip(pairs, orient)]
                PV = [r if s else q for (r, q), s in zip(pairs, orient)]
                if not independent(PH, digits) or not independent(PV, digits):
                    continue
                same_side += 1
                Dset = ring.nbhd(set(PH)) & ring.nbhd(set(PV))
                dbits = sum(1 << z for z in Dset)
                if dbits not in obstructions:
                    obstructions[dbits] = (Ibits, pairs, orient, PH, PV)

    if same_side != 640:
        raise RuntimeError(f"same-side-valid count drift: {same_side}")

    # Enumerate every support-1/2 candidate against published X0.
    xlist = sorted(X0)
    cand = []
    support_hist = {1: 0, 2: 0}
    for q in range(U):
        if q in X0:
            continue
        hits = [z for z in ring.NB[q] if z in X0]
        if 1 <= len(hits) <= 2:
            s = frozenset(hits)
            cand.append((q, s))
            support_hist[len(hits)] += 1

    pools = {}
    for q, s in cand:
        if len(s) == 2:
            key = tuple(sorted(s))
            pools.setdefault(key, []).append(q)
        else:
            a = next(iter(s))
            for b in xlist:
                if b == a:
                    continue
                key = (a, b) if a < b else (b, a)
                pools.setdefault(key, []).append(q)

    new_states = set()
    owner_pairs = 0
    candidate_pairs = 0
    component_skips = 0
    for owners, pool in pools.items():
        pool = sorted(set(pool))
        if len(pool) < 2:
            continue
        owner_pairs += 1
        a, b = owners
        for i, x in enumerate(pool):
            for y in pool[i + 1:]:
                candidate_pairs += 1
                if conflict(x, y, digits):
                    continue
                bits = (Xstart ^ (1 << a) ^ (1 << b)) | (1 << x) | (1 << y)
                if bits.bit_count() != N:
                    raise RuntimeError("two-swap X cardinality drift")
                if bits in Xcomp:
                    component_skips += 1
                    continue
                new_states.add(bits)

    print("ENUM", json.dumps({
        "I_component": len(Icomp), "X_component": len(Xcomp),
        "eligible_I": eligible_I, "nine_pair_subsets": subset_count,
        "orientations": orientation_count, "same_side_valid": same_side,
        "unique_obstruction_masks": len(obstructions),
        "X_support1_candidates": support_hist[1], "X_support2_candidates": support_hist[2],
        "owner_pairs_with_pool": owner_pairs, "candidate_add_pairs": candidate_pairs,
        "component_skips": component_skips, "new_X_states": len(new_states),
    }, sort_keys=True), flush=True)

    checks = 0
    winner = None
    best_bad = None
    best = None
    for xi, Xbits in enumerate(new_states):
        for dbits, witness in obstructions.items():
            checks += 1
            bad = (Xbits & dbits).bit_count()
            if best_bad is None or bad < best_bad:
                best_bad = bad
                best = {"X_state_index": xi, "double_hits": bad}
            if bad == 0:
                winner = (Xbits, witness, xi)
                break
        if winner is not None:
            break

    status = {
        "method": "bpz-t9-exact-X-simultaneous-two-swap-bridge",
        "candidate": winner is not None,
        "I_component_states": len(Icomp),
        "X_component_states": len(Xcomp),
        "eligible_I_states": eligible_I,
        "nine_pair_subsets": subset_count,
        "orientations": orientation_count,
        "same_side_valid": same_side,
        "unique_obstruction_masks": len(obstructions),
        "X_support1_candidates": support_hist[1],
        "X_support2_candidates": support_hist[2],
        "owner_pairs_with_pool": owner_pairs,
        "candidate_add_pairs": candidate_pairs,
        "component_state_skips": component_skips,
        "new_X_two_swap_states": len(new_states),
        "obstruction_checks": checks,
        "best_double_hits": best_bad,
        "best": best,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    Xbits, witness, xi = winner
    Ibits, pairs, orient, PH, PV = witness
    pts, xp = build(Ibits, Xbits, pairs, PH, PV, ring)
    status.update({
        "score": len(pts),
        "winning_X_state_index": xi,
        "private_pairs": [list(z) for z in pairs],
        "orientation": list(orient),
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
