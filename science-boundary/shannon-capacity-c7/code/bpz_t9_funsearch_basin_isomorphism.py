#!/usr/bin/env python3
"""Verify the explicit automorphism relating the two FunSearch t=9 one-hit basins.

The full signed-orbit scan finds exactly 20 one-hit states in image 330 and 20
in image 341.  Their signed masks are complementary and their translations
suggest the C7^5 graph automorphism

    T(x0,...,x4) = (-x0+4, -x1, -x2+4, -x3, -x4+4) mod 7.

This script regenerates all one-hit states for those two images and verifies
that T bijects the complete (auxiliary-set, obstruction-set) state collection.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_fft import funsearch_seed
from bpz_t9_funsearch_exchange_repair import distinct_signed_images

A = 330
B = 341
C = (4, 0, 4, 0, 4)


def collect(image_index, images, obs, digits):
    S0 = set(images[image_index][0])
    FS = np.fft.fftn(f.arr(S0, digits))
    out = []
    for oi, (mask, _witness) in enumerate(obs):
        D = set(f.values(mask))
        FD = np.fft.fftn(f.arr(D, digits))
        corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
        if int(corr.min()) != 1:
            continue
        for idx in np.argwhere(corr == 1):
            t = tuple(int(z) for z in idx)
            S = set(f.shift_set(S0, t, digits, 1))
            hits = S & D
            if len(S) != f.N or not f.independent(S, digits) or len(hits) != 1:
                raise RuntimeError("one-hit replay drift")
            out.append({
                "obstruction_index": oi,
                "translation": t,
                "bad": next(iter(hits)),
                "S": frozenset(S),
                "D": frozenset(D),
            })
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring

    raw = json.loads((args.tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    ring = Ring(f.D)
    digits = tuple(ring.decode(v) for v in range(f.U))
    nb = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    obs = list(f.obstruction_witnesses(I0, ring, digits, nb).items())
    seed = funsearch_seed(digits)
    images = distinct_signed_images(seed, digits)

    a = collect(A, images, obs, digits)
    b = collect(B, images, obs, digits)
    if len(a) != 20 or len(b) != 20:
        raise RuntimeError(f"basin size drift: {len(a)}, {len(b)}")

    def T(v):
        x = digits[v]
        return f.enc(tuple((-x[j] + C[j]) % f.Q for j in range(f.D)))

    bmap = {(z["S"], z["D"]): z for z in b}
    mapping = []
    unmatched = []
    for z in a:
        ts = frozenset(T(v) for v in z["S"])
        td = frozenset(T(v) for v in z["D"])
        q = bmap.get((ts, td))
        if q is None:
            unmatched.append({"a_obstruction": z["obstruction_index"], "a_bad": z["bad"]})
            continue
        if T(z["bad"]) != q["bad"]:
            raise RuntimeError("bad-point mapping drift")
        mapping.append({
            "a_obstruction": z["obstruction_index"],
            "b_obstruction": q["obstruction_index"],
            "a_bad": z["bad"],
            "b_bad": q["bad"],
            "a_translation": list(z["translation"]),
            "b_translation": list(q["translation"]),
        })

    status = {
        "method": "explicit-C7^5-dihedral-automorphism-basin-bijection",
        "image_a": A,
        "image_b": B,
        "map": "x -> -x + (4,0,4,0,4) mod 7",
        "states_a": len(a),
        "states_b": len(b),
        "matched": len(mapping),
        "unmatched": unmatched,
        "bijection": len(mapping) == len(a) == len(b) and not unmatched,
        "mapping": mapping,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print(json.dumps(status, sort_keys=True))
    if not status["bijection"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
