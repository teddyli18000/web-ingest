#!/usr/bin/env python3
"""Refine a fixed-charge N=961 weighted transition-state seed to index one.

The objective uses q886=q960=q380=2/3 and q=1 elsewhere.  Each outer cycle
computes the lowest physical-tangent Hessian mode with the validated complex-
step HVP, minimizes the weighted energy in the hyperplane perpendicular to that
mode, then applies a damped Newton correction along the reaction coordinate.
The target is a stationary point with exactly one non-rigid negative mode.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
from search_n972_mobile_fractional_homotopy import weighted_terms_grad
from search_n961_three_occupancy_simplex import LABELS
import validate_n961_weighted_edge as vw

PI=math.pi


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    x=np.asarray(d['saddle_points'],float); x/=np.linalg.norm(x,axis=1)[:,None]
    return d,sm.xyz_to_vars(x)


def charges():
    q=np.ones(961,float); q[list(LABELS)]=2/3
    return q


def energy_grad(q,c):
    terms,g,_=weighted_terms_grad(q,c)
    e=float(np.sum(np.asarray(terms,np.longdouble),dtype=np.longdouble))
    return e,g


def physical_grad(q,c,Q=None):
    _,g=energy_grad(q,c); y=g/sm.physical_scale(q)
    if Q is not None: y-=Q@(Q.T@y)
    return y


def lowest(q,c,k,tol=2e-5):
    H,Hc,project,nuisance,Q,calls=vw.build_rot_projected_hessian(q,c,1e-20,1e6)
    rng=np.random.default_rng(961380); v0=project(rng.normal(size=len(q))); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=k,which='SA',tol=tol,maxiter=1600,ncv=max(60,5*k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    rows=[]
    for j,lam in enumerate(vals):
        y=V[:,j]; r=float(np.linalg.norm(H.matvec(y)-lam*y))
        rows.append({'index':j,'eigenvalue':float(lam),'ritz_residual':r,
                     'rotation_nuisance_norm':float(np.linalg.norm(nuisance(y)))})
    return vals,V,Q,rows,calls['n']


def wrap_phi(x): return (x+math.pi)%(2*math.pi)-math.pi


def constrained_relax(qref,mode,c,penalty,maxiter):
    n=len(qref)//2; a0=qref.reshape(-1,2); sin0=np.maximum(np.sin(a0[:,0]),1e-6)
    m=mode.reshape(-1,2)
    t0,_,_=weighted_terms_grad(qref,c); ref=np.asarray(t0,np.longdouble)
    e0=float(np.sum(ref,dtype=np.longdouble))
    def coord(q):
        a=q.reshape(-1,2); dth=a[:,0]-a0[:,0]; dph=wrap_phi(a[:,1]-a0[:,1])
        return float(np.sum(np.column_stack([dth,sin0*dph])*m))
    def fg(q):
        t,g,_=weighted_terms_grad(q,c)
        de=float(np.sum(np.asarray(t,np.longdouble)-ref,dtype=np.longdouble))
        z=coord(q); pg=np.empty_like(g).reshape(-1,2)
        pg[:,0]=penalty*z*m[:,0]; pg[:,1]=penalty*z*m[:,1]*sin0
        return de+0.5*penalty*z*z,g+pg.ravel()
    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    r=minimize(fg,qref,jac=True,method='L-BFGS-B',bounds=bounds,
               options={'maxiter':maxiter,'gtol':5e-10,'ftol':1e-15,'maxls':70,'maxcor':40})
    t,_,_=weighted_terms_grad(r.x,c)
    e=e0+float(np.sum(np.asarray(t,np.longdouble)-ref,dtype=np.longdouble))
    return r.x,e,coord(r.x),int(r.nit),bool(r.success),str(r.message)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--outer',type=int,default=8); ap.add_argument('--k',type=int,default=6)
    ap.add_argument('--penalty',type=float,default=2e5); ap.add_argument('--perp-maxiter',type=int,default=650)
    ap.add_argument('--newton-damping',type=float,default=.65); ap.add_argument('--max-reaction-rms',type=float,default=1.5e-4)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,q=load_seed(args.seed_json); c=charges(); hist=[]; hcalls=0; prev=None
    for outer in range(args.outer):
        vals,V,Q,rows,nc=lowest(q,c,args.k); hcalls+=nc
        mode=V[:,0].copy(); mode-=Q@(Q.T@mode); mode/=np.linalg.norm(mode)
        if prev is not None and float(mode@prev)<0: mode=-mode
        prev=mode.copy(); g=physical_grad(q,c,Q); before=float(np.linalg.norm(g)/math.sqrt(len(q)))
        q,eperp,cval,nit,ok,msg=constrained_relax(q,mode,c,args.penalty,args.perp_maxiter)
        vals2,V2,Q2,rows2,nc2=lowest(q,c,args.k); hcalls+=nc2
        mode2=V2[:,0].copy(); mode2-=Q2@(Q2.T@mode2); mode2/=np.linalg.norm(mode2)
        if float(mode2@mode)<0: mode2=-mode2
        prev=mode2.copy(); g2=physical_grad(q,c,Q2); gpar=float(g2@mode2); lam=float(vals2[0])
        coeff=-args.newton_damping*gpar/lam if abs(lam)>.05 else 0.0
        lim=args.max_reaction_rms*math.sqrt(961); coeff=float(np.clip(coeff,-lim,lim))
        dy=coeff*mode2; scale=sm.physical_scale(q); q=q+dy/scale
        eafter,_=energy_grad(q,c); Q3=sm.rotation_basis(q); g3=physical_grad(q,c,Q3)
        gr=float(np.linalg.norm(g3)/math.sqrt(len(q)))
        neg=int(np.sum(vals2<-1e-3))
        print('REFINE',outer,'lam',f'{lam:+.8g}','before',f'{before:.5g}','perpE',f'{eperp:.12f}',
              'constraint',f'{cval:.2e}','gpar',f'{gpar:+.4g}','step',f'{abs(coeff)/math.sqrt(961):.2e}',
              'E',f'{eafter:.12f}','grad',f'{gr:.5g}','neg',neg,flush=True)
        hist.append({'outer':outer,'lambda':lam,'gradient_rms_before':before,'perp_energy':eperp,
                     'constraint_displacement':cval,'perp_nit':nit,'perp_success':ok,'perp_message':msg,
                     'reaction_gradient':gpar,'reaction_step_rms':abs(coeff)/math.sqrt(961),
                     'energy_after':eafter,'gradient_rms_after':gr,'negative_modes_before_step':neg})
    ef,_=energy_grad(q,c); vals,V,Q,rows,nc=lowest(q,c,max(args.k,12),tol=8e-6); hcalls+=nc
    gf=physical_grad(q,c,Q); grf=float(np.linalg.norm(gf)/math.sqrt(len(q))); neg=int(np.sum(vals<-1e-3))
    print('FINAL','E',f'{ef:.12f}','grad',f'{grf:.7g}','neg',neg,'lows',[float(x) for x in vals[:6]],flush=True)
    x=sm.vars_to_xyz(q)[0]
    out={'seed_json':str(args.seed_json),'final_energy':float(ef),'final_gradient_rms':grf,
         'negative_internal_modes_below_-1e-3':neg,'final_eigenvalues':[float(v) for v in vals],
         'final_modes':rows,'history':hist,'hessian_calls':hcalls,'saddle_points':x.tolist(),'edge_points':x.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
