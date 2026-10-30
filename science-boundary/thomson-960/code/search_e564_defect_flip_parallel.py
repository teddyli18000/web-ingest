#!/usr/bin/env python3
"""Targeted 21->20 dislocation search from the C3 e564 Thomson minimum.

The e564 triangulation has nine flippable 7-7 edges whose combinatorial flip
changes coordination 33/906/21 -> 32/908/20.  They form three distinct C3
orbits. For one representative of each requested orbit, locate the smallest
spherical perturbation that actually changes the convex-hull diagonal, then
over-shoot the boundary in several geometrically distinct ways and fully relax
in parallel.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, json, math, pathlib
from collections import Counter, defaultdict
import numpy as np
from scipy.spatial import ConvexHull

from search_from_seed_modes import load_seed, stable_relax_q
import diagnose_soft_modes as sm


def topology(x):
    h=ConvexHull(x); adj=[set() for _ in range(len(x))]; edge_faces=defaultdict(list)
    for a,b,c in h.simplices:
        adj[a].update((b,c)); adj[b].update((a,c)); adj[c].update((a,b))
        for u,v,w in ((a,b,c),(b,c,a),(c,a,b)):
            if u>v: u,v=v,u
            edge_faces[(int(u),int(v))].append(int(w))
    deg=np.array([len(s) for s in adj],dtype=int)
    return deg,edge_faces


def defect_reducing_flips(x):
    deg,ef=topology(x); edges=set(ef); base=int(np.sum(np.abs(deg-6))); out=[]
    for (u,v),opp in ef.items():
        if len(opp)!=2: continue
        a,b=opp
        if (min(a,b),max(a,b)) in edges: continue
        nd=deg.copy(); nd[u]-=1; nd[v]-=1; nd[a]+=1; nd[b]+=1
        if int(np.sum(np.abs(nd-6)))-base != -2: continue
        cc=Counter(nd.tolist())
        if cc.get(5,0)==32 and cc.get(6,0)==908 and cc.get(7,0)==20:
            out.append((u,v,a,b))
    return out


def tangent_to(p,target):
    t=target-float(np.dot(target,p))*p
    return t/float(np.linalg.norm(t))


def perturb(x,quad,amp,pattern):
    u,v,a,b=quad; y=x.copy(); orig=x
    moves=[]
    if pattern in ('balanced','newdiag'):
        moves += [(a,b,+1),(b,a,+1)]
    if pattern in ('balanced','olddiag'):
        moves += [(u,v,-1),(v,u,-1)]
    for i,j,sg in moves:
        p=orig[i]; t=sg*tangent_to(p,orig[j])
        y[i]=math.cos(amp)*p+math.sin(amp)*t
        y[i]/=np.linalg.norm(y[i])
    return y


def flipped(x,quad):
    u,v,a,b=quad; _,ef=topology(x); es=set(ef)
    return (min(u,v),max(u,v)) not in es and (min(a,b),max(a,b)) in es


def threshold(x,quad,pattern):
    hi=0.008
    while hi<=0.08 and not flipped(perturb(x,quad,hi,pattern),quad): hi*=1.35
    if hi>0.08: return None
    lo=0.0
    for _ in range(20):
        mid=(lo+hi)/2
        if flipped(perturb(x,quad,mid,pattern),quad): hi=mid
        else: lo=mid
    return hi


def relax_one(task):
    x,quad,pattern,thr,mult,maxiter=task
    start=perturb(x,quad,thr*mult,pattern)
    sd,_=topology(start); sc=Counter(sd.tolist())
    q=sm.xyz_to_vars(start)
    e,raw,z,nit,ok,msg=stable_relax_q(q,maxiter=maxiter)
    dd,_=topology(z); dc=Counter(dd.tolist())
    return {'quad':list(quad),'pattern':pattern,'threshold':thr,'multiplier':mult,
            'start_coord':{str(k):int(v) for k,v in sorted(sc.items())},
            'energy':float(e),'raw_energy':float(raw),'nit':int(nit),'success':bool(ok),'message':str(msg),
            'coord':{str(k):int(v) for k,v in sorted(dc.items())},'points':z.tolist()}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--patterns',default='balanced,newdiag,olddiag')
    ap.add_argument('--multipliers',default='1.02,1.08,1.18,1.35,1.60,2.00')
    ap.add_argument('--family-indices',default='all',help='comma-separated indices in balanced-threshold order, or all')
    ap.add_argument('--workers',type=int,default=4); ap.add_argument('--maxiter',type=int,default=1800)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(args.seed_json); E0,_=sm.fg(sm.xyz_to_vars(x))
    flips=defect_reducing_flips(x)
    if len(flips)!=9: print(f'WARNING expected 9 flips, got {len(flips)}',flush=True)
    # The three C3 orbits have balanced thresholds near 0.017967, 0.018043,
    # and 0.018446 rad.  Use a tolerance safely below their 7.6e-5 minimum gap.
    tmp=[]
    for q in flips:
        t=threshold(x,q,'balanced')
        if t is not None: tmp.append((t,q))
    tmp.sort()
    reps=[]
    for t,q in tmp:
        if any(abs(t-r[0])<3e-5 for r in reps): continue
        reps.append((t,q))
    if args.family_indices!='all':
        keep={int(s) for s in args.family_indices.split(',') if s}
        reps=[r for i,r in enumerate(reps) if i in keep]
    print('representatives',[(t,q) for t,q in reps],flush=True)
    patterns=[s for s in args.patterns.split(',') if s]
    mults=[float(s) for s in args.multipliers.split(',') if s]
    specs=[]; thresholds={}
    for _,q in reps:
        for p in patterns:
            t=threshold(x,q,p); thresholds[f'{q}:{p}']=t
            print('threshold',q,p,t,flush=True)
            if t is None: continue
            for m in mults: specs.append((x,q,p,t,m,args.maxiter))
    rows=[]
    with cf.ProcessPoolExecutor(max_workers=max(1,args.workers)) as ex:
        futs={ex.submit(relax_one,s):(s[1],s[2],s[4]) for s in specs}
        for fut in cf.as_completed(futs):
            q,p,m=futs[fut]
            try:
                r=fut.result(); rows.append(r)
                print('DONE',q,p,m,f"E={r['energy']:.12f}",'coord',r['coord'],flush=True)
            except Exception as exc:
                print('FAIL',q,p,m,repr(exc),flush=True)
                rows.append({'quad':list(q),'pattern':p,'multiplier':m,'error':repr(exc)})
    good=sorted((r for r in rows if 'energy' in r),key=lambda r:r['energy'])
    basins=[]
    for r in good:
        if any(abs(r['energy']-b['energy'])<2e-6 and r['coord']==b['coord'] for b in basins): continue
        basins.append(r)
        if len(basins)>=12: break
    compact=[{k:v for k,v in r.items() if k!='points'} for r in rows]
    out={'seed_energy':float(E0),'seed_coord':meta.get('coord_counts'),'all_flips':[list(q) for q in flips],
         'representatives':[{'balanced_threshold':float(t),'quad':list(q)} for t,q in reps],
         'thresholds':thresholds,'rows':compact,'lowest_distinct_basins':basins,
         'best_energy':float(good[0]['energy']) if good else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
