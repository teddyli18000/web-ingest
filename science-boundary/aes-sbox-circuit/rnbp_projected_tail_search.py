#!/usr/bin/env python3
"""Search output-aware RNBP prefixes using legal projections of future targets.

A 61-linear RNBP prefix can release all 33 FS101 ANDs, but exact Z3 proves that
its eight outputs cannot be completed in 6 or 7 more linear gates.  The missing
coupling is temporal anticipation: before a future AND atom exists, the portion
of an eventual operand/output supported only on currently released atoms is
already legal and can be synthesized/shared.

This search adds those legal projections as soft targets while retaining exact
next-AND operand preemption.  After all ANDs are released, an exact Z3 tail test
checks the remaining budget for a <=100-gate circuit.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random

import released_and_skeleton as ras
import temporal_rnbp_synth as tr
import rnbp_exact_tail as tail


def project_target(t, stage, sk):
    # Inputs plus already-released AND atoms; preserve affine constant separately.
    low = (1 << (8 + stage)) - 1
    C = 1 << sk["const_bit"]
    return (t & low) | (t & C)


def effective_targets(sk, S, stage, rows, projection_weight):
    agg = {}
    for t, deadline, wt, label in rows:
        dep = tr.max_atom_dep(t, sk["n_and"], sk["const_bit"])
        if dep < stage:
            p = t
            scale = 1.0
        elif projection_weight > 0:
            p = project_target(t, stage, sk)
            # Far-future projections are useful but must not starve the next AND.
            scale = projection_weight / (1.0 + 0.55 * max(0, deadline - stage))
        else:
            continue
        if p == 0 or p in S:
            continue
        # A one-bit input projection is already available; a pure constant or
        # complemented singleton is retained because it can matter affinely.
        key = p
        val = wt * scale
        if key not in agg or val > agg[key][1]:
            agg[key] = (deadline, val, label)
    return [(p, *x) for p, x in agg.items()]


def choose_projected(sk, S, stage, rows, guide, rng, topk, projection_weight):
    C = 1 << sk["const_bit"]
    P = tr.pair_map(S, C)
    if not P:
        return None, {}

    # Exact next-interface completion dominates all soft anticipatory targets.
    if stage < sk["n_and"]:
        need = sk["ands"][stage]
        for t in (need["a"], need["b"]):
            if t not in S and t in P:
                return (t, *P[t]), {"preemptive": True, "pairs": len(P),
                                     "effective_targets": 0}

    active = effective_targets(sk, S, stage, rows, projection_weight)
    if not active:
        return None, {"pairs": len(P), "effective_targets": 0}
    curd = {t: tr.dist2(t, S, P, C) for t, _, _, _ in active}
    scored = []
    for w, witness in P.items():
        score = 0.0; changed = 0
        for t, deadline, wt, _ in active:
            horizon = max(0, deadline - stage)
            weight = wt / (1.0 + 0.25 * horizon)
            rem = tr.residual_closeness(t, w, S, P, C)
            nd = min(curd[t], 1 + rem)
            if nd < curd[t]:
                score += (curd[t] - nd) * 320.0 * weight
                changed += 1
            before = tr.affine_weight(t, sk["const_bit"])
            after = min(tr.affine_weight(t ^ w, sk["const_bit"]),
                        tr.affine_weight(t ^ w ^ C, sk["const_bit"]))
            if after < before:
                score += (before - after) * 1.2 * weight
        if w in guide:
            score += 14.0
        if changed:
            score += 2.5 * changed * changed
        scored.append((score, changed, w, witness))
    scored.sort(key=lambda z: (-z[0], -z[1], z[2]))
    elite = scored[:max(1, min(topk, len(scored)))]
    weights = [1.0 / math.sqrt(i + 1.0) for i in range(len(elite))]
    choice = rng.choices(elite, weights=weights, k=1)[0]
    _, _, w, witness = choice
    return (w, *witness), {"pairs": len(P), "effective_targets": len(active),
                            "elite_best": elite[0][0], "elite_chosen": choice[0]}


def build_prefix(base, rng_seed, topk, projection_weight, max_linear):
    sk = ras.extract_skeleton(base)
    rows = tr.target_rows(sk); guide = tr.original_linear_vectors(base, sk)
    rng = random.Random(rng_seed)
    S = {1 << i for i in range(8)}
    names = {1 << i: f"x{i}" for i in range(8)}
    gates = []; linear = 0; stage = tr.release_ready(sk, S, 0, gates, names); trace = []
    while stage < sk["n_and"] and linear < max_linear:
        move, info = choose_projected(sk, S, stage, rows, guide, rng, topk, projection_weight)
        if move is None:
            break
        w, op, a, b = move
        if w in S:
            raise AssertionError(("duplicate helper", w))
        out = f"w{len(gates)}"
        gates.append({"op": op, "a": names[a], "b": names[b], "out": out})
        S.add(w); names[w] = out; linear += 1
        old = stage; stage = tr.release_ready(sk, S, stage, gates, names)
        trace.append({"linear": linear, "stage_before": old, "stage_after": stage,
                      "guide": w in guide, **info})
    return sk, S, names, gates, linear, stage, trace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(ras.SOURCES), default="fs-101")
    ap.add_argument("--rng-seed", type=int, default=1)
    ap.add_argument("--topk", type=int, default=1)
    ap.add_argument("--projection-weight", type=float, required=True)
    ap.add_argument("--prefix-max-linear", type=int, default=67)
    ap.add_argument("--total-linear-budget", type=int, default=67)
    ap.add_argument("--timeout-ms", type=int, default=120000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    base = ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    sk, S, names, pg, plin, stage, trace = build_prefix(
        base, args.rng_seed, args.topk, args.projection_weight, args.prefix_max_linear)
    slots = args.total_linear_budget - plin
    summary = {"family": args.family, "rng_seed": args.rng_seed, "topk": args.topk,
               "projection_weight": args.projection_weight, "prefix_linear": plin,
               "released_ands": stage, "tail_slots_available": slots,
               "target_total_linear": args.total_linear_budget,
               "target_total_gates": sk["n_and"] + args.total_linear_budget,
               "trace_tail": trace[-20:]}
    if stage != sk["n_and"]:
        summary["status"] = "prefix_incomplete"
    elif slots < 0:
        summary["status"] = "prefix_over_budget"
    else:
        candidate, ts = tail.solve_tail(sk, S, names, pg, slots, args.timeout_ms)
        summary["tail"] = ts; summary["status"] = ts["status"]
        if candidate is not None:
            (out / "candidate.json").write_text(json.dumps(candidate, indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k:v for k,v in summary.items() if k != "trace_tail"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
