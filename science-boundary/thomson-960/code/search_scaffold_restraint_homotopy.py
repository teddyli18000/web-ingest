#!/usr/bin/env python3
"""Continuous release homotopy for a defect-reducing Thomson scaffold.

A 21->20 Delaunay flip can be stabilized while its four quadrilateral vertices
are fixed, but abrupt full release heals back to 21 dislocations.  Replace the
hard constraints by spherical harmonic restraints to the adapted all-fixed
20-dislocation state and continue the restraint stiffness kappa down to zero.
This distinguishes an abrupt-release artifact from a genuine disappearance of
the 20-topology branch at finite restraint.
"""
from __future__ import annotations
import argparse,json,math,pathlib
from collections import Counter
import numpy as np
from scipy.optimize import minimize

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed, stable_relax_q, _geometry_and_gradient
from search_e564_scaffolded_flip import families,fixed_relax
from search_e564_defect_flip_parallel import topology,perturb

PI=math.pi

def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}

def pair_reference(q):
    n=len(q)//2; tri=np.triu_indices(n,1); _,inv,_=_geometry_and_gradient(q)
    return tri,np.asarray(inv[tri],dtype=np.longdouble),float(np.sum(inv[tri],dtype=np.float64))

def restraint_relax(qstart,target_xyz,quad,kappa,maxiter):
    n=len(qstart)//2; tri,ref_terms,ref_abs=pair_reference(qstart); quad=np.asarray(quad,dtype=int)
    targets=np.asarray(target_xyz,dtype=float)[quad]
    def obj(v):
        x,inv,g=_geometry_and_gradient(v)
        delta=np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref_terms,dtype=np.longdouble)
        if kappa>0:
            xx,dth,dph=sm.vars_to_xyz(v)
            sel=xx[quad]; td=targets
            pen=kappa*float(np.sum(1.0-np.sum(sel*td,axis=1)))
            gg=g.reshape(-1,2).copy()
            gg[quad,0] += -kappa*np.sum(td*dth[quad],axis=1)
            gg[quad,1] += -kappa*np.sum(td*dph[quad],axis=1)
            g=gg.ravel()
        else: pen=0.0
        return float(delta)+pen,g
    bounds=[(1e-8,PI-1e-8),(None,None)]*n
    res=minimize(obj,qstart,jac=True,method='L-BFGS-B',bounds=bounds,
                 options={'maxiter':maxiter,'gtol':1e-9,'ftol':1e-15,'maxls':60,'maxcor':40})
    val,_=obj(res.x); x,_,_=sm.vars_to_xyz(res.x); raw,_=sm.fg(res.x)
    # Coulomb energy excludes the restraint. Recompute it by a stable difference
    # from the stage reference so the homotopy can resolve sub-micro changes.
    _,invf,_=_geometry_and_gradient(res.x)
    pair_delta=np.sum(np.asarray(invf[tri],dtype=np.longdouble)-ref_terms,dtype=np.longdouble)
    E=ref_abs+float(pair_delta)
    # Report anchor angular RMS and restraint contribution separately.
    dots=np.clip(np.sum(x[quad]*targets,axis=1),-1.0,1.0)
    ang=np.arccos(dots); anchor_rms=float(np.sqrt(np.mean(ang*ang)))
    penalty=kappa*float(np.sum(1.0-dots)) if kappa>0 else 0.0
    return E,float(raw),res.x,x,int(res.nit),bool(res.success),str(res.message),anchor_rms,penalty

def parse_schedule(s): return [float(x) for x in s.split(',') if x.strip()]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--family',type=int,required=True); ap.add_argument('--multiplier',type=float,required=True)
    ap.add_argument('--schedule',default='3000,1000,300,100,30,10,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=1200); ap.add_argument('--stage-maxiter',type=int,default=1400)
    ap.add_argument('--final-maxiter',type=int,default=2600); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x0=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x0); E0,_=sm.fg(q0)
    fam=families(x0)
    if not 0<=args.family<len(fam): raise RuntimeError(f'family {args.family} outside {len(fam)}')
    t,quad=fam[args.family]; quad=tuple(map(int,quad)); start=perturb(x0,quad,t*args.multiplier,'balanced'); qstart=sm.xyz_to_vars(start); Es,_=sm.fg(qstart)
    Efix,rawfix,qfix,xfix,nitfix,okfix,msgfix=fixed_relax(qstart,list(quad),args.fixed_maxiter); ccfix=counts(xfix)
    print(f'SEED E={E0:.12f} family={args.family} t={t:.9g} mult={args.multiplier:g} start={Es:.9f}',flush=True)
    print(f'FIXED E={Efix:.12f} cc={ccfix} nit={nitfix} ok={okfix}',flush=True)
    target=xfix.copy(); q=qfix.copy(); rows=[]; first_heal=None; last20=None
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,quad,kappa,args.stage_maxiter)
        cc=counts(x); row={'kappa':kappa,'energy':E,'raw_energy':raw,'coord_counts':cc,'anchor_rms':arms,'penalty':pen,'nit':nit,'success':ok,'message':msg}
        rows.append(row); print(f'K {kappa:g} E={E:.12f} cc={cc} anchor={arms:.6g} pen={pen:.6g} nit={nit} ok={ok}',flush=True)
        if cc.get('7')==20: last20={'kappa':kappa,'energy':E,'coord_counts':cc,'points':x.tolist()}
        elif first_heal is None: first_heal={'kappa':kappa,'energy':E,'coord_counts':cc,'anchor_rms':arms}
    # Independent unconstrained stable polish, even if kappa=0 was already used.
    Ef,rawf,xf,nitf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter); ccf=counts(xf)
    final={'energy':Ef,'raw_energy':rawf,'coord_counts':ccf,'nit':nitf,'success':okf,'message':msgf,'points':xf.tolist()}
    print(f'FINAL E={Ef:.12f} cc={ccf} nit={nitf} ok={okf}',flush=True)
    out={'seed_energy':E0,'family':args.family,'threshold':float(t),'quad':list(quad),'multiplier':args.multiplier,
         'start_energy':Es,'all_fixed_energy':Efix,'all_fixed_coord':ccfix,'schedule':parse_schedule(args.schedule),
         'rows':rows,'last_20_state':last20,'first_healed_state':first_heal,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if ccf.get('7')==20:
        p=pathlib.Path(args.out).with_suffix('.best20.json'); p.write_text(json.dumps(final,separators=(',',':'))+'\n'); print('SURVIVING20',Ef,'saved',p,flush=True)

if __name__=='__main__': main()
