#!/usr/bin/env python3
"""Largest neutral exchange in the union of all 32 k6 cover-gap factor pools.

Primary objective is exact score gain selected_new - deleted_baseline. Secondary
objective is selected_new cardinality. For n candidates set M=n+1 and use soft
weight M+1 on selecting each new point and M on keeping each touched baseline
point. One unit of primary gain dominates every possible secondary difference.
"""
from __future__ import annotations
import argparse,json,os
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_global_k6_gap_union_prize import owner_sets
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery


def solve(task):
    root_s,k6_s,q,r,o=task; root=Path(root_s)
    _base,ring,B,fam=load_geometry(root);B=set(B);Cs=owner_sets(Path(k6_s))
    P=terminal_periphery(fam,q,r,o);core={(a,b) for a in B for b in B};baseline=core|P
    if len(baseline)!=134753:raise RuntimeError(("baseline",len(baseline)))
    U={z for z in range(ring.n) if any((ring.NB[z]&B)<=C for C in Cs)};Uv=sorted(U)
    cand=sorted((x,y) for x in Uv for y in Uv if (x,y) not in baseline);idx={p:i for i,p in enumerate(cand)}
    byfirst={}
    for p in P:byfirst.setdefault(p[0],[]).append(p)
    fk=set(byfirst);losses=[]
    for x,y in cand:
        L={(a,b) for a in ring.NB[x]&B for b in ring.NB[y]&B}
        for a in ring.NB[x]&fk:
            for p in byfirst[a]:
                if p[1] in ring.NB[y]:L.add(p)
        if not L<=baseline:raise RuntimeError(("loss outside",(x,y),len(L-baseline)))
        losses.append(L)
    touched=sorted(set().union(*losses));bi={p:i for i,p in enumerate(touched)};n=len(cand);M=n+1;w=WCNF();imp=0
    for i,L in enumerate(losses):
        for p in L:w.append([-(i+1),n+bi[p]+1]);imp+=1
    conflicts=0
    for i,(x,y) in enumerate(cand):
        for a in ring.NB[x]&U:
            for b in ring.NB[y]&U:
                j=idx.get((a,b))
                if j is not None and j>i:w.append([-(i+1),-(j+1)]);conflicts+=1
    for i in range(n):w.append([i+1],weight=M+1)
    for j in range(len(touched)):w.append([-(n+j+1)],weight=M)
    with RC2(w,solver="g4",adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute()
    if model is None:raise RuntimeError("RC2 no model")
    pos={z for z in model if z>0};sel=[i for i in range(n) if i+1 in pos];lost={touched[j] for j in range(len(touched)) if n+j+1 in pos};forced=set()
    for i in sel:forced.update(losses[i])
    if lost!=forced:raise RuntimeError(("loss mismatch",len(lost),len(forced)))
    selected=[cand[i] for i in sel]
    for i,p in enumerate(selected):
        for z in selected[i+1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("new-new",p,z))
        for z in baseline-lost:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("retained",p,z))
    gain=len(selected)-len(lost)
    return {"q":q,"r":r,"terminal_orientation":o,"owner_sets":len(Cs),"union_factor_pool":len(U),"candidates":n,"selected":len(selected),"deleted":len(lost),"gain":gain,"score":134753+gain,"touched_blockers":len(touched),"conflict_clauses":conflicts,"implications":imp,"selected_points":[list(p) for p in selected],"deleted_points":[list(p) for p in sorted(lost)]}


def materialize(root,best,out):
    _base,ring,B,fam=load_geometry(root);P=terminal_periphery(fam,best["q"],best["r"],best["terminal_orientation"]);base={(a,b) for a in B for b in B}|P
    sel={tuple(p) for p in best["selected_points"]};lost={tuple(p) for p in best["deleted_points"]};cand=(base-lost)|sel
    if len(cand)!=134753+best["gain"]:raise RuntimeError(("score",len(cand),best["gain"]))
    def enc(p):return "".join(str(z) for z in ring.decode(p[0])+ring.decode(p[1]))
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({"points":sorted(enc(p) for p in cand)},separators=(",",":"))+"\n");return len(cand)


def main():
    ap=argparse.ArgumentParser();ap.add_argument("tan_root",type=Path);ap.add_argument("k6_json",type=Path);ap.add_argument("output",type=Path);ap.add_argument("certificate",type=Path);ap.add_argument("--workers",type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    tasks=[(str(a.tan_root.resolve()),str(a.k6_json.resolve()),q,r,o) for q in ("O","H","V") for r in ("O","H","V") for o in (0,1)];workers=max(1,min(a.workers,4,len(tasks)));rows=[]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        fs=[ex.submit(solve,t) for t in tasks]
        for f in as_completed(fs):rows.append(f.result())
    rows.sort(key=lambda x:(x["gain"],x["selected"],-x["deleted"]),reverse=True);best=rows[0];score=None
    if best["selected"]>0 and best["gain"]>=0:score=materialize(a.tan_root.resolve(),best,a.certificate)
    out={"method":"exact-lexicographic-global-k6-gap-neutral-plateau","scenario_count":len(rows),"workers":workers,"positive_gain":sum(x["gain"]>0 for x in rows),"nonempty_neutral":sum(x["gain"]==0 and x["selected"]>0 for x in rows),"best":best,"rows":rows,"candidate_materialized":score is not None,"candidate_score":score};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({k:v for k,v in out.items() if k!="rows"},sort_keys=True))
if __name__=="__main__":main()
