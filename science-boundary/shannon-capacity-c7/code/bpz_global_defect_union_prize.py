#!/usr/bin/env python3
"""Exact prize search over the union of all five irreducible BPZ support defects.

Previous exact rectangle searches fixed one ordered defect pair (C_i,C_j) at a
time.  This model instead forms the union U of all five complete factor pools

    P_C = {z in C7^5 : N[z] intersect B subseteq C}

and optimizes arbitrary independent subsets of U x U against one complete
134753-point BPZ terminal baseline.  For every selected new point n=(x,y), all
old baseline points conflicting with n must be deleted.  Core blockers are
exactly

    (N[x] intersect B) x (N[y] intersect B),

so sharing of deleted core cells across different defect rectangles is priced
once.  Peripheral blockers are likewise shared.  Thus the model permits
non-Cartesian mixtures and genuinely nonrectangular unions of core holes inside
this finite candidate universe.

For each of the 18 public terminal configurations we first solve the maximum
closure relaxation that ignores new-new conflicts.  Only a positive relaxation
is sent to exact weighted MaxSAT.  Hard clauses enforce candidate independence
and every required deletion; soft clauses maximize selected-new minus deleted-old.
Any positive optimum is independently replayed and materialized as a Few Shots
certificate for the upstream verifier.
"""
from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from bpz_amplify_row_defects import Dinic
from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery, validate_defects

PINNED_COMMIT = "c753408492dde92a239708986d16c15dbf6c3235"


def max_closure(losses: list[set[tuple[int,int]]]):
    touched = sorted(set().union(*losses)) if losses else []
    bi = {p:i for i,p in enumerate(touched)}
    n, m = len(losses), len(touched)
    s, t = n+m, n+m+1
    d = Dinic(t+1)
    inf = n+m+10
    for i, ls in enumerate(losses):
        d.add(s,i,1)
        for p in ls:
            d.add(i,n+bi[p],inf)
    for j in range(m): d.add(n+j,t,1)
    cut=d.flow(s,t); side=d.source_side(s)
    chosen=[i for i in range(n) if i in side]
    lost=set()
    for i in chosen: lost.update(losses[i])
    gain=len(chosen)-len(lost)
    if gain != n-cut: raise RuntimeError(("closure mismatch",gain,n-cut))
    return gain,chosen,lost


