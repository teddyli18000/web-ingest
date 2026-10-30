#!/usr/bin/env python3
"""Exact arbitrary single-row replacement against the full pinned 10D terminal.

The public 134753 construction is BB union P, with B of size 359 and |P|=5872.
Fix a core row a in B. Select any pairwise nonconfusable 5D outsider set Y and
replace the necessary core cells (a,c), c in union_{y in Y}(N[y] cap B), by
(a,y), y in Y. This script maximizes the true ten-dimensional score delta,
including every terminal-periphery point that must be deleted.

For a row move, only first-coordinate terminal blocks N x q, A x H/V,
D x V/H can meet a. Since N,A,D are disjoint, the periphery loss is exactly a
weighted union of the 16 private-pair endpoints. For fixed a the weights are
determined by |N[a] cap N|, |N[a] cap A|, |N[a] cap D|. Rows are also split by
whether a itself lies in N/A/D, because in that case a few (a,t) are already
baseline periphery points and must not be counted as new rewards.

Only six row-terminal cases are distinct: q in {O,H,V} and orientation in {0,1};
r is irrelevant for row moves. Column moves are symmetric with r in place of q.
A positive optimum is materialized as a full 10D certificate and should be sent
to the upstream Few Shots verifier by the workflow.
"""
from __future__ import annotations
import argparse,json,os
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
import bpz_joint_row_defects_maxsat as J

ENDPOINTS_NAME=('O','H','V')

def candidate_geometry(root:Path):
    _base,ring,B,fam=J.load_geometry(root)
    B=set(B);owners=sorted(B);oi={b:i for i,b in enumerate(owners)}
    cands=[z for z in range(ring.n) if z not in B];idx={z:i for i,z in enumerate(cands)}
    supp=[tuple(oi[b] for b in sorted(ring.NB[z]&B)) for z in cands]
    edges=[];C=set(cands)
    for i,z in enumerate(cands):
        for w in ring.NB[z]&C:
            j=idx[w]
            if j>i:edges.append((i,j))
    Q=sorted(set(fam['O'])|set(fam['H'])|set(fam['V']))
    if len(Q)!=16:raise RuntimeError(('Q',len(Q)))
    qset=set(Q);qi={z:i for i,z in enumerate(Q)}
    hits=[tuple(sorted(qi[t] for t in ring.NB[z]&qset)) for z in cands]
    return ring,B,fam,owners,cands,supp,edges,Q,hits

def row_types(ring,B,fam):
    N,A,D=set(fam['N']),set(fam['A']),set(fam['D'])
    if (N&A) or (N&D) or (A&D):raise RuntimeError('N/A/D not disjoint')
    types={}
    for a in sorted(B):
        counts=(len(ring.NB[a]&N),len(ring.NB[a]&A),len(ring.NB[a]&D))
        mem='N' if a in N else ('A' if a in A else ('D' if a in D else '-'))
        key=counts+(mem,)
        types.setdefault(key,[]).append(a)
    return types

def endpoint_weights(fam,Q,counts,q,orient):
    n,a,d=counts
    qset=set(fam[q]);H=set(fam['H']);V=set(fam['V'])
    sA,sD=(H,V) if orient==0 else (V,H)
    return tuple(int(n*(t in qset)+a*(t in sA)+d*(t in sD)) for t in Q)

def existing_second_coords(fam,q,orient,mem):
    H=set(fam['H']);V=set(fam['V']);qset=set(fam[q]);sA,sD=(H,V) if orient==0 else (V,H)
    if mem=='N':return qset
    if mem=='A':return sA
    if mem=='D':return sD
    return set()

