#!/usr/bin/env python3
"""Scan c7-five's portable U1 367-witness against all BPZ t=9 obstructions.

The witness is loaded from the pinned standalone verifier ``verify/u1.py``
rather than copied.  That verifier independently checks the 367-word set and
its U1 certificate before this program converts it to the shared C7^5 encoding.
Every FFT zero is explicitly replayed before materializing a 134770-point 10D
certificate.
"""
import argparse
import json
import runpy
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f

C7FIVE_COMMIT = "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("c7five_root", type=Path)
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
    obs = f.obstruction_witnesses(I0, ring, digits, nb)

    env = runpy.run_path(str(args.c7five_root / "verify" / "u1.py"))
    witness_words = env["witness"]
    seed = {f.enc(tuple(w)) for w in witness_words}
    if len(seed) != 367 or not f.independent(seed, digits):
        raise RuntimeError("portable U1 witness replay failed")

    FS = np.fft.fftn(f.arr(seed, digits))
    best = None
    hist: dict[str, int] = {}
    winner = None
    zero_fft = 0
    replays = 0
    one_hit_examples = []

    for oi, (mask, w) in enumerate(obs.items()):
        Dset = set(f.values(mask))
        FD = np.fft.fftn(f.arr(Dset, digits))
        corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
        mn = int(corr.min())
        hist[str(mn)] = hist.get(str(mn), 0) + 1
        rec = {"obstruction_index": oi, "min_hits": mn}
        if best is None or mn < best["min_hits"]:
            best = rec
        if mn == 1:
            for idx in np.argwhere(corr == 1)[:20]:
                one_hit_examples.append({"obstruction_index": oi, "translation": [int(z) for z in idx]})
        if mn:
            continue
        for idx in np.argwhere(corr == 0):
            zero_fft += 1
            t = tuple(int(z) for z in idx)
            for sign in (1, -1):
                replays += 1
                X = set(f.shift_set(seed, t, digits, sign))
                if len(X) != 367 or not f.independent(X, digits):
                    raise RuntimeError("U1 translated witness independence replay failed")
                if X & Dset:
                    continue
                winner = (oi, t, sign, X, w)
                break
            if winner:
                break
        if winner:
            break

    status = {
        "method": "bpz-t9-c7-five-u1-witness-all-translations-fft",
        "candidate": winner is not None,
        "score": 134753 if winner is None else 134770,
        "seed_size": len(seed),
        "obstruction_masks_scanned": 160 if winner is None else winner[0] + 1,
        "best": best,
        "min_hit_histogram": hist,
        "one_hit_examples": one_hit_examples[:100],
        "fft_zero_shifts_examined": zero_fft,
        "explicit_replays": replays,
        "source": "molind/c7-five/verify/u1.py",
        "source_commit": C7FIVE_COMMIT,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    oi, t, sign, X, w = winner
    Ibits, pairs, orientation, PH, PV = w
    points, xp = f.build(Ibits, sum(1 << z for z in X), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"score drift {len(points)}")
    status.update({
        "score": len(points),
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
