#!/usr/bin/env python3
"""Measure Boyar-Peralta-style support distance from a released-AND prefix.

Extended-BP defines target distance as the minimum number of currently available
signals whose XOR equals the target, minus one.  In the Few Shots model XNOR has
the same cost as XOR, so for support size >=2 we also allow a free affine constant
flip (target^C) on one combining gate.

For the ~97-signal 56-linear prefixes, exact minimum support through six signals
is cheap via meet-in-the-middle sets of pair and triple XORs.  This gives a useful
long-range metric where the previous <=2-gate reachability test is flat.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib

import released_and_skeleton as ras
import rnbp_prefix_variant_tail as pv


def xor_sets(S):
    xs=sorted(S)
    pairs=set()
    for i,a in enumerate(xs):
        for b in xs[i+1:]: pairs.add(a^b)
    triples=set()
    n=len(xs)
    for i in range(n):
        a=xs[i]
        for j in range(i+1,n):
            ab=a^xs[j]
            for k in range(j+1,n): triples.add(ab^xs[k])
    return pairs,triples


def min_support(t,S,pairs,triples,C,max_support=6):
    if t in S: return 1
    goals=(t,t^C)
    if max_support>=2 and any(g in pairs for g in goals): return 2
    if max_support>=3 and any(g in triples for g in goals): return 3
    if max_support>=4:
        for g in goals:
            if any((g^p) in pairs for p in pairs): return 4
    if max_support>=5:
        # Iterate the smaller pair set against the triple table.
        for g in goals:
            if any((g^p) in triples for p in pairs): return 5
    if max_support>=6:
        for g in goals:
            if any((g^a) in triples for a in triples): return 6
    return None


def representation_counts(t,pairs,triples,C):
    out={}
    # Count meet-in-middle value matches, useful as a crude density signal.
    c4=c5=c6=0
    for g in (t,t^C):
        c4 += sum(1 for p in pairs if (g^p) in pairs)
        c5 += sum(1 for p in pairs if (g^p) in triples)
        c6 += sum(1 for a in triples if (g^a) in triples)
    out["mitm4_hits"]=c4
    out["mitm5_hits"]=c5
    out["mitm6_hits"]=c6
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--family",choices=sorted(ras.SOURCES),default="fs-101")
    ap.add_argument("--projection-weight",type=float,default=0.24)
    ap.add_argument("--deviation-index",type=int,required=True)
    ap.add_argument("--deviation-rank",type=int,required=True)
    ap.add_argument("--max-support",type=int,default=6)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    base=ras.load_circuit(args.family); assert ras.independent_check(base)[0]
    sk,S,names,gates,plin,stage,soft,applied,trace=pv.build_variant(
        base,args.projection_weight,args.deviation_index,args.deviation_rank,67)
    if not applied or stage!=sk["n_and"]:
        raise SystemExit(f"prefix incomplete: applied={applied} stage={stage}")
    pairs,triples=xor_sets(S); C=1<<sk["const_bit"]
    rows=[]
    for i,t in enumerate(sk["outputs"]):
        d=min_support(t,S,pairs,triples,C,args.max_support)
        row={"output":i,"min_support_leq":d,
             "bp_distance_leq":None if d is None else d-1}
        row.update(representation_counts(t,pairs,triples,C))
        rows.append(row)
    summary={"prefix_linear":plin,"available_signals":len(S),
             "pair_xors":len(pairs),"triple_xors":len(triples),
             "deviation_index":args.deviation_index,"deviation_rank":args.deviation_rank,
             "max_support":args.max_support,"outputs":rows}
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=="__main__":main()
