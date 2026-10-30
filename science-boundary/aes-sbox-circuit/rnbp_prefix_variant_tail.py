#!/usr/bin/env python3
"""Enumerate nearby output-aware RNBP prefixes and exact-test their tails.

The projected RNBP search found a 60-linear prefix that releases all 33 FS101
AND atoms, but its 7-gate linear output tail is UNSAT.  This program changes one
non-forced RNBP decision to the rank-r alternative, then follows the deterministic
best-ranked policy again.  Each completed prefix is tested with an exact Z3 tail
under the global 67-linear (=100 total gate) budget.

This deliberately searches prefix diversity instead of further tuning one scalar
projection weight.  A miss is scoped to this single-deviation frontier.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import released_and_skeleton as ras
import temporal_rnbp_synth as tr
import rnbp_exact_tail as tail
import rnbp_projected_tail_search as rp


def ranked_moves(sk, S, stage, rows, guide, projection_weight, limit=16):
    C = 1 << sk["const_bit"]
    P = tr.pair_map(S, C)
    if not P:
        return [], {"pairs": 0, "forced": False}
    if stage < sk["n_and"]:
        need = sk["ands"][stage]
        forced = []
        for t in (need["a"], need["b"]):
            if t not in S and t in P:
                forced.append((t, *P[t]))
        if forced:
            forced.sort(key=lambda x: x[0])
            return [forced[0]], {"pairs": len(P), "forced": True}
    active = rp.effective_targets(sk, S, stage, rows, projection_weight)
    if not active:
        return [], {"pairs": len(P), "forced": False, "effective_targets": 0}
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
    out = [(w, *wit) for _, _, w, wit in scored[:limit]]
    return out, {"pairs": len(P), "forced": False,
                 "effective_targets": len(active),
                 "best_score": scored[0][0] if scored else None}


def build_variant(base, projection_weight, deviation_index, deviation_rank,
                  prefix_max_linear=67):
    sk = ras.extract_skeleton(base)
    rows = tr.target_rows(sk); guide = tr.original_linear_vectors(base, sk)
    S = {1 << i for i in range(8)}
    names = {1 << i: f"x{i}" for i in range(8)}
    gates = []; linear = 0; stage = tr.release_ready(sk, S, 0, gates, names)
    soft_index = 0; deviation_applied = False; trace = []
    while stage < sk["n_and"] and linear < prefix_max_linear:
        moves, info = ranked_moves(sk, S, stage, rows, guide, projection_weight,
                                   limit=max(16, deviation_rank + 1))
        if not moves:
            break
        rank = 0
        current_soft = None
        if not info.get("forced", False):
            current_soft = soft_index
            if soft_index == deviation_index:
                rank = deviation_rank
                deviation_applied = rank < len(moves)
                if not deviation_applied:
                    return sk, S, names, gates, linear, stage, soft_index, False, trace
            soft_index += 1
        if rank >= len(moves):
            return sk, S, names, gates, linear, stage, soft_index, False, trace
        w, op, a, b = moves[rank]
        if w in S:
            raise AssertionError(("duplicate", w))
        out = f"w{len(gates)}"
        gates.append({"op": op, "a": names[a], "b": names[b], "out": out})
        S.add(w); names[w] = out; linear += 1
        old = stage; stage = tr.release_ready(sk, S, stage, gates, names)
        trace.append({"linear": linear, "stage_before": old, "stage_after": stage,
                      "soft_index": current_soft, "chosen_rank": rank, **info})
    return sk, S, names, gates, linear, stage, soft_index, deviation_applied, trace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(ras.SOURCES), default="fs-101")
    ap.add_argument("--projection-weight", type=float, default=0.24)
    ap.add_argument("--deviation-index", type=int, required=True)
    ap.add_argument("--deviation-rank", type=int, required=True)
    ap.add_argument("--prefix-max-linear", type=int, default=67)
    ap.add_argument("--total-linear-budget", type=int, default=67)
    ap.add_argument("--timeout-ms", type=int, default=60000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    base = ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    sk,S,names,pg,plin,stage,soft_count,applied,trace = build_variant(
        base,args.projection_weight,args.deviation_index,args.deviation_rank,
        args.prefix_max_linear)
    slots = args.total_linear_budget - plin
    summary = {"family":args.family,"projection_weight":args.projection_weight,
               "deviation_index":args.deviation_index,"deviation_rank":args.deviation_rank,
               "deviation_applied":applied,"soft_decisions_seen":soft_count,
               "prefix_linear":plin,"released_ands":stage,
               "tail_slots_available":slots,
               "target_total_gates":sk["n_and"]+args.total_linear_budget,
               "trace_tail":trace[-12:]}
    if not applied:
        summary["status"]="invalid_deviation"
    elif stage != sk["n_and"]:
        summary["status"]="prefix_incomplete"
    elif slots < 0:
        summary["status"]="prefix_over_budget"
    else:
        candidate,ts=tail.solve_tail(sk,S,names,pg,slots,args.timeout_ms)
        summary["tail"]=ts; summary["status"]=ts["status"]
        if candidate is not None:
            (out/"candidate.json").write_text(json.dumps(candidate,indent=2)+"\n")
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in summary.items() if k!="trace_tail"},sort_keys=True),flush=True)

if __name__=="__main__": main()
