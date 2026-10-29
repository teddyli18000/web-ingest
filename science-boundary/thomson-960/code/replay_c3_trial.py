#!/usr/bin/env python3
"""Deterministically replay and save one historical exact-C3 smooth-search trial."""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
import search_c3_smooth as c3


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--seed',type=int,required=True)
    ap.add_argument('--trial',type=int,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    root=pathlib.Path(args.few_shots); live,shot=c3.find_live(root)
    points=c3.load_cert(shot/'certificate.json'); reps=c3.c3_representatives(points)
    base=c3.polish(c3.xyz_to_vars(reps),1200); rng=np.random.default_rng(args.seed)
    scales=np.geomspace(0.008,0.20,9); target=None; scale=None; start_e=None
    for t in range(args.trial+1):
        scale=float(scales[t%len(scales)]*math.exp(rng.normal(0.0,0.18)))
        start=c3.perturb(base.x,rng,scale)
        if t==args.trial:
            start_e,_=c3.fg(start); target=c3.polish(start); break
    if target is None: raise RuntimeError('trial not reached')
    x,_,_=c3.vars_to_full(target.x)
    out={'seed':args.seed,'trial':args.trial,'scale':scale,'start_energy':float(start_e),
         'energy':float(target.fun),'live_score':float(live),'nit':int(target.nit),
         'success':bool(target.success),'points':x.tolist()}
    print(f"seed={args.seed} trial={args.trial} scale={scale:.9g} start={start_e:.12f} E={target.fun:.12f} nit={target.nit} ok={target.success}",flush=True)
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
