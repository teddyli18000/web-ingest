#!/usr/bin/env python3
"""Classify an arbitrary saved N=960 configuration by full-space tangent Hessian."""
from __future__ import annotations
import argparse,json,pathlib,math
import numpy as np
from scipy.sparse.linalg import eigsh
import diagnose_soft_modes as sm


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input_json'); ap.add_argument('--k',type=int,default=16)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--out',required=True); args=ap.parse_args()
    d=json.loads(pathlib.Path(args.input_json).read_text()); x=np.asarray(d['points'],float)
    x/=np.linalg.norm(x,axis=1)[:,None]
    if x.shape!=(960,3): raise ValueError(x.shape)
    q=sm.xyz_to_vars(x); E,gq=sm.fg(q); scale=sm.physical_scale(q); gy=gq/scale
    H,raw,Qrot,calls=sm.build_hessian(q,args.fd_step,1e6)
    vals,V=eigsh(H,k=args.k,which='SA',tol=2e-5,maxiter=650,ncv=max(48,3*args.k))
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]; rows=[]
    for j,lam in enumerate(vals):
        y=V[:,j]; Hy=raw(y)+1e6*(Qrot@(Qrot.T@y))
        rows.append({'index':j,'eigenvalue':float(lam),'rotation_overlap':float(np.sum((Qrot.T@y)**2)),
                     'residual':float(np.linalg.norm(Hy-lam*y))})
    neg=int(np.sum(vals<-1e-3))
    out={'input_json':str(args.input_json),'energy':float(E),
         'physical_gradient_rms':float(np.linalg.norm(gy)/math.sqrt(2*960)),
         'physical_gradient_max':float(np.max(np.abs(gy))),
         'negative_internal_modes_below_-1e-3':neg,'modes':rows,'points':x.tolist()}
    print('CLASS',E,out['physical_gradient_rms'],neg,[float(v) for v in vals[:8]],flush=True)
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
