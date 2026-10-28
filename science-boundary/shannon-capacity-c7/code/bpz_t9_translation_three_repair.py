#!/usr/bin/env python3
"""Exact 3-for-3 repair of one-hit BPZ t=9 translated auxiliary sets.

For every public translated 367-set S with a unique obstruction hit x, remove x
and every unordered pair {r,s} of further S-points.  A replacement y is usable
iff N[y] cap S is contained in {x,r,s} and y avoids the obstruction.  Support
groups make the full 20 * C(366,2) removal search small.  Every candidate triple
is tested for pairwise compatibility and replayed exactly.
"""
import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("family_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring

    raw = json.loads((args.tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    X0 = set(map(int, raw["X"]))
    ring = Ring(f.D)
    digits = tuple(ring.decode(v) for v in range(f.U))
    nb = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    obs = f.obstruction_witnesses(I0, ring, digits, nb)

    fam = json.loads((args.family_root / "data" / "family-f.json").read_text())
    states = [set(map(int, s)) for s in fam["states"]]
    seeds = [("bpz-X", X0), ("bpz-I0", I0)] + [
        (f"family-f-{i}", s) for i, s in enumerate(states)
    ]

    obs_items = list(obs.items())
    Fobs = [(m, w, np.fft.fftn(f.arr(f.values(m), digits))) for m, w in obs_items]

    cases = min1_cases = fft_min1_shifts = exact_replays = unique_states = 0
    removal_triples = candidate_pools = candidate_triples = 0
    max_pool = 0
    seen = set()
    winner = None

    for name, S in seeds:
        if len(S) != f.N or not f.independent(S, digits):
            raise RuntimeError(f"seed {name} invalid")
        FS = np.fft.fftn(f.arr(S, digits))
        for oi, (mask, witness, FD) in enumerate(Fobs):
            cases += 1
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            if int(corr.min()) != 1:
                continue
            min1_cases += 1
            Dset = set(f.values(mask))
            for idx in np.argwhere(corr == 1):
                fft_min1_shifts += 1
                t = tuple(int(z) for z in idx)
                for sign in (1, -1):
                    Xset = set(f.shift_set(S, t, digits, sign))
                    hits = Xset & Dset
                    if len(hits) != 1:
                        continue
                    exact_replays += 1
                    key = (name, oi, tuple(sorted(Xset)))
                    if key in seen:
                        continue
                    seen.add(key); unique_states += 1
                    x = next(iter(hits)); xbit = 1 << x
                    Sbits = sum(1 << z for z in Xset)
                    groups = {}
                    for y in range(f.U):
                        if y in Dset:
                            continue
                        sup = nb[y] & Sbits
                        if sup.bit_count() <= 3:
                            groups.setdefault(sup, []).append(y)
                    old = sorted(Xset - {x})
                    g0 = groups.get(0, ())
                    gx = groups.get(xbit, ())
                    for ir in range(len(old)):
                        r = old[ir]; rb = 1 << r
                        gr = groups.get(rb, ()); gxr = groups.get(xbit | rb, ())
                        for s in old[ir + 1:]:
                            removal_triples += 1
                            sb = 1 << s
                            pool = []
                            pool.extend(g0); pool.extend(gx)
                            pool.extend(gr); pool.extend(gxr)
                            pool.extend(groups.get(sb, ()))
                            pool.extend(groups.get(xbit | sb, ()))
                            pool.extend(groups.get(rb | sb, ()))
                            pool.extend(groups.get(xbit | rb | sb, ()))
                            # Support masks partition vertices, hence no duplicates.
                            max_pool = max(max_pool, len(pool))
                            if len(pool) < 3:
                                continue
                            candidate_pools += 1
                            retained = Xset - {x, r, s}
                            for ia, a in enumerate(pool):
                                if a in retained:
                                    raise RuntimeError("support filter admitted retained point")
                                for ib in range(ia + 1, len(pool)):
                                    b = pool[ib]
                                    if b in ring.NB[a]:
                                        continue
                                    for c in pool[ib + 1:]:
                                        candidate_triples += 1
                                        if c in ring.NB[a] or c in ring.NB[b]:
                                            continue
                                        repaired = retained | {a, b, c}
                                        if len(repaired) != f.N or repaired & Dset:
                                            continue
                                        if not f.independent(repaired, digits):
                                            raise RuntimeError("three-repair replay failed")
                                        winner = (name, oi, t, sign, [x,r,s], [a,b,c], repaired, witness, len(pool))
                                        break
                                    if winner: break
                                if winner: break
                            if winner: break
                        if winner: break
                    if winner: break
                if winner: break
            if winner: break
        if winner: break

    status = {
        "method": "bpz-t9-public-translations-exact-three-for-three-repair",
        "candidate": winner is not None,
        "seed_count": len(seeds), "obstruction_masks": len(obs_items),
        "seed_obstruction_cases": cases, "min1_cases": min1_cases,
        "fft_min1_shifts": fft_min1_shifts, "exact_min1_replays": exact_replays,
        "unique_near_states": unique_states, "removal_triples_tested": removal_triples,
        "candidate_pools": candidate_pools, "candidate_triples_checked": candidate_triples,
        "max_candidate_pool": max_pool,
        "family_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    name, oi, t, sign, rem, add, repaired, witness, pool_size = winner
    Ibits, pairs, orient, PH, PV = witness
    points, xp = f.build(Ibits, sum(1 << q for q in repaired), pairs, PH, PV, ring)
    status.update({
        "score": len(points), "winning_seed": name, "winning_obstruction_index": oi,
        "winning_translation": list(t), "translation_sign": sign,
        "removed_auxiliary_points": rem, "added_auxiliary_points": add,
        "winning_candidate_pool": pool_size, "private_pairs": [list(q) for q in pairs],
        "orientation": list(orient), "PH": PH, "PV": PV,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    })
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": points}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)

if __name__ == "__main__": main()
