#!/usr/bin/env python3
"""Classify and descend a constant-occupancy N961 edge-state seed.

The seed is produced by edge_track_n961_simplex_sheets.py at the common
three-occupancy center q886=q960=q380=2/3 (all other charges one, total charge
exactly 960).  We compute the full 961-particle physical-tangent Hessian of the
weighted Coulomb objective with a complex-step analytic-gradient HVP, project
out only the three exact global rotations, validate symmetry/Ritz residuals,
and count genuine internal negative modes.

If negative modes exist, small perturbations along each are weighted-relaxed at
the same fixed charges.  Every child is then projected to ordinary unit-charge
N=960 by deleting labels 886, 960, and 380 and fully polishing.  This certifies
which weighted sheets lie on the unstable sides and tests for a new N960 exit.
"""
from __future__ import annotations

import argparse,json,math,pathlib
import numpy as np
from scipy.sparse.linalg import LinearOperator,eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_size_beam as sbeam
from search_n972_mobile_fractional_homotopy import weighted_terms_grad,stable_weighted_relax
from search_n961_active_transverse_modes import weighted_angular_grad_complex
from search_n961_three_occupancy_simplex import LABELS,classify
from search_n961_occupancy_exchange import sig_json


def physical_weighted_state(x,charges):
    q=sm.xyz_to_vars(x)
    terms,gq,_=weighted_terms_grad(q,charges)
    E=float(np.sum(np.asarray(terms,np.longdouble),dtype=np.longdouble))
    gy=gq/sm.physical_scale(q)
    grms=float(np.linalg.norm(gy)/math.sqrt(len(gy)))
    return q,E,grms


def build_rot_projected_hessian(q0,charges,cs_step=1e-20,penalty=1e6):
    scale=sm.physical_scale(q0); invs=1.0/scale; Q=sm.rotation_basis(q0)
    q0c=np.asarray(q0,dtype=np.complex128); calls={'n':0}
    def project(y):
        y=np.asarray(y,float); return y-Q@(Q.T@y)
    def nuisance(y):
        y=np.asarray(y,float); return y-project(y)
    def raw(y):
        y=np.asarray(y,float)
        if not np.any(y): return np.zeros_like(y)
        dq=invs*y
        gc=weighted_angular_grad_complex(q0c+1j*cs_step*dq,charges)
        calls['n']+=1
        hq=np.imag(gc)/cs_step
        return np.asarray(invs*hq,float)
    def constrained(y):
        yp=project(y); return project(raw(yp))
    def mv(y):
        y=np.asarray(y,float); return constrained(y)+penalty*nuisance(y)
    return LinearOperator((len(q0),len(q0)),matvec=mv,dtype=float),constrained,project,nuisance,Q,calls


def project_n960(x,di,live,maxiter):
    e,y,nit,ok=sbeam.stable_relax(np.delete(np.asarray(x,float),int(di),axis=0),maxiter)
    return {'delete_index':int(di),'energy':float(e),'delta_live':float(e-live),
            'class':classify(e,live),'signature':sig_json(y),'nit':int(nit),'success':bool(ok)}


