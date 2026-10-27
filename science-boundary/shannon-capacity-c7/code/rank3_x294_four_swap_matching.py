#!/usr/bin/env python3
"""Enumerate every exact 4-for-4 exchange relevant to the X_294 Hall closure.

For a 367-point C7^5 independent set F, every replacement vertex has a support
mask consisting of the old F-points it conflicts with.  An exact four-swap
state has four pairwise-compatible replacement vertices whose support-union is
exactly a four-element removed owner set R.

Every possible R is generated exhaustively by support-size patterns:
  * a size-4 support;
  * a size-3 support plus any support introducing the fourth owner;
  * at least two size-2 supports (two or three distinct masks suffice to expose
    all four owners), optionally with a size-1 support;
  * one size-2 support plus two size-1 supports;
  * four size-1 supports.
Repeated support masks need no special R generator: their owner union is already
represented by the same mask plus the remaining support masks.
"""

import argparse
import json
from itertools import combinations
from pathlib import Path

import generalized9 as g
import neutral2_maxsat as nm
import rank3_square_relax as rs
import rank3_x294_two_swap_matching as tw

SPECIAL = 294
BASELINE = 134753


def bits(mask: int):
    while mask:
        lsb = mask & -mask
        yield lsb.bit_length() - 1
        mask ^= lsb


def support_groups(F, digits):
    supports, _ = g.support_masks(F, digits)
    fset = set(F)
    groups = {}
    for v, sm in enumerate(supports):
        if v in fset:
            continue
        bc = sm.bit_count()
        if 1 <= bc <= 4:
            groups.setdefault(sm, []).append(v)
    return supports, groups


def owner_quads(groups):
    by = {k: sorted(m for m in groups if m.bit_count() == k) for k in range(1, 5)}
    s1, s2, s3, s4 = by[1], by[2], by[3], by[4]
    quads = set(s4)

    # Any state using a size-3 support: some other used support introduces the
    # fourth owner. It is enough to union the size-3 mask with one used support.
    other = s1 + s2 + s3
    for a in s3:
        for b in other:
            u = a | b
            if u.bit_count() == 4:
                quads.add(u)

    # States with no size-3/4 support but >=2 distinct size-2 masks.
    # Two doubles can already expose all four owners. If they expose three,
    # either a third double or a singleton exposes the fourth.
    for i, a in enumerate(s2):
        for b in s2[i + 1 :]:
            u = a | b
            bc = u.bit_count()
            if bc == 4:
                quads.add(u)
            elif bc == 3:
                for c in s1:
                    v = u | c
                    if v.bit_count() == 4:
                        quads.add(v)
                for c in s2:
                    v = u | c
                    if v.bit_count() == 4:
                        quads.add(v)

    # Only one distinct double support is used; the other owners must come from
    # singleton supports. Repetition within a support group is allowed later.
    for d in s2:
        for a, b in combinations(s1, 2):
            u = d | a | b
            if u.bit_count() == 4:
                quads.add(u)

    for ss in combinations(s1, 4):
        u = ss[0] | ss[1] | ss[2] | ss[3]
        if u.bit_count() == 4:
            quads.add(u)

    return sorted(quads), {k: len(v) for k, v in by.items()}


def pool_for(R, groups):
    own = list(bits(R))
    pool = []
    for k in range(1, 5):
        for ss in combinations(own, k):
            m = 0
            for i in ss:
                m |= 1 << i
            pool.extend(groups.get(m, ()))
    return sorted(set(pool))


