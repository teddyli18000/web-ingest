#!/usr/bin/env python3
"""Relax a high20<->D2 string, then quench every interior image to minima.

This is a basin-discovery use of the string method rather than a saddle
certification run.  The endpoints are two genuine 32/908/20 minima.  After
multistart ICP/Hungarian correspondence, an 11--15 image spherical string is
relaxed by perpendicular-gradient descent and reparameterization.  Each final
interior image is then independently fully minimized with the stable long-double
energy-difference objective.  Distinct quenched minima reveal intermediate
basins along a physically organized collective transition corridor.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment

import search_topology_morph as tm
import string_record_neighbor as sr


def load_points(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N: raise ValueError('expected 960 points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]


def align_source(source,d2,seed,starts):
    rng=np.random.default_rng(seed)
    rms,R,sa=tm.icp(source,d2,rng,starts=starts,iters=18)
    cost=np.maximum(0.0,2-2*np.clip(d2@sa.T,-1,1))
    ia,ib=linear_sum_assignment(cost)
    if not np.array_equal(ia,np.arange(tm.N)): raise RuntimeError('assignment rows')
    sm=sa[ib]
    mrms=float(np.sqrt(np.mean(np.sum((d2-sm)**2,axis=1))))
    return sm,rms,mrms


def interpolate(L,R,n):
    return [tm.geodesic(L,R,i/(n-1)) for i in range(n)]


def diagnostics(images):
    vals=[]; grads=[]; perps=[]
    for x in images:
        e,g=sr.energy_grad(x); vals.append(float(e)); grads.append(g)
    for i in range(1,len(images)-1):
        tau=sr.path_tangent(images,i)
        gp=grads[i]-float(np.sum(grads[i]*tau))*tau
        perps.append(float(np.sqrt(np.mean(np.sum(gp*gp,axis=1)))))
    return vals,grads,perps


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('source_json')
    ap.add_argument('--seed',type=int,default=7301); ap.add_argument('--starts',type=int,default=16)
    ap.add_argument('--images',type=int,default=11); ap.add_argument('--iterations',type=int,default=260)
    ap.add_argument('--eta',type=float,default=2.2e-4); ap.add_argument('--max-step',type=float,default=6e-4)
    ap.add_argument('--quench-maxiter',type=int,default=2400); ap.add_argument('--out',required=True)
    args=ap.parse_args()
    root=pathlib.Path(args.few_shots)
    live_score,live_dir=tm.find_live(root)
    source=load_points(args.source_json); d2=tm.cert_xyz(root/tm.D2_REL)
    L,rms,mrms=align_source(source,d2,args.seed,args.starts); R=d2
    images=interpolate(L,R,args.images)
    print(f'ALIGN seed={args.seed} nn={rms:.7g} assignment={mrms:.7g} L={tm.raw_energy(L):.12f} R={tm.raw_energy(R):.12f}',flush=True)
    hist=[]
    for it in range(args.iterations):
        vals,grads,perps=diagnostics(images)
        new=[images[0]]; ms=0.0
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=grads[i]-float(np.sum(grads[i]*tau))*tau
            y,s=sr.capped_descent(images[i],gp,args.eta,args.max_step)
            new.append(y); ms=max(ms,s)
        new.append(images[-1]); images,arc=sr.reparameterize(new)
        if it%20==0 or it==args.iterations-1:
            vv,_,pp=diagnostics(images); mp=max(pp) if pp else 0.0
            print(f'ITER {it} min={min(vv):.12f} max={max(vv):.12f} arc={arc:.6g} step={ms:.3g} perp={mp:.6g}',flush=True)
            hist.append({'iteration':it,'energies':vv,'arc':arc,'max_step':ms,'max_perp':mp})
    vals,_,perps=diagnostics(images)

    quenches=[]; novel=[]
    endpoint_es=[tm.raw_energy(L),tm.raw_energy(R)]
    for i,x in enumerate(images[1:-1],1):
        e,y,nit,ok=tm.relax(x,maxiter=args.quench_maxiter); cc=tm.coord_counts(y)
        row={'image':i,'path_energy':vals[i],'energy':e,'delta_live':e-live_score,'coord_counts':cc,'nit':nit,'success':ok}
        quenches.append(row)
        print(f'QUENCH i={i} path={vals[i]:.12f} -> E={e:.12f} dLive={e-live_score:+.9g} cc={cc} nit={nit}',flush=True)
        if cc=={'5':32,'6':908,'7':20} and all(abs(e-z)>2e-6 for z in endpoint_es):
            if all(abs(e-z['energy'])>2e-6 for z in novel):
                novel.append({'image':i,'energy':e,'coord_counts':cc,'points':y.tolist()})
    novel.sort(key=lambda z:z['energy'])
    out={'seed':args.seed,'starts':args.starts,'images':args.images,'iterations':args.iterations,
         'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),
         'icp_nn_rms':rms,'assignment_rms':mrms,'path_energies':vals,
         'max_path_perp':max(perps) if perps else 0.0,'history':hist,'quenches':quenches,
         'novel_20_basins':novel[:12],
         'best_novel_20_energy':novel[0]['energy'] if novel else None,
         'best_delta_live':(novel[0]['energy']-live_score) if novel else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if novel:
        pathlib.Path(str(args.out)+'.best20.json').write_text(json.dumps({'name':'string-quench-20','energy':novel[0]['energy'],'coord_counts':novel[0]['coord_counts'],'points':novel[0]['points']},separators=(',',':'))+'\n')

if __name__=='__main__': main()