def weighted_sheet_class(e,ea,eh,tol=2e-5):
    da,dh=abs(float(e)-float(ea)),abs(float(e)-float(eh))
    if da<tol and da<dh: return 'A-sheet'
    if dh<tol and dh<da: return 'H-sheet'
    return 'other-sheet'


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('edge_json'); ap.add_argument('a_result'); ap.add_argument('h_result')
    ap.add_argument('--k',type=int,default=14); ap.add_argument('--cs-step',type=float,default=1e-20)
    ap.add_argument('--amps',default='.00005,.0001,.0002,.0004,.0008')
    ap.add_argument('--weighted-maxiter',type=int,default=2600); ap.add_argument('--project-maxiter',type=int,default=3800)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    edge=json.load(open(args.edge_json)); da=json.load(open(args.a_result)); dh=json.load(open(args.h_result))
    x=np.asarray(edge['edge_points'],float); x/=np.linalg.norm(x,axis=1)[:,None]
    if x.shape!=(961,3): raise ValueError(x.shape)
    charges=np.ones(961,float); charges[list(LABELS)]=2/3
    if abs(float(np.sum(charges))-960)>1e-10: raise RuntimeError(np.sum(charges))
    ea=float(da['center_weighted_energy']); eh=float(dh['center_weighted_energy'])
    q0,E0,grms=physical_weighted_state(x,charges)
    print('SEED',f'E={E0:.12f}',f'grad={grms:.8g}',f'edge_reported={edge.get("best",{})}',flush=True)

    H,Hc,project,nuisance,Q,calls=build_rot_projected_hessian(q0,charges,args.cs_step,1e6)
    rng=np.random.default_rng(3961001)
    a=project(rng.normal(size=len(q0))); b=project(rng.normal(size=len(q0)))
    a/=np.linalg.norm(a); b/=np.linalg.norm(b)
    Ha,Hb=Hc(a),Hc(b); lhs=float(a@Hb); rhs=float(b@Ha)
    sym_abs=abs(lhs-rhs); sym_rel=sym_abs/max(1.0,abs(lhs),abs(rhs))
    print('SYMMETRY',f'lhs={lhs:.12g}',f'rhs={rhs:.12g}',f'abs={sym_abs:.3e}',f'rel={sym_rel:.3e}',flush=True)
    if sym_rel>2e-7: raise RuntimeError(f'Hessian symmetry failure {sym_rel}')

    v0=project(rng.normal(size=len(q0))); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=args.k,which='SA',tol=2e-9,maxiter=1800,ncv=max(70,5*args.k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    diag=[]; maxres=0.0
    for j,lam in enumerate(vals):
        y=V[:,j]; r=float(np.linalg.norm(H.matvec(y)-lam*y)); n=float(np.linalg.norm(nuisance(y)))
        maxres=max(maxres,r); diag.append({'index':j,'eigenvalue':float(lam),'ritz_residual':r,'rotation_nuisance_norm':n})
        print('MODE',j,f'lambda={lam:.12g}',f'resid={r:.3e}',f'rot={n:.3e}',flush=True)
    if maxres>2e-5: raise RuntimeError(f'Ritz residual too large {maxres}')
    neg=[j for j,v in enumerate(vals) if v<-1e-3]
    print('NEGATIVE_MODES',neg,flush=True)

    amps=[float(z) for z in args.amps.split(',') if z.strip()]
    rows=[]
    for j in neg[:4]:
        d=project(V[:,j]); d/=np.linalg.norm(d)
        for sign in (-1,1):
            for amp in amps:
                qs=sp.exp_perturb(q0,sign*d,amp); xs,_,_=sm.vars_to_xyz(qs)
                ew,y,nit,ok,msg,wgr=stable_weighted_relax(xs,charges,args.weighted_maxiter)
                projs=[project_n960(y,di,args.live_score,args.project_maxiter) for di in LABELS]
                rec={'mode':j,'eigenvalue':float(vals[j]),'sign':sign,'amp':amp,
                     'weighted_energy':float(ew),'weighted_class':weighted_sheet_class(ew,ea,eh),
                     'weighted_grms':float(wgr),'weighted_nit':int(nit),'weighted_success':bool(ok),
                     'weighted_message':str(msg),'projections':projs}
                rows.append(rec)
                print('DESCEND',j,sign,amp,rec['weighted_class'],f'Ew={ew:.12f}',
                      'P',[(p['delete_index'],p['class'],round(p['delta_live'],9)) for p in projs],flush=True)
    allp=[p for r in rows for p in r['projections']]
    seedp=[project_n960(x,di,args.live_score,args.project_maxiter) for di in LABELS]
    allp+=seedp
    best=min(allp,key=lambda p:p['energy']) if allp else None
    out={'live_score':float(args.live_score),'seed_weighted_energy':E0,'seed_physical_gradient_rms':grms,
         'edge_reported_best':edge.get('best'),'center_A_energy':ea,'center_H_energy':eh,
         'hvp':'complex-step','operator':'P_rot H P_rot + rotation penalty','symmetry_abs':sym_abs,'symmetry_rel':sym_rel,
         'eigenvalues':[float(v) for v in vals],'mode_diagnostics':diag,'negative_modes':neg,
         'seed_projections':seedp,'descent_rows':rows,'best_projection':best,'hessian_calls':calls['n']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best is not None and best['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH.json').write_text(json.dumps(best,separators=(',',':'))+'\n')

if __name__=='__main__': main()
