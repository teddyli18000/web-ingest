#!/usr/bin/env python3
"""Validated transverse Hessian search at the N961 fractional A/R boundary.

This corrects the earlier penalty-only formulation.  A large nuisance penalty
H + mu QQ^T does not make the low eigenspace exactly orthogonal to Q when the
physical Hessian couples the retained subspace to nuisance directions.  Tiny
O(1/mu) nuisance components balance that coupling; projecting ARPACK vectors
afterward therefore creates O(1) Ritz residuals.

Here P is the orthogonal projector that removes active rigid rotations and the
empirical A/R continuation secant.  The scientifically relevant constrained
operator is

    P H_active P

on that transverse subspace.  We expose it to ARPACK as

    P H_active P + mu (I-P),

so the desired subspace is invariant.  H_active is evaluated by complex-step
differentiation of the analytic weighted angular gradient.  Random bilinear
symmetry and raw ARPACK Ritz residuals must pass before any perturbation search.
"""
from __future__ import annotations

import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import LinearOperator, eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_live_size_bounce import load_points, voronoi_candidates, relax as size_relax
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from search_from_seed_modes import stable_relax_q
from search_n961_fractional_boundary_modes import classify, counts, parse_schedule
from search_n961_active_transverse_modes import (
    FADE, kabsch_align, tangent_log, weighted_angular_grad_complex, project_return,
)


