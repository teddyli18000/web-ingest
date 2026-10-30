#!/usr/bin/env python3
"""Continuous spherical morph from an arbitrary N=960 minimum to merged D2.

Align the merged 20-dislocation D2 record to the supplied seed with multistart
ICP + Hungarian one-to-one assignment. Geodesic interpolation followed by full
stable relaxation probes whether the seed and D2 are separated by simple basin
boundaries or by additional topological minima.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment

import search_topology_morph as tm
from search_from_seed_modes import load_seed


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('seed_json')
    ap.add_argument('--seed',type=int,default=6101)
    ap.add_argument('--ts',default='0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.90')
    ap.add_argument('--out',required=True); args=ap.parse_args()
    root=pathlib.Path(args.few_shots); rng=np.random.default_rng(args.seed)
    meta,A=load_seed(pathlib.Path(args.seed_json)); B=tm.cert_xyz(root/tm.D2_REL)
    live_score,_=tm.find_live(root)
    rms,R,Ba=tm.icp(B,A,rng,starts=16,iters=18)
    cost=np.maximum(0.0,2-2*np.clip(A@Ba.T,-1,1))
    ia,ib=linear_sum_assignment(cost); assert np.array_equal(ia,np.arange(tm.N))
    Bm=Ba[ib]
    match=float(np.sqrt(np.mean(np.sum((A-Bm)**2,axis=1))))
    EA=tm.raw_energy(A); EB=tm.raw_energy(Bm)
    print(f'seed={args.seed} A={EA:.12f} D2={EB:.12f} icp={rms:.6g} hungarian={match:.6g}',flush=True)
    rows=[]; basins=[]
    for t in [float(s) for s in args.ts.split(',') if s]:
        X=tm.geodesic(A,Bm,t); start=tm.raw_energy(X)
        E,Y,nit,ok=tm.relax(X,maxiter=2100); cc=tm.coord_counts(Y)
        row={'t':t,'start_energy':start,'energy':E,'delta_vs_live':E-live_score,'nit':nit,'success':ok,'coord_counts':cc}
        rows.append(row)
        print(f't={t:.3f} start={start:.9f} E={E:.12f} dLive={E-live_score:+.9g} coord={cc}',flush=True)
        if not any(abs(E-b['energy'])<2e-6 and cc==b['coord_counts'] for b in basins):
            b=dict(row); b['points']=Y.tolist(); basins.append(b); basins.sort(key=lambda z:z['energy']); basins=basins[:10]
    out={'alignment_seed':args.seed,'seed_json':str(args.seed_json),'seed_energy':EA,'d2_energy':EB,
         'live_score':live_score,'icp_nn_rms':rms,'hungarian_rms':match,'rows':rows,
         'lowest_distinct_basins':basins,'best_energy':min(r['energy'] for r in rows)}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
