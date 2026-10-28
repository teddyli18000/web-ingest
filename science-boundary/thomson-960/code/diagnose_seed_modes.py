#!/usr/bin/env python3
"""Full-space low-Hessian diagnostic for an arbitrary saved Thomson N=960 seed."""
from __future__ import annotations
import argparse, json, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh
import diagnose_soft_modes as sm


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=960: raise ValueError('seed must contain 960 points')
    x=np.asarray(p,float); return d,x/np.linalg.norm(x,axis=1)[:,None]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--k',type=int,default=14)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--seed',type=int,default=9607); ap.add_argument('--out',required=True)
    args=ap.parse_args(); meta,x=load_seed(args.seed_json); q=sm.xyz_to_vars(x); E,gq=sm.fg(q)
    scale=sm.physical_scale(q); gp=gq/scale; H,raw,Q,calls=sm.build_hessian(q,args.fd_step,1e6)
    rng=np.random.default_rng(args.seed); v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=args.k,which='SA',tol=1e-5,maxiter=800,ncv=max(40,3*args.k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]; rows=[]
    for j,lam in enumerate(vals):
        y=V[:,j]; Hy=raw(y)+1e6*(Q@(Q.T@y))
        rows.append({'index':j,'eigenvalue':float(lam),'rotation_overlap':float(np.sum((Q.T@y)**2)),
                     'residual':float(np.linalg.norm(Hy-lam*y))})
        print(f'mode={j:02d} lambda={lam:.12g} rot={rows[-1]["rotation_overlap"]:.2e} resid={rows[-1]["residual"]:.2e}',flush=True)
    neg=int(np.sum(vals<-1e-3)); grms=float(np.sqrt(np.mean(gp*gp)))
    print(f'E={E:.12f} grad_rms={grms:.6g} negative={neg}',flush=True)
    out={'seed_json':str(args.seed_json),'energy':float(E),'physical_gradient_rms':grms,
         'negative_internal_modes_below_-1e-3':neg,'fd_step':args.fd_step,'gradient_calls':calls['n'],'modes':rows}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