def enumerate_states(R, pool, supports, digits):
    """Yield every compatible 4-tuple in pool with exact support union R."""
    n = len(pool)
    for ia in range(n):
        a = pool[ia]
        sa = supports[a]
        for ib in range(ia + 1, n):
            b = pool[ib]
            if g.conflict(a, b, digits):
                continue
            sab = sa | supports[b]
            if sab & ~R:
                continue
            for ic in range(ib + 1, n):
                c = pool[ic]
                if g.conflict(a, c, digits) or g.conflict(b, c, digits):
                    continue
                sabc = sab | supports[c]
                if sabc & ~R:
                    continue
                for idd in range(ic + 1, n):
                    d = pool[idd]
                    if (sabc | supports[d]) != R:
                        continue
                    if (
                        g.conflict(a, d, digits)
                        or g.conflict(b, d, digits)
                        or g.conflict(c, d, digits)
                    ):
                        continue
                    yield (a, b, c, d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--family", choices=("r0", "rank3", "x"), required=True)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = rs.load_rank3_state(r0, digits)
    rsup, _ = g.support_masks(r, digits)

    base_model, bst = nm.solve_maxsat(rs.RANK3_K9, r, xset, digits, rsup)
    if base_model is None or bst["score"] != BASELINE:
        raise RuntimeError(f"base drift {bst}")
    _, hs, vs = base_model
    x0 = xset[SPECIAL]
    weights = [sum(1 for f in arr if g.conflict(x0, f, digits)) for arr in vs]
    positive = [j for j, c in enumerate(weights) if c]
    if len(positive) != 366 or any(weights[j] != 1 for j in positive):
        raise RuntimeError("weight drift")

    ridx = {j: k for k, j in enumerate(positive)}
    adj_all = [[] for _ in range(g.U)]
    for j in positive:
        k = ridx[j]
        for v in rs.neighborhood(xset[j], digits):
            adj_all[v].append(k)

    F = list(r0 if args.family == "r0" else r if args.family == "rank3" else xset)
    fsup, groups = support_groups(F, digits)
    quads, support_group_counts = owner_quads(groups)

    base_m = tw.hk([adj_all[v] for v in F], 366)
    if base_m != 366:
        raise RuntimeError(f"base matching {base_m}")

    best_m = base_m
    best = []
    hist = {}
    legal = 0
    candidate_combinations = 0
    max_pool = 0
    owner_quads_with_states = 0

    for qi, R in enumerate(quads):
        owners = tuple(bits(R))
        if len(owners) != 4:
            raise RuntimeError("bad owner quad")
        pool = pool_for(R, groups)
        max_pool = max(max_pool, len(pool))
        before = legal
        # Count the raw four-subsets for diagnostics; actual enumeration prunes
        # incompatibility and requires exact support union.
        if len(pool) >= 4:
            candidate_combinations += (
                len(pool) * (len(pool) - 1) * (len(pool) - 2) * (len(pool) - 3) // 24
            )
        for add in enumerate_states(R, pool, fsup, digits):
            G = F.copy()
            for owner, v in zip(owners, add):
                G[owner] = v
            if len(set(G)) != len(G):
                raise RuntimeError("duplicate replacement state")
            legal += 1
            m = tw.hk([adj_all[z] for z in G], 366)
            hist[m] = hist.get(m, 0) + 1
            rec = (owners, add, G)
            if m < best_m:
                best_m = m
                best = [rec]
            elif m == best_m and len(best) < 100:
                best.append(rec)
        if legal > before:
            owner_quads_with_states += 1
        if (qi + 1) % 10000 == 0:
            print(
                f"PROGRESS quads={qi+1}/{len(quads)} legal={legal} best_matching={best_m}",
                flush=True,
            )

    status = {
        "candidate": False,
        "family": args.family,
        "method": "rank3-x294-exact-four-swap-hall",
        "base_matching": base_m,
        "support_group_counts": support_group_counts,
        "owner_quads": len(quads),
        "owner_quads_with_states": owner_quads_with_states,
        "max_pool": max_pool,
        "candidate_combinations": candidate_combinations,
        "legal_four_swap_states": legal,
        "matching_histogram": {str(k): v for k, v in sorted(hist.items())},
        "min_matching": best_m,
        "max_closure_objective": 367 - best_m,
        "best_states": [
            {"remove": list(o), "add": list(a)} for o, a, _ in best
        ],
        "base_maxsat": bst,
    }

    if best_m <= 365:
        owners, add, G = best[0]
        bidx = [i for i in range(367) if i not in set(rs.RANK3_K9)]
        baseids = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
        obj, cert, nsel, pen, cost, rm, ad = tw.closure(
            G, weights, xset, digits, hs, vs, r, bidx, baseids
        )
        score = BASELINE + (obj - len(hs[SPECIAL]))
        if len(cert) != score or score <= BASELINE:
            raise RuntimeError(f"closure replay score={score} cert={len(cert)} obj={obj}")
        status.update({
            "candidate": True,
            "score": score,
            "winning_remove": list(owners),
            "winning_add": list(add),
            "closure_objective": obj,
            "selected_endpoints": nsel,
            "penalty_old_v_ports": pen,
            "rc2_cost": cost,
            "removed_vs_baseline": rm,
            "added_vs_baseline": ad,
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(z) for z in sorted(cert)]}, separators=(",", ":")) + "\n"
        )

    args.status.parent.mkdir(parents=True, exist_ok=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(("FOUND" if status["candidate"] else "NONE"), json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
