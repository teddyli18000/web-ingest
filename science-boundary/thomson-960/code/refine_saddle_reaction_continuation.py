#!/usr/bin/env python3
"""Refine a shallow-curvature index-1 candidate by reaction-coordinate continuation.

Unlike refine_saddle_hybrid.py, this tool never disables the reaction update merely
because |lambda| is small.  Each outer cycle first minimizes the full positive
subspace in a hyperplane normal to the tracked reaction mode, then applies a
clipped Newton step -g_reaction/lambda along that mode.  The reaction mode is
tracked by overlap after exact pointwise parallel transport, avoiding eigenvalue
ordering switches.  This is intended for CHiSD descendants whose residual
gradient is almost entirely reaction-coordinate gradient.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.sparse.linalg import eigsh
import diagnose_soft_modes as sm
import search_soft_pair as sp
import refine_saddle_hybrid as hy

N=960

def load_seed(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('saddle_points') or d.get('points')
    if p is None: raise ValueError('need saddle_points or points')
    x=np.asarray(p,float); x/=np.linalg.norm(x,axis=1)[:,None]
    return d,sm.xyz_to_vars(x)

def mode_to_cart(q,mode):
    x,eth,eph=sp.tangent_bases(q); a=mode.reshape(-1,2)
    return x,a[:,0,None]*eth+a[:,1,None]*eph

def transport_mode(q0,q1,mode0):
    x,v=mode_to_cart(q0,mode0); y,eth,eph=sp.tangent_bases(q1)
    den=1.0+np.sum(x*y,axis=1)
    if float(np.min(den))<1e-6: raise RuntimeError('near-antipodal reaction transport')
    coef=np.sum(v*y,axis=1)/den; w=v-coef[:,None]*(x+y)
    w-=np.sum(w*y,axis=1)[:,None]*y
    out=np.column_stack([np.sum(w*eth,axis=1),np.sum(w*eph,axis=1)]).ravel()
    out/=np.linalg.norm(out); return out

def modes(q,k=10,fd=3e-6):
    H,raw,Qrot,calls=sm.build_hessian(q,fd,1e6)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=800,ncv=max(48,4*k))
    o=np.argsort(vals); return vals[o],V[:,o],Qrot,raw,calls['n']
def select_tracked(vals,V,Qrot,reference=None):
    W=V.copy(); W-=Qrot@(Qrot.T@W); W/=np.maximum(np.linalg.norm(W,axis=0),1e-300)
    if reference is None: j=int(np.argmin(vals))
    else: j=int(np.argmax(np.abs(reference@W)))
    m=W[:,j].copy()
    if reference is not None and float(reference@m)<0: m=-m
    return j,float(vals[j]),m,W

def final_class(q,k=10):
    vals,V,Qrot,raw,calls=modes(q,k); rows=[]
    for j,lam in enumerate(vals):
        y=V[:,j]; Hy=raw(y)+1e6*(Qrot@(Qrot.T@y))
        rows.append({'index':j,'eigenvalue':float(lam),'rotation_overlap':float(np.sum((Qrot.T@y)**2)),'residual':float(np.linalg.norm(Hy-lam*y))})
    return vals,V,Qrot,rows,calls

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--outer',type=int,default=24)
    ap.add_argument('--penalty',type=float,default=350000); ap.add_argument('--perp-maxiter',type=int,default=550)
    ap.add_argument('--damping',type=float,default=0.75); ap.add_argument('--max-rms-step',type=float,default=0.003)
    ap.add_argument('--min-rms-step',type=float,default=0.00015); ap.add_argument('--target-grad-rms',type=float,default=1.5e-5)
    ap.add_argument('--target-reaction',type=float,default=3e-4); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,q=load_seed(args.seed_json); hist=[]; total_calls=0; prev_mode=None; prev_q=None; prev_g0=None; cap=args.max_rms_step
    for it in range(args.outer):
        vals,V,Qrot,raw,c=modes(q,10); total_calls+=c
        ref=None if prev_mode is None else transport_mode(prev_q,q,prev_mode)
        j,lam,mode,W=select_tracked(vals,V,Qrot,ref)
        gp=hy.physical_grad(q); gp-=Qrot@(Qrot.T@gp); grms0=float(np.linalg.norm(gp)/math.sqrt(2*N)); g00=float(gp@mode)
        # Eliminate perpendicular gradient in the current reaction hyperplane.
        q2,Eperp,cval,nit,ok,msg=hy.constrained_relax(q,mode,args.penalty,args.perp_maxiter)
        ref2=transport_mode(q,q2,mode); vals2,V2,Qrot2,raw2,c2=modes(q2,10); total_calls+=c2
        j2,lam2,mode2,W2=select_tracked(vals2,V2,Qrot2,ref2)
        g2=hy.physical_grad(q2); g2-=Qrot2@(Qrot2.T@g2); grms=float(np.linalg.norm(g2)/math.sqrt(2*N)); g0=float(g2@mode2)
        neg=int(np.sum(vals2<-1e-3))
        print(f'it={it} pre E? grad={grms0:.6g} g0={g00:+.5g} lam={lam:+.6g} j={j} | perp E={Eperp:.12f} grad={grms:.6g} g0={g0:+.5g} lam={lam2:+.6g} j={j2} neg={neg} nit={nit}',flush=True)
        row={'iteration':it,'pre_gradient_rms':grms0,'pre_reaction_gradient':g00,'pre_lambda':lam,'pre_mode_index':j,
             'perp_energy':Eperp,'constraint_displacement':cval,'perp_nit':nit,'perp_success':ok,'perp_message':msg,
             'gradient_rms':grms,'reaction_gradient':g0,'lambda':lam2,'tracked_mode_index':j2,'negative_modes':neg,'step_cap_rms':cap}
        q=q2
        if grms<=args.target_grad_rms and abs(g0)<=args.target_reaction and neg==1:
            row['converged']=True; hist.append(row); prev_mode=mode2; prev_q=q.copy(); break
        # Newton reaction displacement; unlike the old hybrid method there is no
        # small-|lambda| cutoff.  Clipping is what controls near-flat directions.
        if abs(lam2)<1e-8: coeff=math.copysign(cap*math.sqrt(N),g0 if g0 else 1.0)
        else: coeff=-args.damping*g0/lam2
        raw_rms=abs(coeff)/math.sqrt(N)
        step_rms=min(raw_rms,cap)
        if prev_g0 is not None and g0*prev_g0<0:
            cap=max(args.min_rms_step,0.5*cap); step_rms=min(step_rms,cap); row['reaction_gradient_sign_change']=True
        if step_rms<1e-10:
            row['stalled']=True; hist.append(row); prev_mode=mode2; prev_q=q.copy(); break
        direction=mode2 if coeff>=0 else -mode2
        qnext=sp.exp_perturb(q,direction,step_rms)
        Eafter,_=sm.fg(qnext); row['newton_raw_rms']=raw_rms; row['reaction_step_rms']=step_rms; row['energy_after_step']=float(Eafter)
        print(f'  step raw_rms={raw_rms:.6g} used={step_rms:.6g} cap={cap:.6g} Eafter={Eafter:.12f}',flush=True)
        hist.append(row); prev_mode=mode2; prev_q=q.copy(); prev_g0=g0; q=qnext
    E,gq=sm.fg(q); gp=gq/sm.physical_scale(q); grms=float(np.linalg.norm(gp)/math.sqrt(2*N))
    vals,V,Qrot,rows,c=final_class(q,10); total_calls+=c; neg=int(np.sum(vals<-1e-3))
    # Track the final reaction mode against the last continuation direction.
    ref=None if prev_mode is None else transport_mode(prev_q,q,prev_mode)
    j,lam,mode,W=select_tracked(vals,V,Qrot,ref); gproj=hy.physical_grad(q); gproj-=Qrot@(Qrot.T@gproj); g0=float(gproj@mode)
    print(f'FINAL E={E:.12f} grad={grms:.7g} neg={neg} tracked_j={j} lambda={lam:+.9g} g0={g0:+.6g}',flush=True)
    out={'seed_json':str(args.seed_json),'final_energy':float(E),'final_gradient_rms':grms,'negative_internal_modes_below_-1e-3':neg,
         'final_tracked_mode_index':j,'final_tracked_mode_eigenvalue':lam,'final_reaction_gradient':g0,'history':hist,
         'hessian_gradient_calls':total_calls,'final_modes':rows,'saddle_points':sm.vars_to_xyz(q)[0].tolist(),
         'eigenvectors_physical':[V[:,k].tolist() for k in range(V.shape[1])]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
