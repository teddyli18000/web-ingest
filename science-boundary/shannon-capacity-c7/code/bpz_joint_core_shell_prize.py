#!/usr/bin/env python3
"""Exact real 10D prize on the minimal joint-injection obstruction and its owner shell.

The deletion-minimal joint factor/product injection obstruction from run 41233690857
contains six regular support<=2 factors and the four first support3 exceptions.
Proof failure is not a construction, so this script asks the real score question.

Two nested factor universes are optimized over all 18 pinned BPZ terminal baselines:
  core10: exactly the 10 obstruction factors;
  owner-shell: every outside factor of support size <=3 whose exact support is
               contained in the union of core10's core owners.

For every ordered product point we price every conflicting old baseline point
(BxB plus terminal periphery) exactly. Shared deletions are paid once. A maximum-
closure relaxation gates the expensive step; any positive survivor is solved by
weighted MaxSAT with all new-new strong-product conflicts. Positive exact gain is
materialized as a full Few Shots certificate.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from bpz_amplify_row_defects import Dinic
from bpz_joint_row_defects_maxsat import load_geometry, terminal_periphery

PINNED_COMMIT='c753408492dde92a239708986d16c15dbf6c3235'
SOURCE_CORE_RUN=41233690857
CORE_REGULAR=(15759,13359,13109,3813,1504,1299)
EXCEPTIONS=(1012,1025,1285,3722)
CORE_FACTORS=tuple(sorted(set(CORE_REGULAR+EXCEPTIONS)))


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
    for i in chosen: lost.update(losses[i])
    gain=len(chosen)-len(lost)
    if gain!=n-cut: raise RuntimeError(('closure mismatch',gain,n-cut))
    return gain,chosen,lost


def factor_universes(root:Path):
    _base,ring,B,_fam=load_geometry(root); B=set(B)
    support={}
    for z in range(ring.n):
        if z in B: continue
        S=frozenset(ring.NB[z]&B)
        if S: support[z]=S
    for z in CORE_FACTORS:
        if z not in support or len(support[z])>3: raise RuntimeError(('core support drift',z,support.get(z)))
    owners=frozenset().union(*(support[z] for z in CORE_FACTORS))
    shell=tuple(sorted(z for z,S in support.items() if 1<=len(S)<=3 and S<=owners))
    if not set(CORE_FACTORS)<=set(shell): raise RuntimeError('core not in shell')
    return ring,B,support,owners,{'core10':CORE_FACTORS,'owner-shell':shell}


def product_conflict(ring,p,q):
    return q[0] in ring.NB[p[0]] and q[1] in ring.NB[p[1]]


def solve_task(task):
    root_s,mode,factors,q,r,o=task; root=Path(root_s)
    _base,ring,B,fam=load_geometry(root); B=set(B); F=tuple(map(int,factors)); FS=set(F)
    support={z:frozenset(ring.NB[z]&B) for z in F}
    P=terminal_periphery(fam,q,r,o); core={(a,b) for a in B for b in B}; baseline=core|P
    if len(baseline)!=134753: raise RuntimeError(('baseline',len(baseline)))
    candidates=sorted((x,y) for x in F for y in F if (x,y) not in baseline)
    ci={p:i for i,p in enumerate(candidates)}
    by_first={}
    for p in P: by_first.setdefault(p[0],[]).append(p)
    first_keys=set(by_first)
    losses=[]
    for x,y in candidates:
        hit={(a,b) for a in support[x] for b in support[y]}
        for a in ring.NB[x]&first_keys:
            for p in by_first[a]:
                if p[1] in ring.NB[y]: hit.add(p)
        if not hit<=baseline: raise RuntimeError(('loss outside baseline',(x,y),len(hit-baseline)))
        losses.append(hit)
    cg,cs,cd=max_closure(losses)
    result={'mode':mode,'q':q,'r':r,'terminal_orientation':o,'factor_count':len(F),'candidate_count':len(candidates),'closure_gain':cg,'closure_selected':len(cs),'closure_deleted':len(cd),'exact_gain':None,'selected':0,'deleted':0,'status':'closure-closed' if cg<=0 else 'closure-positive'}
    if cg<=0: return result
    touched=sorted(set().union(*losses)); bi={p:i for i,p in enumerate(touched)}; n=len(candidates); y0=n+1
    w=WCNF(); impl=0; confs=0
    for i,ls in enumerate(losses):
        for p in ls: w.append([-(i+1),y0+bi[p]]); impl+=1
    for i,p in enumerate(candidates):
        for j in range(i+1,len(candidates)):
            if product_conflict(ring,p,candidates[j]):
                w.append([-(i+1),-(j+1)]); confs+=1
    for i in range(n): w.append([i+1],weight=1)
    for j in range(len(touched)): w.append([-(y0+j)],weight=1)
    ts=time.time()
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute(); cost=rc2.cost
    if model is None: raise RuntimeError('no RC2 model')
    pos={z for z in model if z>0}; sel=[i for i in range(n) if i+1 in pos]
    lost=set();
    for i in sel: lost.update(losses[i])
    gain=len(sel)-len(lost)
    if gain!=n-cost: raise RuntimeError(('objective drift',gain,n-cost))
    selected=[candidates[i] for i in sel]
    for i,p in enumerate(selected):
        for q2 in selected[i+1:]:
            if product_conflict(ring,p,q2): raise RuntimeError(('selected conflict',p,q2))
    forced=set();
    for i in sel: forced.update(losses[i])
    if forced!=lost: raise RuntimeError('loss replay drift')
    result.update(status='exact-rc2',exact_gain=gain,selected=len(sel),deleted=len(lost),touched_blockers=len(touched),conflict_clauses=confs,implications=impl,exact_seconds=time.time()-ts)
    if gain>0:
        result['selected_points']=[list(p) for p in selected]; result['deleted_points']=[list(p) for p in sorted(lost)]
    return result


def materialize(root:Path,best,out:Path):
    _base,ring,B,fam=load_geometry(root); P=terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']); baseline={(a,b) for a in B for b in B}|P
    selected={tuple(map(int,p)) for p in best['selected_points']}; deleted={tuple(map(int,p)) for p in best['deleted_points']}; cand=(baseline-deleted)|selected
    score=len(cand)
    if score!=134753+int(best['exact_gain']): raise RuntimeError(('score',score,best['exact_gain']))
    def enc(p): return ''.join(str(z) for z in (ring.decode(p[0])+ring.decode(p[1])))
    pts=sorted(enc(p) for p in cand)
    if len(pts)!=len(set(pts)): raise RuntimeError('duplicates')
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    return score


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('certificate',type=Path); ap.add_argument('--workers',type=int,default=4); a=ap.parse_args(); root=a.tan_root.resolve()
    ring,B,support,owners,universes=factor_universes(root)
    tasks=[]
    for mode,F in universes.items():
        for q in ('O','H','V'):
            for r in ('O','H','V'):
                for o in (0,1): tasks.append((str(root),mode,F,q,r,o))
    rows=[]; workers=max(1,min(int(a.workers),4,len(tasks)))
    if workers==1: rows=[solve_task(t) for t in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs=[ex.submit(solve_task,t) for t in tasks]
            for f in as_completed(fs): rows.append(f.result())
    rows.sort(key=lambda x:((x.get('exact_gain') if x.get('exact_gain') is not None else -10**9),x['closure_gain']),reverse=True)
    positive=[x for x in rows if (x.get('exact_gain') or 0)>0]; best=positive[0] if positive else rows[0]; score=None
    if positive: score=materialize(root,best,a.certificate)
    out={'method':'exact-joint-injection-core-owner-shell-terminal-prize','source_core_run':SOURCE_CORE_RUN,'source_commit':PINNED_COMMIT,'core_factors':list(CORE_FACTORS),'owner_union':sorted(owners),'owner_count':len(owners),'universe_sizes':{k:len(v) for k,v in universes.items()},'scenario_count':len(rows),'workers':workers,'positive_exact':len(positive),'best':best,'candidate_materialized':bool(positive),'candidate_score':score,'rows':rows}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='rows'},sort_keys=True))

if __name__=='__main__': main()
