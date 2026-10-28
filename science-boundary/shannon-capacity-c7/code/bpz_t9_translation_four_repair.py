#!/usr/bin/env python3
"""Exact next-radius repair of one-hit BPZ t=9 translated auxiliary sets.

The exact 1-, 2-, and 3-for-3 searches are already negative.  Hence any new
4-for-4 repair may be assumed to add four vertices outside the old 367-set:
if an added vertex were an old removed vertex, cancelling it would give a
smaller repair already covered by those exact searches.

For a one-hit state S with bad point x, a new vertex y can occur in a 4-repair
iff y avoids the obstruction and its conflict support N[y] cap S, together
with x, uses at most four old owners.  We DFS over four pairwise-compatible new
vertices while tracking the exact owner-union.  Whenever four are selected,
the owner-union is the necessary removal set; if it has fewer than four points
we may pad it with arbitrary old points, because by definition none of the
selected additions conflicts with a padded owner.  The repaired set is then
replayed exactly and, on success, materialized as the 134770-point BPZ t=9
certificate.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

import bpz_t9_aux_translation_fft as f


def bit_values(mask):
    while mask:
        b = mask & -mask
        yield b.bit_length() - 1
        mask ^= b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tan_root", type=Path)
    ap.add_argument("family_root", type=Path)
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
    nbmask = [sum(1 << z for z in ring.NB[v]) for v in range(f.U)]
    obs = f.obstruction_witnesses(I0, ring, digits, nbmask)

    fam = json.loads((args.family_root / "data" / "family-f.json").read_text())
    states = [set(map(int, s)) for s in fam["states"]]
    seeds = [("bpz-X", X0), ("bpz-I0", I0)] + [
        (f"family-f-{i}", s) for i, s in enumerate(states)
    ]
    for name, S in seeds:
        if len(S) != f.N or not f.independent(S, digits):
            raise RuntimeError(f"seed {name} invalid")

    obs_items = list(obs.items())
    Fobs = [(m, w, np.fft.fftn(f.arr(f.values(m), digits))) for m, w in obs_items]

    cases = min1_cases = fft_min1_shifts = exact_replays = unique_states = 0
    external_candidates = dfs_nodes = terminal_quads = 0
    max_candidates = max_support_groups = 0
    seen = set()
    winner = None

    for name, S in seeds:
        FS = np.fft.fftn(f.arr(S, digits))
        for oi, (mask, witness, FD) in enumerate(Fobs):
            cases += 1
            corr = np.rint(np.fft.ifftn(np.conj(FS) * FD).real).astype(np.int16)
            if int(corr.min()) != 1:
                continue
            min1_cases += 1
            Dset = set(f.values(mask))
            for idx in np.argwhere(corr == 1):
                fft_min1_shifts += 1
                t = tuple(int(z) for z in idx)
                for sign in (1, -1):
                    Sset = set(f.shift_set(S, t, digits, sign))
                    hits = Sset & Dset
                    if len(hits) != 1:
                        continue
                    exact_replays += 1
                    key = (name, oi, tuple(sorted(Sset)))
                    if key in seen:
                        continue
                    seen.add(key)
                    unique_states += 1
                    x = next(iter(hits))
                    xbit = 1 << x
                    Sbits = sum(1 << z for z in Sset)

                    # Old vertices are omitted deliberately: any repair re-adding
                    # one cancels to a <=3 repair, already exhausted exactly.
                    cand = []
                    support_groups = set()
                    for y in range(f.U):
                        if y in Dset or y in Sset:
                            continue
                        sup = nbmask[y] & Sbits
                        if (sup | xbit).bit_count() <= 4:
                            cand.append((y, sup))
                            support_groups.add(sup)
                    cand.sort()
                    external_candidates += len(cand)
                    max_candidates = max(max_candidates, len(cand))
                    max_support_groups = max(max_support_groups, len(support_groups))

                    chosen = []

                    def dfs(start, owners):
                        nonlocal dfs_nodes, terminal_quads, winner
                        dfs_nodes += 1
                        need = 4 - len(chosen)
                        if len(cand) - start < need:
                            return False
                        if need == 0:
                            terminal_quads += 1
                            rem = set(bit_values(owners))
                            if x not in rem:
                                raise RuntimeError("owner union lost obstruction hit")
                            for q in sorted(Sset):
                                if len(rem) == 4:
                                    break
                                if q not in rem:
                                    rem.add(q)
                            if len(rem) != 4:
                                raise RuntimeError("could not pad removal set")
                            add = [cand[i][0] for i in chosen]
                            repaired = (Sset - rem) | set(add)
                            if len(repaired) != f.N:
                                return False
                            if repaired & Dset:
                                raise RuntimeError("four-repair still hits obstruction")
                            if not f.independent(repaired, digits):
                                raise RuntimeError("four-repair replay failed")
                            winner = (name, oi, t, sign, sorted(rem), add, repaired, witness)
                            return True

                        for i in range(start, len(cand)):
                            y, sup = cand[i]
                            newowners = owners | sup
                            if newowners.bit_count() > 4:
                                continue
                            ok = True
                            for j in chosen:
                                if y in ring.NB[cand[j][0]]:
                                    ok = False
                                    break
                            if not ok:
                                continue
                            chosen.append(i)
                            if dfs(i + 1, newowners):
                                return True
                            chosen.pop()
                        return False

                    if dfs(0, xbit):
                        break
                if winner:
                    break
            if winner:
                break
        if winner:
            break

    status = {
        "method": "bpz-t9-public-translations-owner-union-four-for-four-repair",
        "candidate": winner is not None,
        "seed_count": len(seeds),
        "obstruction_masks": len(obs_items),
        "seed_obstruction_cases": cases,
        "min1_cases": min1_cases,
        "fft_min1_shifts": fft_min1_shifts,
        "exact_min1_replays": exact_replays,
        "unique_near_states": unique_states,
        "external_candidates_total": external_candidates,
        "max_external_candidates_per_state": max_candidates,
        "max_support_groups_per_state": max_support_groups,
        "dfs_nodes": dfs_nodes,
        "terminal_candidate_quads": terminal_quads,
        "family_source_commit": "ae81e0d24b356aef3d388238f6fb4d02c4aa32a5",
    }
    args.status.parent.mkdir(parents=True, exist_ok=True)

    if winner is None:
        status["score"] = 134753
        args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
        return

    name, oi, t, sign, rem, add, repaired, witness = winner
    Ibits, pairs, orient, PH, PV = witness
    points, xp = f.build(Ibits, sum(1 << q for q in repaired), pairs, PH, PV, ring)
    if len(points) != f.TARGET:
        raise RuntimeError(f"target score drift {len(points)}")
    status.update({
        "score": len(points),
        "winning_seed": name,
        "winning_obstruction_index": oi,
        "winning_translation": list(t),
        "translation_sign": sign,
        "removed_auxiliary_points": rem,
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
