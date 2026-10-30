#!/usr/bin/env python3
"""Reproduce and freeze one endpoint of the high20->D2 collective event search."""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from scipy.optimize import linear_sum_assignment
import search_topology_morph as tm
import search_20_event_transfer as ev


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('source_json')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--starts',type=int,default=20)
    ap.add_argument('--kind',choices=['corridor','mask'],required=True)
    ap.add_argument('--t',type=float); ap.add_argument('--frac',type=float); ap.add_argument('--alpha',type=float)
    ap.add_argument('--maxiter',type=int,default=2600); ap.add_argument('--expected',type=float,required=True)
    ap.add_argument('--tol',type=float,default=3e-5); ap.add_argument('--out',required=True)
    args=ap.parse_args()
    root=pathlib.Path(args.few_shots)
    source=ev.load_points(pathlib.Path(args.source_json)); d2=tm.cert_xyz(root/tm.D2_REL)
    rng=np.random.default_rng(args.seed)
    rms,R,sa=tm.icp(source,d2,rng,starts=args.starts,iters=18)
    cost=np.maximum(0.0,2-2*np.clip(d2@sa.T,-1,1)); ia,ib=linear_sum_assignment(cost)
    if not np.array_equal(ia,np.arange(tm.N)): raise RuntimeError('assignment rows')
    sm=sa[ib]
    if args.kind=='corridor':
        if args.t is None: raise ValueError('--t required')
        x=tm.geodesic(sm,d2,args.t); label=f'corridor:t={args.t:g}'
    else:
        if args.frac is None or args.alpha is None: raise ValueError('--frac/--alpha required')
        v,mag=ev.continuation_field(sm,d2); w=ev.smooth_top_fraction(mag,args.frac)
        x=ev.exp_field(d2,v,args.alpha,w); label=f'mask:f={args.frac:g}:a={args.alpha:g}'
    start=tm.raw_energy(x); e,y,nit,ok=tm.relax(x,maxiter=args.maxiter); cc=tm.coord_counts(y)
    print('HARVEST',label,'align',rms,'start',start,'E',e,'cc',cc,'nit',nit,'ok',ok,flush=True)
    if abs(e-args.expected)>args.tol:
        raise RuntimeError(f'endpoint mismatch expected {args.expected} got {e}')
    out={'name':f'genuine20-event-{label}','source_seed':args.seed,'label':label,
         'energy':e,'coord_counts':cc,'alignment_nn_rms':rms,'start_energy':start,
         'nit':nit,'success':ok,'points':y.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
