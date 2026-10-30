#!/usr/bin/env python3
"""Exact 10D terminal prize over the minimal support<=3 owner-assignment obstruction.

The support<=3 owner-clique list-SAT (run 41046652519) returned a 64-factor
assumption core. Independent deletion replay shrinks it to the 63-factor set
below: deleting any one of these factors makes the owner-clique assignment
feasible. This script does not assume that failure of the injection proof gives
a construction; it asks the real ten-dimensional question.

For every BPZ terminal scenario, candidate new points are all ordered pairs
F x F from this 63-factor obstruction, excluding points already in the baseline.
For each candidate we price every conflicting old baseline point exactly,
including both BxB core cells and terminal periphery. Shared deletions are paid
only once. New-new strong-product conflicts are hard clauses. Weighted MaxSAT
therefore computes the exact score gain within this focused universe. Any
positive optimum is materialized as a Few Shots certificate by the workflow.
"""
from __future__ import annotations

import argparse, json, os, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from bpz_amplify_row_defects import Dinic
from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery

PINNED_COMMIT = "c753408492dde92a239708986d16c15dbf6c3235"
SOURCE_RUN = 41046652519
# Inclusion-minimal under an independent exact CSP replay of the returned
# assumption core.  The only redundant returned core factor was z=13015.
FACTORS = (
1436,1504,1528,1595,1620,1687,1986,2046,2737,3072,3709,3813,3824,3898,
3965,3976,4075,4433,4441,4761,5125,5459,6061,6117,6146,6243,6261,6272,
6413,6494,6512,6546,6551,6821,7198,7512,7840,8156,8363,8448,8538,8605,
8617,8709,8881,9258,9900,10216,10277,10544,10613,10618,10664,10665,
10757,10878,10921,11311,12271,12276,12337,12916,13064)


def max_closure(losses):
    touched=sorted(set().union(*losses)) if losses else []
    bi={p:i for i,p in enumerate(touched)}; n=len(losses); m=len(touched)
    s=n+m; t=s+1; g=Dinic(t+1); inf=n+m+10
    for i,ls in enumerate(losses):
        g.add(s,i,1)
        for p in ls:g.add(i,n+bi[p],inf)
    for j in range(m):g.add(n+j,t,1)
    cut=g.flow(s,t); side=g.source_side(s)
    chosen=[i for i in range(n) if i in side]; lost=set()
    for i in chosen:lost.update(losses[i])
    gain=len(chosen)-len(lost)
    if gain!=n-cut:raise RuntimeError(('closure mismatch',gain,n-cut))
    return gain,chosen,lost


