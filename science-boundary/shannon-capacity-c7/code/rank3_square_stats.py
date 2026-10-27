#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path

import generalized9 as g
import rank3_square_relax as rs


def one_bit(mask):
    if not mask or mask & (mask - 1):
        raise ValueError("not singleton")
    return (mask & -mask).bit_length() - 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("r367", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()

    digits = tuple(g.dec5(v) for v in range(g.U))
    r0 = g.load_r(args.r367)
    xset = g.make_x(r0, digits)
    r = rs.load_rank3_state(r0, digits)
    supports, _ = g.support_masks(r, digits)

    kset = set(rs.RANK3_K9)
    bidx = [i for i in range(g.R_SIZE) if i not in kset]
    bmask = sum(1 << i for i in bidx)
    bvals = {r[i] for i in bidx}

    safe = []
    near = defaultdict(list)
    endpoint_hist = defaultdict(int)
    for v, sm in enumerate(supports):
        if v in bvals:
            continue
        m = sm & bmask
        c = m.bit_count()
        endpoint_hist[c] += 1
        if c == 0:
            safe.append(v)
        elif c == 1:
            near[one_bit(m)].append(v)

    x_hist = defaultdict(int)
    x_one = defaultdict(list)
    x_zero = []
    for xi, xv in enumerate(xset):
        m = supports[xv] & bmask
        c = m.bit_count()
        x_hist[c] += 1
        if c == 0:
            x_zero.append(xi)
        elif c == 1:
            x_one[one_bit(m)].append(xi)

    unlock = defaultdict(int)
    detail = defaultdict(lambda: {"h": 0, "v": 0})
    for a, es in near.items():
        for b, xis in x_one.items():
            n = len(es) * len(xis)
            if not n:
                continue
            unlock[(a, b)] += n
            detail[(a, b)]["h"] += n
            unlock[(b, a)] += n
            detail[(b, a)]["v"] += n

    ranked = sorted(unlock.items(), key=lambda kv: (-kv[1], kv[0]))
    out = {
        "state": rs.STATE_INDEX,
        "k9": list(rs.RANK3_K9),
        "base_square": len(bidx) ** 2,
        "safe_endpoints": len(safe),
        "endpoint_conflict_histogram": dict(sorted(endpoint_hist.items())),
        "near1_endpoint_owners": {str(k): len(v) for k, v in sorted(near.items())},
        "x_conflict_histogram": dict(sorted(x_hist.items())),
        "x_zero_indices": x_zero,
        "x_one_owners": {str(k): len(v) for k, v in sorted(x_one.items())},
        "touched_square_vertices": len(unlock),
        "top_square_unlocks": [
            {
                "square_index_pair": [a, b],
                "new_port_candidates": n,
                "h": detail[(a, b)]["h"],
                "v": detail[(a, b)]["v"],
            }
            for (a, b), n in ranked[:100]
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
