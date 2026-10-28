#!/usr/bin/env python3
"""Truncated-Newton refinement of a Thomson first-order saddle.

Starting from an approximate saddle JSON containing `saddle_points`, repeatedly
compute the lowest internal physical-tangent Hessian modes.  Solve Newton's
stationarity equation H delta = -g in that low-mode subspace (including the
single negative reaction mode) and use a small steepest-descent correction for
the unresolved orthogonal gradient.  The full tangent step is capped by RMS
angular displacement and applied with the sphere exponential map.

This is complementary to minimum-mode following: once the correct saddle basin
and one-negative-mode signature are known, Newton steps should remove the
remaining reaction-coordinate gradient much faster.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp

N=960


def load_points(path):
    d=json.loads(pathlib.Path(path).read_text())
    x=np.asarray(d['saddle_points'],float)
    x/=np.linalg.norm(x,axis=1)[:,None]
    return d,x


def physical_grad(q):
    E,gq=sm.fg(q); s=sm.physical_scale(q)
    return E,gq/s


def modes(q,k,fd_step,rot_penalty,seed):
    H,raw,Qrot,calls=sm.build_hessian(q,fd_step,rot_penalty)
    rng=np.random.default_rng(seed)
    v0=rng.normal(size=len(q)); v0-=Qrot@(Qrot.T@v0)
    vals,vecs=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=800,
                    ncv=min(len(q)-1,max(48,4*k)),v0=v0)
    o=np.argsort(vals); vals=vals[o]; vecs=vecs[:,o]
    rows=[]
    for j,lam in enumerate(vals):
        y=vecs[:,j]
        Hy=raw(y)+rot_penalty*(Qrot@(Qrot.T@y))
        rows.append({'index':j,'eigenvalue':float(lam),
                     'rotation_overlap':float(np.sum((Qrot.T@y)**2)),
                     'residual':float(np.linalg.norm(Hy-lam*y))})
    return vals,vecs,Qrot,rows,calls['n']


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('seed_json')
    ap.add_argument('--cycles',type=int,default=8)
    ap.add_argument('--k',type=int,default=10)
    ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--rot-penalty',type=float,default=1e6)
    ap.add_argument('--high-eta',type=float,default=1.2e-4)
    ap.add_argument('--max-rms-step',type=float,default=4e-4)
    ap.add_argument('--newton-damping',type=float,default=0.8)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    meta,x=load_points(args.seed_json); q=sm.xyz_to_vars(x)
    hist=[]; hcalls=0
    E,g=physical_grad(q)
    print(f'start E={E:.12f} grad_rms={np.linalg.norm(g)/math.sqrt(2*N):.7g}',flush=True)
    for cyc in range(args.cycles):
        vals,V,Qrot,rows,c=modes(q,args.k,args.fd_step,args.rot_penalty,20261028+cyc)
        hcalls+=c
        E,g=physical_grad(q); g-=Qrot@(Qrot.T@g)
        coeff=V.T@g
        # Newton correction in the resolved low-mode subspace. Avoid any mode
        # accidentally too close to zero (rigid rotations are already lifted).
        invlam=np.array([1.0/v if abs(v)>0.15 else 0.0 for v in vals])
        delta_low=-args.newton_damping*(V@(coeff*invlam))
        gres=g-V@coeff
        delta=delta_low-args.high_eta*gres
        delta-=Qrot@(Qrot.T@delta)
        rms=float(np.linalg.norm(delta)/math.sqrt(N))
        if rms>args.max_rms_step:
            delta*=args.max_rms_step/rms; rms=args.max_rms_step
        q=sp.exp_perturb(q,delta,rms)
        En,gn=physical_grad(q); grms=float(np.linalg.norm(gn)/math.sqrt(2*N))
        neg=int(np.sum(vals < -1e-3))
        print(f'cycle={cyc} E={E:.12f}->{En:.12f} grad={np.linalg.norm(g)/math.sqrt(2*N):.6g}->{grms:.6g} '
              f'lambda0={vals[0]:.9g} neg={neg} step={rms:.3e} g0={coeff[0]:+.5g}',flush=True)
        hist.append({'cycle':cyc,'energy_before':E,'energy_after':En,
                     'gradient_rms_before':float(np.linalg.norm(g)/math.sqrt(2*N)),
                     'gradient_rms_after':grms,'step_rms':rms,
                     'eigenvalues':[float(v) for v in vals],
                     'gradient_mode_coefficients':[float(v) for v in coeff],
                     'modes':rows})

    E,g=physical_grad(q); grms=float(np.linalg.norm(g)/math.sqrt(2*N))
    vals,V,Qrot,rows,c=modes(q,max(args.k,10),args.fd_step,args.rot_penalty,424242)
    hcalls+=c; neg=int(np.sum(vals < -1e-3))
    print(f'FINAL E={E:.12f} grad_rms={grms:.7g} neg={neg}',flush=True)
    for r in rows:
        print(f"mode={r['index']} lambda={r['eigenvalue']:.12g} rot={r['rotation_overlap']:.2e} resid={r['residual']:.2e}",flush=True)
    out={'seed_json':str(args.seed_json),'seed_energy':meta.get('final_energy',meta.get('climbing_energy')),
         'final_energy':E,'final_gradient_rms':grms,
         'negative_internal_modes_below_-1e-3':neg,'cycles':args.cycles,'k':args.k,
         'newton_damping':args.newton_damping,'high_eta':args.high_eta,
         'max_rms_step':args.max_rms_step,'hessian_gradient_calls':hcalls,
         'history':hist,'final_modes':rows,'saddle_points':sm.vars_to_xyz(q)[0].tolist(),
         'eigenvectors_physical':[V[:,j].tolist() for j in range(V.shape[1])]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
