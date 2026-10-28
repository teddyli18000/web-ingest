#!/usr/bin/env python3
"""Scan the frozen U2-derived 11-private-owner parent for a C7^10 breakthrough.

For the frozen 367-point parent I with 11 distinct private pairs, every valid
orientation gives a t=11 BPZ/Gao-style construction.  With an auxiliary
independent set X of size 367-h after deleting h obstruction hits, the score is

    (367-11)^2 + 2*11*(367-h) = 134810 - 22h.

Thus h <= 2 is already a Few Shots p004 breakthrough (h=2 gives 134766).
We enumerate all 2^11 orientations, deduplicate exact obstruction masks, and
scan translations of several public 367-point C7^5 basins by exact-rounded FFT.
Every promising FFT shift is replayed combinatorially before emitting a 10D
certificate; the workflow then invokes the upstream Few Shots verifier.
"""
import argparse
import json
import runpy
import sys
from itertools import product
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t10_aux_translation_fft as base
from bpz_t9_funsearch_fft import funsearch_seed

T = 11
N = 367
BASELINE = 134753
TARGET_FULL = (N - T) ** 2 + 2 * T * N


def extract_367(ns, digits):
    out = []
    for name, v in ns.items():
        if name.startswith("__"):
            continue
        try:
            if len(v) != 367:
                continue
        except Exception:
            continue
        try:
            words = []
            for w in v:
                if not isinstance(w, (tuple, list)) or len(w) != 5:
                    raise ValueError
                q = tuple(int(x) for x in w)
                if any(not 0 <= x < 7 for x in q):
                    raise ValueError
                words.append(base.enc(q))
            S = frozenset(words)
            if len(S) == 367 and base.independent(S, digits):
                out.append((name, set(S)))
        except Exception:
            pass
    uniq = {}
    for name, S in out:
        uniq.setdefault(frozenset(S), name)
    return [(name, set(S)) for S, name in uniq.items()]


def validate_parent(parent, pairs, ring, digits):
    I = set(parent)
    if len(I) != 367 or not base.independent(I, digits):
        raise RuntimeError("frozen t11 parent is not a 367-point independent set")
    owners = [a for a, q in pairs]
    if len(pairs) != 11 or len(set(owners)) != 11:
        raise RuntimeError("private-pair owner count drift")
    for a, q in pairs:
        if a not in I or q in I:
            raise RuntimeError(f"bad private pair {(a,q)}")
        hits = [z for z in I if q in ring.NB[z]]
        if hits != [a]:
            raise RuntimeError(f"private-pair replay failed {(a,q)} hits={hits}")


def obstruction_witnesses(parent, pairs, ring, digits):
    Ibits = sum(1 << z for z in parent)
    obs = {}
    raw_valid = 0
    hist = {}
    for orient in product((0, 1), repeat=T):
        PH = [q if s else a for (a, q), s in zip(pairs, orient)]
        PV = [a if s else q for (a, q), s in zip(pairs, orient)]
        if not base.independent(PH, digits) or not base.independent(PV, digits):
            continue
        raw_valid += 1
        Dset = ring.nbhd(set(PH)) & ring.nbhd(set(PV))
        mask = sum(1 << z for z in Dset)
        obs.setdefault(mask, (Ibits, tuple(tuple(p) for p in pairs), orient, PH, PV))
    for mask in obs:
        k = mask.bit_count()
        hist[str(k)] = hist.get(str(k), 0) + 1
    return obs, {
        "raw_valid_orientations": raw_valid,
        "distinct_obstructions": len(obs),
        "obstruction_sizes": hist,
    }


