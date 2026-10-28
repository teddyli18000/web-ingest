#!/usr/bin/env python3
"""Refine a shallow Thomson saddle while preserving the string reaction coordinate.

For shallow barriers, repeatedly selecting the lowest Hessian mode can switch to a
positive basin mode and collapse into an endpoint.  This refiner instead derives
the reaction direction from the optimized string's two neighboring images. Each
outer cycle minimizes all directions perpendicular to that path tangent, then
uses a damped Newton correction only along the tangent.  The final Hessian is
computed independently to classify the stationary point.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
import string_record_neighbor as sr
from refine_saddle_hybrid import constrained_relax

N=960


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    req=('saddle_points','left_neighbor_points','right_neighbor_points')
    if any(k not in d for k in req):
        raise ValueError('string JSON must retain saddle and both local neighbor images')
    x=np.asarray(d['saddle_points'],float); x/=np.linalg.norm(x,axis=1)[:,None]
    left=np.asarray(d['left_neighbor_points'],float); left/=np.linalg.norm(left,axis=1)[:,None]
    right=np.asarray(d['right_neighbor_points'],float); right/=np.linalg.norm(right,axis=1)[:,None]
    return d,sm.xyz_to_vars(x),left,right


def path_mode(q,left,right):
    x,eth,eph=sp.tangent_bases(q)
    tc=sr.logmap(x,right)-sr.logmap(x,left)
    n=float(np.linalg.norm(tc))
    if n<1e-14: raise RuntimeError('degenerate local string tangent')
    tc/=n
    y=np.column_stack([np.sum(tc*eth,axis=1),np.sum(tc*eph,axis=1)]).ravel()
    Q=sm.rotation_basis(q); y-=Q@(Q.T@y); y/=np.linalg.norm(y)
    return y,Q


def physical_grad(q,Q=None):
    _,gq=sm.fg(q); g=gq/sm.physical_scale(q)
    if Q is not None: g-=Q@(Q.T@g)
    return g


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('string_json')
    ap.add_argument('--outer',type=int,default=8); ap.add_argument('--penalty',type=float,default=3e5)
    ap.add_argument('--perp-maxiter',type=int,default=700); ap.add_argument('--newton-damping',type=float,default=0.35)
    ap.add_argument('--max-reaction-rms',type=float,default=5e-5); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,q,left,right=load_seed(args.string_json); hist=[]
    for outer in range(args.outer):
        mode,Q=path_mode(q,left,right); g=physical_grad(q,Q); before=float(np.linalg.norm(g)/math.sqrt(2*N))
        q,Eperp,cval,nit,ok,msg=constrained_relax(q,mode,args.penalty,args.perp_maxiter)
        mode,Q=path_mode(q,left,right); g=physical_grad(q,Q); g0=float(g@mode)
        H,raw,Qh,calls=sm.build_hessian(q,args.fd_step,1e6); lam=float(mode@raw(mode))
        coeff=-args.newton_damping*g0/lam if abs(lam)>0.05 else 0.0
        lim=args.max_reaction_rms*math.sqrt(N); coeff=float(np.clip(coeff,-lim,lim))
        if coeff!=0:
            q=sp.exp_perturb(q,mode*np.sign(coeff),abs(coeff)/math.sqrt(N))
        E,_=sm.fg(q); gnew=physical_grad(q); grms=float(np.linalg.norm(gnew)/math.sqrt(2*N))
        print(f'outer={outer} before={before:.6g} perpE={Eperp:.12f} c={cval:.2e} nit={nit} ok={ok} '
              f'g_t={g0:+.4g} k_t={lam:+.7g} newton_rms={abs(coeff)/math.sqrt(N):.3e} -> E={E:.12f} grad={grms:.6g}',flush=True)
        hist.append({'outer':outer,'before_gradient_rms':before,'perp_energy':Eperp,'constraint_displacement':cval,
                     'perp_nit':nit,'perp_success':ok,'perp_message':msg,'tangent_gradient':g0,
                     'tangent_curvature':lam,'reaction_newton_rms':abs(coeff)/math.sqrt(N),'energy_after':E,
                     'gradient_rms_after':grms})
    E,gq=sm.fg(q); gp=gq/sm.physical_scale(q); grms=float(np.linalg.norm(gp)/math.sqrt(2*N))
    H,raw,Qrot,calls=sm.build_hessian(q,args.fd_step,1e6)
    vals,V=eigsh(H,k=10,which='SA',tol=1e-5,maxiter=800,ncv=40); vals=np.sort(vals)
    neg=int(np.sum(vals<-1e-3)); mode,Q=path_mode(q,left,right); tangent_curv=float(mode@raw(mode))
    print(f'FINAL E={E:.12f} grad_rms={grms:.7g} neg={neg} tangent_curvature={tangent_curv:+.8g} lambdas={[float(v) for v in vals[:5]]}',flush=True)
    out={'seed_json':str(args.string_json),'final_energy':float(E),'final_gradient_rms':grms,
         'negative_internal_modes_below_-1e-3':neg,'path_tangent_curvature':tangent_curv,
         'final_eigenvalues':[float(v) for v in vals],'history':hist,
         'saddle_points':sm.vars_to_xyz(q)[0].tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
