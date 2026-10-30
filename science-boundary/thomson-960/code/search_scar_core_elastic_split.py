#!/usr/bin/env python3
"""Split a known e432->B reaction into short-scar core and elastic far field.

The source e432 has one short 5-7-5 defect component while B has twelve full
5-7-5-7-5 scars.  Using meaningful point labels, compute the exact source->target
spherical log displacement.  Define the plastic core by graph distance from the
unique short defect component in the source Delaunay graph; scale core and
complement independently, then fully relax.  This probes whether topology
crossing is localized plasticity, far-field elasticity, or their coupling.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import deque
import numpy as np
from scipy.spatial import ConvexHull
import search_topology_morph as tm
import search_defect_core_transfer as dc


def load(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N: raise ValueError('expected 960 labeled points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]


def graph(x):
    h=ConvexHull(x); adj=[set() for _ in range(len(x))]
    for tri in h.simplices:
        a,b,c=map(int,tri); adj[a].update((b,c)); adj[b].update((a,c)); adj[c].update((a,b))
    deg=np.array([len(s) for s in adj],int)
    return adj,deg


def short_component(adj,deg):
    defects=set(map(int,np.flatnonzero(deg!=6))); seen=set(); comps=[]
    for s in sorted(defects):
        if s in seen: continue
        q=[s]; seen.add(s); comp=[]
        while q:
            u=q.pop(); comp.append(u)
            for v in adj[u]:
                if v in defects and v not in seen:
                    seen.add(v); q.append(v)
        comps.append(comp)
    cand=[c for c in comps if sorted(int(deg[i]) for i in c)==[5,5,7]]
    if len(cand)!=1:
        raise RuntimeError(f'expected unique 5-7-5 component, got {len(cand)}')
    return sorted(cand[0])


def shell_mask(adj,core,shell,decay):
    dist={int(v):0 for v in core}; q=deque(core)
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
    ap.add_argument('--shells',default='0,1,2,3,4')
    ap.add_argument('--core-scales',default='0.45,0.75,1.0,1.25,1.6')
    ap.add_argument('--far-scales',default='0,0.35,0.7,1.0,1.3')
    ap.add_argument('--decay',type=float,default=1.0); ap.add_argument('--maxiter',type=int,default=3400)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    S=load(args.source_json); T=load(args.target_json); adj,deg=graph(S); core=short_component(adj,deg)
    v=dc.log_field(S,T); mag=np.linalg.norm(v,axis=1)
    print('SOURCE',tm.raw_energy(S),tm.coord_counts(S),'TARGET',tm.raw_energy(T),tm.coord_counts(T),flush=True)
    print('SHORT_CORE',core,'degrees',[int(deg[i]) for i in core],'reaction_rms',float(np.sqrt(np.mean(mag*mag))),flush=True)
    rows=[]; saved=[]
    shells=[int(z) for z in args.shells.split(',') if z]; cs=[float(z) for z in args.core_scales.split(',') if z]; fs=[float(z) for z in args.far_scales.split(',') if z]
    for shell in shells:
        w,dist=shell_mask(adj,core,shell,args.decay)
        # Binary support when decay=1; otherwise smooth graph-shell attenuation.
        core_power=float(np.sum((mag*w)**2)/np.sum(mag**2))
        print('SHELL',shell,'active',len(dist),'reaction_power',core_power,flush=True)
        for a in cs:
            for b in fs:
                weights=b+(a-b)*w
                x=dc.exp_field(S,v,1.0,weights); start=tm.raw_energy(x); e,y,nit,ok=tm.relax(x,maxiter=args.maxiter); cc=tm.coord_counts(y)
                row={'shell':shell,'active_vertices':len(dist),'core_reaction_power':core_power,'core_scale':a,'far_scale':b,
                     'start_energy':start,'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,'nit':nit,'success':ok}
                rows.append(row); print('TRY shell',shell,'a',a,'b',b,'E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,flush=True)
                if e<args.live_score+0.18 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
                    saved.append({'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,'shell':shell,
                                  'core_scale':a,'far_scale':b,'points':y.tolist()})
    saved.sort(key=lambda z:z['energy']); best=min(rows,key=lambda z:z['energy'])
    out={'source_energy':tm.raw_energy(S),'target_energy':tm.raw_energy(T),'core_vertices':core,
         'core_degrees':[int(deg[i]) for i in core],'reaction_rms':float(np.sqrt(np.mean(mag*mag))),
         'rows':rows,'distinct_low_basins':saved[:24],'best_energy':best['energy'],'best_delta_live':best['delta_live']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved and saved[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
