#!/usr/bin/env python3
"""Exact global prize over genuine neutral-k5 and all k6 gap factor pools.

Owner sets are the 30 k=5 supports whose maximum independent 5-set can avoid all
deleted owners, plus all 32 exact k=6 clique-cover-gap supports.  Let U be the
union of the complete factor pools P_C={z:N_B[z] subseteq C}.  For each of the
18 BPZ terminal baselines, optimize an arbitrary independent subset of UxU with
explicit shared deletion variables for every old core/periphery blocker.

This strictly contains the simple neutral5 x k6 witness products and the prior
all-32-k6 union model, permits non-Cartesian mixtures and shared nonrectangular
core deletions, and uses maximum closure only as a rigorous upper-bound gate.
Positive exact gain is materialized for the upstream Few Shots verifier.
"""
from __future__ import annotations
import argparse,json,multiprocessing as mp,os
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_global_defect_union_prize import max_closure
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery
from bpz_global_k6_gap_union_prize import owner_sets as k6_owner_sets
G={}
def init_worker(s):
    global G;G=s

def solve_task(t):
    q,r,o=t;ring,B,fam,U,Uv,core=G['ring'],G['B'],G['fam'],G['U'],G['Uv'],G['core']
    P=terminal_periphery(fam,q,r,o);baseline=core|P
    if len(baseline)!=134753:raise RuntimeError(('baseline',len(baseline)))
    cand=sorted((x,y) for x in Uv for y in Uv if (x,y) not in baseline);idx={p:i for i,p in enumerate(cand)}
    byfirst={}
    for p in P:byfirst.setdefault(p[0],[]).append(p)
    fk=set(byfirst);losses=[]
    for x,y in cand:
        L={(a,b) for a in ring.NB[x]&B for b in ring.NB[y]&B}
        for a in ring.NB[x]&fk:
            for p in byfirst[a]:
                if p[1] in ring.NB[y]:L.add(p)
        if not L<=baseline:raise RuntimeError(('loss outside baseline',len(L-baseline)))
        losses.append(L)
    relax,rsel,rlost=max_closure(losses)
    out={'q':q,'r':r,'terminal_orientation':o,'factor_union':len(U),'candidates':len(cand),'relax_gain':relax,'relax_selected':len(rsel),'relax_deleted':len(rlost),'exact_gain':None,'status':'relax-closed' if relax<=0 else 'relax-positive'}
    if relax<=0:return out
    n=len(cand);touched=sorted(set().union(*losses));bi={p:i for i,p in enumerate(touched)};w=WCNF();imp=0
    for i,L in enumerate(losses):
        for p in L:w.append([-(i+1),n+bi[p]+1]);imp+=1
    conflicts=0
    for i,(x,y) in enumerate(cand):
        for a in ring.NB[x]&U:
            for b in ring.NB[y]&U:
                j=idx.get((a,b))
                if j is not None and j>i:w.append([-(i+1),-(j+1)]);conflicts+=1
    for i in range(n):w.append([i+1],weight=1)
    for j in range(len(touched)):w.append([-(n+j+1)],weight=1)
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=True,verbose=0) as rc2:model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('RC2 no model')
    pos={z for z in model if z>0};sel=[i for i in range(n) if i+1 in pos];lost={touched[j] for j in range(len(touched)) if n+j+1 in pos};forced=set()
    for i in sel:forced.update(losses[i])
    if lost!=forced:raise RuntimeError(('loss mismatch',len(lost),len(forced)))
    selected=[cand[i] for i in sel];gain=len(selected)-len(lost)
    if gain!=n-cost:raise RuntimeError(('objective',gain,n-cost))
    for i,p in enumerate(selected):
        for z in selected[i+1:]:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('new-new',p,z))
        for z in baseline-lost:
            if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('retained',p,z))
    out.update(status='exact-rc2',exact_gain=gain,selected=len(selected),deleted=len(lost),touched_blockers=len(touched),conflict_clauses=conflicts,implications=imp)
    if gain>0:out['selected_points']=[list(p) for p in selected];out['deleted_points']=[list(p) for p in sorted(lost)]
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('neutral_audit',type=Path);ap.add_argument('k6_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    _base,ring,B,fam=load_geometry(a.tan_root.resolve());B=set(B);audit=json.loads(a.neutral_audit.read_text());C5=[frozenset(map(int,r['owners'])) for r in audit['rows'] if int(r['min_owner_intersection'])==0]
    if len(C5)!=30:raise RuntimeError(('neutral owner sets',len(C5)))
    C6=k6_owner_sets(a.k6_json.resolve());Cs=list(dict.fromkeys(C5+C6));U={z for z in range(ring.n) if any((ring.NB[z]&B)<=C for C in Cs)};Uv=sorted(U);core={(x,y) for x in B for y in B}
    tasks=[(q,r,o) for q in ('O','H','V') for r in ('O','H','V') for o in (0,1)];state={'ring':ring,'B':B,'fam':fam,'U':U,'Uv':Uv,'core':core};workers=max(1,min(a.workers,4,len(tasks)));ctx=mp.get_context('fork')
    with ctx.Pool(workers,initializer=init_worker,initargs=(state,)) as p:rows=list(p.imap_unordered(solve_task,tasks,chunksize=1))
    rows.sort(key=lambda z:((z['exact_gain'] if z['exact_gain'] is not None else -10**9),z['relax_gain']),reverse=True);exact=[z for z in rows if z['exact_gain'] is not None];best=max(exact,key=lambda z:z['exact_gain']) if exact else max(rows,key=lambda z:z['relax_gain']);score=None
    if best.get('exact_gain',0)>0:
        P=terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']);baseline=core|P;sel={tuple(p) for p in best['selected_points']};lost={tuple(p) for p in best['deleted_points']};cand=(baseline-lost)|sel;score=len(cand)
        if score!=134753+best['exact_gain']:raise RuntimeError(('score',score,best['exact_gain']))
        def enc(p):return ''.join(str(d) for d in ring.decode(p[0])+ring.decode(p[1]))
        pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    out={'method':'exact-global-genuine-neutral5-plus-k6-gap-union-prize','neutral5_owner_sets':len(C5),'k6_owner_sets':len(C6),'distinct_owner_sets':len(Cs),'union_factor_pool':len(U),'scenario_count':len(rows),'workers':workers,'exact_solved':len(exact),'positive_exact':sum((z.get('exact_gain') or 0)>0 for z in rows),'best':best,'rows':rows,'candidate_materialized':score is not None,'candidate_score':score};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='rows'},sort_keys=True))
if __name__=='__main__':main()
