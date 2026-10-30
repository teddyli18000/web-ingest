#!/usr/bin/env python3
"""Exact prize search on complete factor replacement pools for the five irreducible defects.

For each irreducible owner set C define
    P_C = {x in C7^5 : N_B(x) subseteq C}.
This includes support-zero safe endpoints and owner points themselves.  For each
ordered pair (C,D), each public BPZ terminal, and every external vertex in
P_C x P_D, we compute its exact blockers in the 134753 baseline.

We first solve a maximum-closure relaxation that ignores conflicts among new
vertices.  If its optimum is <=0, the true prize optimum is rigorously <=0 and
the scenario is closed.  Only positive-relaxation scenarios are sent to exact
weighted MaxSAT with all candidate-conflict clauses and exact blocker costs.
Thus the search strictly contains every fixed maximum-witness product for these
support rectangles, and also permits non-Cartesian mixtures of alternative 5D
witnesses.  A positive exact optimum is materialized and verified upstream.
"""
from __future__ import annotations
import argparse,json,multiprocessing as mp,os
from pathlib import Path
from bpz_amplify_row_defects import Dinic
from bpz_joint_row_defects_maxsat import load_geometry,terminal_periphery,validate_defects
G={}

def closure(losses):
    touched=sorted(set().union(*losses) if losses else set());loc={p:i for i,p in enumerate(touched)}
    ll=[{loc[p] for p in L} for L in losses];n=len(ll);m=len(touched);s=n+m;t=s+1;d=Dinic(t+1);inf=n+m+10
    for i,L in enumerate(ll):
        d.add(s,i,1)
        for j in L:d.add(i,n+j,inf)
    for j in range(m):d.add(n+j,t,1)
    cut=d.flow(s,t);side=d.source_side(s);sel=[i for i in range(n) if i in side];lost=set()
    for i in sel:lost.update(ll[i])
    gain=len(sel)-len(lost)
    if gain!=n-cut:raise RuntimeError(('closure mismatch',gain,n-cut))
    return gain,sel,{touched[j] for j in lost},len(touched)

def init_worker(state):
    global G;G=state