def build(Ibits, X, pairs, PH, PV, ring):
    I = set(base.values(Ibits))
    R = {a for a, q in pairs}
    if len(R) != T:
        raise RuntimeError("R size drift")
    B = I - R
    NH = ring.nbhd(set(PH)); NV = ring.nbhd(set(PV))
    if X & NH & NV:
        raise RuntimeError("auxiliary still intersects t11 obstruction")
    X0 = X - (NH | NV); XH = X & NH; XV = X & NV
    P = set()
    for A, C in (
        (B, B), (R, X0), (set(PH), XH), (set(PV), XV),
        (X0, R), (XH, set(PV)), (XV, set(PH)),
    ):
        for a in A:
            for c in C:
                P.add((a, c))
    expected = (N - T) ** 2 + 2 * T * len(X)
    if len(P) != expected:
        raise RuntimeError(f"10D score drift {len(P)} != {expected}")
    points = sorted("".join(map(str, ring.decode(a) + ring.decode(c))) for a, c in P)
    return points, (len(X0), len(XH), len(XV))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("c7five_root", type=Path)
    ap.add_argument("parent_json", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring  # type: ignore

    ring = Ring(base.D)
    digits = tuple(ring.decode(v) for v in range(base.U))
    frozen = json.loads(args.parent_json.read_text())
    parent = set(map(int, frozen["points"]))
    pairs = [tuple(map(int, p)) for p in frozen["private_pairs"]]
    validate_parent(parent, pairs, ring, digits)
    obs, ostats = obstruction_witnesses(parent, pairs, ring, digits)
    print("T11_OBSTRUCTIONS", json.dumps(ostats, sort_keys=True), flush=True)
    if not obs:
        raise RuntimeError("no valid t11 orientations")

    raw = json.loads((args.tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"])); X0 = set(map(int, raw["X"]))
    fam = json.loads((args.c7five_root / "data" / "family-f.json").read_text())
    seeds = [("bpz-X", X0), ("bpz-I0", I0), ("t11-parent", parent)]
    seeds += [(f"family-f-{i}", set(map(int, s))) for i, s in enumerate(fam["states"])]
    for fn, label in (("u1.py", "u1"), ("u2.py", "u2")):
        ns = runpy.run_path(str(args.c7five_root / "verify" / fn))
        seeds += [(f"{label}:{name}", S) for name, S in extract_367(ns, digits)]
    seeds.append(("funsearch", set(funsearch_seed(digits))))
    dedup = {}
    for name, S in seeds:
        if len(S) != 367 or not base.independent(S, digits):
            raise RuntimeError(f"invalid seed {name}")
        dedup.setdefault(frozenset(S), name)
    seeds = [(name, set(S)) for S, name in dedup.items()]
    print("SEEDS", json.dumps({"count": len(seeds), "names": [n for n,_ in seeds]}, sort_keys=True), flush=True)

    Fobs = [(mask, w, np.fft.fftn(base.arr(base.values(mask), digits))) for mask, w in obs.items()]
    best = None; hist = {}; cases = 0; winner = None
    for name, S in seeds:
        FS = np.fft.fftn(base.arr(S, digits))
        sbest = 999
        for oi, (mask, witness, FD) in enumerate(Fobs):
            cases += 1
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            mn = int(corr.min()); sbest = min(sbest, mn)
            hist[str(mn)] = hist.get(str(mn), 0) + 1
            rec = {"seed": name, "obstruction_index": oi, "min_hits": mn, "obstruction_size": mask.bit_count()}
            if best is None or mn < best["min_hits"]:
                best = rec
                print("NEW_BEST", json.dumps(best, sort_keys=True), flush=True)
            if mn > 2:
                continue
            Dset = set(base.values(mask))
            for idx in np.argwhere(corr <= 2):
                hfft = int(corr[tuple(idx)])
                if hfft > 2:
                    continue
                tr = tuple(int(z) for z in idx)
                for sign in (1, -1):
                    Xfull = set(base.shift_set(S, tr, digits, sign))
                    if len(Xfull) != 367 or not base.independent(Xfull, digits):
                        raise RuntimeError("translated seed replay failed")
                    hits = Xfull & Dset
                    if len(hits) > 2:
                        continue
                    X = Xfull - Dset
                    score = (N - T) ** 2 + 2 * T * len(X)
                    if score <= BASELINE:
                        continue
                    winner = (name, oi, tr, sign, X, hits, witness, score, mask)
                    break
                if winner:
                    break
            if winner:
                break
        print("SEED_DONE", json.dumps({"seed": name, "best_hits": sbest}, sort_keys=True), flush=True)
        if winner:
            break

    status = {
        "method": "u2-depth2-t11-all-orientations-public367-all-translations",
        "candidate": winner is not None,
        "score": BASELINE if winner is None else winner[7],
        "full_score": TARGET_FULL,
        "t": T,
        "parent_source": frozen.get("source"),
        "parent_depth": frozen.get("depth"),
        "obstruction_stats": ostats,
        "seed_count": len(seeds),
        "seed_obstruction_cases": cases,
        "best": best,
        "min_hit_histogram": hist,
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)
    if winner is None:
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    name, oi, tr, sign, X, hits, witness, score, mask = winner
    Ibits, wpairs, orient, PH, PV = witness
    points, xp = build(Ibits, X, wpairs, PH, PV, ring)
    if len(points) != score or score <= BASELINE:
        raise RuntimeError(f"candidate replay score {len(points)} expected {score}")
    status.update({
        "score": score,
        "winning_seed": name,
        "winning_obstruction_index": oi,
        "winning_obstruction_size": mask.bit_count(),
        "winning_translation": list(tr),
        "translation_sign": sign,
        "deleted_auxiliary_hits": sorted(hits),
        "auxiliary_size": len(X),
        "private_pairs": [list(p) for p in wpairs],
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
