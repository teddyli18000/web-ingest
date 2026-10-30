#!/usr/bin/env python3
"""Exact small-tail preconditioner after a compressed released-AND prefix.

For a prefix that has already released all 33 AND atoms, suppose the eight AES
outputs are terminal leaves: they are generated only after H anonymous affine
helper gates and are not reused as inputs to later outputs.  Under a 67-linear
(100 total gate) budget, a 56-linear prefix permits H<=3 because the eight
outputs themselves cost eight gates.

This script asks Z3 for H XOR/XNOR helpers such that, after adding them, every
output is one XOR/XNOR gate away from the available set.  For fixed H this is an
exact decision procedure for this leaf-output family.  H=3 gives a 100-gate
candidate if SAT.  Any model is reconstructed and independently checked on all
256 AES inputs.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import time

import released_and_skeleton as ras
import rnbp_prefix_variant_tail as pv

try:
    import z3
except ImportError as e:
    raise SystemExit("z3-solver is required") from e


def bv(v, D):
    return z3.BitVecVal(int(v), D)


def select_expr(sel, xs):
    e = xs[-1]
    for i in range(len(xs) - 2, -1, -1):
        e = z3.If(sel == i, xs[i], e)
    return e


def solve(base, weight, dev_index, dev_rank, helpers, timeout_ms):
    sk,S,names_by_vec,prefix_gates,plin,stage,soft,applied,trace = pv.build_variant(
        base, weight, dev_index, dev_rank, 67)
    summary = {
        "projection_weight": weight,
        "deviation_index": dev_index,
        "deviation_rank": dev_rank,
        "deviation_applied": applied,
        "prefix_linear": plin,
        "released_ands": stage,
        "helpers": helpers,
        "target_total_linear": plin + helpers + 8,
        "target_total_gates": sk["n_and"] + plin + helpers + 8,
        "soft_decisions_seen": soft,
    }
    if not applied or stage != sk["n_and"]:
        summary["status"] = "prefix_incomplete"
        return None, summary

    D = sk["const_bit"] + 1
    C = 1 << sk["const_bit"]
    fixed_vecs = sorted(S)
    fixed_names = [names_by_vec[v] for v in fixed_vecs]
    sources = [bv(v,D) for v in fixed_vecs]
    helper_meta = []

    solver = z3.Solver()
    solver.set(timeout=timeout_ms)

    # Anonymous helper gates.  p<q removes operand commutativity.  Reproducing
    # an existing vector is forbidden because it can never help an optimal tail.
    for i in range(helpers):
        p = z3.Int(f"hp_{i}")
        q = z3.Int(f"hq_{i}")
        neg = z3.Bool(f"hneg_{i}")
        solver.add(p >= 0, q >= 0, p < q, q < len(sources))
        pvx = select_expr(p, sources)
        qvx = select_expr(q, sources)
        v = z3.BitVec(f"H_{i}", D)
        solver.add(v == (pvx ^ qvx ^ z3.If(neg, bv(C,D), bv(0,D))))
        for old in sources:
            solver.add(v != old)
        # Helper order is semantic/topological, so no arbitrary lex ordering.
        helper_meta.append((p,q,neg,v))
        sources.append(v)

    # Each output is terminal: one final XOR/XNOR from fixed signals/helpers.
    output_meta = []
    for oi,t in enumerate(sk["outputs"]):
        p = z3.Int(f"op_{oi}")
        q = z3.Int(f"oq_{oi}")
        neg = z3.Bool(f"oneg_{oi}")
        solver.add(p >= 0, q >= 0, p < q, q < len(sources))
        expr = select_expr(p,sources) ^ select_expr(q,sources) ^ z3.If(neg,bv(C,D),bv(0,D))
        solver.add(expr == bv(t,D))
        output_meta.append((p,q,neg))

    t0 = time.time()
    r = solver.check()
    elapsed = time.time() - t0
    summary.update({"status":str(r),"elapsed_s":round(elapsed,3),"fixed_sources":len(fixed_vecs)})
    if r == z3.unknown:
        summary["reason_unknown"] = solver.reason_unknown()
        return None, summary
    if r != z3.sat:
        return None, summary

    m = solver.model()
    gates = [dict(g) for g in prefix_gates]
    src_names = list(fixed_names)
    for i,(p,q,neg,v) in enumerate(helper_meta):
        pi = m.eval(p,model_completion=True).as_long()
        qi = m.eval(q,model_completion=True).as_long()
        op = "XNOR" if z3.is_true(m.eval(neg,model_completion=True)) else "XOR"
        out = f"__tail_helper_{i}"
        gates.append({"op":op,"a":src_names[pi],"b":src_names[qi],"out":out})
        src_names.append(out)

    out_names = []
    for oi,(p,q,neg) in enumerate(output_meta):
        pi = m.eval(p,model_completion=True).as_long()
        qi = m.eval(q,model_completion=True).as_long()
        op = "XNOR" if z3.is_true(m.eval(neg,model_completion=True)) else "XOR"
        out = f"__aes_out_{oi}"
        gates.append({"op":op,"a":src_names[pi],"b":src_names[qi],"out":out})
        out_names.append(out)

    c = ras.prune({"gates":gates,"outputs":out_names})
    ok = ras.independent_check(c)
    if not ok[0]:
        raise AssertionError(("reconstructed model failed AES",ok))
    summary.update({"candidate_gates":len(c["gates"]),
                    "candidate_stats":dict(collections.Counter(g["op"] for g in c["gates"])),
                    "verified_all_256":True})
    return c,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--family",choices=sorted(ras.SOURCES),default="fs-101")
    ap.add_argument("--projection-weight",type=float,default=0.24)
    ap.add_argument("--deviation-index",type=int,required=True)
    ap.add_argument("--deviation-rank",type=int,required=True)
    ap.add_argument("--helpers",type=int,default=3)
    ap.add_argument("--timeout-ms",type=int,default=300000)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    c,s=solve(base,args.projection_weight,args.deviation_index,args.deviation_rank,
              args.helpers,args.timeout_ms)
    if c is not None:
        (out/"candidate.json").write_text(json.dumps(c,indent=2)+"\n")
    (out/"summary.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
    print(json.dumps(s,sort_keys=True),flush=True)

if __name__=="__main__":main()
