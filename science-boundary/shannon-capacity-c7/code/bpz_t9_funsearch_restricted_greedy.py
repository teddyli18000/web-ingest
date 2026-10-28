#!/usr/bin/env python3
"""Grow FunSearch-priority independent sets directly inside C7^5 \ D.

Unlike bpz_t9_funsearch_fft.py, which constructs the public 367-set first and
then translates that frozen set against each t=9 obstruction, this search makes
the obstruction part of the greedy construction.  For each exact BPZ t=9 mask
D, vertices of D are forbidden from the start; the public FunSearch priority
then greedily grows a fresh maximal independent set in the remaining graph.

A size >=367 set immediately supplies the auxiliary X needed for the nominal
134770-point t=9 C7^10 construction.  Every such candidate is replayed before
materialization and is intended to be passed to the Few Shots verifier.
"""

import argparse
import json
import sys
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpz_t9_aux_translation_fft as f
from bpz_t9_funsearch_fft import priority10

TARGET_AUX = 367
BASELINE = 134753


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
    nbmask = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    obs = f.obstruction_witnesses(I0, ring, digits, nbmask)
    if len(obs) != 160:
        raise RuntimeError(f"obstruction count drift: {len(obs)}")

    # Exactly match the public FunSearch priority and np.argmax tie order:
    # itertools.product gives the big-endian flattened order used in the
    # notebook, and stable sorting preserves that order on ties.
    words = list(product(range(f.Q), repeat=f.D))
    ranked_words = sorted(
        enumerate(words), key=lambda z: (-priority10(z[1]), z[0])
    )
    order = [f.enc(w) for _, w in ranked_words]
    if len(order) != f.U or len(set(order)) != f.U:
        raise RuntimeError("priority order drift")

    size_hist: dict[str, int] = {}
    best_size = -1
    best_index = None
    best_set: list[int] | None = None
    winner = None

    for oi, (mask, witness) in enumerate(obs.items()):
        Dset = set(f.values(mask))
        forbidden = bytearray(f.U)
        for v in Dset:
            forbidden[v] = 1
        blocked = bytearray(f.U)
        chosen: list[int] = []
        for v in order:
            if forbidden[v] or blocked[v]:
                continue
            chosen.append(v)
            for u in ring.NB[v]:
                blocked[u] = 1

        if not f.independent(chosen, digits):
            raise RuntimeError(f"greedy replay failed for obstruction {oi}")
        if set(chosen) & Dset:
            raise RuntimeError(f"obstruction replay failed for obstruction {oi}")

        n = len(chosen)
        size_hist[str(n)] = size_hist.get(str(n), 0) + 1
        if n > best_size:
            best_size = n
            best_index = oi
            best_set = chosen

        if n < TARGET_AUX:
            continue

        X = set(chosen[:TARGET_AUX])
        if len(X) != TARGET_AUX or X & Dset or not f.independent(X, digits):
            raise RuntimeError("winning auxiliary replay failed")
        winner = (oi, X, witness, n, len(Dset))
        break

    status = {
        "method": "bpz-t9-funsearch-priority-restricted-greedy",
        "candidate": winner is not None,
        "score": BASELINE if winner is None else 134770,
        "obstruction_masks_scanned": len(obs) if winner is None else winner[0] + 1,
        "size_histogram": {k: size_hist[k] for k in sorted(size_hist, key=int)},
        "best_auxiliary_size": best_size,
        "best_obstruction_index": best_index,
        "best_prefix": best_set[:20] if best_set is not None else [],
        "source_priority": "google-deepmind/funsearch/cyclic_graphs/cyclic_graphs.ipynb",
        "source_commit": "b02fdbfeb1e138ff3fd74592439e645a3a11de69",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    oi, X, witness, raw_size, obstruction_size = winner
    Ibits, pairs, orientation, PH, PV = witness
    points, xp = f.build(Ibits, sum(1 << z for z in X), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    status.update({
        "score": len(points),
        "winning_obstruction_index": oi,
        "raw_greedy_size": raw_size,
        "obstruction_size": obstruction_size,
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
