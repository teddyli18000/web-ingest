#!/usr/bin/env python3
"""Reproduce and freeze the low symmetry-broken basin B from durable basin A.

B was repeatedly reached from A by the third low internal mode with negative
sign near 0.012 rad RMS, but earlier search artifacts intentionally saved full
coordinates only for record-beating candidates.  The transition-network route
now needs B as a durable endpoint for A<->B saddle calculations, so this script
reproduces that branch and always writes the relaxed 960-point coordinates.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed, stable_relax_q


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('seed_a_json')
    ap.add_argument('--mode',type=int,default=2)
    ap.add_argument('--sign',type=int,default=-1,choices=[-1,1])
    ap.add_argument('--amp',type=float,default=0.012)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    _meta,x0=load_seed(args.seed_a_json); q0=sm.xyz_to_vars(x0)
    e0,_=sm.fg(q0)
    H,raw,Qrot,calls=sm.build_hessian(q0,3e-6,1e6)
    k=max(8,args.mode+1)
    rng=np.random.default_rng(9602026)
    v0=rng.normal(size=len(q0)); v0-=Qrot@(Qrot.T@v0)
    vals,vecs=eigsh(H,k=k,which='SA',tol=2e-5,maxiter=700,ncv=max(40,3*k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; vecs=vecs[:,o]
    d=vecs[:,args.mode].copy(); d-=Qrot@(Qrot.T@d); d*=args.sign/np.linalg.norm(d)
    qs=sp.exp_perturb(q0,d,args.amp)
    start,_=sm.fg(qs)
    e,raw_e,x,nit,ok,msg=stable_relax_q(qs,2400)
    print(f'A={e0:.12f} mode={args.mode} lambda={vals[args.mode]:.12g} sign={args.sign} amp={args.amp}',flush=True)
    print(f'start={start:.12f} B={e:.12f} raw={raw_e:.12f} deltaA={e-e0:+.9g} nit={nit} ok={ok}',flush=True)
    out={'source_a':str(args.seed_a_json),'source_energy':e0,'mode':args.mode,
         'eigenvalue':float(vals[args.mode]),'sign':args.sign,'amp':args.amp,
         'start_energy':start,'energy':e,'raw_absolute_energy':raw_e,
         'nit':nit,'success':ok,'message':msg,'gradient_calls_for_modes':calls['n'],
         'points':x.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
