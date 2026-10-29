#!/usr/bin/env python3
"""Generic CHiSD-style downward search from a Thomson index-k stationary state.

The parent Morse index is inferred from its lowest full-space Hessian modes. One
negative direction is chosen as the escape direction; the remaining k-1
negative-dimensional subspace is retained as the target unstable subspace.
During the search this subspace is tracked by maximum projection and orthogonal
Procrustes alignment, which is robust to nearly degenerate symmetry multiplets.

Each outer iteration alternates:
  1. stable full-dimensional L-BFGS minimization with quadratic restraints that
     fix displacement along the retained unstable subspace and the three rigid
     rotation fields;
  2. a HiSD/Newton step inside the tracked subspace, using +g/|lambda| so the
     dynamics is uphill while a tracked curvature is positive and saddle-Newton
     when it is negative.

The explicit rigid-rotation restraint is the Thomson-specific nullspace-
preserving ingredient: the Hessian eigensolver already projects/lifts these
three exact zero modes, and the constrained minimizer should not be allowed to
spend iterations drifting along them.

This generalizes downward_index2_to_index1.py to arbitrary modest Morse index.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.optimize import minimize
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed

N=960
PI=math.pi


def low_modes(q,k,fd,v0=None):
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    kw={'k':k,'which':'SA','tol':1e-5,'maxiter':1000,'ncv':max(60,4*k)}
    if v0 is not None: kw['v0']=v0
    vals,V=eigsh(H,**kw); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    for j in range(V.shape[1]):
        V[:,j]-=Q@(Q.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    return vals,V,Q,raw,calls['n']


def pgrad(q,Q=None):
    _,gq=sm.fg(q); g=gq/sm.physical_scale(q)
    if Q is not None: g-=Q@(Q.T@g)
    return g


def wrap_phi(d): return (d+math.pi)%(2*math.pi)-math.pi


def align_subspace(prev,vals,V,r):
    """Select r current eigenvectors with largest projection onto prev; align basis."""
    score=np.sum((V.T@prev)**2,axis=1)
    ids=np.argsort(score)[-r:]
    ids=ids[np.argsort(vals[ids])]
    W=V[:,ids].copy(); M=W.T@prev
    U,s,VT=np.linalg.svd(M,full_matrices=False)
    R=U@VT; A=W@R
    A,_=np.linalg.qr(A)
    overlap=float(np.sum(s*s)/r)
    return ids,A,overlap


def stable_constrained_relax(qref,modes,penalty,rot_penalty,maxiter):
    n=len(qref)//2; tri=np.triu_indices(n,1)
    x0,_,_=sm.vars_to_xyz(qref); dots=np.clip(x0@x0.T,-1,1)
    r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv0=1/np.sqrt(r2); ref=np.asarray(inv0[tri],dtype=np.longdouble); ref_abs=float(np.sum(inv0[tri],dtype=np.float64))
    a0=qref.reshape(-1,2); sin0=np.maximum(np.sin(a0[:,0]),1e-6)
    M=modes
    R=sm.rotation_basis(qref)
    def displacement(q):
        a=q.reshape(-1,2); dth=a[:,0]-a0[:,0]; dph=wrap_phi(a[:,1]-a0[:,1])
        return np.column_stack([dth,sin0*dph]).ravel()
    def obj(q):
        x,dth,dph=sm.vars_to_xyz(q); dots=np.clip(x@x.T,-1,1)
        r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
        inv=1/np.sqrt(r2); delta=float(np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref,dtype=np.longdouble))
        w=inv/r2; np.fill_diagonal(w,0); gc=w@x-np.sum(w,axis=1)[:,None]*x
        gq=np.column_stack([np.sum(gc*dth,axis=1),np.sum(gc*dph,axis=1)]).ravel()
        y=displacement(q); c=M.T@y; cr=R.T@y
        py=penalty*(M@c) + rot_penalty*(R@cr)
        pq=py.reshape(-1,2).copy(); pq[:,1]*=sin0
        f=delta+0.5*penalty*float(c@c)+0.5*rot_penalty*float(cr@cr)
        return f,gq+pq.ravel()
    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    res=minimize(obj,qref,jac=True,method='L-BFGS-B',bounds=bounds,
                 options={'maxiter':maxiter,'gtol':2e-9,'ftol':1e-15,'maxls':60,'maxcor':35})
    x,_,_=sm.vars_to_xyz(res.x); dots=np.clip(x@x.T,-1,1)
    r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf); inv=1/np.sqrt(r2)
    E=ref_abs+float(np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref,dtype=np.longdouble))
    return res.x,E,int(res.nit),bool(res.success),str(res.message)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--escape-mode',type=int,default=0); ap.add_argument('--sign',type=int,choices=[-1,1],default=1)
    ap.add_argument('--escape-amp',type=float,default=0.0003); ap.add_argument('--outer',type=int,default=14)
    ap.add_argument('--k-search',type=int,default=20); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--penalty',type=float,default=4e5); ap.add_argument('--rot-penalty',type=float,default=2e5)
    ap.add_argument('--perp-maxiter',type=int,default=750)
    ap.add_argument('--reaction-damping',type=float,default=0.35); ap.add_argument('--curv-floor',type=float,default=0.1)
    ap.add_argument('--max-reaction-rms',type=float,default=5e-5); ap.add_argument('--grad-tol',type=float,default=3e-5)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x0=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x0)
    vals0,V0,Q0,raw0,hcalls=low_modes(q0,args.k_search,args.fd_step)
    negids=np.where(vals0<-1e-3)[0]; parent_index=len(negids)
    if parent_index<2: raise RuntimeError(f'need index >=2 parent, got {parent_index}, lows={vals0[:8]}')
    if args.escape_mode<0 or args.escape_mode>=parent_index: raise ValueError('escape-mode must index a negative parent mode')
    esc=V0[:,negids[args.escape_mode]].copy()*args.sign
    keep=[j for i,j in enumerate(negids) if i!=args.escape_mode]
    tracked=V0[:,keep].copy(); tracked,_=np.linalg.qr(tracked); r=tracked.shape[1]
    q=sp.exp_perturb(q0,esc,args.escape_amp); hist=[]; status='max_outer'
    print(f'parent_index={parent_index} parent_lows={vals0[:min(12,len(vals0))].tolist()} escape={args.escape_mode} sign={args.sign} amp={args.escape_amp}',flush=True)
    for outer in range(args.outer):
        vals,V,Q,raw,c=low_modes(q,args.k_search,args.fd_step,v0=tracked[:,0]); hcalls+=c
        ids,tracked,ov=align_subspace(tracked,vals,V,r)
        g=pgrad(q,Q); before=float(np.linalg.norm(g)/math.sqrt(2*N)); gp=tracked.T@g
        q,Eperp,nit,ok,msg=stable_constrained_relax(q,tracked,args.penalty,args.rot_penalty,args.perp_maxiter)
        vals2,V2,Q2,raw2,c2=low_modes(q,args.k_search,args.fd_step,v0=tracked[:,0]); hcalls+=c2
        ids2,tracked,ov2=align_subspace(tracked,vals2,V2,r)
        g2=pgrad(q,Q2); gp2=tracked.T@g2
        K=np.column_stack([raw2(tracked[:,j]) for j in range(r)]); hcalls+=2*r
        K=tracked.T@K; K=0.5*(K+K.T)
        klam,U=np.linalg.eigh(K); coeff=U@((args.reaction_damping/np.maximum(np.abs(klam),args.curv_floor))*(U.T@gp2))
        delta=tracked@coeff; drms=float(np.linalg.norm(delta)/math.sqrt(N))
        if drms>args.max_reaction_rms: delta*=args.max_reaction_rms/drms; drms=args.max_reaction_rms
        if drms>0: q=sp.exp_perturb(q,delta/drms,drms)
        E,_=sm.fg(q); vals3,V3,Q3,raw3,c3=low_modes(q,args.k_search,args.fd_step,v0=tracked[:,0]); hcalls+=c3
        g3=pgrad(q,Q3); grms=float(np.linalg.norm(g3)/math.sqrt(2*N)); neg=int(np.sum(vals3<-1e-3))
        print(f'outer={outer} E={E:.12f} grad={grms:.4g} neg={neg} subov={ov:.4f}/{ov2:.4f} '
              f'K={klam.tolist()} step={drms:.2e}',flush=True)
        hist.append({'outer':outer,'energy':E,'gradient_rms':grms,'negative_modes':neg,
                     'subspace_overlap_before':ov,'subspace_overlap_after':ov2,'selected_indices_before':ids.tolist(),
                     'selected_indices_after':ids2.tolist(),'tracked_curvatures':[float(v) for v in klam],
                     'tracked_gradient':[float(v) for v in gp2],'reaction_step_rms':drms,'perp_energy':Eperp,
                     'perp_nit':nit,'perp_success':ok,'perp_message':msg})
        if grms<args.grad_tol and neg==parent_index-1:
            status='converged'; break
    Ef,_=sm.fg(q); valsf,Vf,Qf,rawf,c=low_modes(q,max(args.k_search,24),args.fd_step,v0=tracked[:,0]); hcalls+=c
    gf=pgrad(q,Qf); grmsf=float(np.linalg.norm(gf)/math.sqrt(2*N)); negf=int(np.sum(valsf<-1e-3))
    print(f'FINAL status={status} E={Ef:.12f} grad={grmsf:.7g} neg={negf} lows={valsf[:12].tolist()}',flush=True)
    out={'seed_json':str(args.seed_json),'parent_index':parent_index,'parent_eigenvalues':[float(v) for v in vals0],
         'escape_mode':args.escape_mode,'sign':args.sign,'escape_amp':args.escape_amp,'target_index':parent_index-1,
         'status':status,'final_energy':float(Ef),'final_gradient_rms':grmsf,'negative_internal_modes_below_-1e-3':negf,
         'final_eigenvalues':[float(v) for v in valsf],'history':hist,'hessian_gradient_calls':hcalls,
         'rot_penalty':args.rot_penalty,'saddle_points':sm.vars_to_xyz(q)[0].tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
