#!/usr/bin/env python3
"""Couple the e564 global C3-breaking soft doublet to a local 21->20 scar flip.

Pure low-mode perturbations and pure Delaunay-flip perturbations probe different
parts of the reaction coordinate.  This search aligns a direction in the lowest
C3 doublet with the infinitesimal local balanced flip field of one scar family,
pre-deforms the whole configuration along that soft direction, then recomputes
and crosses the local Delaunay boundary before full unconstrained relaxation.
"""
from __future__ import annotations
import argparse, json, math, pathlib
from collections import Counter
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import load_seed, stable_relax_q
from search_e564_defect_flip_parallel import (
    topology, defect_reducing_flips, threshold, perturb
)

N=960


def flip_field(q,quad):
    """Infinitesimal balanced-flip tangent field in physical coordinates."""
    x,eth,eph=sp.tangent_bases(q)
    u,v,a,b=quad
    y=np.zeros((len(x),2),dtype=float)
    def tangent_to(p,t):
        z=t-float(np.dot(t,p))*p
        return z/np.linalg.norm(z)
    for i,j,sg in ((a,b,1.0),(b,a,1.0),(u,v,-1.0),(v,u,-1.0)):
        dx=sg*tangent_to(x[i],x[j])
        y[i,0]=float(dx@eth[i]); y[i,1]=float(dx@eph[i])
    return y.ravel()


def find_families(x):
    rows=[]
    for q in defect_reducing_flips(x):
        t=threshold(x,q,'balanced')
        if t is not None: rows.append((t,q))
    rows.sort()
    reps=[]
    for t,q in rows:
        if any(abs(t-s)<3e-5 for s,_ in reps): continue
        reps.append((t,q))
    if len(reps)!=3:
        raise RuntimeError(f'expected 3 flip families, got {reps}')
    return reps


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--family',type=int,choices=[0,1,2],required=True)
    ap.add_argument('--soft-sign',type=int,choices=[-1,1],required=True)
    ap.add_argument('--soft-amps',default='0.002,0.004,0.008,0.014')
    ap.add_argument('--flip-mults',default='1.02,1.15,1.40,1.80')
    ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--maxiter',type=int,default=1800); ap.add_argument('--out',required=True)
    args=ap.parse_args()

    meta,x0=load_seed(args.seed_json); q0=sm.xyz_to_vars(x0); E0,g0=sm.fg(q0)
    fams=find_families(x0); base_thr,quad=fams[args.family]

    H,raw,Q,calls=sm.build_hessian(q0,args.fd_step,1e6)
    rng=np.random.default_rng(564539 + args.family)
    v0=rng.normal(size=len(q0)); v0-=Q@(Q.T@v0)
    vals,V=eigsh(H,k=6,which='SA',tol=1e-6,maxiter=800,ncv=32,v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    pair=V[:,:2].copy()
    for j in range(2): pair[:,j]-=Q@(Q.T@pair[:,j])
    pair,_=np.linalg.qr(pair)
    yf=flip_field(q0,quad); yf-=Q@(Q.T@yf)
    proj=pair@(pair.T@yf)
    frac=float(proj@proj/max(yf@yf,1e-300))
    if np.linalg.norm(proj)<1e-12: raise RuntimeError('flip has negligible soft-pair projection')
    soft=proj/np.linalg.norm(proj)
    print(f'family={args.family} quad={quad} base_thr={base_thr:.9g} sign={args.soft_sign:+d}',flush=True)
    print(f'lambdas={vals[:6].tolist()} flip_pair_fraction={frac:.7g}',flush=True)

    samps=[float(s) for s in args.soft_amps.split(',') if s]
    mults=[float(s) for s in args.flip_mults.split(',') if s]
    rows=[]; basins=[]
    for sa in samps:
        qs=sp.exp_perturb(q0,args.soft_sign*soft,sa)
        xs,_,_=sm.vars_to_xyz(qs)
        degs,_=topology(xs); pre_coord=Counter(degs.tolist())
        # Keep the same labelled scar quartet and resolve its new local boundary.
        th=threshold(xs,quad,'balanced')
        Es,_=sm.fg(qs)
        print(f'SOFT a={sa:.5g} E={Es:.12f} coord={dict(pre_coord)} threshold={th}',flush=True)
        if th is None:
            rows.append({'soft_amp':sa,'soft_sign':args.soft_sign,'threshold':None,
                         'pre_energy':Es,'pre_coord':{str(k):int(v) for k,v in pre_coord.items()}})
            continue
        for mult in mults:
            start=perturb(xs,quad,th*mult,'balanced')
            ds,_=topology(start); start_coord=Counter(ds.tolist()); qstart=sm.xyz_to_vars(start)
            Estart,_=sm.fg(qstart)
            e,rawE,z,nit,ok,msg=stable_relax_q(qstart,maxiter=args.maxiter)
            df,_=topology(z); coord=Counter(df.tolist())
            row={'soft_amp':sa,'soft_sign':args.soft_sign,'threshold':th,'flip_mult':mult,
                 'pre_energy':Es,'start_energy':Estart,
                 'start_coord':{str(k):int(v) for k,v in sorted(start_coord.items())},
                 'energy':e,'raw_energy':rawE,'nit':nit,'success':ok,'message':msg,
                 'coord':{str(k):int(v) for k,v in sorted(coord.items())}}
            rows.append(row)
            print(f"DONE a={sa:.4g} mult={mult:.3g} start={Estart:.9f} E={e:.12f} coord={row['coord']}",flush=True)
            if not any(abs(e-b['energy'])<2e-6 and row['coord']==b['coord'] for b in basins):
                b=dict(row); b['points']=z.tolist(); basins.append(b); basins.sort(key=lambda r:r['energy']); basins=basins[:10]

    good=[r for r in rows if 'energy' in r]
    best=min((r['energy'] for r in good),default=float('inf'))
    out={'seed_energy':E0,'family':args.family,'quad':list(quad),'base_threshold':base_thr,
         'soft_sign':args.soft_sign,'soft_amps':samps,'flip_multipliers':mults,
         'eigenvalues':[float(v) for v in vals],'flip_pair_fraction':frac,
         'hessian_gradient_calls':calls['n'],'rows':rows,'lowest_distinct_basins':basins,
         'best_energy':best}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
