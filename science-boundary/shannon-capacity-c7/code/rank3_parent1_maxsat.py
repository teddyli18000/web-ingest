#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import generalized9 as g
import neutral2_maxsat as nm
import neutral2_sweep as ns

BASELINE = 134_753
STATE_INDEX = 18
K9 = (60, 160, 231, 244, 250, 267, 330, 344, 364)
EXPECTED_REMOVE = (267, 294)
EXPECTED_ADD = (15083, 16388)


def load_state(r0, digits):
    supports0, _ = g.support_masks(r0, digits)
    states = ns.enumerate_states(r0, digits, supports0)
    r, rem, add = states[STATE_INDEX - 1]
    if tuple(rem) != EXPECTED_REMOVE or tuple(add) != EXPECTED_ADD:
        raise RuntimeError(f"state-18 drift: rem={rem} add={add}")
    return r


def private_moves(r, supports):
    rset = set(r)
    out = []
    for u, sm in enumerate(supports):
        if u in rset or sm.bit_count() != 1:
            continue
        a = (sm & -sm).bit_length() - 1
        out.append((a, u))
    return sorted(out)


def replace_support_bit(supports, owner, new_vertex, digits):
    bit = 1 << owner
    keep_mask = ~bit
    out = [0] * g.U
    for v, sm in enumerate(supports):
        if g.conflict(v, new_vertex, digits):
            out[v] = sm | bit
        else:
            out[v] = sm & keep_mask
    return out


def serialize_model(model):
    safe, hs, vs = model
    return {
        "safe": safe,
        "selected_h": [[i, e] for i, arr in enumerate(hs) for e in arr],
        "selected_v": [[i, e] for i, arr in enumerate(vs) for e in arr],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("baseline", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("model_output", type=Path)
    ap.add_argument("status", type=Path)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = load_state(r0, digits)
    supports, _ = g.support_masks(r, digits)
    moves = private_moves(r, supports)
    print("MOVES", json.dumps({"count": len(moves), "moves": moves}), flush=True)

    best = None
    best_model = None
    best_r = None
    tested = 0
    for owner, u in moves:
        r2 = list(r)
        old = r2[owner]
        r2[owner] = u
        if len(set(r2)) != g.R_SIZE:
            raise RuntimeError("duplicate parent after one-swap")
        supports2 = replace_support_bit(supports, owner, u, digits)
        # Independent-set sanity: every parent point must only conflict with itself.
        for i, rv in enumerate(r2):
            sm = supports2[rv]
            if sm != (1 << i):
                raise RuntimeError(f"parent independence failed owner={owner} i={i} mask={sm}")

        model, stats = nm.solve_maxsat(K9, r2, xset, digits, supports2)
        tested += 1
        rec = {
            "owner": owner,
            "old": old,
            "new": u,
            "owner_in_k9": owner in K9,
            "stats": stats,
        }
        print("RESULT", json.dumps(rec, sort_keys=True), flush=True)
        if best is None or stats["score"] > best["stats"]["score"]:
            best = rec
            best_model = model
            best_r = r2

    if best is None or best_model is None or best_r is None:
        raise RuntimeError("no one-swap models evaluated")

    candidate = nm.build_candidate(K9, best_model, best_r, xset, digits)
    if len(candidate) != best["stats"]["score"]:
        raise RuntimeError("best score mismatch")

    model_data = {
        "method": "rank3-parent1-maxsat",
        "state_index": STATE_INDEX,
        "k9": list(K9),
        "tested_moves": tested,
        "best_move": best,
        "parent": best_r,
        "model": serialize_model(best_model),
    }
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.model_output.write_text(json.dumps(model_data, separators=(",", ":")) + "\n")

    baseline = {int(p, 7) for p in json.loads(args.baseline.read_text())["points"]}
    status = {
        "candidate": len(candidate) > BASELINE,
        "score": len(candidate),
        "method": "rank3-parent1-maxsat",
        "moves": len(moves),
        "tested_moves": tested,
        "best": best,
        "removed_vs_baseline": len(baseline - candidate),
        "added_vs_baseline": len(candidate - baseline),
    }
    if len(candidate) > BASELINE:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"points": [g.dec10(v) for v in sorted(candidate)]}, separators=(",", ":")) + "\n"
        )
        print("FOUND", json.dumps(status, sort_keys=True), flush=True)
    else:
        print("NONE", json.dumps(status, sort_keys=True), flush=True)
    args.status.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