def solve_scenario(task):
    root_s,q,r,o=task; root=Path(root_s)
    _base,ring,B,fam=load_geometry(root); B=set(B); F=set(FACTORS)
    # Recompute all exact supports and pin the structural census.
    supports={z:frozenset(ring.NB[z]&B) for z in FACTORS}
    hist={k:sum(len(s)==k for s in supports.values()) for k in (1,2,3)}
    if hist!={1:9,2:18,3:36} or any(not s or len(s)>3 for s in supports.values()):
        raise RuntimeError(('factor/support drift',hist))
    P=terminal_periphery(fam,q,r,o); core={(a,b) for a in B for b in B}; baseline=core|P
    if len(baseline)!=134753:raise RuntimeError(('baseline',len(baseline)))
    candidates=sorted((x,y) for x in FACTORS for y in FACTORS if (x,y) not in baseline)
    ci={p:i for i,p in enumerate(candidates)}
    by_first={}
    for p in P:by_first.setdefault(p[0],[]).append(p)
    first_keys=set(by_first)
    losses=[]
    for x,y in candidates:
        hit={(a,b) for a in supports[x] for b in supports[y]}
        for a in ring.NB[x]&first_keys:
            for p in by_first[a]:
                if p[1] in ring.NB[y]:hit.add(p)
        if not hit<=baseline:raise RuntimeError(('loss outside baseline',(x,y),len(hit-baseline)))
        losses.append(hit)
    cg,cs,cd=max_closure(losses)
    result={'q':q,'r':r,'terminal_orientation':o,'factor_count':len(FACTORS),'candidate_count':len(candidates),'closure_gain':cg,'closure_selected':len(cs),'closure_deleted':len(cd),'exact_gain':None,'selected':0,'deleted':0,'status':'closure-closed' if cg<=0 else 'closure-positive'}
    if cg<=0:return result
    touched=sorted(set().union(*losses)); bi={p:i for i,p in enumerate(touched)}; nc=len(candidates)
    def xv(i):return i+1
    def zv(j):return nc+j+1
    w=WCNF(); impl=0; confs=0
    for i,ls in enumerate(losses):
        for p in ls:w.append([-xv(i),zv(bi[p])]);impl+=1
    for i,(x,y) in enumerate(candidates):
        for a in ring.NB[x]&F:
            for b in ring.NB[y]&F:
                j=ci.get((a,b))
                if j is not None and j>i:w.append([-xv(i),-xv(j)]);confs+=1
    for i in range(nc):w.append([xv(i)],weight=1)
    for j in range(len(touched)):w.append([-zv(j)],weight=1)
    t=time.time()
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('no RC2 model')
    pos={z for z in model if z>0};sel=[i for i in range(nc) if xv(i) in pos]
    lost={touched[j] for j in range(len(touched)) if zv(j) in pos};forced=set()
    for i in sel:forced.update(losses[i])
    if lost!=forced:raise RuntimeError(('loss drift',len(lost),len(forced)))
    gain=len(sel)-len(lost)
    if gain!=nc-cost:raise RuntimeError(('objective',gain,nc-cost))
    selected=[candidates[i] for i in sel]
    # Independent new-new conflict replay.
    for i,p in enumerate(selected):
        for z in selected[i+1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('selected conflict',p,z))
    result.update({'status':'exact-rc2','exact_gain':gain,'selected':len(sel),'deleted':len(lost),'touched_blockers':len(touched),'conflict_clauses':confs,'implications':impl,'exact_seconds':time.time()-t})
    if gain>0:
        result['selected_points']=[list(p) for p in selected];result['deleted_points']=[list(p) for p in sorted(lost)]
    return result


def materialize(root,best,out):
    _base,ring,B,fam=load_geometry(root);P=terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']);baseline={(a,b) for a in B for b in B}|P
    selected={tuple(map(int,p)) for p in best['selected_points']};deleted={tuple(map(int,p)) for p in best['deleted_points']};cand=(baseline-deleted)|selected
    score=len(cand)
    if score!=134753+int(best['exact_gain']):raise RuntimeError(('score',score))
    def enc(p):return ''.join(str(z) for z in (ring.decode(p[0])+ring.decode(p[1])))
    pts=sorted(enc(p) for p in cand)
    if len(pts)!=len(set(pts)):raise RuntimeError('duplicates')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n');return score


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args();root=a.tan_root.resolve()
    tasks=[(str(root),q,r,o) for q in ('O','H','V') for r in ('O','H','V') for o in (0,1)];workers=max(1,min(a.workers,4,len(tasks)))
    rows=[]
    if workers==1:rows=[solve_scenario(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs=[ex.submit(solve_scenario,t) for t in tasks]
            for f in as_completed(fs):rows.append(f.result())
    rows.sort(key=lambda x:((x['exact_gain'] if x['exact_gain'] is not None else -10**9),x['closure_gain']),reverse=True)
    positive=[x for x in rows if (x.get('exact_gain') or 0)>0];best=positive[0] if positive else rows[0];score=None
    if positive:score=materialize(root,best,a.certificate)
    out={'method':'exact-support3-mincore-product-terminal-prize','source_run':SOURCE_RUN,'source_commit':PINNED_COMMIT,'factor_count':len(FACTORS),'scenario_count':len(rows),'workers':workers,'positive_exact':len(positive),'best':best,'candidate_materialized':bool(positive),'candidate_score':score,'rows':rows}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='rows'},sort_keys=True))
if __name__=='__main__':main()
