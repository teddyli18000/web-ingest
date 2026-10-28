#!/usr/bin/env python3
"""Escape the live Thomson N=960 minimum along a low Hessian doublet.

Recomputes the lowest full-space physical tangent modes, selects an indicated
near-degenerate pair, forms a phase direction in that 2-D subspace, applies
geodesic perturbations with increasing RMS angular amplitude, and fully relaxes
without any symmetry constraint.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib

import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh
from scipy.spatial import cKDTree

import diagnose_soft_modes as sm

PI=math.pi


def relax_q(q0,maxiter=1200):
    n=len(q0)//2
    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    res=minimize(sm.fg,q0,jac=True,method="L-BFGS-B",bounds=bounds,
                 options={"maxiter":maxiter,"gtol":2e-9,"ftol":1e-15,
                          "maxls":50,"maxcor":30})
    x,_,_=sm.vars_to_xyz(res.x)
    return float(res.fun),x,int(res.nit),bool(res.success)


def rz(a,ang):
    c,s=math.cos(ang),math.sin(ang)
    R=np.array([[c,-s,0.0],[s,c,0.0],[0.0,0.0,1.0]])
    return a@R.T,R


def tangent_bases(q):
    x,dth,dph=sm.vars_to_xyz(q)
    st=np.maximum(np.linalg.norm(dph,axis=1),1e-10)
    eph=dph/st[:,None]
    return x,dth,eph


def transform_c3(y,q):
    """Apply +120 degree z rotation to a physical tangent vector field."""
    x,eth,eph=tangent_bases(q)
    xr,R=rz(x,2*PI/3)
    tree=cKDTree(x)
    dist,dest=tree.query(xr,k=1)
    if float(np.max(dist))>2e-7 or len(np.unique(dest))!=len(x):
        raise RuntimeError(f"C3 point mapping failed maxdist={np.max(dist)}")
    a=y.reshape(-1,2)
    dx=a[:,0,None]*eth + a[:,1,None]*eph
    dxr=dx@R.T
    out=np.zeros_like(a)
    out[dest,0]=np.sum(dxr*eth[dest],axis=1)
    out[dest,1]=np.sum(dxr*eph[dest],axis=1)
    return out.ravel()


def exp_perturb(q,y_dir,rms_amp):
    """Sphere exponential map for a physical tangent direction."""
    x,eth,eph=tangent_bases(q)
    n=len(x)
    u=y_dir.reshape(-1,2)
    u=u*(rms_amp*math.sqrt(n)/np.linalg.norm(y_dir))
    dx=u[:,0,None]*eth + u[:,1,None]*eph
    a=np.linalg.norm(dx,axis=1)
    y=np.empty_like(x)
    small=a<1e-14
    y[small]=x[small]
    ns=~small
    y[ns]=np.cos(a[ns,None])*x[ns] + np.sin(a[ns,None])*(dx[ns]/a[ns,None])
    y/=np.linalg.norm(y,axis=1)[:,None]
    return sm.xyz_to_vars(y)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots")
    ap.add_argument("--pair-start",type=int,choices=[0,3,7,10,12],default=0)
    ap.add_argument("--phase-deg",type=float,default=0.0)
    ap.add_argument("--fd-step",type=float,default=3e-6)
    ap.add_argument("--amps",default="0.004,0.008,0.016,0.032,0.064,0.10,0.15")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    root=pathlib.Path(args.few_shots)
    live_score,shot=sm.find_live(root)
    x0=sm.load_cert(shot/"certificate.json")
    q0=sm.xyz_to_vars(x0)
    e0,_=sm.fg(q0)
    H,raw_hy,Qrot,calls=sm.build_hessian(q0,args.fd_step,1e6)
    k=max(6,args.pair_start+2)
    vals,vecs=eigsh(H,k=k,which="SA",tol=2e-5,maxiter=500,ncv=max(40,3*k))
    order=np.argsort(vals); vals=vals[order]; vecs=vecs[:,order]
    i=args.pair_start
    V=vecs[:,i:i+2].copy()
    V-=Qrot@(Qrot.T@V)
    V,_=np.linalg.qr(V)

    TV=np.column_stack([transform_c3(V[:,j],q0) for j in range(2)])
    M=V.T@TV
    subspace_res=float(np.linalg.norm(TV-V@M))
    print(f"live={shot.relative_to(root)} score={live_score:.10f} E0={e0:.12f}",flush=True)
    print(f"pair={i}/{i+1} lambdas={vals[i]:.12g},{vals[i+1]:.12g}",flush=True)
    print("c3_pair_matrix="+np.array2string(M,precision=8)+f" subspace_res={subspace_res:.3e}",flush=True)

    phase=math.radians(args.phase_deg)
    direction=math.cos(phase)*V[:,0] + math.sin(phase)*V[:,1]
    direction/=np.linalg.norm(direction)
    amps=[float(z) for z in args.amps.split(',') if z]
    rows=[]
    best_e=e0; best_x=None
    for amp in amps:
        qs=exp_perturb(q0,direction,amp)
        es,_=sm.fg(qs)
        e,x,nit,ok=relax_q(qs)
        imp=e0-e
        rows.append({"amp":amp,"start_energy":es,"energy":e,"improvement":imp,
                     "nit":nit,"success":ok})
        print(f"phase={args.phase_deg:g} amp={amp:.5f} start={es:.9f} min={e:.12f} improvement={imp:.9g} nit={nit} ok={ok}",flush=True)
        if e<best_e:
            best_e=e; best_x=x.copy()

    data={
        "live_shot":str(shot.relative_to(root)),"live_score":live_score,
        "base_double_energy":e0,"pair_start":i,"eigenvalues":[float(vals[i]),float(vals[i+1])],
        "phase_deg":args.phase_deg,"c3_pair_matrix":M.tolist(),"c3_subspace_residual":subspace_res,
        "rows":rows,"best_float_energy":best_e,"best_improvement":e0-best_e,
        "gradient_calls_for_modes":calls["n"],
        "best_points":best_x.tolist() if best_x is not None and e0-best_e>2e-7 else None,
    }
    pathlib.Path(args.out).write_text(json.dumps(data,indent=2)+"\n")

if __name__=="__main__":
    main()
