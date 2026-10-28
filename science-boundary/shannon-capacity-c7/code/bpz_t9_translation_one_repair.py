#!/usr/bin/env python3
"""Exact 1-for-1 repair of near-miss BPZ t=9 translated auxiliary sets.

For each of 38 public 367-point C7^5 independent sets and each of the 160
BPZ t=9 obstruction masks D, FFT finds all translations minimizing |(S+t)∩D|.
Whenever the minimum is one, replay the translation exactly, delete the unique
point in D, and exhaust all 7^5 possible replacement vertices.  A replacement
is valid iff it lies outside D and outside the closed neighborhood of the
remaining 366 points.  Such a repair is therefore an exact obstruction-free
367-set and yields the 134770-point Definition-2 construction.
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
    repair_attempts = 0
    unique_near_states = 0
    seen = set()
    winner = None
    first_near = None

    for name, S in seeds:
        FS = np.fft.fftn(f.arr(S, digits))
        for oi, (mask, witness, FD) in enumerate(Fobs):
            cases += 1
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            mn = int(corr.min())
            if mn != 1:
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
                    bad = next(iter(hits))
                    retained = Xset - {bad}
                    if len(retained) != f.N - 1 or not f.independent(retained, digits):
                        raise RuntimeError("near-state replay failed")
                    forbidden = ring.nbhd(retained)
                    candidates = [v for v in range(f.U) if v not in forbidden and v not in Dset]
                    repair_attempts += len(candidates)
                    if first_near is None:
                        first_near = {
                            "seed": name,
                            "obstruction_index": oi,
                            "translation": list(t),
                            "translation_sign": sign,
                            "bad": bad,
                            "replacement_candidates": len(candidates),
                        }
                    if not candidates:
                        continue
                    y = candidates[0]
                    repaired = retained | {y}
                    if len(repaired) != f.N or not f.independent(repaired, digits):
                        raise RuntimeError("replacement replay independence failed")
                    if repaired & Dset:
                        raise RuntimeError("replacement still hits obstruction")
                    winner = (name, oi, t, sign, bad, y, repaired, witness, len(candidates))
                    break
                if winner:
                    break
            if winner:
                break
        if winner:
            break

    status = {
        "method": "bpz-t9-public-translations-exact-one-for-one-repair",
        "candidate": winner is not None,
        "seed_count": len(seeds),
        "obstruction_masks": len(obs_items),
        "seed_obstruction_cases": cases,
        "min1_cases": min1_cases,
        "fft_min1_shifts": fft_min1_shifts,
        "exact_min1_replays": exact_min1_replays,
        "unique_near_states": unique_near_states,
        "replacement_candidates_examined": repair_attempts,
        "first_near_state": first_near,
        "family_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    name, oi, t, sign, bad, y, repaired, witness, ncand = winner
    Ibits, pairs, orient, PH, PV = witness
    Xbits = sum(1 << z for z in repaired)
    points, xp = f.build(Ibits, Xbits, pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    status.update({
        "score": len(points),
        "winning_seed": name,
        "winning_obstruction_index": oi,
        "winning_translation": list(t),
        "translation_sign": sign,
        "removed_auxiliary_point": bad,
        "added_auxiliary_point": y,
        "replacement_candidates": ncand,
        "private_pairs": [list(z) for z in pairs],
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
