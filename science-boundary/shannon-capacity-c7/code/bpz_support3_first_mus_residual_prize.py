#!/usr/bin/env python3
"""Exact raw-core prize on the first support-3 owner-assignment obstruction.

The support<=2 factor universe admits a certified owner-clique map f, hence every
R x R independent set injects into touched core cells via (f(u),f(v)).  The
first deletion-minimal obstruction to extending that map to support-3 consists
of four factors E={1012,1025,1285,3722}.

For F=R union E, any candidate with an exception coordinate is potentially
unchargeable by the product injection.  Also retain an R x R candidate when its
assigned cell lies in a core cell that *some* exception-containing candidate
could touch.  Every omitted R x R candidate has an assigned cell outside that
entire exception footprint region, so omitted selected candidates can still be
charged injectively to distinct core cells disjoint from all retained residual
footprints.  Therefore positive raw gain in F x F implies positive prize in the
residual instance built here.

The residual decomposes by both conflict edges and shared core-cell costs.  In
the pinned geometry it has twenty 56-candidate components and one 22120-point
giant component.  Objective per component is exactly

  selected candidates - activated core cells.

A nonpositive optimum for every component closes this first support-3
obstruction before terminal-periphery losses are considered.
"""
from __future__ import annotations
import argparse,json,itertools,os,time
from collections import defaultdict,Counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
import bpz_joint_row_defects_maxsat as J
from bpz_low_support_owner_clique_assignment import solve_2sat

EXCEPTIONS=(1012,1025,1285,3722)

def build_support2_assignment(ring,B):
    B=set(B);factors=[];support={}
    for z in range(ring.n):
        if z in B:continue
        S=tuple(sorted(ring.NB[z]&B))
        if 1<=len(S)<=2:factors.append(z);support[z]=S
    singleton=[z for z in factors if len(support[z])==1];binary=[z for z in factors if len(support[z])==2]
    if (len(factors),len(singleton),len(binary))!=(425,50,375):raise RuntimeError(('support2 census',len(factors),len(singleton),len(binary)))
    vid={z:i for i,z in enumerate(binary)};eligible=defaultdict(list)
    for z in singleton:eligible[support[z][0]].append((z,None))
    for z in binary:
        a,b=support[z];eligible[a].append((z,False));eligible[b].append((z,True))
    def forbid(z,val):
        i=vid[z]+1;return i if val is False else -i
    clauses=[]
    for owner,L in eligible.items():
        for i,(z,vz) in enumerate(L):
            for w,vw in L[i+1:]:
                if w in ring.NB[z]:continue
                if vz is None and vw is None:raise RuntimeError(('forced nonclique',owner,z,w))
                if vz is None:clauses.append((forbid(w,vw),))
                elif vw is None:clauses.append((forbid(z,vz),))
                else:clauses.append((forbid(z,vz),forbid(w,vw)))
    assignment,_=solve_2sat(len(binary),clauses)
    if assignment is None:raise RuntimeError('support2 assignment UNSAT')
    fmap={z:support[z][0] for z in singleton}
    for z,val in zip(binary,assignment):fmap[z]=support[z][1 if val else 0]
    groups=defaultdict(list)
    for z,b in fmap.items():groups[b].append(z)
    for b,L in groups.items():
        for i,z in enumerate(L):
            for w in L[i+1:]:
                if w not in ring.NB[z]:raise RuntimeError(('assignment replay',b,z,w))
    return factors,support,fmap

