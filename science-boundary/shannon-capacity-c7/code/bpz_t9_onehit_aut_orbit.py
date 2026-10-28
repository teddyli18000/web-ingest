#!/usr/bin/env python3
"""Exhaust signed-coordinate automorphisms of the 20 BPZ t=9 one-hit states.

The public translation scan found 20 exact one-hit states.  Translation alone
was then repaired exactly through several radii.  This program explores a
strictly larger symmetry orbit: for each one-hit state S and its fixed t=9
obstruction D, apply every signed coordinate permutation of C7^5
(5! * 2^5 = 3840 linear automorphisms), and for every transformed set optimize
all 7^5 translations simultaneously by FFT correlation.

Every FFT zero is replayed with integer coordinates before constructing the
nominal 134770-point C7^10 certificate.  Therefore a FOUND result is concrete;
a NONE result exhausts this full signed-permutation-plus-translation orbit for
the chosen one-hit case.
"""

import argparse
import json
import sys
from itertools import permutations, product
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f
import bpz_t9_exchange_repair as ex


def transform_set(S, perm, signs, digits):
    out = []
    for v in S:
        w = digits[v]
        y = tuple((signs[j] * w[perm[j]]) % 7 for j in range(5))
        out.append(f.enc(y))
    return set(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("family_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--case", type=int, required=True)
    args = ap.parse_args()
    if not 0 <= args.case < 20:
        raise SystemExit("case must be 0..19")

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring

    raw = json.loads((args.tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    X0 = set(map(int, raw["X"]))
    ring = Ring(f.D)
    digits = tuple(ring.decode(v) for v in range(f.U))
    nb = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]

    cases = ex.one_hit_cases(I0, X0, ring, digits, nb, args.family_root)
    c = cases[args.case]
    S0 = set(c["S"])
    Dset = set(c["D"])
    if len(S0) != f.N or not f.independent(S0, digits) or len(S0 & Dset) != 1:
        raise RuntimeError("one-hit case drift")

    FD = np.fft.fftn(f.arr(Dset, digits))
    transforms = 0
    unique_sets = 0
    duplicate_sets = 0
    hist = {}
    best = None
    one_hit = []
    winner = None
    seen = set()

    for perm in permutations(range(5)):
        for signs in product((1, -1), repeat=5):
            transforms += 1
            S = transform_set(S0, perm, signs, digits)
            if len(S) != f.N or not f.independent(S, digits):
                raise RuntimeError("signed-coordinate transform broke independence")
            key = tuple(sorted(S))
            if key in seen:
                duplicate_sets += 1
                continue
            seen.add(key)
            unique_sets += 1

            FS = np.fft.fftn(f.arr(S, digits))
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            mn = int(corr.min())
            hist[str(mn)] = hist.get(str(mn), 0) + 1
            rec = {
                "min_hits": mn,
                "perm": list(perm),
                "signs": list(signs),
            }
            if best is None or mn < best["min_hits"]:
                best = rec

            if mn == 1 and len(one_hit) < 100:
                idx = np.argwhere(corr == 1)[0]
                one_hit.append({**rec, "translation_fft_index": [int(z) for z in idx]})
            if mn != 0:
                continue

            for idx in np.argwhere(corr == 0):
                t = tuple(int(z) for z in idx)
                for shift_sign in (1, -1):
                    X = set(f.shift_set(S, t, digits, shift_sign))
                    if len(X) != f.N or not f.independent(X, digits):
                        raise RuntimeError("zero-hit replay lost independence")
                    if X & Dset:
                        continue
                    winner = (perm, signs, t, shift_sign, X)
                    break
                if winner:
                    break
            if winner:
                break
        if winner:
            break

    status = {
        "method": "bpz-t9-onehit-full-signed-coordinate-orbit-plus-translations",
        "candidate": winner is not None,
        "case_index": args.case,
        "seed": c["seed"],
        "obstruction_index": c["obstruction_index"],
        "starting_translation": list(c["translation"]),
        "starting_translation_sign": c["translation_sign"],
        "linear_automorphisms_total": 120 * 32,
        "linear_automorphisms_examined": transforms,
        "unique_transformed_sets": unique_sets,
        "duplicate_transformed_sets": duplicate_sets,
        "best": best,
        "min_hit_histogram": hist,
        "one_hit_examples": one_hit,
        "family_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    perm, signs, t, shift_sign, X = winner
    Ibits, pairs, orient, PH, PV = c["witness"]
    points, xp = f.build(Ibits, sum(1 << z for z in X), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift: {len(points)}")
    status.update({
        "score": len(points),
        "winning_perm": list(perm),
        "winning_signs": list(signs),
        "winning_translation": list(t),
        "winning_translation_sign": shift_sign,
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
