#!/usr/bin/env python3
"""Upward index-1 eigenvector following from a Thomson local minimum.

This implements the core sign structure of 1-CHiSD / eigenvector following in
physical product-of-spheres tangent coordinates.  Starting from a minimum
perturbed along a selected soft Hessian mode, the tracked mode is followed by
maximum eigenvector overlap.  Its gradient component is stepped *uphill* while
its curvature is positive; after the curvature turns negative the same formula
becomes the Newton step toward an index-1 saddle.  All orthogonal low modes and
the unresolved gradient residual are stepped downhill.

Unlike ordinary minimization or ordinary Newton, this can leave the parent
minimum and converge to the transition state that bounds its basin.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed

N=960


def low_modes(q,k,fd,v0=None):
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    kwargs={'k':k,'which':'SA','tol':1e-5,'maxiter':900,'ncv':max(40,4*k)}
    if v0 is not None: kwargs['v0']=v0
    vals,V=eigsh(H,**kwargs); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    for j in range(V.shape[1]):
        V[:,j]-=Q@(Q.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    return vals,V,Q,calls['n']


def pgrad(q,Q=None):
    _,gq=sm.fg(q); g=gq/sm.physical_scale(q)
    if Q is not None: g-=Q@(Q.T@g)
    return g


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--mode',type=int,default=0); ap.add_argument('--sign',type=int,choices=[-1,1],default=1)
    ap.add_argument('--escape-amp',type=float,default=0.0015); ap.add_argument('--steps',type=int,default=100)
    ap.add_argument('--k',type=int,default=10); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--curv-floor',type=float,default=0.35); ap.add_argument('--residual-scale',type=float,default=0.01)
    ap.add_argument('--max-step-rms',type=float,default=0.00018); ap.add_argument('--grad-tol',type=float,default=3e-5)
    ap.add_argument('--max-energy-rise',type=float,default=0.08); ap.add_argument('--out',required=True); args=ap.parse_args()

    meta,x0=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x0); E0,_=sm.fg(q0)
    vals,V,Q,calls=low_modes(q0,max(args.k,args.mode+2),args.fd_step); hcalls=calls
    target=V[:,args.mode].copy(); q=sp.exp_perturb(q0,args.sign*target,args.escape_amp)
    hist=[]; status='max_steps'
    print(f'parentE={E0:.12f} mode={args.mode} lambda={vals[args.mode]:.9g} sign={args.sign} escape={args.escape_amp}',flush=True)

    for it in range(args.steps):
        vals,V,Q,c=low_modes(q,args.k,args.fd_step,v0=target); hcalls+=c
        overlaps=np.abs(V.T@target); jt=int(np.argmax(overlaps)); vt=V[:,jt].copy()
        if float(vt@target)<0: vt=-vt
        ov=float(abs(vt@target)); target=vt
        g=pgrad(q,Q); grms=float(np.linalg.norm(g)/math.sqrt(2*N)); comps=V.T@g
        # Low-subspace eigenvector-following step.
        delta=np.zeros_like(g)
        for j,lam in enumerate(vals):
            den=max(abs(float(lam)),args.curv_floor)
            if j==jt:
                delta += (float(comps[j])/den)*V[:,j]  # uphill / saddle-Newton
            else:
                delta += (-float(comps[j])/den)*V[:,j] # downhill
        gres=g-V@comps
        delta += -args.residual_scale*gres
        drms=float(np.linalg.norm(delta)/math.sqrt(N))
        if drms>args.max_step_rms: delta*=args.max_step_rms/drms; drms=args.max_step_rms
        q=sp.exp_perturb(q,delta,drms) if drms>0 else q
        E,_=sm.fg(q); neg=int(np.sum(vals<-1e-3))
        if it%2==0 or grms<args.grad_tol:
            print(f'it={it:03d} E={E:.12f} dE={E-E0:+.7g} grad={grms:.4g} target={jt} '
                  f'lam={vals[jt]:+.6g} ov={ov:.4f} neg={neg} step={drms:.2e}',flush=True)
        hist.append({'iteration':it,'energy':E,'delta_from_parent':E-E0,'gradient_rms_before':grms,
                     'target_index':jt,'target_eigenvalue':float(vals[jt]),'target_overlap':ov,
                     'negative_low_modes':neg,'step_rms':drms})
        if E-E0>args.max_energy_rise:
            status='energy_guard'; break
        # Re-evaluate convergence on the next spectrum: current grms is pre-step,
        # so require a small pre-step gradient and index one before accepting.
        if grms<args.grad_tol and neg==1:
            status='converged'; break

    Ef,gq=sm.fg(q); gf=gq/sm.physical_scale(q); grmsf=float(np.linalg.norm(gf)/math.sqrt(2*N))
    valsf,Vf,Qf,c=low_modes(q,max(args.k,12),args.fd_step,v0=target); hcalls+=c; negf=int(np.sum(valsf<-1e-3))
    overlaps=np.abs(Vf.T@target); jt=int(np.argmax(overlaps)); ov=float(overlaps[jt])
    print(f'FINAL status={status} E={Ef:.12f} dE={Ef-E0:+.9g} grad={grmsf:.6g} neg={negf} '
          f'target={jt} lambda={valsf[jt]:+.8g} ov={ov:.5f} lows={valsf[:6].tolist()}',flush=True)
    out={'seed_json':str(args.seed_json),'parent_energy':E0,'mode':args.mode,'sign':args.sign,'escape_amp':args.escape_amp,
         'status':status,'final_energy':float(Ef),'delta_from_parent':float(Ef-E0),'final_gradient_rms':grmsf,
         'negative_internal_modes_below_-1e-3':negf,'final_eigenvalues':[float(v) for v in valsf],
         'final_target_index':jt,'final_target_overlap':ov,'history':hist,'hessian_gradient_calls':hcalls,
         'saddle_points':sm.vars_to_xyz(q)[0].tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
