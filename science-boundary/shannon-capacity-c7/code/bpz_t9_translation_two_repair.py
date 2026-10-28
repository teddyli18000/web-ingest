#!/usr/bin/env python3
"""Exact 2-for-2 repair of one-hit BPZ t=9 translated auxiliary sets.

For every public translated 367-set S with |S cap D|=1, let x be the unique
obstruction hit.  Any 2-for-2 repair must remove x and one further r in S.
A possible replacement y must have conflict support N[y] cap S contained in
{x,r}.  We compute these support groups exactly over all 7^5 vertices and test
all candidate replacement pairs for compatibility.  Thus this exhausts every
2-for-2 obstruction-avoiding repair of all min-hit-one translations found by
the 38-public-seed FFT scan.
"""
import argparse
import json
import sys
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
    for name, S in seeds:
        if len(S) != f.N or not f.independent(S, digits):
            raise RuntimeError(f"seed {name} invalid")

    obs_items = list(obs.items())
    Fobs = [(m, w, np.fft.fftn(f.arr(f.values(m), digits))) for m, w in obs_items]

    cases = 0
    min1_cases = 0
    fft_min1_shifts = 0
    exact_min1_replays = 0
    unique_near_states = 0
    second_removals = 0
    candidate_pools = 0
    candidate_pairs = 0
    max_pool = 0
    seen = set()
    winner = None
    first_near = None

    for name, S in seeds:
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
                    exact_min1_replays += 1
                    key = (name, oi, tuple(sorted(Xset)))
                    if key in seen:
                        continue
                    seen.add(key)
                    unique_near_states += 1
                    x = next(iter(hits))
                    if first_near is None:
                        first_near = {
                            "seed": name,
                            "obstruction_index": oi,
                            "translation": list(t),
                            "translation_sign": sign,
                            "bad": x,
                        }

                    Sbits = sum(1 << z for z in Xset)
                    groups = {}
                    for y in range(f.U):
                        if y in Dset:
                            continue
                        sup = nb[y] & Sbits
                        if sup.bit_count() <= 2:
                            groups.setdefault(sup, []).append(y)

                    xbit = 1 << x
                    gx = groups.get(xbit, ())
                    g0 = groups.get(0, ())
                    for r in Xset:
                        if r == x:
                            continue
                        second_removals += 1
                        rbit = 1 << r
                        pool = list(g0)
                        pool.extend(gx)
                        pool.extend(groups.get(rbit, ()))
                        pool.extend(groups.get(xbit | rbit, ()))
                        # The support groups are disjoint, but keep this defensive
                        # deduplication so future Ring changes cannot duplicate IDs.
                        pool = sorted(set(pool))
                        max_pool = max(max_pool, len(pool))
                        if len(pool) < 2:
                            continue
                        candidate_pools += 1
                        retained = Xset - {x, r}
                        for ia, y in enumerate(pool):
                            # A retained old point cannot occur because its self-bit
                            # would lie outside {x,r}; replay explicitly anyway.
                            if y in retained:
                                raise RuntimeError("support filter admitted retained vertex")
                            for z in pool[ia + 1:]:
                                candidate_pairs += 1
                                if z in ring.NB[y]:
                                    continue
                                repaired = retained | {y, z}
                                if len(repaired) != f.N:
                                    continue
                                if repaired & Dset:
                                    raise RuntimeError("two-repair still hits obstruction")
                                if not f.independent(repaired, digits):
                                    raise RuntimeError("two-repair independence replay failed")
                                winner = (name, oi, t, sign, x, r, y, z, repaired, witness, len(pool))
                                break
                            if winner:
                                break
                        if winner:
                            break
                    if winner:
                        break
                if winner:
                    break
            if winner:
                break
        if winner:
            break

    status = {
        "method": "bpz-t9-public-translations-exact-two-for-two-repair",
        "candidate": winner is not None,
        "seed_count": len(seeds),
        "obstruction_masks": len(obs_items),
        "seed_obstruction_cases": cases,
        "min1_cases": min1_cases,
        "fft_min1_shifts": fft_min1_shifts,
        "exact_min1_replays": exact_min1_replays,
        "unique_near_states": unique_near_states,
        "second_removals_tested": second_removals,
        "candidate_pools": candidate_pools,
        "candidate_pairs_checked": candidate_pairs,
        "max_candidate_pool": max_pool,
        "first_near_state": first_near,
        "family_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    name, oi, t, sign, x, r, y, z, repaired, witness, pool_size = winner
    Ibits, pairs, orient, PH, PV = witness
    Xbits = sum(1 << q for q in repaired)
    points, xp = f.build(Ibits, Xbits, pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    status.update({
        "score": len(points),
        "winning_seed": name,
        "winning_obstruction_index": oi,
        "winning_translation": list(t),
        "translation_sign": sign,
        "removed_auxiliary_points": [x, r],
        "added_auxiliary_points": [y, z],
        "winning_candidate_pool": pool_size,
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
