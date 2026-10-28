#!/usr/bin/env python3
"""Hybrid eigenvector-following refinement for a Thomson first-order saddle.

Each outer cycle:
  1. compute the lowest internal Hessian eigenvector (reaction mode),
  2. minimize energy in the local hyperplane perpendicular to that mode using
     stable-difference L-BFGS plus a stiff quadratic reaction-coordinate restraint,
  3. recompute the mode and apply a damped Newton correction along it.

This directly targets the failure mode of low-mode-only refinement: the reaction
coordinate can already be nearly stationary while thousands of positive modes
still carry residual gradient.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp

N=960
PI=math.pi


def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    x=np.asarray(d['saddle_points'],float); x/=np.linalg.norm(x,axis=1)[:,None]
    return d,sm.xyz_to_vars(x)


def geom_grad(q):
    x,dth,dph=sm.vars_to_xyz(q)
    dots=np.clip(x@x.T,-1.0,1.0)
    r2=np.maximum(2.0-2.0*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1.0/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0.0)
    gc=w@x-np.sum(w,axis=1)[:,None]*x
    gq=np.column_stack([np.sum(gc*dth,axis=1),np.sum(gc*dph,axis=1)]).ravel()
    return x,inv,gq


def physical_grad(q):
    _,_,gq=geom_grad(q); return gq/sm.physical_scale(q)


def lowest(q,k=6,fd=3e-6):
    H,raw,Qrot,calls=sm.build_hessian(q,fd,1e6)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=800,ncv=max(40,4*k))
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    return vals,V,Qrot,calls['n']


def wrap_phi(d):
    return (d+math.pi)%(2*math.pi)-math.pi


def constrained_relax(qref,mode,penalty,maxiter):
    n=len(qref)//2; tri=np.triu_indices(n,1)
    _,inv0,_=geom_grad(qref)
    ref=np.asarray(inv0[tri],dtype=np.longdouble)
    ref_abs=float(np.sum(inv0[tri],dtype=np.float64))
    a0=qref.reshape(-1,2); sin0=np.maximum(np.sin(a0[:,0]),1e-6)
    m=mode.reshape(-1,2)

    def disp_and_c(q):
        a=q.reshape(-1,2)
        dth=a[:,0]-a0[:,0]
        dph=wrap_phi(a[:,1]-a0[:,1])
        y=np.column_stack([dth,sin0*dph])
        c=float(np.sum(y*m))
        return c

    def obj(q):
        _,inv,gq=geom_grad(q)
        delta=float(np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref,dtype=np.longdouble))
        c=disp_and_c(q)
        gp=np.empty_like(gq).reshape(-1,2)
        gp[:,0]=penalty*c*m[:,0]
        gp[:,1]=penalty*c*m[:,1]*sin0
        return delta+0.5*penalty*c*c, gq+gp.ravel()

    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    res=minimize(obj,qref,jac=True,method='L-BFGS-B',bounds=bounds,
                 options={'maxiter':maxiter,'gtol':5e-10,'ftol':1e-15,
                          'maxls':60,'maxcor':40})
    _,inv,_=geom_grad(res.x)
    E=ref_abs+float(np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref,dtype=np.longdouble))
    return res.x,E,disp_and_c(res.x),int(res.nit),bool(res.success),str(res.message)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('seed_json')
    ap.add_argument('--outer',type=int,default=5)
    ap.add_argument('--penalty',type=float,default=2e5)
    ap.add_argument('--perp-maxiter',type=int,default=500)
    ap.add_argument('--newton-damping',type=float,default=0.8)
    ap.add_argument('--max-reaction-rms',type=float,default=5e-4)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    meta,q=load_seed(args.seed_json); hist=[]; hcalls=0
    for outer in range(args.outer):
        vals,V,Qrot,c=lowest(q); hcalls+=c
        mode=V[:,0].copy(); mode-=Qrot@(Qrot.T@mode); mode/=np.linalg.norm(mode)
        gp=physical_grad(q); gp-=Qrot@(Qrot.T@gp)
        before_rms=float(np.linalg.norm(gp)/math.sqrt(2*N)); before_g0=float(gp@mode)
        q,Erest,cval,nit,ok,msg=constrained_relax(q,mode,args.penalty,args.perp_maxiter)

        vals2,V2,Qrot2,c2=lowest(q); hcalls+=c2
        mode2=V2[:,0].copy(); mode2-=Qrot2@(Qrot2.T@mode2); mode2/=np.linalg.norm(mode2)
        if float(mode2@mode)<0: mode2=-mode2
        g2=physical_grad(q); g2-=Qrot2@(Qrot2.T@g2)
        g0=float(g2@mode2); lam=float(vals2[0])
        coeff=-args.newton_damping*g0/lam if abs(lam)>0.1 else 0.0
        maxcoeff=args.max_reaction_rms*math.sqrt(N)
        coeff=float(np.clip(coeff,-maxcoeff,maxcoeff))
        delta=coeff*mode2
        rms=abs(coeff)/math.sqrt(N)
        if rms>0:
            q=sp.exp_perturb(q,delta,rms)
        Eafter,_=sm.fg(q); gafter=physical_grad(q)
        grms=float(np.linalg.norm(gafter)/math.sqrt(2*N))
        print(f'outer={outer} lambda={lam:.9g} before_grad={before_rms:.6g} before_g0={before_g0:+.4g} '
              f'perp_E={Erest:.12f} c={cval:.3e} nit={nit} ok={ok} g0={g0:+.4g} '
              f'newton_rms={rms:.3e} -> E={Eafter:.12f} grad={grms:.6g}',flush=True)
        hist.append({'outer':outer,'lambda':lam,'before_gradient_rms':before_rms,
                     'before_reaction_gradient':before_g0,'perp_energy':Erest,
                     'constraint_displacement':cval,'perp_nit':nit,'perp_success':ok,
                     'perp_message':msg,'post_perp_reaction_gradient':g0,
                     'reaction_newton_rms':rms,'energy_after':Eafter,
                     'gradient_rms_after':grms})

    E,gq=sm.fg(q); gp=gq/sm.physical_scale(q); grms=float(np.linalg.norm(gp)/math.sqrt(2*N))
    vals,V,Qrot,c=lowest(q,k=10); hcalls+=c; neg=int(np.sum(vals<-1e-3))
    rows=[]
    H,raw,Qr,calls=sm.build_hessian(q,3e-6,1e6)
    for j,lam in enumerate(vals):
        y=V[:,j]; Hy=raw(y)+1e6*(Qr@(Qr.T@y))
        rows.append({'index':j,'eigenvalue':float(lam),
                     'rotation_overlap':float(np.sum((Qr.T@y)**2)),
                     'residual':float(np.linalg.norm(Hy-lam*y))})
    print(f'FINAL E={E:.12f} grad_rms={grms:.7g} neg={neg} lambdas={[float(v) for v in vals[:5]]}',flush=True)
    out={'seed_json':str(args.seed_json),'final_energy':float(E),'final_gradient_rms':grms,
         'negative_internal_modes_below_-1e-3':neg,'outer':args.outer,
         'penalty':args.penalty,'newton_damping':args.newton_damping,
         'hessian_gradient_calls':hcalls,'history':hist,'final_modes':rows,
         'saddle_points':sm.vars_to_xyz(q)[0].tolist(),
         'eigenvectors_physical':[V[:,j].tolist() for j in range(V.shape[1])]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
