#!/usr/bin/env python3
"""Screened C3-preserving crossover between the live record and a distinct C3 minimum.

This combines the two upstream ingredients that succeeded separately for p007:
C3 reduced-space exploration (current record) and cut-and-splice genetic global
recombination (previous D2 record).  We deterministically reproduce a known
non-record C3 minimum from the earlier smooth-field campaign, then generate
children by selecting whole C3 orbits from the two parents with a C3-invariant
wavy cut score z + a sin(theta)^2 cos(3(phi-phase)). Parent B may also be
rotated by an arbitrary azimuth, which commutes with C3.

Children are screened for close pairs and raw energy; only the best few are
fully relaxed in exact C3 orbit space with a stable pair-energy-difference
objective. Requires numpy/scipy.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.optimize import minimize

import search_c3_smooth as c3

PI=math.pi
NREP=320
N=960
TRI=np.triu_indices(N,1)


def full_from_reps(reps):
    return c3.vars_to_full(c3.xyz_to_vars(reps))[0]

def raw_energy(reps):
    x=full_from_reps(reps); d=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*d,1e-300); np.fill_diagonal(r2,np.inf)
    return float(np.sum(np.asarray((1/np.sqrt(r2))[TRI],np.longdouble),dtype=np.longdouble))
def min_pair(reps):
    x=full_from_reps(reps); d=x@x.T; np.fill_diagonal(d,-1); return math.sqrt(max(0.,2-2*float(np.max(d))))

def terms_grad(v):
    x,dth,dph=c3.vars_to_full(v); dots=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0); gc=w@x-np.sum(w,axis=1)[:,None]*x
    gt=np.sum(gc*dth,axis=1).reshape(3,-1).sum(axis=0); gp=np.sum(gc*dph,axis=1).reshape(3,-1).sum(axis=0)
    return inv[TRI],np.column_stack([gt,gp]).ravel()
def stable_polish(v0,maxiter=1000):
    ref,g0=terms_grad(v0); ref=np.asarray(ref,np.longdouble); E0=float(np.sum(ref,dtype=np.longdouble))
    def fg(v):
        t,g=terms_grad(v); return float(np.sum(np.asarray(t,np.longdouble)-ref,dtype=np.longdouble)),g
    bounds=[(1e-7,PI-1e-7),(None,None)]*NREP
    r=minimize(fg,v0,jac=True,method='L-BFGS-B',bounds=bounds,options={'maxiter':maxiter,'gtol':1e-9,'ftol':1e-15,'maxls':60,'maxcor':30})
    de,_=fg(r.x); return E0+de,r.x,int(r.nit),bool(r.success)
def reproduce_parent(base_v,seed,target_trial):
    rng=np.random.default_rng(seed); scales=np.geomspace(0.008,0.20,9); last=None
    for t in range(target_trial+1):
        scale=float(scales[t%len(scales)]*math.exp(rng.normal(0.,0.18)))
        start=c3.perturb(base_v,rng,scale)
        # use the same historical absolute polish first to reproduce the basin,
        # then stable-polish the result for accurate ranking.
        r=c3.polish(start); E,v,nit,ok=stable_polish(r.x,1200); last=(E,v,scale,int(r.nit)+nit,ok)
        print(f'parent_trial={t} scale={scale:.5f} E={E:.12f}',flush=True)
    return last

def rep_angles(reps):
    z=reps[:,2]; phi=np.arctan2(reps[:,1],reps[:,0]); st2=np.maximum(0.,1-z*z); return z,phi,st2
def rotate_z(reps,a):
    return c3.rz(reps,a)
def child_from(P,Q,rng):
    # arbitrary z rotation of Q preserves its C3 point group
    twist=float(rng.uniform(0.,2*PI/3)); Qr=rotate_z(Q,twist)
    amp=float(rng.uniform(-0.55,0.55)); phase=float(rng.uniform(0.,2*PI/3)); k=int(rng.choice([80,110,140,160,180,210,240]))
    zP,pP,sP=rep_angles(P); zQ,pQ,sQ=rep_angles(Qr)
    scoreP=zP+amp*sP*np.cos(3*(pP-phase)); scoreQ=zQ+amp*sQ*np.cos(3*(pQ-phase))
    iP=np.argpartition(scoreP,-k)[-k:]; iQ=np.argpartition(scoreQ,NREP-k-1)[:NREP-k]
    reps=np.vstack([P[iP],Qr[iQ]])
    return reps,{'twist':twist,'cut_amp':amp,'cut_phase':phase,'k_from_record':k}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--parent-seed',type=int,required=True); ap.add_argument('--target-trial',type=int,required=True)
    ap.add_argument('--seed',type=int,required=True); ap.add_argument('--children',type=int,default=60); ap.add_argument('--relax-top',type=int,default=6); ap.add_argument('--out',required=True)
    args=ap.parse_args(); root=pathlib.Path(args.few_shots); live_score,shot=c3.find_live(root); pts=c3.load_cert(shot/'certificate.json')
    P=c3.c3_representatives(pts); base_v=c3.xyz_to_vars(P); baseE,base_v,_,_=stable_polish(base_v,1200); P=c3.vars_to_full(base_v)[0][:NREP]
    pE,pv,pscale,pnit,pok=reproduce_parent(base_v,args.parent_seed,args.target_trial); Q=c3.vars_to_full(pv)[0][:NREP]
    print(f'live_score={live_score:.10f} record_c3={baseE:.12f} parent2={pE:.12f} delta_parent={pE-baseE:+.9g}',flush=True)
    if abs(pE-baseE)<1e-5: raise RuntimeError('selected parent collapsed to record; choose a distinct target trial')
    rng=np.random.default_rng(args.seed); safe=[]
    for i in range(args.children):
        reps,meta=child_from(P,Q,rng); md=min_pair(reps)
        if md<0.052: continue
        E=raw_energy(reps); safe.append((E,md,i,reps,meta))
    safe.sort(key=lambda t:t[0]); print(f'children={args.children} safe={len(safe)}',flush=True)
    for s in safe[:min(10,len(safe))]: print(f'screen i={s[2]} E={s[0]:.9f} md={s[1]:.5f} meta={s[4]}',flush=True)
    rows=[]; best=baseE; bestv=None
    for rank,s in enumerate(safe[:args.relax_top]):
        E0,md,i,reps,meta=s; E,v,nit,ok=stable_polish(c3.xyz_to_vars(reps),1500)
        row={'rank':rank,'screen_index':i,'start_energy':E0,'min_pair':md,'energy':E,'delta_vs_live':E-live_score,'nit':nit,'success':ok,**meta}; rows.append(row)
        print(f'relax rank={rank} E={E:.12f} dlive={E-live_score:+.9g} nit={nit} meta={meta}',flush=True)
        if E<best: best=E; bestv=v.copy()
    bestpts=c3.vars_to_full(bestv)[0] if bestv is not None else None
    out={'live_score':live_score,'live_shot':str(shot.relative_to(root)),'record_c3_energy':baseE,
         'parent_seed':args.parent_seed,'target_trial':args.target_trial,'parent2_energy':pE,'parent2_scale':pscale,
         'children':args.children,'safe_count':len(safe),'rows':rows,'best_float_energy':best,'best_delta_vs_live':best-live_score,
         'best_points':bestpts.tolist() if bestpts is not None and best<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
