#!/usr/bin/env python3
"""Exact ordered tail synthesis after a 56-linear released-AND prefix.

For the two known 56-linear FS101 prefixes, every AES output is farther than two
additional XOR/XNOR gates from the prefix signal set.  Hence any tail computing
all eight distinct outputs must begin with at least two non-output helper gates.
Under the 67-linear / 100-total-gate budget, the tail has at most 11 gates, so it
contains exactly eight output-producing gates and at most three non-output
helpers.

This solver fixes the first two slots as helpers and, for H=3, enumerates the
position of the only remaining helper.  Every other slot must generate one of the
eight AES output affine forms; output identities are a permutation, and earlier
outputs may feed later helpers/outputs.  Thus H=2/3 covers every <=100 tail for a
prefix satisfying the >2-gate output-distance premise, unlike the terminal-leaf
preconditioner model.
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


def bv(v,D): return z3.BitVecVal(int(v),D)


def select_expr(sel,xs):
    e=xs[-1]
    for i in range(len(xs)-2,-1,-1):
        e=z3.If(sel==i,xs[i],e)
    return e


def selected_target(sel,targets,D):
    e=bv(targets[-1],D)
    for i in range(len(targets)-2,-1,-1):
        e=z3.If(sel==i,bv(targets[i],D),e)
    return e


def solve(base,weight,dev_index,dev_rank,helpers,extra_helper_pos,timeout_ms):
    sk,S,names_by_vec,prefix_gates,plin,stage,soft,applied,trace=pv.build_variant(
        base,weight,dev_index,dev_rank,67)
    nslots=8+helpers
    summary={"projection_weight":weight,"deviation_index":dev_index,
             "deviation_rank":dev_rank,"deviation_applied":applied,
             "prefix_linear":plin,"released_ands":stage,"helpers":helpers,
             "slots":nslots,"extra_helper_pos":extra_helper_pos,
             "target_total_linear":plin+nslots,
             "target_total_gates":sk["n_and"]+plin+nslots}
    if not applied or stage!=sk["n_and"]:
        summary["status"]="prefix_incomplete"; return None,summary
    if helpers not in (2,3):
        raise ValueError("helpers must be 2 or 3")
    if helpers==2:
        helper_positions={0,1}
        if extra_helper_pos is not None:
            raise ValueError("no extra helper position for helpers=2")
    else:
        if extra_helper_pos is None or not (2<=extra_helper_pos<nslots):
            raise ValueError(("extra helper position",extra_helper_pos,nslots))
        helper_positions={0,1,extra_helper_pos}

    D=sk["const_bit"]+1; C=1<<sk["const_bit"]
    fixed_vecs=sorted(S); fixed_names=[names_by_vec[v] for v in fixed_vecs]
    sources=[bv(v,D) for v in fixed_vecs]
    source_names=list(fixed_names)
    solver=z3.Solver(); solver.set(timeout=timeout_ms)
    slot_meta=[]; output_ids=[]
    target_set=[bv(t,D) for t in sk["outputs"]]

    for slot in range(nslots):
        p=z3.Int(f"p_{slot}"); q=z3.Int(f"q_{slot}"); neg=z3.Bool(f"neg_{slot}")
        solver.add(p>=0,q>=0,p<q,q<len(sources))
        expr=select_expr(p,sources)^select_expr(q,sources)^z3.If(neg,bv(C,D),bv(0,D))
        v=z3.BitVec(f"V_{slot}",D); solver.add(v==expr)
        if slot in helper_positions:
            # A true helper is neither already available nor itself an AES output.
            for old in sources: solver.add(v!=old)
            for t in target_set: solver.add(v!=t)
            oid=None
        else:
            oid=z3.Int(f"oid_{slot}")
            solver.add(oid>=0,oid<8,v==selected_target(oid,sk["outputs"],D))
            output_ids.append(oid)
        slot_meta.append((slot,p,q,neg,v,oid))
        sources.append(v)
        source_names.append(f"__tail_slot_{slot}")

    # There are exactly eight output slots; each AES output must occur once.
    assert len(output_ids)==8
    solver.add(z3.Distinct(*output_ids))

    t0=time.time(); r=solver.check(); elapsed=time.time()-t0
    summary.update({"status":str(r),"elapsed_s":round(elapsed,3),
                    "fixed_sources":len(fixed_vecs),
                    "helper_positions":sorted(helper_positions)})
    if r==z3.unknown:
        summary["reason_unknown"]=solver.reason_unknown(); return None,summary
    if r!=z3.sat: return None,summary

    m=solver.model(); gates=[dict(g) for g in prefix_gates]
    names=list(fixed_names); out_names=[None]*8
    for slot,p,q,neg,v,oid in slot_meta:
        pi=m.eval(p,model_completion=True).as_long(); qi=m.eval(q,model_completion=True).as_long()
        op="XNOR" if z3.is_true(m.eval(neg,model_completion=True)) else "XOR"
        out=f"__tail_slot_{slot}"
        gates.append({"op":op,"a":names[pi],"b":names[qi],"out":out})
        names.append(out)
        if oid is not None:
            oi=m.eval(oid,model_completion=True).as_long(); out_names[oi]=out
    assert all(x is not None for x in out_names),out_names
    c=ras.prune({"gates":gates,"outputs":out_names})
    ok=ras.independent_check(c)
    if not ok[0]: raise AssertionError(("ordered tail failed AES",ok))
    summary.update({"candidate_gates":len(c["gates"]),"verified_all_256":True,
                    "candidate_stats":dict(collections.Counter(g["op"] for g in c["gates"]))})
    return c,summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--family",choices=sorted(ras.SOURCES),default="fs-101")
    ap.add_argument("--projection-weight",type=float,default=0.24)
    ap.add_argument("--deviation-index",type=int,required=True)
    ap.add_argument("--deviation-rank",type=int,required=True)
    ap.add_argument("--helpers",type=int,choices=[2,3],required=True)
    ap.add_argument("--extra-helper-pos",type=int)
    ap.add_argument("--timeout-ms",type=int,default=300000)
    ap.add_argument("--out",required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    c,s=solve(base,args.projection_weight,args.deviation_index,args.deviation_rank,
              args.helpers,args.extra_helper_pos,args.timeout_ms)
    if c is not None: (out/"candidate.json").write_text(json.dumps(c,indent=2)+"\n")
    (out/"summary.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n")
    print(json.dumps(s,sort_keys=True),flush=True)

if __name__=="__main__":main()
