#!/usr/bin/env python3
"""Construct a deterministic geodesic seed on a stationary state's low doublet.

The seed basis is canonicalized under C3 exactly as in the local Landau analysis.
Both `points` and `saddle_points` are emitted so the same file can be consumed by
arbitrary-seed Hessian diagnostics and by the saddle refiners.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh
import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed
from search_seed_c3_negative_pair import canonicalize_pair_near


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--phase-deg',type=float,required=True); ap.add_argument('--rms-amp',type=float,required=True)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x=load_seed(pathlib.Path(args.seed_json)); q=sm.xyz_to_vars(x); E0,_=sm.fg(q)
    H,raw,Q,calls=sm.build_hessian(q,args.fd_step,1e6)
    rng=np.random.default_rng(9601515); v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=6,which='SA',tol=1e-5,maxiter=800,ncv=40,v0=v0); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    pair=V[:,:2].copy(); pair-=Q@(Q.T@pair); pair,_=np.linalg.qr(pair)
    pair,M,resid,ai,ac,maperr=canonicalize_pair_near(pair,q)
    a=math.radians(args.phase_deg); direction=math.cos(a)*pair[:,0]+math.sin(a)*pair[:,1]; direction/=np.linalg.norm(direction)
    qs=sp.exp_perturb(q,direction,args.rms_amp); E,_=sm.fg(qs); pts=sm.vars_to_xyz(qs)[0].tolist()
    print(f'parent={E0:.12f} phase={args.phase_deg:g} amp={args.rms_amp:g} seed={E:.12f} dE={E-E0:+.9g}',flush=True)
    out={'parent_json':str(args.seed_json),'parent_energy':E0,'phase_deg':args.phase_deg,'rms_amp':args.rms_amp,
         'energy':E,'parent_eigenvalues':[float(v) for v in vals],'c3_pair_matrix':M.tolist(),
         'c3_subspace_residual':resid,'c3_mapping_max_error':maperr,'canonical_anchor_point':ai,
         'canonical_anchor_component':ac,'points':pts,'saddle_points':pts}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
