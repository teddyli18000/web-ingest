#!/usr/bin/env python3
"""CHiSD-inspired downward search from an index-2 Thomson stationary state.

Given an index-2 parent, choose an escape phase in its two-dimensional negative
eigenspace, perturb along that direction, and retain the orthogonal negative
direction as the desired index-1 reaction mode. The reaction mode is tracked by
maximum eigenvector overlap, not eigenvalue ordering.

The target mode follows the HiSD sign rule: its gradient component is always
reversed relative to minimization. Numerically the reaction step is
`+ damping * g_target / |lambda_target|` (with a curvature floor). Therefore a
positive-curvature tracked mode is pushed uphill back toward a basin boundary,
while once its curvature is negative the same rule is stable toward the saddle.
All orthogonal directions are minimized by constrained all-dimensional L-BFGS.

For C, direct energy-curvature audits show the quadratic negative-curvature
region extends only to roughly 6e-4 RMS before nonlinear terms reverse the
energy trend. The default escape is therefore 3e-4 RMS; milliradian-scale kicks
are finite-amplitude basin probes, not local downward-search initializations.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from refine_saddle_hybrid import constrained_relax
from search_from_seed_modes import load_seed
from search_seed_c3_negative_pair import canonicalize_pair_near

N=960


def low_modes(q,k,fd):
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=900,ncv=max(40,4*k))
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    for j in range(V.shape[1]):
        V[:,j]-=Q@(Q.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    return vals,V,Q,raw,calls['n']


def physical_grad(q,Q=None):
    _,gq=sm.fg(q); g=gq/sm.physical_scale(q)
    if Q is not None: g-=Q@(Q.T@g)
    return g


def track_mode(prev,vals,V):
    overlaps=np.abs(V.T@prev); j=int(np.argmax(overlaps)); v=V[:,j].copy()
    if float(v@prev)<0: v=-v
    return j,float(vals[j]),v,float(overlaps[j])


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--escape-phase-deg',type=float,required=True)
    ap.add_argument('--escape-amp',type=float,default=0.0003)
    ap.add_argument('--outer',type=int,default=10); ap.add_argument('--k',type=int,default=8)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--penalty',type=float,default=3e5)
    ap.add_argument('--perp-maxiter',type=int,default=650); ap.add_argument('--reaction-damping',type=float,default=0.35)
    ap.add_argument('--curv-floor',type=float,default=0.15); ap.add_argument('--max-reaction-rms',type=float,default=8e-5)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    meta,x0=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x0)
    vals0,V0,Q0,raw0,hcalls=low_modes(q0,max(args.k,6),args.fd_step)
    if vals0[1]>=-1e-3: raise RuntimeError(f'parent is not index-2 in low spectrum: {vals0[:4]}')
    pair=V0[:,:2].copy(); pair,_=np.linalg.qr(pair); pair,M,resid,ai,ac,maperr=canonicalize_pair_near(pair,q0)
    a=math.radians(args.escape_phase_deg)
    escape=math.cos(a)*pair[:,0]+math.sin(a)*pair[:,1]; escape/=np.linalg.norm(escape)
    target=-math.sin(a)*pair[:,0]+math.cos(a)*pair[:,1]; target/=np.linalg.norm(target)
    q=sp.exp_perturb(q0,escape,args.escape_amp)
    hist=[]; total_hcalls=hcalls
    print(f'parent lambdas={vals0[:4].tolist()} phase={args.escape_phase_deg:g} amp={args.escape_amp:g} '
          f'C3M={M.tolist()} resid={resid:.3e} maperr={maperr:.3e}',flush=True)

    for outer in range(args.outer):
        vals,V,Q,raw,c=low_modes(q,args.k,args.fd_step); total_hcalls+=c
        j,lam,mode,ov=track_mode(target,vals,V); target=mode
        g=physical_grad(q,Q); before=float(np.linalg.norm(g)/math.sqrt(2*N)); gt=float(g@mode)
        q,Eperp,cval,nit,ok,msg=constrained_relax(q,mode,args.penalty,args.perp_maxiter)

        vals2,V2,Q2,raw2,c2=low_modes(q,args.k,args.fd_step); total_hcalls+=c2
        j2,lam2,mode2,ov2=track_mode(target,vals2,V2); target=mode2
        g2=physical_grad(q,Q2); gt2=float(g2@mode2)
        den=max(abs(lam2),args.curv_floor)
        coeff=args.reaction_damping*gt2/den
        lim=args.max_reaction_rms*math.sqrt(N); coeff=float(np.clip(coeff,-lim,lim))
        if coeff!=0: q=sp.exp_perturb(q,mode2*np.sign(coeff),abs(coeff)/math.sqrt(N))
        E,_=sm.fg(q); gnew=physical_grad(q); grms=float(np.linalg.norm(gnew)/math.sqrt(2*N))
        row={'outer':outer,'tracked_index_before':j,'tracked_lambda_before':lam,'overlap_before':ov,
             'gradient_rms_before':before,'tracked_gradient_before':gt,'perp_energy':Eperp,
             'constraint_displacement':cval,'perp_nit':nit,'perp_success':ok,'perp_message':msg,
             'tracked_index_after':j2,'tracked_lambda_after':lam2,'overlap_after':ov2,
             'tracked_gradient_after':gt2,'reaction_step_rms':abs(coeff)/math.sqrt(N),
             'energy_after':E,'gradient_rms_after':grms}
        hist.append(row)
        print(f'outer={outer} mode={j}->{j2} lambda={lam:+.6g}->{lam2:+.6g} ov={ov:.4f}/{ov2:.4f} '
              f'Eperp={Eperp:.12f} gt={gt2:+.3g} drms={abs(coeff)/math.sqrt(N):.2e} '
              f'E={E:.12f} grad={grms:.3g}',flush=True)

    Ef,gq=sm.fg(q); gp=gq/sm.physical_scale(q); grms=float(np.linalg.norm(gp)/math.sqrt(2*N))
    vals,V,Q,raw,c=low_modes(q,max(args.k,12),args.fd_step); total_hcalls+=c
    neg=int(np.sum(vals<-1e-3)); j,lam,mode,ov=track_mode(target,vals,V)
    print(f'FINAL E={Ef:.12f} grad={grms:.7g} neg={neg} tracked={j} lambda={lam:+.8g} overlap={ov:.5f} '
          f'lows={vals[:6].tolist()}',flush=True)
    out={'seed_json':str(args.seed_json),'parent_energy':float(meta.get('energy',meta.get('seed_energy',float('nan')))),
         'parent_eigenvalues':[float(v) for v in vals0],'escape_phase_deg':args.escape_phase_deg,
         'escape_amp':args.escape_amp,'c3_pair_matrix':M.tolist(),'c3_subspace_residual':resid,
         'c3_mapping_max_error':maperr,'final_energy':float(Ef),'final_gradient_rms':grms,
         'negative_internal_modes_below_-1e-3':neg,'final_eigenvalues':[float(v) for v in vals],
         'final_tracked_mode_index':j,'final_tracked_mode_eigenvalue':lam,'final_tracked_overlap':ov,
         'history':hist,'hessian_gradient_calls':total_hcalls,'saddle_points':sm.vars_to_xyz(q)[0].tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
