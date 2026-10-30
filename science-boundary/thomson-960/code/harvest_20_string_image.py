#!/usr/bin/env python3
"""Reproduce a selected quenched image from a genuine20->D2 string search.

This recovers lower-topology minima (e.g. 19/18 dislocations) that were found
by ``search_20_string_quench.py`` but were not written with coordinates because
that discovery script only persisted novel 20-dislocation endpoints.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np

import search_topology_morph as tm
import search_20_string_quench as sq
import string_record_neighbor as sr


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('source_json')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--starts',type=int,default=18)
    ap.add_argument('--images',type=int,default=11); ap.add_argument('--iterations',type=int,default=260)
    ap.add_argument('--eta',type=float,default=2.2e-4); ap.add_argument('--max-step',type=float,default=6e-4)
    ap.add_argument('--image-index',type=int,required=True)
    ap.add_argument('--quench-maxiter',type=int,default=2800)
    ap.add_argument('--expected',type=float,required=True); ap.add_argument('--tol',type=float,default=5e-5)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    source=sq.load_points(args.source_json); d2=tm.cert_xyz(root/tm.D2_REL)
    L,rms,mrms=sq.align_source(source,d2,args.seed,args.starts)
    images=sq.interpolate(L,d2,args.images)
    for it in range(args.iterations):
        vals,grads,perps=sq.diagnostics(images)
        new=[images[0]]
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=grads[i]-float(np.sum(grads[i]*tau))*tau
            y,_=sr.capped_descent(images[i],gp,args.eta,args.max_step)
            new.append(y)
        new.append(images[-1]); images,_=sr.reparameterize(new)
    vals,_,perps=sq.diagnostics(images)
    idx=args.image_index
    if idx<=0 or idx>=len(images)-1: raise ValueError('image index must be interior')
    e,y,nit,ok=tm.relax(images[idx],maxiter=args.quench_maxiter)
    cc=tm.coord_counts(y)
    print(f'HARVEST seed={args.seed} image={idx} path={vals[idx]:.12f} E={e:.12f} cc={cc} align={mrms:.7g} maxperp={max(perps):.6g} nit={nit} ok={ok}',flush=True)
    if abs(e-args.expected)>args.tol:
        raise RuntimeError(f'endpoint mismatch expected {args.expected} got {e}')
    out={'name':f'genuine20-string-{args.seed}-image{idx}','source_seed':args.seed,
         'image_index':idx,'path_energy':vals[idx],'energy':e,'coord_counts':cc,
         'icp_nn_rms':rms,'assignment_rms':mrms,'max_path_perp':max(perps),
         'nit':nit,'success':ok,'points':y.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
