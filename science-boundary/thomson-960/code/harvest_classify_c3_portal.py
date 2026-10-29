#!/usr/bin/env python3
"""Replay one deterministic C3 smooth-search trial and classify its full-space Morse spectrum."""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import search_c3_smooth as c3
import diagnose_soft_modes as sm
from harvest_saddle_branch import coord_counts, c3_z_rms


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots')
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--trial',type=int,required=True)
    ap.add_argument('--k',type=int,default=24); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    root=pathlib.Path(args.few_shots); live_score,shot=c3.find_live(root)
    pts=c3.load_cert(shot/'certificate.json'); reps=c3.c3_representatives(pts); v0=c3.xyz_to_vars(reps)
    base=c3.polish(v0,1200); rng=np.random.default_rng(args.seed)
    scales=np.geomspace(0.008,0.20,9); selected=None
    for t in range(args.trial+1):
        scale=float(scales[t%len(scales)]*math.exp(rng.normal(0.0,0.18)))
        start=c3.perturb(base.x,rng,scale); start_e,_=c3.fg(start); res=c3.polish(start)
        print(f'trial={t} scale={scale:.8g} start={start_e:.9f} min={float(res.fun):.12f} nit={res.nit} ok={res.success}',flush=True)
        if t==args.trial: selected=(scale,start_e,res)
    scale,start_e,res=selected; x,_,_=c3.vars_to_full(res.x); x/=np.linalg.norm(x,axis=1)[:,None]
    q=sm.xyz_to_vars(x); E,gq=sm.fg(q); gy=gq/sm.physical_scale(q); grms=float(np.linalg.norm(gy)/math.sqrt(len(gy)))
    H,raw,Q,calls=sm.build_hessian(q,args.fd_step,1e6)
    vals,V=eigsh(H,k=args.k,which='SA',tol=1e-5,maxiter=1000,ncv=max(60,4*args.k))
    vals=np.sort(vals); neg=int(np.sum(vals<-1e-3)); crms,cmax=c3_z_rms(x); cc=coord_counts(x)
    print(f'CLASS E={E:.12f} dLive={E-live_score:+.9g} grad={grms:.6g} neg<{args.k}={neg} lows={vals[:12].tolist()} coord={cc} c3={crms:.3e}',flush=True)
    out={'seed':args.seed,'trial':args.trial,'scale':scale,'start_energy':start_e,
         'c3_energy':float(res.fun),'c3_nit':int(res.nit),'c3_success':bool(res.success),
         'live_score':live_score,'live_shot':str(shot.relative_to(root)),'full_energy':float(E),
         'delta_vs_live':float(E-live_score),'full_gradient_rms':grms,'hessian_k':args.k,
         'negative_modes_among_k':neg,'lowest_eigenvalues':[float(v) for v in vals],
         'hessian_gradient_calls':calls['n'],'coord_counts':cc,'c3_z_rms':crms,'c3_z_max':cmax,
         'points':x.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
