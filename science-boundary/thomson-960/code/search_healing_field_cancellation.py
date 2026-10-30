#!/usr/bin/env python3
"""Oppose the coherent 20->21 healing field after a scaffolded defect flip.

For an e545 21-dislocation minimum, first cross one defect-reducing Delaunay
boundary and relax with the four flip vertices fixed, producing an adapted
20-dislocation scaffold state X20.  Abrupt release returns to e545.  Treat the
finite displacement field log_X20(e545) as the observed nonlinear healing
field h, then extrapolate from X20 along -alpha*h before unconstrained release.
The outside-quad variant freezes h to zero on the four scaffold vertices while
reversing the global elastic response elsewhere.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed, stable_relax_q
from search_e553_event_composition import kabsch,sphere_log,sphere_exp
from search_e564_scaffolded_flip import families,fixed_relax
from search_e564_defect_flip_parallel import topology,perturb


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}

def rms(v): return float(np.sqrt(np.mean(np.sum(v*v,axis=1))))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--family',type=int,required=True); ap.add_argument('--multiplier',type=float,default=1.05)
    ap.add_argument('--field',choices=['full','outside-quad'],required=True)
    ap.add_argument('--alphas',default='0.15,0.3,0.5,0.8,1.2,1.8,2.5,3.5')
    ap.add_argument('--fixed-maxiter',type=int,default=1200); ap.add_argument('--release-maxiter',type=int,default=2600)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x21=load_seed(pathlib.Path(args.seed_json)); q21=sm.xyz_to_vars(x21); E21,_=sm.fg(q21)
    fam=families(x21)
    if not 0<=args.family<len(fam): raise RuntimeError(f'family {args.family} outside {len(fam)}')
    t,quad=fam[args.family]; quad=tuple(map(int,quad))
    start=perturb(x21,quad,t*args.multiplier,'balanced'); qstart=sm.xyz_to_vars(start); Es,_=sm.fg(qstart)
    E20,raw20,q20,x20,nit20,ok20,msg20=fixed_relax(qstart,list(quad),args.fixed_maxiter); cc20=counts(x20)
    # Align the known healed endpoint by one rigid rotation only; point labels
    # remain identical because x20 was generated continuously from x21.
    R=kabsch(x21,x20); healed=x21@R; h=sphere_log(x20,healed)
    hfull=h.copy()
    if args.field=='outside-quad': h[list(quad)]=0.0
    print(f'SEED {E21:.12f} family={args.family} t={t:.9g} mult={args.multiplier:g} field={args.field}',flush=True)
    print(f'FIXED20 {E20:.12f} cc={cc20} heal_rms_full={rms(hfull):.7g} used_rms={rms(h):.7g}',flush=True)
    rows=[]; basins=[]; best20=None
    for a in [float(x) for x in args.alphas.split(',') if x]:
        xs=sphere_exp(x20,-a*h); ccs=counts(xs); qs=sm.xyz_to_vars(xs); Estart,_=sm.fg(qs)
        E,raw,x,nit,ok,msg=stable_relax_q(qs,maxiter=args.release_maxiter); cc=counts(x)
        r={'alpha':a,'start_energy':Estart,'start_coord':ccs,'energy':E,'coord_counts':cc,'nit':nit,'success':ok,'message':msg}
        rows.append(r); print(f'A {a:g} start={Estart:.9f} {ccs} -> E={E:.12f} {cc} nit={nit} ok={ok}',flush=True)
        if not any(abs(E-b['energy'])<2e-6 and cc==b['coord_counts'] for b in basins):
            basins.append(dict(r,points=x.tolist())); basins.sort(key=lambda z:z['energy'])
        if cc.get('7')==20 and (best20 is None or E<best20['energy']): best20=dict(r,points=x.tolist())
    out={'seed_energy':E21,'family':args.family,'threshold':float(t),'quad':list(quad),'multiplier':args.multiplier,'field':args.field,
         'fixed20_energy':E20,'fixed20_coord':cc20,'healing_rms_full':rms(hfull),'healing_rms_used':rms(h),'rows':rows,
         'distinct_basins':basins[:16],'best_20_basin':best20}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best20 is not None:
        p=pathlib.Path(args.out).with_suffix('.best20.json'); p.write_text(json.dumps(best20,separators=(',',':'))+'\n'); print('SURVIVING20',best20['energy'],'saved',p,flush=True)

if __name__=='__main__': main()
