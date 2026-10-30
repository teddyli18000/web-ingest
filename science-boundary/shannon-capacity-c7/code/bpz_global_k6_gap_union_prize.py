#!/usr/bin/env python3
"""Exact nonrectangular prize search over all 32 k=6 cover-gap support sets.

The 28 reducible k6 gaps cannot improve as isolated 6->7 replacements, but their
complete factor pools may contain vertices absent from the five irreducible raw
+1 pools. This search unions the complete pools P_C for every exact k6 gap and
optimizes arbitrary independent subsets of UxU against each complete 134753 BPZ
terminal baseline. Core/periphery deletions are shared globally, so this covers
nonrectangular unions of footprint rectangles. Maximum closure is only an upper
bound gate; open terminals are solved exactly by weighted MaxSAT.
"""
from __future__ import annotations
import argparse,json,os
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_global_defect_union_prize import max_closure
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery
PINNED_COMMIT="c753408492dde92a239708986d16c15dbf6c3235"

def owner_sets(path:Path):
    d=json.loads(path.read_text()); rows=d.get("cover_gap_cases",[])
    if d.get("k")!=6 or len(rows)!=32: raise RuntimeError(("k6 gap input",d.get("k"),len(rows)))
    out=[]
    for z in rows:
        C=frozenset(map(int,z["owners"]));
        if len(C)!=6: raise RuntimeError(("owners",C))
        out.append(C)
    return out

def solve(task):
    root_s,k6_s,q,r,o=task; root=Path(root_s)
    _base,ring,B,fam=load_geometry(root); B=set(B); Cs=owner_sets(Path(k6_s))
    P=terminal_periphery(fam,q,r,o); core={(a,b) for a in B for b in B}; baseline=core|P
    if len(baseline)!=134753: raise RuntimeError(("baseline",len(baseline)))
    U={z for z in range(ring.n) if any((ring.NB[z]&B)<=C for C in Cs)}
    Uv=sorted(U); cand=sorted((x,y) for x in Uv for y in Uv if (x,y) not in baseline); idx={p:i for i,p in enumerate(cand)}
    byfirst={}
    for p in P: byfirst.setdefault(p[0],[]).append(p)
    fk=set(byfirst); losses=[]
    for x,y in cand:
        L={(a,b) for a in ring.NB[x]&B for b in ring.NB[y]&B}
        for a in ring.NB[x]&fk:
            for p in byfirst[a]:
                if p[1] in ring.NB[y]: L.add(p)
        if not L<=baseline: raise RuntimeError(("loss outside baseline",(x,y),len(L-baseline)))
        losses.append(L)
    rg,rs,rl=max_closure(losses)
    out={"q":q,"r":r,"terminal_orientation":o,"owner_sets":len(Cs),"union_factor_pool":len(U),"candidates":len(cand),"relax_gain":rg,"relax_selected":len(rs),"relax_deleted":len(rl),"exact_gain":None,"status":"relax-closed" if rg<=0 else "relax-positive"}
    if rg<=0:return out
    touched=sorted(set().union(*losses)); bi={p:i for i,p in enumerate(touched)}; n=len(cand)
    w=WCNF(); implications=0
    for i,L in enumerate(losses):
        for p in L: w.append([-(i+1),n+bi[p]+1]); implications+=1
    conflicts=0
    for i,(x,y) in enumerate(cand):
        for a in ring.NB[x]&U:
            for b in ring.NB[y]&U:
                j=idx.get((a,b))
                if j is not None and j>i: w.append([-(i+1),-(j+1)]);conflicts+=1
    for i in range(n):w.append([i+1],weight=1)
    for j in range(len(touched)):w.append([-(n+j+1)],weight=1)
    with RC2(w,solver="g4",adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError("RC2 no model")
    pos={z for z in model if z>0}; sel=[i for i in range(n) if i+1 in pos]; lost={touched[j] for j in range(len(touched)) if n+j+1 in pos}; forced=set()
    for i in sel:forced.update(losses[i])
    if lost!=forced:raise RuntimeError(("loss mismatch",len(lost),len(forced)))
    gain=len(sel)-len(lost)
    if gain!=n-cost:raise RuntimeError(("objective",gain,n-cost))
    selected=[cand[i] for i in sel]
    for i,p in enumerate(selected):
        for z in selected[i+1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("new-new",p,z))
        for z in baseline-lost:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(("retained",p,z))
    out.update(status="exact-rc2",exact_gain=gain,selected=len(sel),deleted=len(lost),touched_blockers=len(touched),conflict_clauses=conflicts,implications=implications)
    if gain>0:out["selected_points"]=[list(p) for p in selected];out["deleted_points"]=[list(p) for p in sorted(lost)]
    return out

def materialize(root:Path,best,out:Path):
    _base,ring,B,fam=load_geometry(root);P=terminal_periphery(fam,best["q"],best["r"],best["terminal_orientation"]);base={(a,b) for a in B for b in B}|P
    sel={tuple(p) for p in best["selected_points"]};lost={tuple(p) for p in best["deleted_points"]};cand=(base-lost)|sel
    if len(cand)!=134753+int(best["exact_gain"]):raise RuntimeError(("score",len(cand)))
    def enc(p):return "".join(str(z) for z in ring.decode(p[0])+ring.decode(p[1]))
    pts=sorted(enc(p) for p in cand);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({"points":pts},separators=(",",":"))+"\n");return len(pts)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("tan_root",type=Path);ap.add_argument("k6_json",type=Path);ap.add_argument("output",type=Path);ap.add_argument("certificate",type=Path);ap.add_argument("--workers",type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    tasks=[(str(a.tan_root.resolve()),str(a.k6_json.resolve()),q,r,o) for q in ("O","H","V") for r in ("O","H","V") for o in (0,1)];workers=max(1,min(a.workers,4,len(tasks)));rows=[]
    if workers==1: rows=[solve(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs=[ex.submit(solve,t) for t in tasks]
            for f in as_completed(fs):rows.append(f.result())
    rows.sort(key=lambda x:((x.get("exact_gain") if x.get("exact_gain") is not None else -10**9),x["relax_gain"]),reverse=True);exact=[x for x in rows if x.get("exact_gain") is not None];best=max(exact,key=lambda x:x["exact_gain"]) if exact else max(rows,key=lambda x:x["relax_gain"]);score=None
    if best.get("exact_gain",0)>0:score=materialize(a.tan_root.resolve(),best,a.certificate)
    out={"method":"exact-global-k6-gap-union-prize","source_commit":PINNED_COMMIT,"scenario_count":len(rows),"workers":workers,"exact_solved":len(exact),"positive_exact":sum((x.get("exact_gain") or 0)>0 for x in rows),"best":best,"rows":rows,"candidate_materialized":score is not None,"candidate_score":score};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n");print(json.dumps({k:v for k,v in out.items() if k!="rows"},sort_keys=True))
if __name__=="__main__":main()