def build_residual(root:Path):
    _base,ring,B,_fam=J.load_geometry(root);B=set(B)
    regular,support,fmap=build_support2_assignment(ring,B)
    for z in EXCEPTIONS:
        if z in B:raise RuntimeError(('exception in B',z))
        support[z]=tuple(sorted(ring.NB[z]&B))
        if len(support[z])!=3:raise RuntimeError(('exception support',z,support[z]))
    factors=regular+list(EXCEPTIONS);F=set(factors)
    possible_exception_cells=set()
    for e in EXCEPTIONS:
        for u in factors:
            for a in support[e]:
                for b in support[u]:
                    possible_exception_cells.add((a,b));possible_exception_cells.add((b,a))
    cand=set()
    for e in EXCEPTIONS:
        for u in factors:cand.add((e,u));cand.add((u,e))
    for u in regular:
        for v in regular:
            if (fmap[u],fmap[v]) in possible_exception_cells:cand.add((u,v))
    candidates=sorted(cand);idx={p:i for i,p in enumerate(candidates)}
    cellsets=[tuple((a,b) for a in support[u] for b in support[v]) for u,v in candidates]
    edges=[]
    for i,(u,v) in enumerate(candidates):
        for u2 in ring.NB[u]&F:
            for v2 in ring.NB[v]&F:
                j=idx.get((u2,v2))
                if j is not None and j>i:edges.append((i,j))
    # Component union by conflict or shared cost cell.
    n=len(candidates);par=list(range(n));sz=[1]*n
    def find(x):
        while par[x]!=x:par[x]=par[par[x]];x=par[x]
        return x
    def union(a,b):
        a=find(a);b=find(b)
        if a==b:return
        if sz[a]<sz[b]:a,b=b,a
        par[b]=a;sz[a]+=sz[b]
    first={}
    for i,cs in enumerate(cellsets):
        for c in cs:
            if c in first:union(i,first[c])
            else:first[c]=i
    for i,j in edges:union(i,j)
    comps=defaultdict(list)
    for i in range(n):comps[find(i)].append(i)
    edgeby=defaultdict(list)
    for i,j in edges:
        r=find(i)
        if r!=find(j):raise RuntimeError('conflict crosses components')
        edgeby[r].append((i,j))
    return ring,regular,support,fmap,candidates,cellsets,edges,comps,edgeby,possible_exception_cells

def solve_component(payload):
    comp,candidates,cellsets,edges,solver=payload
    loc={g:i for i,g in enumerate(comp)};cells=sorted({c for g in comp for c in cellsets[g]});ci={c:i for i,c in enumerate(cells)}
    nv=len(comp);w=WCNF();ec=0;ac=0
    gset=set(comp)
    for i,j in edges:
        if i in gset and j in gset:w.append([-(loc[i]+1),-(loc[j]+1)]);ec+=1
    y0=nv+1
    for g in comp:
        x=loc[g]+1
        for c in cellsets[g]:w.append([-x,y0+ci[c]]);ac+=1
    for i in range(nv):w.append([i+1],weight=1)
    for j in range(len(cells)):w.append([-(y0+j)],weight=1)
    t=time.time()
    with RC2(w,solver=solver,adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('RC2 no model')
    pos={z for z in model if z>0};sel=[g for g in comp if loc[g]+1 in pos];used=set()
    for g in sel:used.update(cellsets[g])
    prize=len(sel)-len(used)
    if prize!=nv-cost:raise RuntimeError(('objective drift',prize,nv-cost))
    return {'component_size':nv,'core_cells':len(cells),'conflict_edges':ec,'activations':ac,'solver':solver,'seconds':time.time()-t,'prize':prize,'selected_count':len(sel),'activated_cells':len(used),'selected_candidates':[list(candidates[g]) for g in sel]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--solver',default='g4');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args();root=a.tan_root.resolve()
    ring,regular,support,fmap,candidates,cellsets,edges,comps,edgeby,K=build_residual(root)
    parts=sorted(comps.values(),key=len,reverse=True)
    sizes=Counter(map(len,parts))
    # Solve the 20 tiny components directly, then the giant in one worker.  The workflow
    # may race this entire script with a second backend rather than duplicating components here.
    results=[]
    for comp in parts[1:]:results.append(solve_component((comp,candidates,cellsets,edges,a.solver)))
    if any(r['prize']>0 for r in results):raise RuntimeError(('unexpected positive tiny component',results))
    giant=solve_component((parts[0],candidates,cellsets,edges,a.solver));results.insert(0,giant)
    total=sum(r['prize'] for r in results)
    out={'method':'exact-support3-first-mus-residual-prize','exceptions':list(EXCEPTIONS),'regular_factors':len(regular),'factor_universe':len(regular)+len(EXCEPTIONS),'possible_exception_cells':len(K),'residual_candidates':len(candidates),'residual_conflict_edges':len(edges),'component_size_histogram':{str(k):v for k,v in sorted(sizes.items())},'components':results,'total_prize':total,'closed_nonpositive':total<=0}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='components'},sort_keys=True));print('giant',json.dumps({k:v for k,v in giant.items() if k!='selected_candidates'},sort_keys=True))
if __name__=='__main__':main()
