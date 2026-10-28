#!/usr/bin/env python3
"""Second-hop basin search from an arbitrary saved N=960 Thomson minimum.

The seed JSON must contain a 960x3 floating `points` array. We compute the
lowest full-space physical tangent Hessian modes after lifting rigid rotations,
push along one selected eigenvector in either sign over increasing RMS angular
amplitudes, and fully relax. Results are compared both to the seed and to the
live Few Shots p007 record discovered at runtime.

For local relaxation we minimize a *termwise pair-energy difference* relative
to the perturbed start, accumulated in long double, while keeping the analytic
gradient unchanged. This avoids L-BFGS line-search/ftol loss of resolution from
optimizing an absolute Coulomb energy of order 4.4e5 when the scientifically
relevant local changes are 1e-8--1e-3.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp

PI=math.pi


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    pts=d.get("points") if isinstance(d,dict) else d
    if pts is None or len(pts)!=960:
        raise ValueError("seed must contain 960 points")
    x=np.asarray(pts,dtype=float)
    x/=np.linalg.norm(x,axis=1)[:,None]
    return d,x


def _geometry_and_gradient(v):
    """Return xyz and analytic angular gradient without trusting total-E sum."""
    x,dth,dph=sm.vars_to_xyz(v)
    dots=np.clip(x@x.T,-1.0,1.0)
    r2=np.maximum(2.0-2.0*dots,1e-300)
    np.fill_diagonal(r2,np.inf)
    inv=1.0/np.sqrt(r2)
    w=inv/r2
    np.fill_diagonal(w,0.0)
    gc=w@x-np.sum(w,axis=1)[:,None]*x
    gt=np.sum(gc*dth,axis=1)
    gp=np.sum(gc*dph,axis=1)
    return x,inv,np.column_stack([gt,gp]).ravel()


def stable_relax_q(qstart,maxiter=1800):
    """L-BFGS on a stable pairwise energy difference relative to qstart."""
    n=len(qstart)//2
    tri=np.triu_indices(n,1)
    _,inv0,_=_geometry_and_gradient(qstart)
    ref_terms=np.asarray(inv0[tri],dtype=np.longdouble)
    # Absolute reference is used only to report the final energy. Its ordinary
    # double summation uncertainty is ~1e-9 here, safely below the 1e-6 record
    # margin; any candidate is subsequently judged by the exact verifier.
    ref_abs=float(np.sum(inv0[tri],dtype=np.float64))

    def obj(v):
        _x,inv,g=_geometry_and_gradient(v)
        delta=np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref_terms,
                     dtype=np.longdouble)
        return float(delta),g

    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    res=minimize(obj,qstart,jac=True,method="L-BFGS-B",bounds=bounds,
                 options={"maxiter":maxiter,"gtol":1e-9,"ftol":1e-15,
                          "maxls":60,"maxcor":40})
    delta,_=obj(res.x)
    x,_,_=sm.vars_to_xyz(res.x)
    # Also expose an ordinary absolute-energy recomputation as a diagnostic.
    raw_abs,_=sm.fg(res.x)
    return ref_abs+delta,float(raw_abs),x,int(res.nit),bool(res.success),str(res.message)


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
        e,raw_e,x,nit,ok,msg=stable_relax_q(qs)
        row={"amp":amp,"start_energy":es,"energy":e,"raw_absolute_energy":raw_e,
             "delta_vs_seed":e-e0,"delta_vs_live_score":e-live_score,
             "nit":nit,"success":ok,"message":msg}
        rows.append(row)
        print(f"amp={amp:.5f} start={es:.9f} min={e:.12f} raw={raw_e:.12f} dseed={e-e0:+.9g} dlive={e-live_score:+.9g} nit={nit} ok={ok}",flush=True)
        if e<best_e:
            best_e=e; best_x=x.copy()

    out={
      "seed_json":str(args.seed_json),"seed_energy":e0,
      "live_shot":str(live_shot.relative_to(root)),"live_score":live_score,
      "mode":args.mode,"sign":args.sign,"eigenvalue":float(vals[args.mode]),
      "rotation_overlap":rot_overlap,"stable_difference_objective":True,"rows":rows,
      "best_float_energy":best_e,"best_delta_vs_seed":best_e-e0,
      "best_delta_vs_live_score":best_e-live_score,
      "gradient_calls_for_modes":calls["n"],
      "best_points":best_x.tolist() if best_x is not None and best_e < live_score-2e-7 else None,
    }
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+"\n")

if __name__=="__main__": main()
