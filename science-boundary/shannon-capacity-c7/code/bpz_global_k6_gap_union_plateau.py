#!/usr/bin/env python3
"""Largest exact neutral move in the union of all 32 k6 cover-gap factor pools.

Primary objective is true score gain; secondary objective is number of selected
new vertices.  Each of the 18 terminal baselines is modeled independently with
exact shared old-point deletions and all new-new conflicts.  The resulting best
nonempty gain-0 state is a verifier-valid distant 134753 mother state; a positive
gain would already be a breakthrough candidate.
"""
from __future__ import annotations
import argparse,json,multiprocessing as mp,os
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery
from bpz_global_k6_gap_union_prize import owner_sets
G={}
def init_worker(s):
    global G;G=s

def solve_task(t):
    q,r,o=t;ring,B,fam,U,Uv,core=G["ring"],G["B"],G["fam"],G["U"],G["Uv"],G["core"]
    P=terminal_periphery(fam,q,r,o);baseline=core|P
    if len(baseline)!=134753:raise RuntimeError(("baseline",len(baseline)))
    cand=sorted((x,y) for x in Uv for y in Uv if (x,y) not in baseline);idx={p:i for i,p in enumerate(cand)};byfirst={}
    for p in P:byfirst.setdefault(p[0],[]).append(p)
    fk=set(byfirst);losses=[]
    for x,y in cand:
        L={(a,b) for a in ring.NB[x]&B for b in ring.NB[y]&B}
        for a in ring.NB[x]&fk:
            for p in byfirst[a]:
                if p[1] in ring.NB[y]:L.add(p)
        if not L<=baseline:raise RuntimeError(("loss outside baseline",len(L-baseline)))
        losses.append(L)
    n=len(cand);touched=sorted(set().union(*losses));bi={p:i for i,p in enumerate(touched)};w=WCNF()
    for i,L in enumerate(losses):
        for p in L:w.append([-(i+1),n+bi[p]+1])
    conflicts=0
    for i,(x,y) in enumerate(cand):
        for a in ring.NB[x]&U:
            for b in ring.NB[y]&U:
                j=idx.get((a,b))
                if j is not None and j>i:w.append([-(i+1),-(j+1)]);conflicts+=1
    M=n+1
    for i in range(n):w.append([i+1],weight=M+1)
    for j in range(len(touched)):w.append([-(n+j+1)],weight=M)
    with RC2(w,solver="g4",adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute()
    if model is None:raise RuntimeError("RC2 no model")
    pos={z for z in model if z>0};sel=[i for i in range(n) if i+1 in pos];lost={touched[j] for j in range(len(touched)) if n+j+1 in pos};forced=set()
    for i in sel:forced.update(losses[i])
    if lost!=forced:raise RuntimeError(("loss mismatch",len(lost),len(forced)))
    selected=[cand[i] for i in sel];gain=len(selected)-len(lost)
    for i,p in enumerate(selected):
        for z in selected[i+1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("new-new",p,z))
        for z in baseline-lost:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("retained",p,z))
    return {"q":q,"r":r,"terminal_orientation":o,"gain":gain,"selected":len(selected),"deleted":len(lost),"candidates":n,"touched_blockers":len(touched),"conflicts":conflicts,"selected_points":[list(p) for p in selected],"deleted_points":[list(p) for p in sorted(lost)]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("tan_root",type=Path);ap.add_argument("k6_json",type=Path);ap.add_argument("output",type=Path);ap.add_argument("certificate",type=Path);ap.add_argument("--workers",type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    _base,ring,B,fam=load_geometry(a.tan_root.resolve());B=set(B);Cs=owner_sets(a.k6_json.resolve());U={z for z in range(ring.n) if any((ring.NB[z]&B)<=C for C in Cs)};Uv=sorted(U);core={(x,y) for x in B for y in B};tasks=[(q,r,o) for q in ("O","H","V") for r in ("O","H","V") for o in (0,1)]
    state={"ring":ring,"B":B,"fam":fam,"U":U,"Uv":Uv,"core":core};workers=max(1,min(a.workers,4,len(tasks)));ctx=mp.get_context("fork")
    with ctx.Pool(workers,initializer=init_worker,initargs=(state,)) as p:rows=list(p.imap_unordered(solve_task,tasks,chunksize=1))
    rows.sort(key=lambda z:(z["gain"],z["selected"],-z["deleted"]),reverse=True);best=rows[0]
    if best["selected"]<=0:raise RuntimeError(("no nonempty optimum",best))
    P=terminal_periphery(fam,best["q"],best["r"],best["terminal_orientation"]);baseline=core|P;sel={tuple(p) for p in best["selected_points"]};lost={tuple(p) for p in best["deleted_points"]};cand=(baseline-lost)|sel
    if len(cand)!=134753+best["gain"]:raise RuntimeError(("score",len(cand),best["gain"]))
    def enc(p):return "".join(str(z) for z in ring.decode(p[0])+ring.decode(p[1]))
    pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({"points":pts},separators=(",",":"))+"\n")
    out={"method":"exact-lexicographic-global-k6-gap-union","owner_sets":len(Cs),"union_factor_pool":len(U),"scenario_count":len(rows),"workers":workers,"best":best,"top10":rows[:10],"candidate_score":len(pts)};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({k:v for k,v in out.items() if k!="top10"},sort_keys=True))
if __name__=="__main__":main()
