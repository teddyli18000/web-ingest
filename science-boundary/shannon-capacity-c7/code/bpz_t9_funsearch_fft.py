#!/usr/bin/env python3
"""Scan DeepMind FunSearch's public 367-set in C7^5 against BPZ t=9 obstructions.

The seed is reconstructed deterministically from the priority function published
in google-deepmind/funsearch, cyclic_graphs/cyclic_graphs.ipynb, pinned at
b02fdbfeb1e138ff3fd74592439e645a3a11de69.  The notebook's floating-point
priority has coefficients in tenths, so we multiply the score by ten and use
integer arithmetic.  Repeated ``np.argmax`` with blocking is equivalent to
sorting the static priorities descending and breaking ties by the notebook's
lexicographic flattened vertex index, then greedily accepting unblocked words.

For each of the 160 exact BPZ t=9 obstruction masks we evaluate every 7^5
translation of the FunSearch seed via exact-rounded FFT correlation.  Any FFT
zero is replayed combinatorially before materializing a 134770-point C7^10
certificate for the Few Shots verifier.
"""
import argparse
import json
import sys
from itertools import product
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f

FUNSEARCH_COMMIT = "b02fdbfeb1e138ff3fd74592439e645a3a11de69"


def priority10(el: tuple[int, ...], num_nodes: int = 7, n: int = 5) -> int:
    """Ten times the exact public FunSearch priority for C7^5."""
    score = 0
    for i in range(n):
        score += 10 if el[i] == el[(i + 2) % n] else -10
        x = (
            (n - 2) * el[i]
            - el[(i + 1) % n]
            - el[(i + 2) % n]
            - (n + 1) * el[(i + 3) % n]
        ) % num_nodes
        score -= 5 * (x - el[(i + 1) % n]) ** 2
        score += (num_nodes - 1 - (x - 1) % num_nodes) ** 2
        score += 2 * (num_nodes - 1 - (x - 2) % num_nodes) ** 2
    return score


def funsearch_seed(digits: tuple[tuple[int, ...], ...]) -> set[int]:
    # The notebook enumerates tuples with itertools.product(range(7), repeat=5),
    # i.e. lexicographic / big-endian flattened order.  Keep that tie order
    # explicitly, while converting accepted tuples to this workspace's enc().
    words = list(product(range(f.Q), repeat=f.D))
    ranked = sorted(
        enumerate(words),
        key=lambda z: (-priority10(z[1]), z[0]),
    )

    blocked: set[tuple[int, ...]] = set()
    accepted: list[tuple[int, ...]] = []
    deltas = tuple(product((-1, 0, 1), repeat=f.D))
    for _, w in ranked:
        if w in blocked:
            continue
        accepted.append(w)
        for d in deltas:
            blocked.add(tuple((w[k] + d[k]) % f.Q for k in range(f.D)))

    seed = {f.enc(w) for w in accepted}
    if len(accepted) != 367 or len(seed) != 367:
        raise RuntimeError(f"FunSearch reconstruction drift: accepted={len(accepted)} unique={len(seed)}")
    if not f.independent(seed, digits):
        raise RuntimeError("FunSearch reconstructed seed is not independent")
    return seed


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
    obs = f.obstruction_witnesses(I0, ring, digits, nb)
    seed = funsearch_seed(digits)

    FS = np.fft.fftn(f.arr(seed, digits))
    best = None
    hist: dict[str, int] = {}
    zero_fft = 0
    replays = 0
    winner = None
    one_hit_examples = []

    for oi, (mask, witness) in enumerate(obs.items()):
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
                one_hit_examples.append({
                    "obstruction_index": oi,
                    "translation": [int(z) for z in idx],
                })
        if mn != 0:
            continue

        for idx in np.argwhere(corr == 0):
            zero_fft += 1
            t = tuple(int(z) for z in idx)
            for sign in (1, -1):
                replays += 1
                X = set(f.shift_set(seed, t, digits, sign))
                if len(X) != 367 or not f.independent(X, digits):
                    raise RuntimeError("translated FunSearch seed replay failed")
                if X & Dset:
                    continue
                winner = (oi, t, sign, X, witness)
                break
            if winner:
                break
        if winner:
            break

    status = {
        "method": "bpz-t9-funsearch-c7-367-all-translations-fft",
        "candidate": winner is not None,
        "score": 134753 if winner is None else 134770,
        "seed_size": len(seed),
        "obstruction_masks_scanned": 160 if winner is None else winner[0] + 1,
        "best": best,
        "min_hit_histogram": hist,
        "one_hit_examples": one_hit_examples[:100],
        "fft_zero_shifts_examined": zero_fft,
        "explicit_replays": replays,
        "source": "google-deepmind/funsearch/cyclic_graphs/cyclic_graphs.ipynb",
        "source_commit": FUNSEARCH_COMMIT,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    oi, t, sign, X, witness = winner
    Ibits, pairs, orientation, PH, PV = witness
    points, xp = f.build(Ibits, sum(1 << z for z in X), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
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
