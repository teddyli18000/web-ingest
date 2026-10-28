#!/usr/bin/env python3
"""Validate an arbitrary near-stationary index-1 Thomson seed by its true negative mode.

The seed is Hessian-classified in full physical tangent coordinates. If it has
exactly one internal negative mode, perturb directly along ± that eigenvector at
requested RMS amplitudes and fully relax each child with the stable termwise
pair-energy-difference objective. This avoids all mode-tracking/refinement and
answers the topological question: which minima lie on the two reaction sides?
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q

N=960


def load_any_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('points') if isinstance(d,dict) else None
    if p is None and isinstance(d,dict): p=d.get('saddle_points')
    if p is None or len(p)!=N: raise ValueError('seed must contain 960 points or saddle_points')
    x=np.asarray(p,float); return d,x/np.linalg.norm(x,axis=1)[:,None]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('seed_json')
    ap.add_argument('--amps',default='0.00005,0.0001,0.0002,0.0003'); ap.add_argument('--k',type=int,default=10)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--out',required=True); args=ap.parse_args()
    root=pathlib.Path(args.few_shots); live_score,live_shot=sm.find_live(root); meta,x=load_any_seed(args.seed_json); q=sm.xyz_to_vars(x)
    E0,gq=sm.fg(q); gp=gq/sm.physical_scale(q); grms=float(np.linalg.norm(gp)/math.sqrt(2*N))
    H,raw,Q,calls=sm.build_hessian(q,args.fd_step,1e6)
    rng=np.random.default_rng(9601001); v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=args.k,which='SA',tol=1e-5,maxiter=900,ncv=max(40,4*args.k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    neg=int(np.sum(vals<-1e-3)); mode=V[:,0].copy(); mode-=Q@(Q.T@mode); mode/=np.linalg.norm(mode)
    print(f'seed E={E0:.12f} grad={grms:.7g} neg={neg} lows={vals[:5].tolist()}',flush=True)
    if neg!=1: raise RuntimeError(f'expected exactly one negative mode, got {neg}')
    rows=[]
    for sign in (-1,1):
        for amp in [float(z) for z in args.amps.split(',') if z]:
            qs=sp.exp_perturb(q,sign*mode,amp); start,_=sm.fg(qs)
            E,rawE,y,nit,ok,msg=stable_relax_q(qs,2600)
            row={'sign':sign,'amp':amp,'start_energy':start,'energy':E,'delta_vs_live':E-live_score,
                 'nit':nit,'success':ok,'message':msg}
            rows.append(row)
            print(f'sign={sign:+d} amp={amp:.6g} start={start:.12f} E={E:.12f} dlive={E-live_score:+.9g} nit={nit}',flush=True)
    out={'seed_json':str(args.seed_json),'live_score':live_score,'live_shot':str(live_shot.relative_to(root)),
         'seed_energy':E0,'seed_gradient_rms':grms,'negative_internal_modes_below_-1e-3':neg,
         'eigenvalues':[float(v) for v in vals],'gradient_calls_for_modes':calls['n'],'rows':rows}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__': main()
