#!/usr/bin/env python3
"""Audit Hessian curvature against actual geodesic energy along a low mode.

A Hessian eigenvalue is only a local statement.  For high-dimensional Thomson
stationary states, an RMS kick that looks small per particle can already leave
the quadratic region because its total tangent norm scales as sqrt(N).  This
script computes a selected physical-tangent eigenmode and compares

    E(exp_x(±a v)) - E(x)

against the quadratic prediction `0.5 * lambda * N * a^2` over user-specified
RMS amplitudes.  It reports where the observed energy trend ceases to agree in
sign with the local curvature.  Use this before choosing CHiSD/downward escape
amplitudes for a newly harvested portal.
"""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed

N=960


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--mode',type=int,default=0); ap.add_argument('--k',type=int,default=6)
    ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--amps',default='1e-5,3e-5,1e-4,2e-4,3e-4,4e-4,5e-4,6e-4,7e-4,8e-4,1e-3,1.5e-3')
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(pathlib.Path(args.seed_json)); q=sm.xyz_to_vars(x); E0,gq=sm.fg(q)
    H,raw,Q,calls=sm.build_hessian(q,args.fd_step,1e6)
    rng=np.random.default_rng(9600700+args.mode); v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=max(args.k,args.mode+1),which='SA',tol=1e-5,maxiter=800,ncv=40,v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]; v=V[:,args.mode].copy(); v-=Q@(Q.T@v); v/=np.linalg.norm(v)
    lam=float(vals[args.mode]); rows=[]
    print(f'E0={E0:.12f} mode={args.mode} lambda={lam:+.12g}',flush=True)
    for a in [float(z) for z in args.amps.split(',') if z]:
        Ep,_=sm.fg(sp.exp_perturb(q,v,a)); Em,_=sm.fg(sp.exp_perturb(q,-v,a))
        pred=0.5*lam*N*a*a
        row={'amp':a,'plus_delta':Ep-E0,'minus_delta':Em-E0,'quadratic_prediction':pred,
             'plus_sign_matches_curvature':bool((Ep-E0)*lam>=0),'minus_sign_matches_curvature':bool((Em-E0)*lam>=0)}
        rows.append(row)
        print(f'a={a:.6g} plus={Ep-E0:+.9g} minus={Em-E0:+.9g} quad={pred:+.9g}',flush=True)
    out={'seed_json':str(args.seed_json),'energy':E0,'physical_gradient_rms':float(np.sqrt(np.mean((gq/sm.physical_scale(q))**2))),
         'mode':args.mode,'eigenvalue':lam,'eigenvalues':[float(z) for z in vals],
         'fd_step':args.fd_step,'gradient_calls':calls['n'],'rows':rows}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