def terminal_task(task):
    from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    q,r,o=task;ring,B,fam,defects,pools,Bcore=G['ring'],G['B'],G['fam'],G['defects'],G['pools'],G['Bcore']
    P=terminal_periphery(fam,q,r,o);baseline=Bcore|P
    if len(baseline)!=134753:raise RuntimeError(('baseline',q,r,o,len(baseline)))
    byfirst={}
    for p in P:byfirst.setdefault(p[0],[]).append((p[1],p))
    first=set(byfirst);bcache={}
    def blockers(p):
        if p in bcache:return bcache[p]
        x,y=p;L=set()
        for a in ring.NB[x]&B:
            for b in ring.NB[y]&B:L.add((a,b))
        for a in ring.NB[x]&first:
            for b,z in byfirst[a]:
                if b in ring.NB[y]:L.add(z)
        bcache[p]=L;return L
    out=[];best=None
    for ia,da in enumerate(defects):
      for ib,db in enumerate(defects):
        cand=sorted({(x,y) for x in pools[ia] for y in pools[ib]}-baseline)
        losses=[blockers(p) for p in cand]
        relax,rsel,rlost,touched=closure(losses)
        exact=0;selected=[];lost=set();conflicts=0;status='relax-closed'
        if relax>0:
            status='exact-rc2';n=len(cand);dv={};w=WCNF()
            def bv(p):
                if p not in dv:dv[p]=n+len(dv)+1
                return dv[p]
            for i,L in enumerate(losses):
                for p in L:w.append([-(i+1),bv(p)])
            for i,(x,y) in enumerate(cand):
                for j in range(i+1,n):
                    u,v=cand[j]
                    if u in ring.NB[x] and v in ring.NB[y]:w.append([-(i+1),-(j+1)]);conflicts+=1
            for i in range(n):w.append([i+1],weight=1)
            for z in dv.values():w.append([-z],weight=1)
            with RC2(w,solver='g4',adapt=True,exhaust=True,incr=False,verbose=0) as rc2:
                model=rc2.compute();cost=rc2.cost
            if model is None:raise RuntimeError('RC2 no model')
            pos={z for z in model if z>0};selected=[cand[i] for i in range(n) if i+1 in pos];lost={p for p,z in dv.items() if z in pos};exact=n-cost
            if exact!=len(selected)-len(lost):raise RuntimeError(('objective',exact,len(selected),len(lost)))
            if exact>relax:raise RuntimeError(('relax bound violated',exact,relax))
        e={'q':q,'r':r,'terminal_orientation':o,'left':da['name'],'right':db['name'],'pool_left':len(pools[ia]),'pool_right':len(pools[ib]),'candidates':len(cand),'touched_blockers':touched,'relax_gain':relax,'exact_gain':exact,'conflicts':conflicts,'status':status,'selected':len(selected),'deleted':len(lost),'score':134753+exact}
        out.append(e);rank=(exact,relax,len(selected),-len(lost))
        if best is None or rank>best[0]:best=(rank,e,selected,sorted(lost))
    return {'results':out,'best':best[1],'selected':best[2],'lost':best[3]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));a=ap.parse_args()
    root=a.tan_root.resolve();_base,ring,B,fam=load_geometry(root);defects=validate_defects(ring,B)
    if len(defects)!=5:raise RuntimeError(('defects',len(defects)))
    pools=[]
    for d in defects:
        C=set(d['C']);P=[]
        for z in range(ring.n):
            if (ring.NB[z]&B)<=C:P.append(z)
        pools.append(tuple(P))
    Bcore={(x,y) for x in B for y in B};state={'ring':ring,'B':B,'fam':fam,'defects':defects,'pools':pools,'Bcore':Bcore}
    tasks=[(q,r,o) for q in ('O','H','V') for r in ('O','H','V') for o in (0,1)];workers=max(1,min(a.workers,4,len(tasks)));ctx=mp.get_context('fork')
    if workers==1:init_worker(state);packs=[terminal_task(t) for t in tasks]
    else:
        with ctx.Pool(workers,initializer=init_worker,initargs=(state,)) as P:packs=list(P.imap_unordered(terminal_task,tasks,chunksize=1))
    results=[e for p in packs for e in p['results']];bp=max(packs,key=lambda p:(p['best']['exact_gain'],p['best']['relax_gain'],p['best']['selected'],-p['best']['deleted']));best=bp['best'];sel={tuple(x) for x in bp['selected']};lost={tuple(x) for x in bp['lost']};score=None
    if best['exact_gain']>0:
        P=terminal_periphery(fam,best['q'],best['r'],best['terminal_orientation']);baseline=Bcore|P;cand=(baseline-lost)|sel;score=len(cand)
        if score!=134753+best['exact_gain']:raise RuntimeError(('size',score,best))
        sv=list(sel)
        for i,p in enumerate(sv):
            for z in sv[i+1:]:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('new-new',p,z))
            for z in baseline-lost:
                if z[0] in ring.NB[p[0]] and z[1] in ring.NB[p[1]]:raise RuntimeError(('new-old',p,z))
        def enc(p):return ''.join(str(d) for d in (ring.decode(p[0])+ring.decode(p[1])))
        pts=sorted(enc(p) for p in cand);a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    results.sort(key=lambda e:(e['exact_gain'],e['relax_gain'],e['selected'],-e['deleted']),reverse=True)
    out={'method':'exact-full-factor-support-rectangle-prize','factor_pool_sizes':[len(p) for p in pools],'scenario_count':len(results),'relax_positive':sum(e['relax_gain']>0 for e in results),'exact_solved':sum(e['status']=='exact-rc2' for e in results),'positive_exact':sum(e['exact_gain']>0 for e in results),'best':best,'top20':results[:20],'candidate_materialized':best['exact_gain']>0,'candidate_score':score,'workers':workers}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='top20'},sort_keys=True))
if __name__=='__main__':main()
