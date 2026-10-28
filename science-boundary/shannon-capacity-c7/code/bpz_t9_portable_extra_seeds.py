#!/usr/bin/env python3
"""Scan additional portable c7-five 367-word witnesses against BPZ t=9.

The original public-seed scan used BPZ I0/X and the 36 Family-F states.  The
portable c7-five verification bundle contains further explicit 367-word sets:
- two parents plus one witness in data/core-overlap.json.gz;
- the U1 witness exposed by verify/u1.py;
- every 367-word independent-set object exposed by verify/u2.py.

This program executes the pinned portable U1/U2 checkers (without -O), extracts
all explicit 367-sets from their globals, verifies each again under the common
C7^5 model, removes exact duplicates of the original 38 seeds, and scans every
translation against all 160 BPZ t=9 obstruction masks by exact-rounded FFT.
Any FFT zero is replayed combinatorially before a 134770 certificate is emitted.
"""
import argparse
import gzip
import json
import runpy
import sys
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f


def native_encode_word(w):
    # c7-five portable checkers use most-significant-coordinate-first encoding.
    return sum(int(x) * 7 ** (4 - i) for i, x in enumerate(w))


def normalize_set(obj):
    if not isinstance(obj, (list, tuple, set, frozenset)) or len(obj) != f.N:
        return None
    out = []
    try:
        for z in obj:
            if isinstance(z, int):
                v = z
            elif isinstance(z, (list, tuple)) and len(z) == f.D:
                if any(not isinstance(x, int) or not 0 <= x < 7 for x in z):
                    return None
                v = native_encode_word(z)
            else:
                return None
            if not 0 <= v < f.U:
                return None
            out.append(v)
    except Exception:
        return None
    if len(set(out)) != f.N:
        return None
    return set(out)


def module_witnesses(path):
    ns = runpy.run_path(str(path), run_name="__portable_witness_probe__")
    found = []
    for name, obj in ns.items():
        S = normalize_set(obj)
        if S is not None:
            found.append((name, S))
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("c7five_root", type=Path)
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

    family = json.loads((args.c7five_root / "data" / "family-f.json").read_text())
    original = [("bpz-X", X0), ("bpz-I0", I0)] + [
        (f"family-f-{i}", set(map(int, s))) for i, s in enumerate(family["states"])
    ]
    original_keys = {tuple(sorted(S)) for _, S in original}

    candidates = []
    core_path = args.c7five_root / "data" / "core-overlap.json.gz"
    with gzip.open(core_path, "rt") as h:
        bundle = json.load(h)
    parents = bundle["parents"]
    if len(parents) != 2:
        raise RuntimeError(f"core-overlap parent drift: {len(parents)}")
    candidates.extend((f"core-overlap-parent-{i}", set(map(int, p))) for i, p in enumerate(parents))
    candidates.append(("core-overlap-witness", set(map(int, bundle["witness"]))))

    for checker in ("u1.py", "u2.py"):
        path = args.c7five_root / "verify" / checker
        for name, S in module_witnesses(path):
            candidates.append((f"{checker[:-3]}:{name}", S))

    # Validate, exact-deduplicate, and distinguish genuinely new exact sets.
    all_seen = set(original_keys)
    seeds = []
    duplicates = []
    invalid = []
    for name, S in candidates:
        key = tuple(sorted(S))
        if len(S) != f.N or not f.independent(S, digits):
            invalid.append(name)
            continue
        if key in all_seen:
            duplicates.append(name)
            continue
        all_seen.add(key)
        seeds.append((name, S))
    if invalid:
        raise RuntimeError(f"portable candidate independence drift: {invalid}")
    if not seeds:
        raise RuntimeError("no new portable 367-set seeds found")

    obs_items = list(obs.items())
    Fobs = [(mask, w, np.fft.fftn(f.arr(f.values(mask), digits))) for mask, w in obs_items]
    cases = zero_fft = replays = 0
    hist = {}
    per_seed = []
    best = None
    winner = None
    min1_states = []

    for name, S in seeds:
        FS = np.fft.fftn(f.arr(S, digits))
        seed_best = 10**9
        seed_hist = {}
        for oi, (mask, w, FD) in enumerate(Fobs):
            cases += 1
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            mn = int(corr.min())
            seed_best = min(seed_best, mn)
            seed_hist[str(mn)] = seed_hist.get(str(mn), 0) + 1
            hist[str(mn)] = hist.get(str(mn), 0) + 1
            rec = {"seed": name, "obstruction_index": oi, "min_hits": mn}
            if best is None or mn < best["min_hits"]:
                best = rec
            if mn == 1:
                for idx in np.argwhere(corr == 1):
                    t = tuple(int(z) for z in idx)
                    # Store only exact one-hit replays, deduped later by set key.
                    for sign in (1, -1):
                        Xset = set(f.shift_set(S, t, digits, sign))
                        hits = Xset & set(f.values(mask))
                        if len(hits) == 1:
                            min1_states.append({
                                "seed": name, "obstruction_index": oi,
                                "translation": list(t), "translation_sign": sign,
                                "bad": next(iter(hits)),
                            })
            if mn != 0:
                continue
            Dset = set(f.values(mask))
            for idx in np.argwhere(corr == 0):
                zero_fft += 1
                t = tuple(int(z) for z in idx)
                for sign in (1, -1):
                    replays += 1
                    Xset = set(f.shift_set(S, t, digits, sign))
                    if len(Xset) != f.N or not f.independent(Xset, digits):
                        raise RuntimeError("portable translated seed independence replay failed")
                    if Xset & Dset:
                        continue
                    winner = (name, t, sign, Xset, w, oi)
                    break
                if winner:
                    break
            if winner:
                break
        per_seed.append({"seed": name, "min_hits": seed_best, "histogram": seed_hist})
        print("SEED_DONE", json.dumps(per_seed[-1], sort_keys=True), flush=True)
        if winner:
            break

    status = {
        "method": "bpz-t9-portable-extra-c7five-seeds-all-translations-FFT",
        "candidate": winner is not None,
        "original_seed_count": len(original),
        "portable_candidates_seen": len(candidates),
        "exact_duplicates": duplicates,
        "new_seed_count": len(seeds),
        "new_seed_names": [name for name, _ in seeds],
        "obstruction_masks": len(obs_items),
        "seed_obstruction_cases": cases,
        "fft_zero_shifts_examined": zero_fft,
        "explicit_zero_replays": replays,
        "best": best,
        "min_hit_histogram": hist,
        "per_seed": per_seed,
        "one_hit_replay_records": len(min1_states),
        "one_hit_examples": min1_states[:100],
        "c7five_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    name, t, sign, X, w, oi = winner
    Ibits, pairs, orient, PH, PV = w
    pts, xp = f.build(Ibits, sum(1 << z for z in X), pairs, PH, PV, ring)
    status.update({
        "score": len(pts),
        "winning_seed": name,
        "winning_obstruction_index": oi,
        "winning_translation": list(t),
        "translation_sign": sign,
        "private_pairs": [list(z) for z in pairs],
        "orientation": list(orient),
        "PH": PH,
        "PV": PV,
        "X_partition": {"X0": xp[0], "XH": xp[1], "XV": xp[2]},
    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"points": pts}, separators=(",", ":")) + "\n")
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
    print("FOUND", json.dumps(status, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
