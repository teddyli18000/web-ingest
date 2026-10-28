#!/usr/bin/env python3
"""Exact blocker-budget repairs for one-hit states in the FunSearch signed orbit.

The DeepMind FunSearch C7^5 367-set has 768 distinct signed-coordinate images.
For each selected image and every exact BPZ t=9 obstruction, FFT correlation
finds all translations meeting the obstruction in exactly one point.  After
pre-deleting that bad point, a budget-r repair asks for r+1 pairwise-compatible
new vertices whose union of blockers against the retained 366-set has size at
most r.  This is exactly the input accepted by the pinned c7-five
exchange_dfs.cpp solver.

The signed images are sharded before the FFT work, so independent Actions can
cover the whole orbit without recomputing all 122,880 image/obstruction cases.
Every solver witness is replayed in C7^5 and then materialized as the nominal
134770-point BPZ t=9 C7^10 certificate.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from itertools import permutations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bpz_t9_aux_translation_fft as f
import bpz_t9_exchange_repair as ex
from bpz_t9_funsearch_fft import FUNSEARCH_COMMIT, funsearch_seed


def distinct_signed_images(seed, digits):
    images = {}
    for perm in permutations(range(f.D)):
        for negmask in range(1 << f.D):
            S = frozenset(
                f.enc(
                    tuple(
                        ((-digits[v][perm[j]]) % f.Q)
                        if ((negmask >> j) & 1)
                        else digits[v][perm[j]]
                        for j in range(f.D)
                    )
                )
                for v in seed
            )
            if len(S) != f.N or not f.independent(S, digits):
                raise RuntimeError("signed image invalid")
            images.setdefault(S, (perm, negmask))
    if len(images) != 768:
        raise RuntimeError(f"signed orbit drift: {len(images)} != 768")
    return list(images.items())


def run_case(solver, cutoff, budget, S, bad, Dset, ring):
    with tempfile.TemporaryDirectory() as td:
        inp = Path(td) / "exchange.txt"
        retained, candidates, blockers = ex.export_input(inp, S, bad, Dset, ring, budget)
        with inp.open("rb") as src:
            p = subprocess.run(
                [str(solver), str(cutoff), "--budget-bitsets"],
                stdin=src,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
    if p.returncode != 0:
        raise RuntimeError(f"exchange_dfs failed rc={p.returncode}: {p.stderr[-2000:]}")
    lines = [z for z in p.stdout.splitlines() if z.strip()]
    if not lines:
        raise RuntimeError("exchange_dfs produced no JSON")
    search = json.loads(lines[-1])
    return retained, candidates, blockers, search, p.stderr[-1000:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("solver", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("status", type=Path)
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--shards", type=int, default=16)
    ap.add_argument("--budget", type=int, default=4)
    ap.add_argument("--cutoff", type=int, default=240)
    args = ap.parse_args()
    if not 0 <= args.shard < args.shards:
        raise SystemExit("bad shard")
    if not 1 <= args.budget <= 8:
        raise SystemExit("budget must be 1..8")

    sys.path.insert(0, str(args.tan_root.resolve()))
    from shannon.certificates import Ring

    raw = json.loads((args.tan_root / "data" / "base_c7.json").read_text())
    I0 = set(map(int, raw["I0"]))
    ring = Ring(f.D)
    digits = tuple(ring.decode(v) for v in range(f.U))
    nb = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    obs = list(f.obstruction_witnesses(I0, ring, digits, nb).items())
    Fobs = [(mask, witness, np.fft.fftn(f.arr(f.values(mask), digits))) for mask, witness in obs]
    seed = funsearch_seed(digits)
    images = distinct_signed_images(seed, digits)

    image_count = fft_cases = min1_cases = min1_shifts = exact_replays = unique_states = 0
    searched = exhausted = cutoffs = 0
    candidate_vertices_max = 0
    seen = set()
    case_summaries = []
    winner = None

    for ii, (Sfro, meta) in enumerate(images):
        if ii % args.shards != args.shard:
            continue
        image_count += 1
        perm, negmask = meta
        S0 = set(Sfro)
        FS = np.fft.fftn(f.arr(S0, digits))
        for oi, (mask, witness, FD) in enumerate(Fobs):
            fft_cases += 1
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            if int(corr.min()) != 1:
                continue
            min1_cases += 1
            Dset = set(f.values(mask))
            for idx in np.argwhere(corr == 1):
                min1_shifts += 1
                t = tuple(int(z) for z in idx)
                # Sign reversals are already part of the signed image.
                S = set(f.shift_set(S0, t, digits, 1))
                hits = S & Dset
                if len(S) != f.N or not f.independent(S, digits):
                    raise RuntimeError("translated signed image replay failed")
                if len(hits) != 1:
                    continue
                exact_replays += 1
                key = (oi, tuple(sorted(S)))
                if key in seen:
                    continue
                seen.add(key)
                unique_states += 1
                bad = next(iter(hits))
                retained, candidates, blockers, search, stderr_tail = run_case(
                    args.solver, args.cutoff, args.budget, S, bad, Dset, ring
                )
                searched += 1
                candidate_vertices_max = max(candidate_vertices_max, len(candidates))
                st = search.get("status")
                if st == "exhausted":
                    exhausted += 1
                elif st == "cutoff":
                    cutoffs += 1
                rec = {
                    "image": ii,
                    "perm": list(perm),
                    "negmask": negmask,
                    "obstruction_index": oi,
                    "translation": list(t),
                    "bad": bad,
                    "candidate_vertices": len(candidates),
                    "search_status": st,
                    "search": search,
                }
                case_summaries.append(rec)
                print("CASE", json.dumps(rec, sort_keys=True), flush=True)
                if st != "witness":
                    continue

                chosen = [int(z) for z in search.get("chosen", [])]
                target = args.budget + 1
                if len(chosen) != target or any(not 0 <= z < len(candidates) for z in chosen):
                    raise RuntimeError(f"bad solver witness {chosen}")
                add = [candidates[z] for z in chosen]
                owner_ids = set()
                for y in add:
                    b = blockers[y]
                    while b:
                        q = b & -b
                        owner_ids.add(retained[q.bit_length() - 1])
                        b ^= q
                if len(owner_ids) > args.budget:
                    raise RuntimeError("blocker budget replay failed")
                rem = {bad} | owner_ids
                for q in retained:
                    if len(rem) == target:
                        break
                    if q not in rem:
                        rem.add(q)
                if len(rem) != target:
                    raise RuntimeError("could not pad removal set")
                repaired = (S - rem) | set(add)
                if len(repaired) != f.N or repaired & Dset or not f.independent(repaired, digits):
                    raise RuntimeError("repair exact replay failed")
                winner = {
                    "image": ii,
                    "perm": list(perm),
                    "negmask": negmask,
                    "obstruction_index": oi,
                    "translation": list(t),
                    "bad": bad,
                    "removed": sorted(rem),
                    "added": add,
                    "repaired": repaired,
                    "witness": witness,
                    "search": search,
                    "solver_stderr_tail": stderr_tail,
                }
                break
            if winner:
                break
        if winner:
            break

    status = {
        "method": "bpz-t9-funsearch-signed-onehit-blocker-budget-exchange-dfs",
        "candidate": winner is not None,
        "score": 134753 if winner is None else 134770,
        "shard": args.shard,
        "shards": args.shards,
        "budget": args.budget,
        "target_additions": args.budget + 1,
        "cutoff": args.cutoff,
        "distinct_signed_images_total": len(images),
        "images_scanned": image_count,
        "image_obstruction_cases": fft_cases,
        "min1_image_obstruction_cases": min1_cases,
        "fft_min1_shifts": min1_shifts,
        "exact_min1_replays": exact_replays,
        "unique_onehit_states": unique_states,
        "searched_states": searched,
        "exhausted_states": exhausted,
        "cutoff_states": cutoffs,
        "complete": winner is not None or (searched == exhausted and cutoffs == 0),
        "max_candidate_vertices": candidate_vertices_max,
        "case_summaries": case_summaries,
        "funsearch_source_commit": FUNSEARCH_COMMIT,
        "exchange_solver_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    Ibits, pairs, orient, PH, PV = winner["witness"]
    points, xp = f.build(Ibits, sum(1 << q for q in winner["repaired"]), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    status.update({
        "score": len(points),
        "winning_image": winner["image"],
        "winning_perm": winner["perm"],
        "winning_negmask": winner["negmask"],
        "winning_obstruction_index": winner["obstruction_index"],
        "winning_translation": winner["translation"],
        "removed_auxiliary_points": winner["removed"],
        "added_auxiliary_points": winner["added"],
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
