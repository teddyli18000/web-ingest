#!/usr/bin/env python3
"""Relax a string between two Thomson minima and quench every interior image.

This is a basin-discovery calculation, not a transition-state certification.
The source and target are arbitrary 960-point minima supplied as JSON. A
multistart ICP/Hungarian correspondence initializes a spherical string,
perpendicular-gradient string dynamics curves it toward a transition corridor,
and every final interior image is fully relaxed. All distinct low minima are
retained irrespective of defect topology.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment

import search_topology_morph as tm
import string_record_neighbor as sr


def load_points(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N:
        raise ValueError('expected 960 points')
    x=np.asarray(p,float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def align_source(source,target,seed,starts):
    rng=np.random.default_rng(seed)
    rms,R,sa=tm.icp(source,target,rng,starts=starts,iters=18)
    cost=np.maximum(0.0,2-2*np.clip(target@sa.T,-1,1))
    ia,ib=linear_sum_assignment(cost)
    if not np.array_equal(ia,np.arange(tm.N)):
        raise RuntimeError('assignment rows')
    sm=sa[ib]
    mrms=float(np.sqrt(np.mean(np.sum((target-sm)**2,axis=1))))
    return sm,rms,mrms


def interpolate(L,R,n):
    return [tm.geodesic(L,R,i/(n-1)) for i in range(n)]


def diagnostics(images):
    vals=[]; grads=[]; perps=[]
    for x in images:
        e,g=sr.energy_grad(x)
        vals.append(float(e)); grads.append(g)
    for i in range(1,len(images)-1):
        tau=sr.path_tangent(images,i)
        gp=grads[i]-float(np.sum(grads[i]*tau))*tau
        perps.append(float(np.sqrt(np.mean(np.sum(gp*gp,axis=1)))))
    return vals,grads,perps


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--starts',type=int,default=18)
    ap.add_argument('--images',type=int,default=13); ap.add_argument('--iterations',type=int,default=320)
    ap.add_argument('--eta',type=float,default=2.0e-4); ap.add_argument('--max-step',type=float,default=5.0e-4)
    ap.add_argument('--quench-maxiter',type=int,default=2800)
    ap.add_argument('--retain-window',type=float,default=0.45)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    live_score,live_dir=tm.find_live(root)
    source=load_points(args.source_json); target=load_points(args.target_json)
    L,rms,mrms=align_source(source,target,args.seed,args.starts); R=target
    eL=tm.raw_energy(L); eR=tm.raw_energy(R)
    images=interpolate(L,R,args.images)
    print(f'ALIGN seed={args.seed} nn={rms:.7g} assignment={mrms:.7g} L={eL:.12f} {tm.coord_counts(L)} R={eR:.12f} {tm.coord_counts(R)}',flush=True)

    hist=[]
    for it in range(args.iterations):
        vals,grads,perps=diagnostics(images)
        new=[images[0]]; ms=0.0
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=grads[i]-float(np.sum(grads[i]*tau))*tau
            y,s=sr.capped_descent(images[i],gp,args.eta,args.max_step)
            new.append(y); ms=max(ms,s)
        new.append(images[-1])
        images,arc=sr.reparameterize(new)
        if it%20==0 or it==args.iterations-1:
            vv,_,pp=diagnostics(images); mp=max(pp) if pp else 0.0
            print(f'ITER {it} min={min(vv):.12f} max={max(vv):.12f} arc={arc:.6g} step={ms:.3g} perp={mp:.6g}',flush=True)
            hist.append({'iteration':it,'energies':vv,'arc':arc,'max_step':ms,'max_perp':mp})

    vals,_,perps=diagnostics(images)
    endpoint_meta=[
        {'energy':eL,'coord_counts':tm.coord_counts(L),'name':'source'},
        {'energy':eR,'coord_counts':tm.coord_counts(R),'name':'target'},
    ]
    quenches=[]; saved=[]
    ceiling=max(eL,eR)+args.retain_window
    for i,x in enumerate(images[1:-1],1):
        e,y,nit,ok=tm.relax(x,maxiter=args.quench_maxiter)
        cc=tm.coord_counts(y)
        endpoint_like=any(abs(e-z['energy'])<2e-6 and cc==z['coord_counts'] for z in endpoint_meta)
        row={'image':i,'path_energy':vals[i],'energy':e,'delta_live':e-live_score,
             'coord_counts':cc,'nit':nit,'success':ok,'endpoint_like':endpoint_like}
        quenches.append(row)
        print(f'QUENCH i={i} path={vals[i]:.12f} -> E={e:.12f} dLive={e-live_score:+.9g} cc={cc} endpoint={endpoint_like} nit={nit}',flush=True)
        if e < ceiling and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
            saved.append({'image':i,'energy':e,'delta_live':e-live_score,
                          'coord_counts':cc,'endpoint_like':endpoint_like,'points':y.tolist()})
    saved.sort(key=lambda z:z['energy'])
    best=min(saved,key=lambda z:z['energy']) if saved else None
    novel=[z for z in saved if not z['endpoint_like']]
    out={'seed':args.seed,'starts':args.starts,'images':args.images,'iterations':args.iterations,
         'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),
         'source_energy':eL,'source_coord':tm.coord_counts(L),
         'target_energy':eR,'target_coord':tm.coord_counts(R),
         'icp_nn_rms':rms,'assignment_rms':mrms,'path_energies':vals,
         'max_path_perp':max(perps) if perps else 0.0,'history':hist,'quenches':quenches,
         'distinct_low_basins':saved[:24],
         'novel_low_basins':novel[:24],
         'best_energy':best['energy'] if best else None,
         'best_delta_live':best['delta_live'] if best else None}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best is not None and best['energy'] < live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(
            json.dumps({'name':'pair-string-candidate','energy':best['energy'],
                        'coord_counts':best['coord_counts'],'points':best['points']},
                       separators=(',',':'))+'\n')
    if novel:
        pathlib.Path(str(args.out)+'.best-novel.json').write_text(
            json.dumps({'name':'pair-string-novel','energy':novel[0]['energy'],
                        'coord_counts':novel[0]['coord_counts'],'points':novel[0]['points']},
                       separators=(',',':'))+'\n')


if __name__=='__main__':
    main()
