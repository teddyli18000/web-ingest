#!/usr/bin/env python3
"""Explore the genuine 20-dislocation landscape using a learned high20 -> D2 event.

The durable ``basin-20-morph-9136.json`` is a fully unconstrained 32/908/20
minimum, while the historical Few Shots D2 solution is a much lower 32/908/20
minimum.  Rather than trying to create 20-topology from the 21-dislocation e545
family, this script treats the displacement between two *actual* 20-topology
minima as a collective grain-boundary event.

For each multistart ICP/Hungarian alignment it searches:
  * the spherical geodesic corridor from high20 to D2;
  * finite extrapolations through D2;
  * smooth displacement-magnitude masks of the continuation field at D2,
    separating defect-core-dominated from global elastic motion.
Every endpoint is fully unconstrained and relaxed with the long-double stable
pair-energy-difference objective from ``search_topology_morph``.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.optimize import linear_sum_assignment

import search_topology_morph as tm


def load_points(path: pathlib.Path) -> np.ndarray:
    d=json.loads(path.read_text())
    pts=d.get('points') if isinstance(d,dict) else d
    if pts is None or len(pts)!=tm.N:
        raise ValueError('source must contain 960 points')
    x=np.asarray(pts,float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def continuation_field(source: np.ndarray, target: np.ndarray):
    """Log-vector at target continuing from source through target."""
    c=np.clip(np.sum(source*target,axis=1),-1.0,1.0)
    th=np.arccos(c)
    s=np.sin(th)
    v=np.zeros_like(target)
    good=s>1e-10
    v[good]=(th[good]/s[good])[:,None]*(c[good,None]*target[good]-source[good])
    # Tiny separations: first-order tangent continuation.
    bad=~good
    if np.any(bad):
        z=target[bad]-source[bad]
        z-=np.sum(z*target[bad],axis=1)[:,None]*target[bad]
        v[bad]=z
    mag=np.linalg.norm(v,axis=1)
    return v,mag


def exp_field(base: np.ndarray, v: np.ndarray, scale: float, weights: np.ndarray):
    z=v*(scale*weights)[:,None]
    a=np.linalg.norm(z,axis=1)
    out=np.empty_like(base)
    small=a<1e-12
    out[small]=base[small]+z[small]
    q=~small
    out[q]=np.cos(a[q])[:,None]*base[q]+(np.sin(a[q])/a[q])[:,None]*z[q]
    return out/np.linalg.norm(out,axis=1)[:,None]


def smooth_top_fraction(mag: np.ndarray, frac: float):
    if frac>=0.999:
        return np.ones_like(mag)
    thr=float(np.quantile(mag,1.0-frac))
    width=max(2e-5,0.12*float(np.std(mag)))
    z=np.clip((mag-thr)/width,-40,40)
    return 1.0/(1.0+np.exp(-z))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots')
    ap.add_argument('source_json')
    ap.add_argument('--seed',type=int,default=7201)
    ap.add_argument('--starts',type=int,default=18)
    ap.add_argument('--maxiter',type=int,default=2200)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    source=load_points(pathlib.Path(args.source_json))
    d2=tm.cert_xyz(root/tm.D2_REL)
    live_score,live_dir=tm.find_live(root)
    rng=np.random.default_rng(args.seed)

    rms,R,sa=tm.icp(source,d2,rng,starts=args.starts,iters=18)
    cost=np.maximum(0.0,2-2*np.clip(d2@sa.T,-1,1))
    ia,ib=linear_sum_assignment(cost)
    if not np.array_equal(ia,np.arange(tm.N)):
        raise RuntimeError('unexpected assignment rows')
    sm=sa[ib]
    match_rms=float(np.sqrt(np.mean(np.sum((d2-sm)**2,axis=1))))
    print(f'ALIGN seed={args.seed} nn_rms={rms:.7g} assignment_rms={match_rms:.7g}',flush=True)
    print(f'SOURCE E={tm.raw_energy(sm):.12f} cc={tm.coord_counts(sm)} D2 E={tm.raw_energy(d2):.12f} cc={tm.coord_counts(d2)} live={live_score:.10f}',flush=True)

    rows=[]
    best=(float('inf'),None,None)

    def run(label,x):
        nonlocal best
        start=tm.raw_energy(x)
        e,y,nit,ok=tm.relax(x,maxiter=args.maxiter)
        cc=tm.coord_counts(y) if e<live_score+2.0 else None
        r={'label':label,'start_energy':start,'energy':e,'delta_live':e-live_score,
           'nit':nit,'success':ok,'coord_counts':cc}
        rows.append(r)
        print(f"{label} start={start:.9f} E={e:.12f} dLive={e-live_score:+.9g} cc={cc} nit={nit}",flush=True)
        if e<best[0]: best=(e,y.copy(),label)

    # Corridor and continuation through D2.  Include slightly negative t to
    # probe the opposite side of the high20 basin along the same collective event.
    for t in (-0.20,-0.10,0.15,0.30,0.45,0.60,0.75,0.90,1.05,1.12,1.25,1.40,1.60):
        run(f'corridor:t={t:g}',tm.geodesic(sm,d2,t))

    v,mag=continuation_field(sm,d2)
    print('FIELD rms',float(np.sqrt(np.mean(mag*mag))),'q',np.quantile(mag,[0,.25,.5,.75,.9,.95,1]).tolist(),flush=True)
    for frac in (0.15,0.30,0.50,0.75,1.0):
        w=smooth_top_fraction(mag,frac)
        for alpha in (-0.80,-0.45,0.25,0.50,0.85,1.20):
            run(f'mask:f={frac:g}:a={alpha:g}',exp_field(d2,v,alpha,w))

    good20=[r for r in rows if r.get('coord_counts')=={'5':32,'6':908,'7':20}]
    out={
      'seed':args.seed,'starts':args.starts,'source_json':args.source_json,
      'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),
      'icp_nn_rms':rms,'assignment_rms':match_rms,
      'field_rms':float(np.sqrt(np.mean(mag*mag))),
      'rows':rows,'best_energy':best[0],'best_label':best[2],
      'best_delta_live':best[0]-live_score,
      'best20_energy':min((r['energy'] for r in good20),default=None),
      'best_points':best[1].tolist() if best[1] is not None and best[0]<live_score-2e-7 else None,
    }
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__':
    main()
