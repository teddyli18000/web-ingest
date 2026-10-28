#!/usr/bin/env python3
"""Exact blocker-budget repair driver for BPZ t=9 one-hit translations.

For a one-hit translated 367-set S, let x be the unique obstruction point and
pre-delete x.  A k-for-k repair is then equivalent to choosing k new vertices
outside S and the obstruction that are pairwise nonconfusable and whose union
of blockers against S\{x} has size at most k-1.  The c7-five exchange_dfs.cpp
solver searches exactly this problem: with radius r it selects r+1 compatible
candidates using at most r blockers.

This driver regenerates the 20 public one-hit states exactly, exports one case
to exchange_dfs's bitset format, runs the pinned solver, replays any witness,
and materializes the corresponding 134770-point BPZ certificate.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f


def one_hit_cases(I0, X0, ring, digits, nbmask, family_root):
    obs = f.obstruction_witnesses(I0, ring, digits, nbmask)
    fam = json.loads((family_root / "data" / "family-f.json").read_text())
    states = [set(map(int, s)) for s in fam["states"]]
    seeds = [("bpz-X", X0), ("bpz-I0", I0)] + [
        (f"family-f-{i}", s) for i, s in enumerate(states)
    ]
    obs_items = list(obs.items())
    Fobs = [(m, w, np.fft.fftn(f.arr(f.values(m), digits))) for m, w in obs_items]
    seen = set()
    out = []
    for name, S in seeds:
        if len(S) != f.N or not f.independent(S, digits):
            raise RuntimeError(f"seed {name} invalid")
        FS = np.fft.fftn(f.arr(S, digits))
        for oi, (mask, witness, FD) in enumerate(Fobs):
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            if int(corr.min()) != 1:
                continue
            Dset = set(f.values(mask))
            for idx in np.argwhere(corr == 1):
                t = tuple(int(z) for z in idx)
                for sign in (1, -1):
                    Sset = set(f.shift_set(S, t, digits, sign))
                    hits = Sset & Dset
                    if len(hits) != 1:
                        continue
                    key = (name, oi, tuple(sorted(Sset)))
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({
                        "seed": name,
                        "obstruction_index": oi,
                        "translation": t,
                        "translation_sign": sign,
                        "S": Sset,
                        "bad": next(iter(hits)),
                        "D": Dset,
                        "witness": witness,
                    })
    if len(out) != 20:
        raise RuntimeError(f"one-hit case drift: {len(out)} != 20")
    return out


def export_input(path, S, bad, Dset, ring, budget):
    retained = sorted(S - {bad})
    old_index = {v: i for i, v in enumerate(retained)}
    blockers = {}
    candidates = []
    for y in range(f.U):
        if y in S or y in Dset:
            continue
        b = 0
        for z in ring.NB[y]:
            i = old_index.get(z)
            if i is not None:
                b |= 1 << i
        if b.bit_count() <= budget:
            blockers[y] = b
            candidates.append(y)
    candidates.sort(key=lambda y: (blockers[y].bit_count(), y))
    pi = {v: i for i, v in enumerate(candidates)}
    n = len(candidates)
    cw = (n + 63) // 64
    bw = (len(retained) + 63) // 64
    if bw != 6:
        raise RuntimeError(f"blocker word drift {bw}")
    full = (1 << n) - 1
    mask64 = (1 << 64) - 1
    with path.open("w", encoding="ascii") as h:
        h.write(f"{n} {bw} {budget}\n")
        for v in candidates:
            incompatible = 0
            for z in ring.NB[v]:
                j = pi.get(z)
                if j is not None:
                    incompatible |= 1 << j
            compatible = full ^ incompatible
            vals = [(blockers[v] >> (64 * j)) & mask64 for j in range(bw)]
            vals += [(compatible >> (64 * j)) & mask64 for j in range(cw)]
            h.write(" ".join(f"{q:x}" for q in vals) + "\n")
    return retained, candidates, blockers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("family_root", type=Path)
    ap.add_argument("solver", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--case", type=int, required=True)
    ap.add_argument("--budget", type=int, default=4)
    ap.add_argument("--cutoff", type=int, default=540)
    args = ap.parse_args()
    if not 0 <= args.case < 20:
        raise SystemExit("case must be 0..19")
    if not 1 <= args.budget <= 8:
        raise SystemExit("budget must be 1..8")

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring

    raw = json.loads((args.tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    X0 = set(map(int, raw["X"]))
    ring = Ring(f.D)
    digits = tuple(ring.decode(v) for v in range(f.U))
    nbmask = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    cases = one_hit_cases(I0, X0, ring, digits, nbmask, args.family_root)
    c = cases[args.case]
    S, bad, Dset = c["S"], c["bad"], c["D"]

    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "exchange.txt"
        retained, candidates, blockers = export_input(inp, S, bad, Dset, ring, args.budget)
        with inp.open("rb") as src:
            p = subprocess.run(
                [str(args.solver), str(args.cutoff), "--budget-bitsets"],
                stdin=src, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                check=False, text=True,
            )
    if p.returncode != 0:
        raise RuntimeError(f"exchange_dfs failed rc={p.returncode}: {p.stderr[-2000:]}")
    lines = [z for z in p.stdout.splitlines() if z.strip()]
    if not lines:
        raise RuntimeError("exchange_dfs produced no JSON")
    search = json.loads(lines[-1])
    target_additions = args.budget + 1
    status = {
        "method": "bpz-t9-one-hit-c7-five-blocker-budget-exchange-dfs",
        "case_index": args.case,
        "seed": c["seed"],
        "obstruction_index": c["obstruction_index"],
        "translation": list(c["translation"]),
        "translation_sign": c["translation_sign"],
        "bad": bad,
        "budget": args.budget,
        "target_additions": target_additions,
        "candidate_vertices": len(candidates),
        "search": search,
        "solver_stderr_tail": p.stderr[-2000:],
        "candidate": search.get("status") == "witness",
        "complete": search.get("status") in ("witness", "exhausted"),
        "family_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
        "exchange_solver_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if not status["candidate"]:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print(search.get("status", "UNKNOWN").upper(), json.dumps(status, sort_keys=True), flush=True)
        return

    chosen = [int(i) for i in search.get("chosen", [])]
    if len(chosen) != target_additions or any(not 0 <= i < len(candidates) for i in chosen):
        raise RuntimeError(f"bad solver witness {chosen}")
    add = [candidates[i] for i in chosen]
    owner_ids = set()
    for y in add:
        b = blockers[y]
        while b:
            q = b & -b
            owner_ids.add(retained[q.bit_length() - 1])
            b ^= q
    if len(owner_ids) > args.budget:
        raise RuntimeError("witness blocker budget replay failed")
    rem = {bad} | owner_ids
    for q in retained:
        if len(rem) == target_additions:
            break
        if q not in rem:
            rem.add(q)
    if len(rem) != target_additions:
        raise RuntimeError("could not pad removal set")
    repaired = (S - rem) | set(add)
    if len(repaired) != f.N or repaired & Dset or not f.independent(repaired, digits):
        raise RuntimeError("exchange witness exact replay failed")

    Ibits, pairs, orient, PH, PV = c["witness"]
    points, xp = f.build(Ibits, sum(1 << q for q in repaired), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    status.update({
        "score": len(points),
        "removed_auxiliary_points": sorted(rem),
        "added_auxiliary_points": add,
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
