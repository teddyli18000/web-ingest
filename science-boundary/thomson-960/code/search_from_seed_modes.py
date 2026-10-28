#!/usr/bin/env python3
"""Second-hop basin search from an arbitrary saved N=960 Thomson minimum.

The seed JSON must contain a 960x3 floating `points` array. We compute the
lowest full-space physical tangent Hessian modes after lifting rigid rotations,
push along one selected eigenvector in either sign over increasing RMS angular
amplitudes, and fully relax. Results are compared both to the seed and to the
live Few Shots p007 record discovered at runtime.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    pts=d.get("points") if isinstance(d,dict) else d
    if pts is None or len(pts)!=960:
        raise ValueError("seed must contain 960 points")
    x=np.asarray(pts,dtype=float)
    x/=np.linalg.norm(x,axis=1)[:,None]
    return d,x


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots")
    ap.add_argument("seed_json")
    ap.add_argument("--mode",type=int,required=True)
    ap.add_argument("--sign",type=int,choices=[-1,1],required=True)
    ap.add_argument("--k",type=int,default=12)
    ap.add_argument("--fd-step",type=float,default=3e-6)
    ap.add_argument("--amps",default="0.003,0.006,0.010,0.016,0.024,0.036,0.052,0.075")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    live_score,live_shot=sm.find_live(root)
    seed_meta,x0=load_seed(args.seed_json)
    q0=sm.xyz_to_vars(x0)
    e0,g0=sm.fg(q0)
    H,raw,Qrot,calls=sm.build_hessian(q0,args.fd_step,1e6)
    k=max(args.k,args.mode+1)
    rng=np.random.default_rng(960000+args.mode)
    v0=rng.normal(size=len(q0)); v0-=Qrot@(Qrot.T@v0)
    vals,vecs=eigsh(H,k=k,which="SA",tol=2e-5,maxiter=600,ncv=max(40,3*k),v0=v0)
    order=np.argsort(vals); vals=vals[order]; vecs=vecs[:,order]
    direction=vecs[:,args.mode].copy()
    direction-=Qrot@(Qrot.T@direction)
    direction*=args.sign/np.linalg.norm(direction)
    rot_overlap=float(np.sum((Qrot.T@direction)**2))

    print(f"seed_energy={e0:.12f} live_score={live_score:.10f} mode={args.mode} sign={args.sign} lambda={vals[args.mode]:.12g}",flush=True)
    print(f"rotation_overlap={rot_overlap:.3e} seed_grad_rms={np.sqrt(np.mean((g0/sm.physical_scale(q0))**2)):.3e}",flush=True)

    amps=[float(s) for s in args.amps.split(',') if s]
    rows=[]; best_e=e0; best_x=None
    for amp in amps:
        qs=sp.exp_perturb(q0,direction,amp)
        es,_=sm.fg(qs)
        e,x,nit,ok=sp.relax_q(qs,1600)
        row={"amp":amp,"start_energy":es,"energy":e,"delta_vs_seed":e-e0,
             "delta_vs_live_score":e-live_score,"nit":nit,"success":ok}
        rows.append(row)
        print(f"amp={amp:.5f} start={es:.9f} min={e:.12f} dseed={e-e0:+.9g} dlive={e-live_score:+.9g} nit={nit} ok={ok}",flush=True)
        if e<best_e:
            best_e=e; best_x=x.copy()

    out={
      "seed_json":str(args.seed_json),"seed_energy":e0,
      "live_shot":str(live_shot.relative_to(root)),"live_score":live_score,
      "mode":args.mode,"sign":args.sign,"eigenvalue":float(vals[args.mode]),
      "rotation_overlap":rot_overlap,"rows":rows,
      "best_float_energy":best_e,"best_delta_vs_seed":best_e-e0,
      "best_delta_vs_live_score":best_e-live_score,
      "gradient_calls_for_modes":calls["n"],
      "best_points":best_x.tolist() if best_x is not None and best_e < live_score-2e-7 else None,
    }
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+"\n")

if __name__=="__main__": main()
