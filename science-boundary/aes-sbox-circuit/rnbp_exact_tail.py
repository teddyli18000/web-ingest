#!/usr/bin/env python3
"""Build an RNBP nonlinear-interface prefix, then solve the output tail exactly.

The temporal RNBP heuristic can release all 33 AND atoms using substantially fewer
linear helpers than the published 101-gate circuit, but its greedy output finish is
poor.  Once all ANDs are released, the remaining problem is purely affine.  This
script freezes that prefix and asks Z3 whether all eight AES output forms can be
made available with K additional XOR/XNOR gates.  K=6 after a 61-linear prefix
would give 33 + 61 + 6 = 100 total gates.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import time

import released_and_skeleton as ras
import temporal_rnbp_synth as tr

try:
    import z3
except ImportError as e:
    raise SystemExit("z3-solver is required") from e


def bv(v, D):
    return z3.BitVecVal(v, D)


def select_expr(sel, sources):
    e = sources[-1]
    for i in range(len(sources) - 2, -1, -1):
        e = z3.If(sel == i, sources[i], e)
    return e


def build_prefix(base, rng_seed, topk, max_linear):
    sk = ras.extract_skeleton(base)
    rows = tr.target_rows(sk)
    guide = tr.original_linear_vectors(base, sk)
    rng = random.Random(rng_seed)
    S = {1 << i for i in range(8)}
    names = {1 << i: f"x{i}" for i in range(8)}
    gates = []
    stage = tr.release_ready(sk, S, 0, gates, names)
    linear = 0
    trace = []
    while stage < sk["n_and"] and linear < max_linear:
        move, info = tr.choose_move(sk, S, stage, rows, guide, rng, topk)
        if move is None:
            break
        w, op, a, b = move
        if w in S:
            raise AssertionError(("duplicate helper", w))
        out = f"w{len(gates)}"
        gates.append({"op": op, "a": names[a], "b": names[b], "out": out})
        S.add(w); names[w] = out; linear += 1
        old = stage
        stage = tr.release_ready(sk, S, stage, gates, names)
        trace.append({"linear": linear, "stage_before": old, "stage_after": stage, **info})
    return sk, S, names, gates, linear, stage, trace


def solve_tail(sk, S, names_by_vec, prefix_gates, slots, timeout_ms):
    D = sk["const_bit"] + 1
    C = 1 << sk["const_bit"]
    fixed_vecs = sorted(S)
    source_vecs = list(fixed_vecs)
    source_names = [names_by_vec[v] for v in fixed_vecs]
    sources = [bv(v, D) for v in fixed_vecs]
    solver = z3.Solver(); solver.set(timeout=timeout_ms)
    meta = []
    for i in range(slots):
        p = z3.Int(f"p_{i}"); q = z3.Int(f"q_{i}"); neg = z3.Bool(f"neg_{i}")
        solver.add(p >= 0, q >= 0, p < q, q < len(sources))
        pv = select_expr(p, sources); qv = select_expr(q, sources)
        v = z3.BitVec(f"T_{i}", D)
        solver.add(v == (pv ^ qv ^ z3.If(neg, bv(C, D), bv(0, D))))
        # Avoid wasting a slot reproducing an already available affine function.
        for old in sources:
            solver.add(v != old)
        sources.append(v)
        meta.append((p, q, neg))
    outs = []
    for oi, t in enumerate(sk["outputs"]):
        q = z3.Int(f"out_{oi}")
        solver.add(q >= 0, q < len(sources), select_expr(q, sources) == bv(t, D))
        outs.append(q)
    t0 = time.time(); r = solver.check(); elapsed = time.time() - t0
    result = {"tail_slots": slots, "status": str(r), "elapsed_s": round(elapsed, 3)}
    if r == z3.unknown:
        result["reason_unknown"] = solver.reason_unknown()
        return None, result
    if r != z3.sat:
        return None, result

    model = solver.model()
    gates = [dict(g) for g in prefix_gates]
    names = list(source_names)
    for i, (p, q, neg) in enumerate(meta):
        pi = model.eval(p, model_completion=True).as_long()
        qi = model.eval(q, model_completion=True).as_long()
        op = "XNOR" if z3.is_true(model.eval(neg, model_completion=True)) else "XOR"
        out = f"__tail_{i}"
        gates.append({"op": op, "a": names[pi], "b": names[qi], "out": out})
        names.append(out)
    output_names = [names[model.eval(q, model_completion=True).as_long()] for q in outs]
    c = ras.prune({"gates": gates, "outputs": output_names})
    ok = ras.independent_check(c)
    if not ok[0]:
        raise AssertionError(("tail model failed AES", ok))
    result.update({"candidate_gates": len(c["gates"]), "verified_all_256": True,
                   "stats": dict(collections.Counter(g["op"] for g in c["gates"]))})
    return c, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(ras.SOURCES), default="fs-101")
    ap.add_argument("--rng-seed", type=int, default=1)
    ap.add_argument("--topk", type=int, default=1)
    ap.add_argument("--prefix-max-linear", type=int, default=67)
    ap.add_argument("--tail-slots", type=int, default=6)
    ap.add_argument("--timeout-ms", type=int, default=300000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    base = ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    sk, S, names, pg, plin, stage, trace = build_prefix(
        base, args.rng_seed, args.topk, args.prefix_max_linear)
    summary = {"family": args.family, "rng_seed": args.rng_seed, "topk": args.topk,
               "prefix_linear": plin, "released_ands": stage,
               "prefix_gates": len(pg), "target_total_linear": plin + args.tail_slots,
               "target_total_gates": sk["n_and"] + plin + args.tail_slots,
               "trace_tail": trace[-20:]}
    if stage != sk["n_and"]:
        summary["status"] = "prefix_incomplete"
    else:
        candidate, tail = solve_tail(sk, S, names, pg, args.tail_slots, args.timeout_ms)
        summary["tail"] = tail; summary["status"] = tail["status"]
        if candidate is not None:
            (out / "candidate.json").write_text(json.dumps(candidate, indent=2) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k:v for k,v in summary.items() if k != "trace_tail"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
