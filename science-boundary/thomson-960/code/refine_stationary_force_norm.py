#!/usr/bin/env python3
"""Refine an approximate Thomson stationary state by minimizing tangent-force norm.

Amore et al. (J. Stat. Phys. 192, 132, 2025) reformulate the stationary-point
problem as minimization of the squared tangent force.  In our notation the
physical tangent energy gradient is g; stationary configurations are exactly the
zero-valued global minima of

    V = 1/2 ||g||^2.

The physical-coordinate gradient of V is H g, where H is the tangent Hessian of
the Coulomb energy.  We obtain H g matrix-free with the same centered finite-
difference HVP used by diagnose_soft_modes.py.  This avoids reaction Newton
steps -g/lambda and is therefore useful for shallow-curvature separatrix seeds.

A nonzero local minimum of V is possible in principle, so convergence is never
accepted merely from the optimizer flag: final tangent-force norm, Hessian
index, and H*g residual are all reported for independent certification.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh
import diagnose_soft_modes as sm

N=960
PI=math.pi

def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('saddle_points') or d.get('points')
    if p is None: raise ValueError('need saddle_points or points')
    x=np.asarray(p,float); x/=np.linalg.norm(x,axis=1)[:,None]
    if x.shape!=(N,3): raise ValueError(x.shape)
    return d,sm.xyz_to_vars(x)

def force_norm_fg(q,fd_step):
    E,gq=sm.fg(q); scale=sm.physical_scale(q); gy=gq/scale; Q=sm.rotation_basis(q)
    # Remove tiny numerical leakage into exact rigid rotations.
    gy=gy-Q@(Q.T@gy)
    V=0.5*float(gy@gy)
    # raw_hy is the physical tangent Hessian action.  Its centered difference
    # normalizes the supplied vector internally, so H*g remains stable even
    # when ||g|| is already small.
    H,raw,Q2,calls=sm.build_hessian(q,fd_step,0.0)
    hgy=raw(gy); hgy-=Q@(Q.T@hgy)
    # y=(dtheta,sin(theta)dphi), hence dV/dq = scale * dV/dy.
    gV=scale*hgy
    return V,gV,E,gy,hgy,calls['n']

def classify(q,k,fd_step):
    E,gq=sm.fg(q);scale=sm.physical_scale(q);gy=gq/scale;Q=sm.rotation_basis(q);gy-=Q@(Q.T@gy)
    H,raw,Q,calls=sm.build_hessian(q,fd_step,1e6)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=850,ncv=max(48,4*k));o=np.argsort(vals);vals=vals[o];V=V[:,o]
    rows=[]
    for j,lam in enumerate(vals):
        y=V[:,j];Hy=raw(y)+1e6*(Q@(Q.T@y));rows.append({'index':j,'eigenvalue':float(lam),'rotation_overlap':float(np.sum((Q.T@y)**2)),'residual':float(np.linalg.norm(Hy-lam*y))})
    # H*g without rotation penalty is a direct first-order stationarity check for V.
    hgy=raw(gy);hgy-=Q@(Q.T@hgy)
    return E,gy,hgy,vals,V,rows,calls['n']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('seed_json');ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--maxiter',type=int,default=450);ap.add_argument('--gtol',type=float,default=1e-10);ap.add_argument('--k',type=int,default=10)
    ap.add_argument('--out',required=True);args=ap.parse_args();meta,q0=load_seed(args.seed_json)
    evals={'n':0,'hvp_grad_calls':0};best={'V':float('inf')}
    def fg(q):
        V,gV,E,gy,hgy,c=force_norm_fg(q,args.fd_step);evals['n']+=1;evals['hvp_grad_calls']+=c
        grms=float(np.linalg.norm(gy)/math.sqrt(2*N));hg=float(np.linalg.norm(hgy)/math.sqrt(2*N))
        if V<best['V']:
            best.update(V=V,E=E,force_rms=grms,hg_rms=hg)
        if evals['n']==1 or evals['n']%10==0:
            print(f'eval={evals["n"]} E={E:.12f} V={V:.6e} force_rms={grms:.6g} Hg_rms={hg:.6g}',flush=True)
        return V,gV
    bounds=[(1e-8,PI-1e-8),(None,None)]*N
    r=minimize(fg,q0,jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':args.maxiter,'gtol':args.gtol,'ftol':1e-15,'maxls':60,'maxcor':32})
    E,gy,hgy,vals,vecs,rows,calls=classify(r.x,args.k,args.fd_step);evals['hvp_grad_calls']+=calls
    force_rms=float(np.linalg.norm(gy)/math.sqrt(2*N));force_max=float(np.max(np.abs(gy)));hg_rms=float(np.linalg.norm(hgy)/math.sqrt(2*N));neg=int(np.sum(vals<-1e-3))
    print(f'FINAL E={E:.12f} V={0.5*float(gy@gy):.6e} force_rms={force_rms:.7g} force_max={force_max:.7g} Hg_rms={hg_rms:.7g} neg={neg} lambdas={[float(v) for v in vals[:5]]}',flush=True)
    out={'seed_json':str(args.seed_json),'source_metadata':{k:meta.get(k) for k in ('final_energy','energy','phase_deg','negative_modes') if k in meta},
         'optimizer_success':bool(r.success),'optimizer_message':str(r.message),'nit':int(r.nit),'nfev':int(r.nfev),'evaluations':evals,
         'final_energy':float(E),'force_norm_objective':0.5*float(gy@gy),'physical_gradient_rms':force_rms,'physical_gradient_max':force_max,
         'Hg_rms':hg_rms,'negative_internal_modes_below_-1e-3':neg,'modes':rows,
         'stationary_points':sm.vars_to_xyz(r.x)[0].tolist(),'eigenvectors_physical':[vecs[:,j].tolist() for j in range(vecs.shape[1])]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__':main()
