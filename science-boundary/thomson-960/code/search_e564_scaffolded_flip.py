#!/usr/bin/env python3
"""Scaffold a 21->20 Thomson defect flip before releasing it.

A direct post-flip configuration may heal before the surrounding 956 points can
cooperatively reorganize. This search crosses one defect-reducing Delaunay
boundary, temporarily holds the four quadrilateral vertices fixed while all
other points minimize, then releases all 960 points. Descendant 21-dislocation
minima need not retain the same number of non-equivalent flippable scar families,
so family discovery is data-driven.
"""
from __future__ import annotations
import argparse,json,math,pathlib
from collections import Counter
import numpy as np
from scipy.optimize import minimize

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed, stable_relax_q, _geometry_and_gradient
from search_e564_defect_flip_parallel import topology, defect_reducing_flips, threshold, perturb

PI=math.pi


def families(x):
    rows=sorted((threshold(x,q,'balanced'),q) for q in defect_reducing_flips(x))
    reps=[]
    for t,q in rows:
        if t is None: continue
        # Symmetry-equivalent copies differ at ~1e-8, while distinct descendant
        # families can be separated by only a few 1e-5 rad.
        if any(abs(t-s)<1e-5 for s,_ in reps): continue
        reps.append((t,q))
    if not reps: raise RuntimeError('no defect-reducing 21->20 flip family found')
    return reps


def fixed_relax(qstart,fixed_points,maxiter=1400):
    n=len(qstart)//2; tri=np.triu_indices(n,1)
    _,inv0,_=_geometry_and_gradient(qstart)
    ref=np.asarray(inv0[tri],dtype=np.longdouble); ref_abs=float(np.sum(inv0[tri],dtype=np.float64))
    fixed=set(int(i) for i in fixed_points)
    free_coords=np.array([2*i+j for i in range(n) if i not in fixed for j in (0,1)],dtype=int)
    base=qstart.copy(); z0=base[free_coords].copy()
    def obj(z):
        q=base.copy(); q[free_coords]=z
        _x,inv,g=_geometry_and_gradient(q)
        delta=np.sum(np.asarray(inv[tri],dtype=np.longdouble)-ref,dtype=np.longdouble)
        return float(delta),g[free_coords]
    bounds=[(1e-8,PI-1e-8) if c%2==0 else (None,None) for c in free_coords]
    r=minimize(obj,z0,jac=True,method='L-BFGS-B',bounds=bounds,
               options={'maxiter':maxiter,'gtol':1e-9,'ftol':1e-15,'maxls':60,'maxcor':40})
    q=base.copy(); q[free_coords]=r.x; delta,_=obj(r.x); x,_,_=sm.vars_to_xyz(q); raw,_=sm.fg(q)
    return ref_abs+delta,float(raw),q,x,int(r.nit),bool(r.success),str(r.message)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--family',type=int,required=True)
    ap.add_argument('--multipliers',default='1.05,1.20,1.50,2.00')
    ap.add_argument('--fixed-maxiter',type=int,default=1400); ap.add_argument('--release-maxiter',type=int,default=2200)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x0=load_seed(args.seed_json); E0,_=sm.fg(sm.xyz_to_vars(x0))
    fam=families(x0)
    if args.family<0 or args.family>=len(fam): raise RuntimeError(f'family index {args.family} outside {len(fam)} discovered families: {fam}')
    t,q=fam[args.family]; fixed=list(q)
    rows=[]; basins=[]
    print(f'families={[(float(a),list(b)) for a,b in fam]}',flush=True)
    print(f'family={args.family} quad={q} threshold={t:.9g}',flush=True)
    for m in [float(s) for s in args.multipliers.split(',') if s]:
        start=perturb(x0,q,t*m,'balanced'); ds,_=topology(start); sc=Counter(ds.tolist())
        qstart=sm.xyz_to_vars(start); Estart,_=sm.fg(qstart)
        Ef,rawf,qf,xf,nitf,okf,msgf=fixed_relax(qstart,fixed,args.fixed_maxiter)
        df,_=topology(xf); fc=Counter(df.tolist())
        Er,rawr,xr,nitr,okr,msgr=stable_relax_q(qf,maxiter=args.release_maxiter)
        dr,_=topology(xr); rc=Counter(dr.tolist())
        row={'multiplier':m,'start_energy':Estart,'start_coord':{str(k):int(v) for k,v in sorted(sc.items())},
             'fixed_energy':Ef,'fixed_raw_energy':rawf,'fixed_coord':{str(k):int(v) for k,v in sorted(fc.items())},
             'fixed_nit':nitf,'fixed_success':okf,'fixed_message':msgf,
             'release_energy':Er,'release_raw_energy':rawr,'release_coord':{str(k):int(v) for k,v in sorted(rc.items())},
             'release_nit':nitr,'release_success':okr,'release_message':msgr}
        rows.append(row)
        print(f"m={m:.3g} start={Estart:.9f} fixed={Ef:.12f} {row['fixed_coord']} release={Er:.12f} {row['release_coord']}",flush=True)
        if not any(abs(Er-b['release_energy'])<2e-6 and row['release_coord']==b['release_coord'] for b in basins):
            b=dict(row); b['points']=xr.tolist(); basins.append(b); basins.sort(key=lambda a:a['release_energy']); basins=basins[:8]
    out={'seed_energy':E0,'discovered_families':[{'threshold':float(a),'quad':list(b)} for a,b in fam],
         'family':args.family,'quad':list(q),'threshold':t,'rows':rows,
         'lowest_distinct_release_basins':basins,'best_release_energy':min(r['release_energy'] for r in rows)}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