def solve_scenario(task):
    root_s,q,r,o=task; root=Path(root_s)
    _base,ring,B,fam=load_geometry(root)
    defects=validate_defects(ring,B)
    P=terminal_periphery(fam,q,r,o)
    core={(a,b) for a in B for b in B}
    baseline=core|P
    if len(baseline)!=134753: raise RuntimeError(("baseline size",len(baseline)))

    # Complete factor pools, including support-zero endpoints and deleted owners.
    pools=[]; U=set()
    for d in defects:
        C=d["C"]
        pc={z for z in range(ring.n) if (ring.NB[z]&B) <= C}
        pools.append(pc); U.update(pc)
    pool_sizes=[len(x) for x in pools]
    if pool_sizes != [37,40,39,39,39]: raise RuntimeError(("factor pool drift",pool_sizes))
    U=sorted(U); Us=set(U)

    candidates=sorted((x,y) for x in U for y in U if (x,y) not in baseline)
    ci={p:i for i,p in enumerate(candidates)}

    # Index the periphery by first coordinate for exact conflict lookups.
    by_first={}
    for p in P: by_first.setdefault(p[0],[]).append(p)
    first_keys=set(by_first)

    losses=[]
    for x,y in candidates:
        hit={(a,b) for a in (ring.NB[x]&B) for b in (ring.NB[y]&B)}
        for a in ring.NB[x]&first_keys:
            for p in by_first[a]:
                if p[1] in ring.NB[y]: hit.add(p)
        if not hit or not hit <= baseline:
            # Empty loss would be a direct add-1 and is allowed mathematically,
            # but it should not occur for a verified record baseline.
            if not hit: pass
            else: raise RuntimeError(("blocker outside baseline",(x,y),len(hit-baseline)))
        losses.append(hit)

    relax_gain,relax_sel,relax_lost=max_closure(losses)
    result={
        "q":q,"r":r,"terminal_orientation":o,
        "factor_pool_sizes":pool_sizes,"union_factor_pool":len(U),
        "candidates":len(candidates),"relax_gain":relax_gain,
        "relax_selected":len(relax_sel),"relax_deleted":len(relax_lost),
        "status":"relax-closed" if relax_gain<=0 else "relax-positive",
        "exact_gain":None,"selected":0,"deleted":0,
    }
    if relax_gain<=0: return result

    touched=sorted(set().union(*losses)); bi={p:i for i,p in enumerate(touched)}
    nc=len(candidates)
    def xv(i): return i+1
    def zv(j): return nc+j+1
    w=WCNF(); implications=0
    for i,ls in enumerate(losses):
        for p in ls:
            w.append([-xv(i),zv(bi[p])]); implications+=1

    # Strong-product conflicts generated through the small factor universe.
    conflict_clauses=0
    for i,(x,y) in enumerate(candidates):
        for a in ring.NB[x]&Us:
            for b in ring.NB[y]&Us:
                j=ci.get((a,b))
                if j is not None and j>i:
                    w.append([-xv(i),-xv(j)]); conflict_clauses+=1
    for i in range(nc): w.append([xv(i)],weight=1)
    for j in range(len(touched)): w.append([-zv(j)],weight=1)

    with RC2(w,solver="g4",adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute(); cost=rc2.cost
    if model is None: raise RuntimeError("RC2 no model")
    pos={z for z in model if z>0}
    sel=[i for i in range(nc) if xv(i) in pos]
    lost={touched[j] for j in range(len(touched)) if zv(j) in pos}
    forced=set()
    for i in sel: forced.update(losses[i])
    if lost != forced: raise RuntimeError(("loss mismatch",len(lost),len(forced)))
    gain=len(sel)-len(lost)
    if gain != nc-cost: raise RuntimeError(("objective mismatch",gain,nc-cost))

    # Independent replay of selected-selected compatibility and retained baseline.
    selected=[candidates[i] for i in sel]
    for i,p in enumerate(selected):
        x,y=p
        for z in selected[i+1:]:
            if z[0] in ring.NB[x] and z[1] in ring.NB[y]:
                raise RuntimeError(("selected conflict",p,z))
        for old in baseline-lost:
            if old[0] in ring.NB[x] and old[1] in ring.NB[y]:
                raise RuntimeError(("retained blocker",p,old))

    result.update({
        "status":"exact-rc2","exact_gain":gain,"selected":len(sel),
        "deleted":len(lost),"touched_blockers":len(touched),
        "conflict_clauses":conflict_clauses,"implications":implications,
    })
    if gain>0:
        result["selected_points"]=[list(p) for p in selected]
        result["deleted_points"]=[list(p) for p in sorted(lost)]
    return result


def materialize(root:Path,best,out:Path):
    _base,ring,B,fam=load_geometry(root)
    P=terminal_periphery(fam,best["q"],best["r"],best["terminal_orientation"])
    baseline={(a,b) for a in B for b in B}|P
    selected={tuple(map(int,p)) for p in best["selected_points"]}
    deleted={tuple(map(int,p)) for p in best["deleted_points"]}
    cand=(baseline-deleted)|selected
    if len(cand)!=134753+int(best["exact_gain"]): raise RuntimeError(("score",len(cand)))
    def enc(p): return "".join(str(z) for z in (ring.decode(p[0])+ring.decode(p[1])))
    pts=sorted(enc(p) for p in cand)
    if len(pts)!=len(set(pts)): raise RuntimeError("duplicates")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"points":pts},separators=(",",":"))+"\n")
    return len(pts)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("tan_root",type=Path); ap.add_argument("output",type=Path); ap.add_argument("certificate",type=Path); ap.add_argument("--workers",type=int,default=max(1,os.cpu_count() or 1)); a=ap.parse_args()
    root=a.tan_root.resolve()
    tasks=[(str(root),q,r,o) for q in ("O","H","V") for r in ("O","H","V") for o in (0,1)]
    workers=max(1,min(a.workers,4,len(tasks)))
    rows=[]
    if workers==1:
        rows=[solve_scenario(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs=[ex.submit(solve_scenario,t) for t in tasks]
            for f in as_completed(fs): rows.append(f.result())
    rows.sort(key=lambda x: ((x["exact_gain"] if x["exact_gain"] is not None else -10**9),x["relax_gain"]),reverse=True)
    exact=[x for x in rows if x["exact_gain"] is not None]
    best=max(exact,key=lambda x:x["exact_gain"]) if exact else max(rows,key=lambda x:x["relax_gain"])
    score=None
    if best.get("exact_gain",0)>0: score=materialize(root,best,a.certificate)
    out={"method":"exact-global-five-defect-union-prize","source_commit":PINNED_COMMIT,"scenario_count":len(rows),"workers":workers,"exact_solved":len(exact),"positive_exact":sum((x.get("exact_gain") or 0)>0 for x in rows),"best":best,"rows":rows,"candidate_materialized":score is not None,"candidate_score":score}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps({k:v for k,v in out.items() if k!="rows"},sort_keys=True))

if __name__=="__main__": main()
