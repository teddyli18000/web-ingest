#!/usr/bin/env python3
"""Deterministically reproduce and quench one image of a pair string."""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np
import search_topology_morph as tm
import search_pair_string_quench as ps
import string_record_neighbor as sr


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('few_shots'); ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--starts',type=int,default=20)
    ap.add_argument('--images',type=int,default=13); ap.add_argument('--iterations',type=int,default=340)
    ap.add_argument('--eta',type=float,default=2.0e-4); ap.add_argument('--max-step',type=float,default=5.0e-4)
    ap.add_argument('--image-index',type=int,required=True); ap.add_argument('--quench-maxiter',type=int,default=3000)
    ap.add_argument('--expected',type=float); ap.add_argument('--tol',type=float,default=5e-5)
    ap.add_argument('--expected-five',type=int); ap.add_argument('--expected-six',type=int); ap.add_argument('--expected-seven',type=int)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    source=ps.load_points(args.source_json); target=ps.load_points(args.target_json)
    L,rms,mrms=ps.align_source(source,target,args.seed,args.starts); R=target
    images=ps.interpolate(L,R,args.images)
    last_perp=None
    for it in range(args.iterations):
        vals,grads,perps=ps.diagnostics(images)
        new=[images[0]]
        for i in range(1,len(images)-1):
            tau=sr.path_tangent(images,i)
            gp=grads[i]-float(np.sum(grads[i]*tau))*tau
            y,_=sr.capped_descent(images[i],gp,args.eta,args.max_step)
            new.append(y)
        new.append(images[-1]); images,_=sr.reparameterize(new)
        last_perp=max(perps) if perps else 0.0
    idx=args.image_index
    if idx<=0 or idx>=len(images)-1: raise ValueError('image-index must be interior')
    path_e=tm.raw_energy(images[idx])
    e,y,nit,ok=tm.relax(images[idx],maxiter=args.quench_maxiter); cc=tm.coord_counts(y)
    print(f'HARVEST seed={args.seed} image={idx} path={path_e:.12f} E={e:.12f} cc={cc} nn={rms:.7g} assign={mrms:.7g} maxperp={last_perp:.6g} nit={nit} ok={ok}',flush=True)
    if args.expected is not None and abs(e-args.expected)>args.tol:
        raise RuntimeError(f'energy mismatch {e} vs expected {args.expected}')
    exp={}
    if args.expected_five is not None: exp['5']=args.expected_five
    if args.expected_six is not None: exp['6']=args.expected_six
    if args.expected_seven is not None: exp['7']=args.expected_seven
    if exp and cc!=exp: raise RuntimeError(f'topology mismatch {cc} vs {exp}')
    out={'name':'harvested-pair-string-image','energy':e,'coord_counts':cc,
         'source':{'seed':args.seed,'image':idx,'path_energy':path_e,'iterations':args.iterations,
                   'icp_nn_rms':rms,'assignment_rms':mrms,'max_path_perp':last_perp},
         'points':y.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
