#!/usr/bin/env python3
"""Topology-preserving cross-size propagation of a twinned Thomson defect family.

Historical N~1000 Thomson minima can contain a 'twinned' grain-boundary motif:
two 7-coordinated sites share a Delaunay edge.  The current N=960 record family
instead consists of separated 5-7-5-7-5 scars.  Ordinary neighboring-size
propagation ranks only by energy and can immediately heal away the topology we
want to test.  Here each add/remove move is restricted to the regular sixfold
bulk, at configurable graph distance from the current 5/7 defect core, and beam
selection prioritizes descendants that still contain 7-7 edges before energy.

This is a search over a different defect family, not another perturbation of the
record basin.  Local minimization uses the stable long-double pair-difference
objective from search_size_beam.py.
"""
from __future__ import annotations
import argparse,json,pathlib,math
import numpy as np
from scipy.spatial import ConvexHull
import search_size_beam as sb
from analyze_twinned_motif import load_xyz


def topology(x):
    h=ConvexHull(x); n=len(x); nb=[set() for _ in range(n)]; edges=set()
    for tri in h.simplices:
        a,b,c=map(int,tri)
        for u,v in ((a,b),(b,c),(c,a)):
            if u>v:u,v=v,u
            edges.add((u,v)); nb[u].add(v);nb[v].add(u)
    z=np.array([len(s) for s in nb],int)
    e77=[(a,b) for a,b in edges if z[a]==7 and z[b]==7]
    return h,nb,z,e77

def expanded_core(nb,z,hops):
    core=set(np.flatnonzero(z!=6))
    for _ in range(hops):
        core |= {v for u in list(core) for v in nb[u]}
    return core

def insertion_candidates(x,h,core):
    sites=[]; facets=[]
    for tri in h.simplices:
        tri=list(map(int,tri))
        if any(v in core for v in tri): continue
        a,b,c=x[tri]; n=np.cross(b-a,c-a); nn=np.linalg.norm(n)
        if nn<1e-14: continue
        n=n/nn
        if float(n@a)<0:n=-n
        sites.append(n);facets.append(tri)
    if not sites:return np.empty((0,3)),np.empty(0),[]
    y=np.asarray(sites); vals=np.empty(len(y))
    for lo in range(0,len(y),250):
        q=y[lo:lo+250]; dots=np.clip(q@x.T,-1,1)
        vals[lo:lo+len(q)]=np.sum(1/np.sqrt(np.maximum(2-2*dots,1e-15)),axis=1)
    return y,vals,facets

def state_meta(x):
    h,nb,z,e77=topology(x)
    return {'coordination_counts':{str(k):int(np.sum(z==k)) for k in sorted(set(map(int,z)))},
            'topological_charge':int(np.sum(6-z)),'seven_seven_edges':len(e77)}

def branch_insert(state,branch,hops,tag):
    E,x,hist=state; hull,nb,z,e77=topology(x); core=expanded_core(nb,z,hops); sites,vals,facets=insertion_candidates(x,hull,core)
    if len(sites)==0:return []
    ids=np.argsort(vals)[:branch]; out=[]
    for rank,j in enumerate(ids):
        y=np.vstack([x,sites[j]]); e,q,nit,ok=sb.stable_relax(y,1200); meta=state_meta(q)
        step={'move':'insert','rank':rank,'site':int(j),'facet':facets[int(j)],'pre_potential':float(vals[j]),
              'n':len(q),'energy':e,'nit':nit,'success':ok,**meta}
        print(f'{tag} INS r={rank} n={len(q)} E={e:.12f} e77={meta["seven_seven_edges"]} coord={meta["coordination_counts"]} nit={nit}',flush=True)
        out.append((e,q,hist+[step]))
    return out

def branch_remove(state,branch,hops,tag):
    E,x,hist=state; hull,nb,z,e77=topology(x); core=expanded_core(nb,z,hops); c=sb.energy_contrib(x)
    allowed=np.array([i for i in range(len(x)) if i not in core and z[i]==6],int)
    if not len(allowed):return []
    ids=allowed[np.argsort(c[allowed])[-branch:][::-1]];out=[]
    for rank,j in enumerate(ids):
        y=np.delete(x,int(j),axis=0); e,q,nit,ok=sb.stable_relax(y,1200); meta=state_meta(q)
        step={'move':'remove','rank':rank,'index':int(j),'pre_contribution':float(c[j]),'n':len(q),
              'energy':e,'nit':nit,'success':ok,**meta}
        print(f'{tag} REM r={rank} n={len(q)} E={e:.12f} e77={meta["seven_seven_edges"]} coord={meta["coordination_counts"]} nit={nit}',flush=True)
        out.append((e,q,hist+[step]))
    return out

def keep_family(states,beam,min_e77,tol=2e-7):
    ranked=[]
    for s in states:
        meta=state_meta(s[1]); penalty=0 if meta['seven_seven_edges']>=min_e77 else 1
        ranked.append((penalty,s[0],s,meta))
    ranked.sort(key=lambda t:(t[0],t[1])); keep=[]
    for penalty,E,s,meta in ranked:
        if all(abs(E-q[0])>tol for q in keep):keep.append(s)
        if len(keep)>=beam:break
    return keep

def main():
    ap=argparse.ArgumentParser();ap.add_argument('xyz');ap.add_argument('few_shots')
    ap.add_argument('--target',type=int,default=960);ap.add_argument('--branch',type=int,default=2);ap.add_argument('--beam',type=int,default=2)
    ap.add_argument('--core-hops',type=int,default=2);ap.add_argument('--min-e77',type=int,default=1);ap.add_argument('--out',required=True)
    args=ap.parse_args();x=load_xyz(args.xyz); n0=len(x); e0,x,nit,ok=sb.stable_relax(x,1200); initial=state_meta(x)
    live,_=sb.find_live(pathlib.Path(args.few_shots))
    print(f'parent n={n0} polished={e0:.12f} topology={initial} target={args.target} live960={live:.10f}',flush=True)
    beam=[(e0,x,[])]; move='insert' if n0<args.target else 'remove'; steps=abs(args.target-n0)
    for step in range(steps):
        cand=[]
        for bi,s in enumerate(beam):
            if move=='insert':cand+=branch_insert(s,args.branch,args.core_hops,f'step{step+1}/b{bi}')
            else:cand+=branch_remove(s,args.branch,args.core_hops,f'step{step+1}/b{bi}')
        if not cand:raise RuntimeError(f'no candidates at step {step+1}')
        beam=keep_family(cand,args.beam,args.min_e77)
        print('KEEP',step+1,[(len(s[1]),s[0],state_meta(s[1])['seven_seven_edges']) for s in beam],flush=True)
    finals=sorted(beam,key=lambda s:(0 if state_meta(s[1])['seven_seven_edges']>=args.min_e77 else 1,s[0]))
    best=finals[0];E,x,hist=best;meta=state_meta(x)
    print(f'FINAL E={E:.12f} delta_live={E-live:+.9g} topology={meta}',flush=True)
    out={'source_n':n0,'target_n':args.target,'source_polished_energy':e0,'source_topology':initial,'live_score':live,
         'branch':args.branch,'beam':args.beam,'core_hops':args.core_hops,'min_e77':args.min_e77,
         'best_float_energy':E,'delta_vs_live':E-live,'best_topology':meta,'history':hist,
         'final_beam':[{'energy':s[0],'topology':state_meta(s[1]),'history':s[2]} for s in finals],
         'best_points':x.tolist() if len(x)==960 and E<live-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
