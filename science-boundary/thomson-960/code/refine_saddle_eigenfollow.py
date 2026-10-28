#!/usr/bin/env python3
"""Refine the R<->A string climbing image toward a first-order saddle.

Input is the JSON artifact from string_record_neighbor.py.  The current climbing
image is already close to the low R/A barrier but is not stationary.  This code
periodically recomputes the lowest full-space physical-tangent Hessian mode and
uses hybrid eigenvector following: ascend along the lowest mode, descend in all
orthogonal directions, while lifting the three rigid sphere rotations.

The scientific acceptance criterion is not low energy.  A useful result should
have a small physical gradient and exactly one negative internal Hessian mode.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh


def load_saddle(path: pathlib.Path) -> np.ndarray:
    d=json.loads(path.read_text())
    x=np.asarray(d['saddle_points'],dtype=float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def xyz_to_vars(x):
    th=np.arccos(np.clip(x[:,2],-1.0,1.0))
    ph=np.arctan2(x[:,1],x[:,0])
    return np.column_stack([th,ph]).ravel()


def vars_to_xyz(v):
    a=v.reshape(-1,2); th,ph=a[:,0],a[:,1]
    st,ct=np.sin(th),np.cos(th); cp,sp=np.cos(ph),np.sin(ph)
    x=np.column_stack([st*cp,st*sp,ct])
    dth=np.column_stack([ct*cp,ct*sp,-st])
    dph=np.column_stack([-st*sp,st*cp,np.zeros_like(st)])
    return x,dth,dph


def fg(v):
    x,dth,dph=vars_to_xyz(v)
    dots=np.clip(x@x.T,-1.0,1.0)
    r2=np.maximum(2.0-2.0*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1.0/np.sqrt(r2)
    E=float(np.sum(np.triu(inv,1),dtype=np.longdouble))
    w=inv/r2; np.fill_diagonal(w,0.0)
    gc=w@x-np.sum(w,axis=1)[:,None]*x
    gt=np.sum(gc*dth,axis=1); gp=np.sum(gc*dph,axis=1)
    return E,np.column_stack([gt,gp]).ravel()


def physical_scale(q):
    a=q.reshape(-1,2); s=np.empty_like(a)
    s[:,0]=1.0; s[:,1]=np.maximum(np.sin(a[:,0]),1e-6)
    return s.ravel()


def rotation_basis(q):
    x,dth,dph=vars_to_xyz(q)
    st=np.maximum(np.linalg.norm(dph,axis=1),1e-8)
    eph=dph/st[:,None]
    cols=[]
    for axis in np.eye(3):
        dx=np.cross(np.broadcast_to(axis,x.shape),x)
        yth=np.sum(dx*dth,axis=1)
        yph=np.sum(dx*eph,axis=1)
        cols.append(np.column_stack([yth,yph]).ravel())
    Q,_=np.linalg.qr(np.column_stack(cols))
    return Q


def physical_gradient(q):
    E,gq=fg(q); scale=physical_scale(q)
    return E,gq/scale,scale


def build_hessian(q0,fd_step,rot_penalty):
    scale=physical_scale(q0); invs=1.0/scale; Qrot=rotation_basis(q0)
    calls={'n':0}
    def raw_hy(y):
        y=np.asarray(y,float); yn=float(np.linalg.norm(y))
        if yn==0.0: return np.zeros_like(y)
        u=y/yn; dq=invs*u
        _,gp=fg(q0+fd_step*dq); _,gm=fg(q0-fd_step*dq)
        calls['n']+=2
        hq=(gp-gm)*(yn/(2.0*fd_step))
        return invs*hq
    def mv(y):
        y=np.asarray(y,float)
        return raw_hy(y)+rot_penalty*(Qrot@(Qrot.T@y))
    return LinearOperator((len(q0),len(q0)),matvec=mv,dtype=float),raw_hy,Qrot,calls


def lowest_modes(q,k,fd_step,rot_penalty,tol):
    H,raw,Qrot,calls=build_hessian(q,fd_step,rot_penalty)
    vals,vecs=eigsh(H,k=k,which='SA',tol=tol,maxiter=700,ncv=min(len(q)-1,max(36,4*k)))
    order=np.argsort(vals); vals=vals[order]; vecs=vecs[:,order]
    rows=[]
    for j,lam in enumerate(vals):
        y=vecs[:,j]
        Hy=raw(y)+rot_penalty*(Qrot@(Qrot.T@y))
        rows.append({'index':j,'eigenvalue':float(lam),
                     'rotation_overlap':float(np.sum((Qrot.T@y)**2)),
                     'residual':float(np.linalg.norm(Hy-lam*y))})
    return vals,vecs,rows,calls['n']


def step_eigenfollow(q,mode,eta,max_rms):
    E,g,scale=physical_gradient(q)
    Qrot=rotation_basis(q); g=g-Qrot@(Qrot.T@g)
    mode=mode-Qrot@(Qrot.T@mode); mode/=max(np.linalg.norm(mode),1e-30)
    # Min-mode following: reverse the force component along the reaction mode.
    force=-g+2.0*float(g@mode)*mode
    dy=eta*force
    rms=float(np.linalg.norm(dy)/math.sqrt(len(q)//2))
    if rms>max_rms: dy*=max_rms/rms; rms=max_rms
    dq=dy/scale
    return q+dq,E,float(np.linalg.norm(g)/math.sqrt(len(q))),rms,float(g@mode)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('string_json')
    ap.add_argument('--cycles',type=int,default=8)
    ap.add_argument('--steps-per-cycle',type=int,default=70)
    ap.add_argument('--eta',type=float,default=2.5e-4)
    ap.add_argument('--max-rms-step',type=float,default=7e-6)
    ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--rot-penalty',type=float,default=1e6)
    ap.add_argument('--final-k',type=int,default=8)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    q=xyz_to_vars(load_saddle(pathlib.Path(args.string_json)))
    history=[]; prev_mode=None; total_hcalls=0
    E0,g0,_=physical_gradient(q)
    print(f'start E={E0:.12f} grad_rms={np.linalg.norm(g0)/math.sqrt(len(q)):.6g}',flush=True)

    for cyc in range(args.cycles):
        vals,vecs,rows,hcalls=lowest_modes(q,4,args.fd_step,args.rot_penalty,3e-5)
        total_hcalls+=hcalls
        mode=vecs[:,0]
        if prev_mode is not None and float(mode@prev_mode)<0: mode=-mode
        prev_mode=mode.copy()
        print(f'cycle={cyc} lambda0={vals[0]:.9g} lambdas={[float(v) for v in vals[:4]]} hcalls={hcalls}',flush=True)
        last=None
        for it in range(args.steps_per_cycle):
            q,E,grms,srms,gpar=step_eigenfollow(q,mode,args.eta,args.max_rms_step)
            last=(E,grms,srms,gpar)
            if it%20==0 or it==args.steps_per_cycle-1:
                print(f'  step={it} E={E:.12f} grad_rms={grms:.6g} step_rms={srms:.3e} gpar={gpar:.4g}',flush=True)
        history.append({'cycle':cyc,'eigenvalues':[float(v) for v in vals],
                        'mode_rows':rows,'end_energy':last[0],'end_grad_rms':last[1],
                        'end_step_rms':last[2],'end_gradient_parallel':last[3]})

    Ef,gf,_=physical_gradient(q); grms=float(np.linalg.norm(gf)/math.sqrt(len(q)))
    vals,vecs,rows,hcalls=lowest_modes(q,args.final_k,args.fd_step,args.rot_penalty,1e-5)
    total_hcalls+=hcalls
    neg=int(np.sum(vals < -1e-3))
    print(f'FINAL E={Ef:.12f} grad_rms={grms:.6g} negative_modes={neg}',flush=True)
    for r in rows: print(f"mode={r['index']} lambda={r['eigenvalue']:.12g} rot={r['rotation_overlap']:.2e} resid={r['residual']:.2e}",flush=True)
    out={'start_energy':E0,'final_energy':Ef,'final_gradient_rms':grms,
         'negative_internal_modes_below_-1e-3':neg,'fd_step':args.fd_step,
         'eta':args.eta,'max_rms_step':args.max_rms_step,'cycles':args.cycles,
         'steps_per_cycle':args.steps_per_cycle,'hessian_gradient_calls':total_hcalls,
         'history':history,'final_modes':rows,'saddle_points':vars_to_xyz(q)[0].tolist(),
         'eigenvectors_physical':[vecs[:,j].tolist() for j in range(min(args.final_k,vecs.shape[1]))]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