def build_projected_operator(q0_full, charges, secant, cs_step=1e-20, nuisance_penalty=1e6):
    nfull=len(q0_full)//2
    nact=nfull-1
    scale=sm.physical_scale(q0_full); invs=1.0/scale
    qact=sm.xyz_to_vars(sm.vars_to_xyz(q0_full)[0][:-1])
    Qrot=sm.rotation_basis(qact)
    sec=np.asarray(secant,float).copy()
    sec-=Qrot@(Qrot.T@sec)
    sn=float(np.linalg.norm(sec))
    if sn<1e-10: raise RuntimeError(f'vanishing secant {sn}')
    sec/=sn
    q0c=np.asarray(q0_full,dtype=np.complex128)
    calls={'n':0}

    def project(y):
        y=np.asarray(y,float)
        z=y-Qrot@(Qrot.T@y)
        z-=sec*float(sec@z)
        return z

    def nuisance(y):
        return np.asarray(y,float)-project(y)

    def raw_active(y):
        y=np.asarray(y,float)
        if not np.any(y): return np.zeros_like(y)
        yf=np.zeros(2*nfull,float); yf[:2*nact]=y
        dq=invs*yf
        gc=weighted_angular_grad_complex(q0c+1j*cs_step*dq,charges)
        calls['n']+=1
        hq=np.imag(gc)/cs_step
        hy=invs*hq
        return np.asarray(hy[:2*nact],float)

    def constrained(y):
        yp=project(y)
        return project(raw_active(yp))

    def mv(y):
        y=np.asarray(y,float)
        return constrained(y)+nuisance_penalty*nuisance(y)

    H=LinearOperator((2*nact,2*nact),matvec=mv,dtype=float)
    return H,constrained,project,nuisance,Qrot,sec,calls


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('a_json')
    ap.add_argument('--lambda-hi',type=float,default=.15)
    ap.add_argument('--lambda-value',type=float,default=.125)
    ap.add_argument('--lambda-lo',type=float,default=.10)
    ap.add_argument('--schedule',default='1,.8,.6,.4,.25,.15,.1,.075,.06,.05,.04,.03,.025,.02,.015,.01,.007,.005,.003,.001,0')
    ap.add_argument('--modes',default='0,1,2,3,4,5')
    ap.add_argument('--amps',default='.0015,.003,.006,.012,.02')
    ap.add_argument('--k',type=int,default=10)
    ap.add_argument('--cs-step',type=float,default=1e-20)
    ap.add_argument('--nuisance-penalty',type=float,default=1e6)
    ap.add_argument('--weighted-maxiter',type=int,default=1800)
    ap.add_argument('--return-maxiter',type=int,default=4200)
    ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    hi,lam,lo=map(float,(args.lambda_hi,args.lambda_value,args.lambda_lo))
    if not 0<=lo<lam<hi<=1: raise ValueError((lo,lam,hi))
    _,a=load_points(pathlib.Path(args.a_json))
    sel=voronoi_candidates(a)[3]
    hub=size_relax(np.vstack([a,np.asarray(sel['point'],float)[None,:]]),3200)
    x=np.asarray(hub['points'],float)
    if abs(hub['energy']-445303.247369582)>5e-4: raise RuntimeError(hub['energy'])

    trace=[]
    for lv in parse_schedule(args.schedule,hi):
        charges=np.ones(961,float); charges[FADE]=lv
        ew,x,nit,ok,msg,grms=stable_weighted_relax(x,charges,args.weighted_maxiter)
        trace.append({'lambda':lv,'energy':float(ew),'grms':float(grms),'nit':int(nit),'success':bool(ok)})
        print('CONT',lv,f'{ew:.12f}',f'grms={grms:.3g}',flush=True)
    xhi=x.copy()
    for lv in (lam,lo):
        charges=np.ones(961,float); charges[FADE]=lv
        ew,x,nit,ok,msg,grms=stable_weighted_relax(x,charges,args.weighted_maxiter)
        trace.append({'lambda':lv,'energy':float(ew),'grms':float(grms),'nit':int(nit),'success':bool(ok)})
        print('CONT',lv,f'{ew:.12f}',f'grms={grms:.3g}',flush=True)
        if lv==lam: xmid=x.copy()
        else: xlo=x.copy()

    chi=project_return(xhi,args.live_score,args.return_maxiter)
    base=project_return(xmid,args.live_score,args.return_maxiter)
    clo=project_return(xlo,args.live_score,args.return_maxiter)
    print('BRACKET',chi['class'],base['class'],clo['class'],flush=True)
    if chi['class']==clo['class']: raise RuntimeError('lost A/R bracket')

    ahi,_,_=kabsch_align(xmid,xhi); alo,_,_=kabsch_align(xmid,xlo)
    sec=tangent_log(xmid[:-1],ahi[:-1])-tangent_log(xmid[:-1],alo[:-1])
    sec_rms_deriv=float(np.linalg.norm(sec)/math.sqrt(960)/(hi-lo))
    q0=sm.xyz_to_vars(xmid); charges=np.ones(961,float); charges[FADE]=lam
    H,Hc,project,nuisance,Qrot,svec,calls=build_projected_operator(
        q0,charges,sec,args.cs_step,args.nuisance_penalty)

    rng=np.random.default_rng(2961000+int(round(lam*1e6)))
    aa=project(rng.normal(size=1920)); bb=project(rng.normal(size=1920))
    aa/=np.linalg.norm(aa); bb/=np.linalg.norm(bb)
    Haa=Hc(aa); Hbb=Hc(bb)
    lhs=float(aa@Hbb); rhs=float(bb@Haa)
    sym_abs=abs(lhs-rhs); sym_rel=sym_abs/max(1.0,abs(lhs),abs(rhs))
    print('SYMMETRY',lhs,rhs,sym_abs,sym_rel,flush=True)
    if sym_rel>2e-7: raise RuntimeError(f'symmetry {sym_rel}')

    modes=[int(z) for z in args.modes.split(',') if z.strip()]
    amps=[float(z) for z in args.amps.split(',') if z.strip()]
    k=max(args.k,max(modes)+1)
    v0=project(rng.normal(size=1920)); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=k,which='SA',tol=2e-9,maxiter=1500,ncv=max(60,5*k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    print('EIGENVALUES',[float(v) for v in vals],flush=True)

    diag=[]; max_res=0.0
    for m in modes:
        y=V[:,m]
        Hy=H.matvec(y)
        res=float(np.linalg.norm(Hy-vals[m]*y))
        nrm=float(np.linalg.norm(nuisance(y)))
        max_res=max(max_res,res)
        rec={'mode':m,'eigenvalue':float(vals[m]),'ritz_residual':res,'nuisance_norm':nrm}
        diag.append(rec)
        print('MODE',m,f'eig={vals[m]:.12g}',f'resid={res:.3e}',f'nuis={nrm:.3e}',flush=True)
    if max_res>2e-5: raise RuntimeError(f'Ritz residual {max_res}')

    qact=sm.xyz_to_vars(xmid[:-1]); rows=[]
    for m in modes:
        d=project(V[:,m]); d/=np.linalg.norm(d)
        for sign in (-1,1):
            for amp in amps:
                qp=sp.exp_perturb(qact,d*sign,amp)
                e,raw,y,nit,ok,msg=stable_relax_q(qp,maxiter=args.return_maxiter)
                r={'mode':m,'eigenvalue':float(vals[m]),'sign':sign,'amp':amp,'energy':float(e),
                   'delta_live':float(e-args.live_score),'class':classify(e,args.live_score),
                   'coord_counts':counts(y),'nit':int(nit),'success':bool(ok),'message':str(msg)}
                rows.append(r)
                print('RETURN',m,sign,amp,r['class'],f'{e:.12f}',f"d={r['delta_live']:+.9g}",flush=True)
    rows.sort(key=lambda r:r['energy'])
    best=min([base['energy']]+[r['energy'] for r in rows])
    out={'live_score':float(args.live_score),'lambda_hi':hi,'lambda':lam,'lambda_lo':lo,
         'hub_energy':float(hub['energy']),'hub_triangle':sel['triangle'],'continuation_trace':trace,
         'control_hi':chi,'baseline':base,'control_lo':clo,'secant_derivative_rms':sec_rms_deriv,
         'operator':'P H_active P + nuisance penalty','hvp':'complex-step','complex_step':args.cs_step,
         'symmetry_abs':sym_abs,'symmetry_rel':sym_rel,'eigenvalues':[float(v) for v in vals],
         'mode_diagnostics':diag,'rows':rows,'best_energy':float(best),
         'best_delta_live':float(best-args.live_score),'hessian_calls':calls['n']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('validated projected-transverse candidate below live\n')

if __name__=='__main__': main()
