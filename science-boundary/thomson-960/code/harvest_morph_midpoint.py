#!/usr/bin/env python3
"""Harvest the non-endpoint basin reached at the D2<->C3 geodesic morph midpoint.

Reproduces the seed-5011 ICP/Hungarian correspondence used by
search_topology_morph.py, evaluates t=0.5 only, fully relaxes with the same
stable termwise-difference objective, and ALWAYS saves final coordinates plus
Delaunay coordination counts. The first broad morph scan found this midpoint
converges to an independent basin about +2.138 above the live record while
t<=0.4 returns C3 and t>=0.6 returns D2.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment

import search_topology_morph as tm


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--seed',type=int,default=5011); ap.add_argument('--t',type=float,default=0.5); ap.add_argument('--out',required=True)
    args=ap.parse_args(); root=pathlib.Path(args.few_shots); rng=np.random.default_rng(args.seed)
    live_score,live_dir=tm.find_live(root)
    A=tm.cert_xyz(live_dir/'certificate.json'); B=tm.cert_xyz(root/tm.D2_REL)
    rms,R,Ba=tm.icp(B,A,rng)
    cost=np.maximum(0.0,2-2*np.clip(A@Ba.T,-1,1)); ia,ib=linear_sum_assignment(cost); assert np.array_equal(ia,np.arange(tm.N))
    Bm=Ba[ib]; match_rms=float(np.sqrt(np.mean(np.sum((A-Bm)**2,axis=1))))
    X=tm.geodesic(A,Bm,args.t); start=tm.raw_energy(X)
    E,Y,nit,ok=tm.relax(X); cc=tm.coord_counts(Y)
    print(f'live={live_score:.10f} t={args.t:.5f} icp_nn_rms={rms:.6g} hungarian_rms={match_rms:.6g}')
    print(f'start={start:.12f} E={E:.12f} dlive={E-live_score:+.12g} nit={nit} ok={ok} coord={cc}')
    out={'seed':args.seed,'t':args.t,'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),
         'icp_nn_rms':rms,'hungarian_rms':match_rms,'start_energy':start,'energy':E,'delta_vs_live':E-live_score,
         'nit':nit,'success':ok,'coord_counts':cc,'points':Y.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
