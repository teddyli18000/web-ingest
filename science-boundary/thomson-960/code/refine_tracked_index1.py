#!/usr/bin/env python3
"""Refine a near index-1 Thomson stationary state while tracking one reaction mode.

The reaction eigenvector is followed by maximum overlap, not by eigenvalue order.
All orthogonal directions are minimized with the stable constrained L-BFGS used
elsewhere in this topic.  Along the tracked direction we use a damped Newton
step when curvature is negative; if the tracked curvature temporarily becomes
positive we switch to the HiSD uphill sign instead of collapsing into a minimum.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np

import diagnose_soft_modes as sm
import search_soft_pair as sp
from downward_index2_to_index1 import low_modes, physical_grad, track_mode
from refine_saddle_hybrid import constrained_relax

N=960


def load_state(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('saddle_points', d.get('points'))
    if p is None or len(p)!=N: raise ValueError('expected 960 saddle_points/points')
    x=np.asarray(p,float); x/=np.linalg.norm(x,axis=1)[:,None]
    return d,sm.xyz_to_vars(x)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--outer',type=int,default=18); ap.add_argument('--k',type=int,default=10)
    ap.add_argument('--fd-step',type=float,default=3e-6); ap.add_argument('--penalty',type=float,default=4e5)
    ap.add_argument('--perp-maxiter',type=int,default=800); ap.add_argument('--reaction-damping',type=float,default=0.45)
    ap.add_argument('--curv-floor',type=float,default=0.08); ap.add_argument('--max-reaction-rms',type=float,default=3e-5)
    ap.add_argument('--grad-tol',type=float,default=2e-5); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,q=load_state(args.seed_json); hist=[]; hcalls=0
    vals,V,Q,raw,c=low_modes(q,max(args.k,12),args.fd_step); hcalls+=c
    target=V[:,0].copy()
    print(f'seed E={sm.fg(q)[0]:.12f} grad={np.linalg.norm(physical_grad(q,Q))/math.sqrt(2*N):.6g} lows={vals[:5].tolist()}',flush=True)
    status='max_outer'
    for outer in range(args.outer):
        vals,V,Q,raw,c=low_modes(q,args.k,args.fd_step); hcalls+=c
        j,lam,mode,ov=track_mode(target,vals,V); target=mode
        g=physical_grad(q,Q); before=float(np.linalg.norm(g)/math.sqrt(2*N)); gt=float(g@mode)
        q,Eperp,cval,nit,ok,msg=constrained_relax(q,mode,args.penalty,args.perp_maxiter)
        vals2,V2,Q2,raw2,c2=low_modes(q,args.k,args.fd_step); hcalls+=c2
        j2,lam2,mode2,ov2=track_mode(target,vals2,V2); target=mode2
        g2=physical_grad(q,Q2); gt2=float(g2@mode2)
        if lam2 < 0:
            den=-max(abs(lam2),args.curv_floor)
            coeff=-args.reaction_damping*gt2/den
        else:
            den=max(lam2,args.curv_floor)
            coeff=+args.reaction_damping*gt2/den
        lim=args.max_reaction_rms*math.sqrt(N); coeff=float(np.clip(coeff,-lim,lim))
        if coeff!=0: q=sp.exp_perturb(q,mode2*np.sign(coeff),abs(coeff)/math.sqrt(N))
        E,_=sm.fg(q); vals3,V3,Q3,raw3,c3=low_modes(q,args.k,args.fd_step); hcalls+=c3
        g3=physical_grad(q,Q3); grms=float(np.linalg.norm(g3)/math.sqrt(2*N)); neg=int(np.sum(vals3<-1e-3))
        row={'outer':outer,'tracked_index_before':j,'lambda_before':lam,'overlap_before':ov,
             'gradient_rms_before':before,'tracked_gradient_before':gt,'perp_energy':Eperp,
             'constraint_displacement':cval,'perp_nit':nit,'perp_success':ok,'perp_message':msg,
             'tracked_index_after':j2,'lambda_after':lam2,'overlap_after':ov2,'tracked_gradient_after':gt2,
             'reaction_step_rms':abs(coeff)/math.sqrt(N),'energy_after':E,'gradient_rms_after':grms,
             'negative_modes_after':neg,'lowest_after':[float(v) for v in vals3[:5]]}
        hist.append(row)
        print(f'outer={outer} mode={j}->{j2} lam={lam:+.5g}->{lam2:+.5g} ov={ov:.4f}/{ov2:.4f} '
              f'gt={gt2:+.3g} step={abs(coeff)/math.sqrt(N):.2e} E={E:.12f} grad={grms:.3g} neg={neg}',flush=True)
        if grms<args.grad_tol and neg==1:
            status='converged'; break
    Ef,_=sm.fg(q); valsf,Vf,Qf,rawf,c=low_modes(q,max(args.k,12),args.fd_step); hcalls+=c
    gf=physical_grad(q,Qf); grmsf=float(np.linalg.norm(gf)/math.sqrt(2*N)); negf=int(np.sum(valsf<-1e-3))
    j,lam,mode,ov=track_mode(target,valsf,Vf)
    print(f'FINAL status={status} E={Ef:.12f} grad={grmsf:.7g} neg={negf} tracked={j} lambda={lam:+.8g} ov={ov:.5f} lows={valsf[:6].tolist()}',flush=True)
    out={'seed_json':str(args.seed_json),'status':status,'final_energy':float(Ef),'final_gradient_rms':grmsf,
         'negative_internal_modes_below_-1e-3':negf,'final_eigenvalues':[float(v) for v in valsf],
         'final_tracked_mode_index':j,'final_tracked_mode_eigenvalue':lam,'final_tracked_overlap':ov,
         'history':hist,'hessian_gradient_calls':hcalls,'saddle_points':sm.vars_to_xyz(q)[0].tolist(),
         'final_modes':[{'index':i,'eigenvalue':float(valsf[i])} for i in range(len(valsf))],
         'eigenvectors_physical':[Vf[:,i].tolist() for i in range(Vf.shape[1])]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
