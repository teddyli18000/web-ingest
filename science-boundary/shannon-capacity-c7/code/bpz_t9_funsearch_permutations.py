#!/usr/bin/env python3
"""Scan all distinct coordinate-permutation images of FunSearch's C7^5 367-set.

Translations are scanned by FFT for every one of the 160 BPZ t=9 obstruction
masks.  The FunSearch seed has a 5-cycle coordinate stabilizer, so the 120
coordinate permutations collapse to 24 distinct images; this is checked rather
than assumed.  Any zero is replayed exactly and materialized as a 134770-point
C7^10 certificate.
"""
import argparse
import json
import sys
from itertools import permutations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_fft import FUNSEARCH_COMMIT, funsearch_seed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring  # type: ignore

    raw = json.loads((args.tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    ring = Ring(f.D)
    digits = tuple(ring.decode(v) for v in range(f.U))
    nb = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    obs = list(f.obstruction_witnesses(I0, ring, digits, nb).items())
    seed = funsearch_seed(digits)

    images: dict[frozenset[int], tuple[int, ...]] = {}
    for perm in permutations(range(f.D)):
        S = frozenset(f.enc(tuple(digits[v][perm[j]] for j in range(f.D))) for v in seed)
        if len(S) != 367 or not f.independent(S, digits):
            raise RuntimeError(f"coordinate image invalid: {perm}")
        images.setdefault(S, perm)
    if len(images) != 24:
        raise RuntimeError(f"FunSearch coordinate-orbit drift: expected 24 distinct, got {len(images)}")

    Fobs = [(mask, witness, np.fft.fftn(f.arr(f.values(mask), digits))) for mask, witness in obs]
    best = None
    hist: dict[str, int] = {}
    winner = None
    cases = 0
    per_image = []

    for ii, (Sfro, perm) in enumerate(images.items()):
        S = set(Sfro)
        FS = np.fft.fftn(f.arr(S, digits))
        image_best = 10**9
        for oi, (mask, witness, FD) in enumerate(Fobs):
            cases += 1
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            mn = int(corr.min())
            image_best = min(image_best, mn)
            hist[str(mn)] = hist.get(str(mn), 0) + 1
            rec = {"image": ii, "perm": list(perm), "obstruction_index": oi, "min_hits": mn}
            if best is None or mn < best["min_hits"]:
                best = rec
            if mn:
                continue
            Dset = set(f.values(mask))
            for idx in np.argwhere(corr == 0):
                t = tuple(int(z) for z in idx)
                for sign in (1, -1):
                    X = set(f.shift_set(S, t, digits, sign))
                    if len(X) != 367 or not f.independent(X, digits):
                        raise RuntimeError("permuted/translated FunSearch replay failed")
                    if X & Dset:
                        continue
                    winner = (ii, perm, oi, t, sign, X, witness)
                    break
                if winner:
                    break
            if winner:
                break
        per_image.append({"image": ii, "perm": list(perm), "min_hits": image_best})
        print("IMAGE_DONE", json.dumps(per_image[-1], sort_keys=True), flush=True)
        if winner:
            break

    status = {
        "method": "bpz-t9-funsearch-distinct-coordinate-permutations-all-translations-fft",
        "candidate": winner is not None,
        "score": 134753 if winner is None else 134770,
        "raw_coordinate_permutations": 120,
        "distinct_coordinate_images": len(images),
        "seed_obstruction_cases": cases,
        "best": best,
        "min_hit_histogram": hist,
        "per_image": per_image,
        "source_commit": FUNSEARCH_COMMIT,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    ii, perm, oi, t, sign, X, witness = winner
    Ibits, pairs, orientation, PH, PV = witness
    points, xp = f.build(Ibits, sum(1 << z for z in X), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"score drift {len(points)}")
    status.update({
        "score": len(points),
        "winning_image": ii,
        "winning_perm": list(perm),
        "winning_obstruction_index": oi,
        "winning_translation": list(t),
        "translation_sign": sign,
        "private_pairs": [list(z) for z in pairs],
        "orientation": list(orientation),
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
