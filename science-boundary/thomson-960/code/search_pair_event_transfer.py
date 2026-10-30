#!/usr/bin/env python3
"""Transfer/extrapolate a collective event learned between two Thomson minima.

Given source and target 960-point minima, find a multistart ICP/Hungarian point
correspondence, then search the geodesic event and smooth displacement-localized
versions of its continuation *through the target*.  This is intended for real
low-energy topology-changing pairs (e.g. D2 20-dislocation -> e569 19-dislocation,
or e569 -> current live record), where continuation may expose a qualitatively
new defect family rather than another random local perturbation.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment
import search_topology_morph as tm
import search_20_event_transfer as ev


def load(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=tm.N: raise ValueError('expected 960 points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]


def align(source,target,seed,starts):
    rng=np.random.default_rng(seed)
    rms,R,sa=tm.icp(source,target,rng,starts=starts,iters=18)
    cost=np.maximum(0.0,2-2*np.clip(target@sa.T,-1,1))
    ia,ib=linear_sum_assignment(cost)
    if not np.array_equal(ia,np.arange(tm.N)): raise RuntimeError('assignment rows')
    sm=sa[ib]
    mrms=float(np.sqrt(np.mean(np.sum((target-sm)**2,axis=1))))
    return sm,rms,mrms


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--starts',type=int,default=18)
    ap.add_argument('--maxiter',type=int,default=2600)
    ap.add_argument('--ts',default='-0.35,-0.15,0.25,0.5,0.75,1.08,1.16,1.28,1.45,1.70,2.0')
    ap.add_argument('--fracs',default='0.12,0.20,0.35,0.55,0.80,1.0')
    ap.add_argument('--alphas',default='-0.8,-0.45,0.20,0.45,0.75,1.05,1.40')
    ap.add_argument('--live-score',type=float,default=444368.3924061973)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    source=load(args.source_json); target=load(args.target_json)
    sm,rms,mrms=align(source,target,args.seed,args.starts)
    es=tm.raw_energy(sm); et=tm.raw_energy(target)
    print(f'PAIR seed={args.seed} source={es:.12f} {tm.coord_counts(sm)} target={et:.12f} {tm.coord_counts(target)} nn={rms:.7g} assign={mrms:.7g}',flush=True)
    rows=[]; saved=[]
    def run(label,x):
        start=tm.raw_energy(x); e,y,nit,ok=tm.relax(x,maxiter=args.maxiter); cc=tm.coord_counts(y)
        row={'label':label,'start_energy':start,'energy':e,'delta_live':e-args.live_score,'coord_counts':cc,'nit':nit,'success':ok}
        rows.append(row); print(label,'start',f'{start:.9f}','E',f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}','cc',cc,'nit',nit,flush=True)
        if e < max(es,et)+0.35:
            if all(abs(e,z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
                saved.append({'energy':e,'coord_counts':cc,'label':label,'points':y.tolist()})
    for t in [float(z) for z in args.ts.split(',') if z]:
        run(f'geo:t={t:g}',tm.geodesic(sm,target,t))
    v,mag=ev.continuation_field(sm,target)
    print('FIELD_RMS',float(np.sqrt(np.mean(mag*mag))),'quantiles',np.quantile(mag,[0,.25,.5,.75,.9,.95,1]).tolist(),flush=True)
    for f in [float(z) for z in args.fracs.split(',') if z]:
        w=ev.smooth_top_fraction(mag,f)
        for a in [float(z) for z in args.alphas.split(',') if z]:
            run(f'mask:f={f:g}:a={a:g}',ev.exp_field(target,v,a,w))
    saved.sort(key=lambda z:z['energy'])
    best=min(rows,key=lambda z:z['energy'])
    out={'seed':args.seed,'source_energy':es,'source_coord':tm.coord_counts(sm),'target_energy':et,'target_coord':tm.coord_counts(target),
         'icp_nn_rms':rms,'assignment_rms':mrms,'rows':rows,'best_energy':best['energy'],'best_label':best['label'],
         'best_delta_live':best['delta_live'],'distinct_low_basins':saved[:16]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved:
        pathlib.Path(str(args.out)+'.best.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
