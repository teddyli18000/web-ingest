#!/usr/bin/env python3
"""Exact repair of translated public auxiliaries whose minimum obstruction hit is two.

For a translated 367-set S with |S cap D|=2, both obstruction points are forced
deletions.  After deleting them, exhaust all 7^5 vertices outside D and outside
the closed neighborhood of the remaining 365 points, and test every compatible
pair of candidates.  Any pair restores an obstruction-free 367-set and hence a
134770-point BPZ t=9 C7^10 construction.
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
    min2_cases = 0
    fft_min2_shifts = 0
    exact_min2_replays = 0
    unique_near_states = 0
    candidate_vertices = 0
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
            if int(corr.min()) != 2:
                continue
            min2_cases += 1
            Dset = set(f.values(mask))
            for idx in np.argwhere(corr == 2):
                fft_min2_shifts += 1
                t = tuple(int(z) for z in idx)
                for sign in (1, -1):
                    Xset = set(f.shift_set(S, t, digits, sign))
                    hits = Xset & Dset
                    if len(hits) != 2:
                        continue
                    exact_min2_replays += 1
                    key = (name, oi, tuple(sorted(Xset)))
                    if key in seen:
                        continue
                    seen.add(key)
                    unique_near_states += 1
                    retained = Xset - hits
                    if len(retained) != f.N - 2 or not f.independent(retained, digits):
                        raise RuntimeError("two-hit retained replay failed")
                    forbidden = ring.nbhd(retained)
                    pool = [v for v in range(f.U) if v not in forbidden and v not in Dset]
                    candidate_vertices += len(pool)
                    max_pool = max(max_pool, len(pool))
                    if first_near is None:
                        first_near = {
                            "seed": name,
                            "obstruction_index": oi,
                            "translation": list(t),
                            "translation_sign": sign,
                            "hits": sorted(hits),
                            "candidate_pool": len(pool),
                        }
                    for ia, y in enumerate(pool):
                        for z in pool[ia + 1:]:
                            candidate_pairs += 1
                            if z in ring.NB[y]:
                                continue
                            repaired = retained | {y, z}
                            if len(repaired) != f.N or repaired & Dset:
                                continue
                            if not f.independent(repaired, digits):
                                raise RuntimeError("two-hit repair replay failed")
                            winner = (name, oi, t, sign, sorted(hits), y, z, repaired, witness, len(pool))
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
        "method": "bpz-t9-public-translations-exact-two-hit-two-for-two-repair",
        "candidate": winner is not None,
        "seed_count": len(seeds),
        "obstruction_masks": len(obs_items),
        "seed_obstruction_cases": cases,
        "min2_cases": min2_cases,
        "fft_min2_shifts": fft_min2_shifts,
        "exact_min2_replays": exact_min2_replays,
        "unique_near_states": unique_near_states,
        "candidate_vertices_total": candidate_vertices,
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

    name, oi, t, sign, hits, y, z, repaired, witness, pool_size = winner
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
        "removed_auxiliary_points": hits,
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
