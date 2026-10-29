#!/usr/bin/env python3
"""Edge-track a basin boundary inside an index-2 Thomson unstable manifold.

For C, the smallest-amplitude negative-doublet portrait has phase 40 deg -> B
and 45 deg -> D.  We first bisect that phase interval using fully relaxed basin
labels.  The resulting point lies exponentially close to the B/D basin boundary.
A long Riemannian gradient descent from this boundary shadows its stable manifold
and approaches the intervening index-1 edge state before roundoff eventually
selects one basin.  The minimum-gradient point along the trajectory is saved as
a saddle seed.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_seed_c3_negative_pair as cp
import string_record_neighbor as sr
from search_from_seed_modes import load_seed,stable_relax_q

N=960

def classify(q,bE,dE):
    E,raw,x,nit,ok,msg=stable_relax_q(q,2200)
    label='B' if abs(E-bE)<abs(E-dE) else 'D'
    return label,E,x,nit,ok

def build_pair(q,fd=3e-6):
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    rng=np.random.default_rng(9607001); v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=6,which='SA',tol=1e-5,maxiter=800,ncv=40,v0=v0); o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    pair=V[:,:2].copy(); pair-=Q@(Q.T@pair); pair,_=np.linalg.qr(pair)
    pair,M,resid,ai,ac,maperr=cp.canonicalize_pair_near(pair,q)
    return vals,pair,M,resid,maperr

def phase_q(q0,pair,phase_deg,amp):
    a=math.radians(phase_deg); d=math.cos(a)*pair[:,0]+math.sin(a)*pair[:,1]; d/=np.linalg.norm(d)
    return sp.exp_perturb(q0,d,amp)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--b-json',required=True); ap.add_argument('--d-json',required=True)
    ap.add_argument('--phase-lo',type=float,default=40.0); ap.add_argument('--phase-hi',type=float,default=45.0); ap.add_argument('--amp',type=float,default=0.0015)
    ap.add_argument('--bisect',type=int,default=18); ap.add_argument('--flow-steps',type=int,default=5000); ap.add_argument('--eta',type=float,default=0.00035)
    ap.add_argument('--max-step',type=float,default=0.00010); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x0=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x0); E0,g0=sm.fg(q0); vals,pair,M,resid,maperr=build_pair(q0)
    b=json.loads(pathlib.Path(args.b_json).read_text()); d=json.loads(pathlib.Path(args.d_json).read_text()); bE=float(b.get('energy',b.get('raw_absolute_energy'))); dE=float(d.get('energy',d.get('raw_absolute_energy')))
    lo,hi=args.phase_lo,args.phase_hi; qlo=phase_q(q0,pair,lo,args.amp); qhi=phase_q(q0,pair,hi,args.amp)
    llo,Elo,_,_,_=classify(qlo,bE,dE); lhi,Ehi,_,_,_=classify(qhi,bE,dE)
    print(f'C={E0:.12f} eig={vals[:3].tolist()} lo={lo} -> {llo}/{Elo:.12f} hi={hi} -> {lhi}/{Ehi:.12f}',flush=True)
    if {llo,lhi}!={'B','D'}: raise RuntimeError('initial phases do not bracket B/D')
    hist_b=[]
    for it in range(args.bisect):
        mid=0.5*(lo+hi); qm=phase_q(q0,pair,mid,args.amp); lab,Em,_,nit,ok=classify(qm,bE,dE)
        hist_b.append({'iteration':it,'phase_deg':mid,'label':lab,'relaxed_energy':Em,'nit':nit,'success':ok})
        print(f'bisect={it:02d} phase={mid:.12f} -> {lab} E={Em:.12f}',flush=True)
        if lab==llo: lo=mid; qlo=qm
        else: hi=mid; qhi=qm
    phase=0.5*(lo+hi); q=phase_q(q0,pair,phase,args.amp); x,_,_=sm.vars_to_xyz(q)
    best={'grad_rms':1e300}; flow=[]; rising=0
    for it in range(args.flow_steps+1):
        E,g=sr.energy_grad(x); grms=float(np.sqrt(np.mean(np.sum(g*g,axis=1))))
        if grms<best['grad_rms']:
            best={'iteration':it,'energy':E,'grad_rms':grms,'points':x.copy()}; rising=0
        elif best['grad_rms']<2e-3 and grms>best['grad_rms']*4: rising+=1
        if it%25==0 or it==args.flow_steps:
            print(f'flow={it:04d} E={E:.12f} grad={grms:.7g} best={best["grad_rms"]:.7g}@{best["iteration"]}',flush=True)
            flow.append({'iteration':it,'energy':E,'gradient_rms':grms,'best_gradient_rms':best['grad_rms']})
        if rising>=20:
            print('stopping after clear departure from edge state',flush=True); break
        if it==args.flow_steps: break
        x,_=sr.capped_descent(x,g,args.eta,args.max_step)
    bx=best.pop('points')
    out={'seed_json':str(args.seed_json),'seed_energy':E0,'negative_eigenvalues':[float(vals[0]),float(vals[1])],
         'pair_matrix':M.tolist(),'pair_subspace_residual':resid,'mapping_max_error':maperr,'amp':args.amp,
         'phase_bracket':[lo,hi],'boundary_phase_deg':phase,'bisection':hist_b,'flow':flow,'best':best,
         'saddle_points':bx.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__': main()