def solve_type(payload):
    root_s,q,orient,key,rows,solver=payload;root=Path(root_s)
    counts=tuple(key[:3]);mem=key[3]
    ring,B,fam,owners,cands,supp,edges,Q,hits=candidate_geometry(root)
    existing=existing_second_coords(fam,q,orient,mem)
    keep=[i for i,z in enumerate(cands) if z not in existing]
    local_of={old:i for i,old in enumerate(keep)};lcands=[cands[i] for i in keep]
    lsupp=[supp[i] for i in keep];lhits=[hits[i] for i in keep]
    n=len(keep);m=len(owners);x0=1;y0=n+1;e0=y0+m
    weights=endpoint_weights(fam,Q,counts,q,orient);wcnf=WCNF()
    for oi,oj in edges:
        i=local_of.get(oi);j=local_of.get(oj)
        if i is not None and j is not None:wcnf.append([-(x0+i),-(x0+j)])
    for i,S in enumerate(lsupp):
        x=x0+i
        for u in S:wcnf.append([-x,y0+u])
        for h in lhits[i]:wcnf.append([-x,e0+h])
    for i in range(n):wcnf.append([x0+i],weight=1)
    for u in range(m):wcnf.append([-(y0+u)],weight=1)
    for h,cost in enumerate(weights):
        if cost:wcnf.append([-(e0+h)],weight=cost)
    with RC2(wcnf,solver=solver,adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('RC2 returned no model')
    pos={v for v in model if v>0};sel=[i for i in range(n) if x0+i in pos]
    Y=[lcands[i] for i in sel];C=set();E=set()
    for i in sel:C.update(lsupp[i]);E.update(lhits[i])
    actual=len(Y)-len(C)-sum(weights[h] for h in E)
    if actual!=n-cost:raise RuntimeError(('objective drift',actual,n-cost))
    for ii,z in enumerate(Y):
        for t in Y[ii+1:]:
            if t in ring.NB[z]:raise RuntimeError(('selected conflict',z,t))
    return {'q':q,'orientation':orient,'counts':list(counts),'membership':mem,'rows':rows,'row_representative':rows[0],'row_type_multiplicity':len(rows),'endpoint_weights':list(weights),'baseline_second_coords':sorted(existing),'delta':actual,'selected_count':len(Y),'owner_count':len(C),'periphery_loss_count':sum(weights[h] for h in E),'selected':sorted(Y),'owners':[owners[u] for u in sorted(C)],'hit_endpoints':[Q[h] for h in sorted(E)],'hard':len(wcnf.hard),'soft':len(wcnf.soft)}

def materialize(root:Path,best,out:Path):
    ring,B,fam,owners,cands,supp,edges,Q,hits=candidate_geometry(root)
    a=int(best['row_representative']);Y=set(map(int,best['selected']));C=set(map(int,best['owners']))
    q=best['q'];orient=int(best['orientation']);P=J.terminal_periphery(fam,q,'O',orient)
    removed_core={(a,c) for c in C};new={(a,y) for y in Y}
    if new&P:raise RuntimeError(('selected baseline point',sorted(new&P)[:5]))
    loss={p for p in P if any((p[0] in ring.NB[n[0]] and p[1] in ring.NB[n[1]]) for n in new)}
    core={(u,v) for u in B for v in B};kept=P-loss
    if len(loss)!=int(best['periphery_loss_count']):raise RuntimeError(('loss replay',len(loss),best['periphery_loss_count']))
    if not removed_core<=core or new&core:raise RuntimeError('partition drift')
    def cf10(x,y):return y[0] in ring.NB[x[0]] and y[1] in ring.NB[x[1]]
    for npt in new:
        if any(cf10(npt,p) for p in (core-removed_core)):raise RuntimeError(('new-core',npt))
        if any(cf10(npt,p) for p in kept):raise RuntimeError(('new-periphery',npt))
    nv=list(new)
    for i,x in enumerate(nv):
        for y in nv[i+1:]:
            if cf10(x,y):raise RuntimeError(('new-new',x,y))
    cand=(core-removed_core)|kept|new;expected=134753+int(best['delta'])
    if len(cand)!=expected:raise RuntimeError(('score',len(cand),expected))
    def enc10(p):return ''.join(str(z) for z in ring.decode(p[0])+ring.decode(p[1]))
    pts=sorted(enc10(p) for p in cand)
    if len(pts)!=len(set(pts)):raise RuntimeError('duplicate certificate points')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'points':pts},separators=(',',':'))+'\n')
    return len(pts)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=max(1,os.cpu_count() or 1));ap.add_argument('--solver',default='g4');a=ap.parse_args();root=a.tan_root.resolve()
    ring,B,fam,*_=candidate_geometry(root);types=row_types(ring,B,fam);tasks=[]
    for q in ENDPOINTS_NAME:
        for orient in (0,1):
            for key,rows in types.items():tasks.append((str(root),q,orient,key,rows,a.solver))
    workers=max(1,min(a.workers,4,len(tasks)));results=[]
    if workers==1:
        for t in tasks:results.append(solve_type(t))
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            fs=[ex.submit(solve_type,t) for t in tasks]
            for f in as_completed(fs):results.append(f.result())
    results.sort(key=lambda r:(r['delta'],r['selected_count'],-r['periphery_loss_count']),reverse=True);best=results[0]
    score=materialize(root,best,a.certificate) if best['delta']>0 else None
    status={'method':'exact-arbitrary-single-row-full-terminal-prize','distinct_row_types':len(types),'tasks':len(tasks),'workers':workers,'best':best,'top20':results[:20],'candidate_materialized':best['delta']>0,'candidate_score':score}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in status.items() if k!='top20'},sort_keys=True))
if __name__=='__main__':main()
