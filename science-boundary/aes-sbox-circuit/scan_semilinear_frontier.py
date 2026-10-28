#!/usr/bin/env python3
"""Cheap global lower-bound scan over all 2040 semilinear p008 transforms.

We keep the merged-102 nonlinear construction and transport it through

    P(x) = c * x^(2^k),  c != 0,  k in 0..7,

while enumerating all 3^9 product-plane orientations.  Before spending exact
linear-synthesis time, this script computes a rigorous component lower bound

    prelinear_target_count + abstract_middle_support + output_target_count.

The first and third terms count distinct non-input linear targets, hence are lower
bounds on two-input XOR/XNOR gates.  The middle term is exact if correction values
may be arbitrary input-linear byte masks: for each AES input bit the desired four
middle-output coefficients form a vector in GF(2)^4, and the selected correction
positions must have column span containing every such vector.  We enumerate all
subsets of the nine fixed middle columns to obtain the minimum possible support.

A retained-18-gate-core 101 construction needs variable outer cost <=36, so any
orientation with this lower bound >36 is impossible in that family.  A low bound is
only a screen, not a construction: exact prelinear/output synthesis and correction
realization are still required.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import pathlib
import time

import search_plane_middle5 as mid
import search_plane_prelinear17 as lin
import search_semilinear_outer as outer


ALL_ORIENTATIONS = tuple(itertools.product(range(3), repeat=9))


def span(columns):
    values = {0}
    for col in columns:
        values |= {x ^ col for x in tuple(values)}
    return frozenset(values)


# All 512 physical support subsets, ordered first by cardinality.  Keeping the
# actual positions makes best witnesses independently checkable.
SUPPORTS = []
for bits in range(1 << len(mid.COLS)):
    positions = tuple(i for i in range(len(mid.COLS)) if (bits >> i) & 1)
    SUPPORTS.append((len(positions), positions, span(mid.COLS[i] for i in positions)))
SUPPORTS.sort(key=lambda x: (x[0], x[1]))


def middle_rhs_vectors(delta):
    """Return the GF(2)^4 RHS vectors used across the eight input coefficients."""
    vectors = set()
    for bit in range(8):
        v = 0
        for j in range(4):
            v |= ((delta[j] >> bit) & 1) << j
        vectors.add(v)
    return frozenset(vectors)


def middle_support_lb(delta):
    required = middle_rhs_vectors(delta)
    for cost, positions, values in SUPPORTS:
        if required <= values:
            return cost, positions
    raise AssertionError("all nine middle columns must span every reachable RHS")


def add4(a, b):
    return [a[i] ^ b[i] for i in range(4)]


def scan_transform(c, k, save_best=12):
    planes, outpairs, corrections = outer.transported_data(c, k)

    pre_opts = [[set(outer.orient(pair, ch)) for ch in range(3)] for pair in planes]
    out_opts = [[set(outer.dual_columns(pair, ch)) for ch in range(3)] for pair in outpairs]

    base_delta = [0, 0, 0, 0]
    for i, value in enumerate(corrections):
        if value:
            base_delta = add4(base_delta, outer.contribution(mid.COLS[i], value))

    delta_opts = []
    for i, (a, b) in enumerate(planes):
        delta_opts.append([
            [0, 0, 0, 0],
            outer.contribution(mid.COLS[i], a),
            outer.contribution(mid.COLS[i], b),
        ])

    best_lb = 99
    best = []
    count_le36 = 0
    histogram = collections.Counter()
    component_histogram = collections.Counter()

    for choices in ALL_ORIENTATIONS:
        pre = set()
        out = set()
        delta = list(base_delta)
        for i, ch in enumerate(choices):
            pre.update(pre_opts[i][ch])
            out.update(out_opts[i][ch])
            delta = add4(delta, delta_opts[i][ch])

        npre = len(pre - lin.INPUTS - {0})
        nout = len(out - lin.INPUTS - {0})
        support, support_positions = middle_support_lb(delta)
        lb = npre + support + nout
        histogram[lb] += 1
        component_histogram[(npre, support, nout)] += 1
        if lb <= 36:
            count_le36 += 1

        witness = {
            "orientations": list(choices),
            "pre_target_count": npre,
            "middle_support_lb": support,
            "middle_support_positions": list(support_positions),
            "output_target_count": nout,
            "variable_cost_lb": lb,
            "total_gate_lb": 65 + lb,
        }
        if lb < best_lb:
            best_lb = lb
            best = [witness]
        elif lb == best_lb and len(best) < save_best:
            best.append(witness)

    return {
        "c": c,
        "c_hex": f"0x{c:02x}",
        "k": k,
        "transform_index": k * 255 + (c - 1),
        "orientations": len(ALL_ORIENTATIONS),
        "best_variable_cost_lb": best_lb,
        "best_total_gate_lb": 65 + best_lb,
        "orientations_lb_le_36": count_le36,
        "lb_histogram": {str(x): histogram[x] for x in sorted(histogram)},
        "component_histogram": {
            f"{a},{s},{b}": n for (a, s, b), n in sorted(component_histogram.items())
        },
        "best_witnesses": best,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--shards", type=int, default=32)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.shards <= 0 or not 0 <= args.shard < args.shards:
        raise SystemExit("require 0 <= shard < shards")

    started = time.time()
    rows = []
    global_best = 99
    for idx in range(2040):
        if idx % args.shards != args.shard:
            continue
        k, rem = divmod(idx, 255)
        c = rem + 1
        row = scan_transform(c, k)
        rows.append(row)
        global_best = min(global_best, row["best_variable_cost_lb"])
        print(json.dumps({
            "TRANSFORM": {
                "index": idx,
                "c": row["c_hex"],
                "k": k,
                "best_variable_cost_lb": row["best_variable_cost_lb"],
                "orientations_lb_le_36": row["orientations_lb_le_36"],
            }
        }, sort_keys=True), flush=True)

    rows.sort(key=lambda r: (
        r["best_variable_cost_lb"],
        -r["orientations_lb_le_36"],
        r["transform_index"],
    ))
    summary = {
        "shard": args.shard,
        "shards": args.shards,
        "transforms": len(rows),
        "orientations_per_transform": len(ALL_ORIENTATIONS),
        "best_variable_cost_lb": None if not rows else global_best,
        "transforms_with_some_lb_le_36": sum(r["orientations_lb_le_36"] > 0 for r in rows),
        "elapsed_seconds": round(time.time() - started, 3),
        "proof_scope": (
            "rigorous lower bound for retained-18-core semilinear/plane family; "
            "middle support assumes arbitrary correction byte masks and therefore "
            "can only underestimate realizable gate cost"
        ),
    }

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "transforms.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
