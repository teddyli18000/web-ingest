#!/usr/bin/env python3
"""Topology-aware local Delaunay flip transfer between two labeled Thomson minima.

With a meaningful pointwise correspondence (e.g. e432 -> B-natural), compare
spherical Delaunay triangulations and identify exact bistellar flips: a source
edge (a,b) with adjacent triangles (a,b,c),(a,b,d) disappears while the target
contains opposite edge (c,d).  Then move only the four flip vertices, or one/two
graph shells around them, along the source->target log displacement before full
unconstrained relaxation.  This targets the combinatorial scar-completion event
rather than a radial displacement mask.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import defaultdict,deque
import numpy as np
from scipy.spatial import ConvexHull
import search_topology_morph as tm
import search_defect_core_transfer as dc


def load(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N: raise ValueError('expected 960 labeled points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]


def triangulation(x):
    h=ConvexHull(x); tris=[tuple(map(int,t)) for t in h.simplices]
    edge_tris=defaultdict(list); adj=[set() for _ in range(len(x))]
    for t in tris:
        a,b,c=t
        for u,v in ((a,b),(b,c),(c,a)):
            e=tuple(sorted((u,v))); edge_tris[e].append(t); adj[u].add(v); adj[v].add(u)
    return edge_tris,adj


def exact_flips(source,target):
    es,adj=triangulation(source); et,_=triangulation(target)
    set_s=set(es); set_t=set(et); out=[]
    for e in sorted(set_s-set_t):
        ts=es[e]
        if len(ts)!=2: continue
        a,b=e
        opp=[]
        for t in ts:
            q=[z for z in t if z not in e]
            if len(q)!=1: break
            opp.append(q[0])
        if len(opp)!=2 or opp[0]==opp[1]: continue
        f=tuple(sorted(opp))
        if f in set_t and f not in set_s:
            out.append({'delete_edge':[a,b],'add_edge':list(f),'vertices':sorted({a,b,*opp})})
    # each flip should appear once via its deleted edge
    return out,adj


def shell_weights(adj,core,shell,decay):
    dist={int(v):0 for v in core}; q=deque(dist)
    while q:
        u=q.popleft(); d=dist[u]
        if d>=shell: continue
        for v in adj[u]:
            if v not in dist:
                dist[v]=d+1; q.append(v)
    w=np.zeros(len(adj),float)
    for i,d in dist.items(): w[i]=decay**d
    return w,dist


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--alphas',default='0.25,0.45,0.70,0.95,1.15,1.40,1.75,2.10')
    ap.add_argument('--shells',default='0,1,2'); ap.add_argument('--decay',type=float,default=0.55)
    ap.add_argument('--maxiter',type=int,default=3200); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    S=load(args.source_json); T=load(args.target_json)
    flips,adj=exact_flips(S,T)
    print('SOURCE',tm.raw_energy(S),tm.coord_counts(S),'TARGET',tm.raw_energy(T),tm.coord_counts(T),'EXACT_FLIPS',len(flips),flush=True)
    for i,f in enumerate(flips): print('FLIP',i,f,flush=True)
    v=dc.log_field(S,T); alphas=[float(z) for z in args.alphas.split(',') if z]; shells=[int(z) for z in args.shells.split(',') if z]
    rows=[]; saved=[]
    for fi,f in enumerate(flips):
        core=f['vertices']
        for shell in shells:
            w,dist=shell_weights(adj,core,shell,args.decay)
            for a in alphas:
                x=dc.exp_field(S,v,a,w); start=tm.raw_energy(x); e,y,nit,ok=tm.relax(x,maxiter=args.maxiter); cc=tm.coord_counts(y)
                row={'flip':fi,'delete_edge':f['delete_edge'],'add_edge':f['add_edge'],'shell':shell,'alpha':a,
                     'active_vertices':len(dist),'start_energy':start,'energy':e,'delta_live':e-args.live_score,
                     'coord_counts':cc,'nit':nit,'success':ok}
                rows.append(row)
                print('TRY',fi,'shell',shell,'a',a,'n',len(dist),'E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,flush=True)
                if e<args.live_score+0.25 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
                    saved.append({'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,
                                  'flip':fi,'shell':shell,'alpha':a,'points':y.tolist()})
    # Joint application of all exact source->target flips if more than one exists.
    if flips:
        core=sorted({vtx for f in flips for vtx in f['vertices']})
        for shell in shells:
            w,dist=shell_weights(adj,core,shell,args.decay)
            for a in alphas:
                x=dc.exp_field(S,v,a,w); start=tm.raw_energy(x); e,y,nit,ok=tm.relax(x,maxiter=args.maxiter); cc=tm.coord_counts(y)
                row={'flip':'all','shell':shell,'alpha':a,'active_vertices':len(dist),'start_energy':start,'energy':e,
                     'delta_live':e-args.live_score,'coord_counts':cc,'nit':nit,'success':ok}; rows.append(row)
                print('TRY all shell',shell,'a',a,'n',len(dist),'E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,flush=True)
                if e<args.live_score+0.25 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
                    saved.append({'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,'flip':'all','shell':shell,'alpha':a,'points':y.tolist()})
    saved.sort(key=lambda z:z['energy']); best=min(rows,key=lambda z:z['energy']) if rows else None
    out={'source_energy':tm.raw_energy(S),'source_coord':tm.coord_counts(S),'target_energy':tm.raw_energy(T),'target_coord':tm.coord_counts(T),
         'flips':flips,'rows':rows,'distinct_low_basins':saved[:24],
         'best_energy':best['energy'] if best else None,'best_delta_live':best['delta_live'] if best else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved and saved[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
