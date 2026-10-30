#!/usr/bin/env python3
"""Stage the release of a defect-reducing 21->20 scaffold.

Earlier searches cross a Delaunay 21->20 boundary, hold all four quadrilateral
vertices fixed while the other 956 points reorganize, then release all four at
once. Every e545 test healed back to 21 dislocations. This experiment tests a
different interface: release one scaffold vertex at a time, fully relaxing the
currently free coordinates after each release, and branch over release order.
The beam keeps distinct low-energy 20-dislocation intermediates, so the full
release is reached through adapted 20-topology states instead of one abrupt
constraint removal.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed, stable_relax_q
from search_e564_scaffolded_flip import families,fixed_relax
from search_e564_defect_flip_parallel import topology,perturb


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}

def ndisl(cc): return int(cc.get('7',0))

def distinct_push(rows,node,beam,tol=2e-6):
    # At fixed release depth, equal-energy/equal-topology descendants are almost
    # always the same basin. Preserve different fixed sets and release histories
    # only when they lead to numerically distinct energies.
    for r in rows:
        if r['fixed']==node['fixed'] and r['coord_counts']==node['coord_counts'] and abs(r['energy']-node['energy'])<tol:
            if node['energy']<r['energy']: r.update(node)
            return
    rows.append(node); rows.sort(key=lambda z:(ndisl(z['coord_counts'])!=20,z['energy'])); del rows[beam:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--family',type=int,required=True); ap.add_argument('--multiplier',type=float,required=True)
    ap.add_argument('--stage-maxiter',type=int,default=1000); ap.add_argument('--final-maxiter',type=int,default=2400)
    ap.add_argument('--beam',type=int,default=10); ap.add_argument('--out',required=True); args=ap.parse_args()
    meta,x0=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x0); E0,_=sm.fg(q0)
    fam=families(x0)
    if not 0<=args.family<len(fam): raise RuntimeError(f'family {args.family} outside {len(fam)}: {fam}')
    t,quad=fam[args.family]; quad=tuple(map(int,quad)); fixed0=tuple(sorted(quad))
    start=perturb(x0,quad,t*args.multiplier,'balanced'); qstart=sm.xyz_to_vars(start)
    Es,_=sm.fg(qstart); Efix,raw,qfix,xfix,nit,ok,msg=fixed_relax(qstart,list(fixed0),args.stage_maxiter); ccfix=counts(xfix)
    print(f'BASE seed={E0:.12f} family={args.family} t={t:.9g} m={args.multiplier:g} start={Es:.9f}',flush=True)
    print(f'ALL_FIXED E={Efix:.12f} cc={ccfix} nit={nit} ok={ok}',flush=True)
    root={'energy':Efix,'coord_counts':ccfix,'fixed':list(fixed0),'released':[],'q':qfix,'points':xfix.tolist(),'nit':nit,'success':ok}
    levels=[{'depth':0,'nodes':[{k:v for k,v in root.items() if k!='q'}]}]
    frontier=[root]
    for depth in range(1,len(fixed0)+1):
        cand=[]
        for node in frontier:
            fixed=tuple(node['fixed'])
            for v in fixed:
                rem=tuple(i for i in fixed if i!=v)
                E,raw,q,x,nit,ok,msg=fixed_relax(node['q'],list(rem),args.stage_maxiter)
                cc=counts(x); child={'energy':E,'coord_counts':cc,'fixed':list(rem),'released':node['released']+[v],
                    'q':q,'points':x.tolist(),'nit':nit,'success':ok,'message':msg}
                print(f'DEPTH {depth} release={child["released"]} fixed={list(rem)} E={E:.12f} cc={cc} nit={nit}',flush=True)
                distinct_push(cand,child,args.beam)
        # Prefer 20-dislocation states, but if none survive retain the best other
        # states as evidence of where the staged path heals.
        twenty=[z for z in cand if ndisl(z['coord_counts'])==20]
        frontier=(twenty if twenty else cand)[:args.beam]
        levels.append({'depth':depth,'nodes':[{k:v for k,v in z.items() if k!='q'} for z in frontier]})
        if not frontier: break
    finals=[]
    # Independently polish every surviving fully released node. If the last
    # staged fixed_relax already had no fixed vertices this is a second check.
    for node in frontier:
        if node['fixed']: continue
        q=sm.xyz_to_vars(np.asarray(node['points'],float))
        E,raw,x,nit,ok,msg=stable_relax_q(q,maxiter=args.final_maxiter); cc=counts(x)
        r={'energy':E,'coord_counts':cc,'released':node['released'],'nit':nit,'success':ok,'message':msg,'points':x.tolist()}
        finals.append(r); print(f'FINAL order={r["released"]} E={E:.12f} cc={cc} nit={nit}',flush=True)
    finals.sort(key=lambda z:(ndisl(z['coord_counts'])!=20,z['energy']))
    out={'seed_energy':E0,'family':args.family,'threshold':float(t),'quad':list(quad),'multiplier':args.multiplier,
         'start_energy':Es,'all_fixed_energy':Efix,'all_fixed_coord':ccfix,'levels':levels,'finals':finals,
         'surviving_20':[z for z in finals if ndisl(z['coord_counts'])==20]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if out['surviving_20']:
        p=pathlib.Path(args.out).with_suffix('.best20.json'); p.write_text(json.dumps(out['surviving_20'][0],separators=(',',':'))+'\n')
        print('SURVIVING20',out['surviving_20'][0]['energy'],'saved',p,flush=True)

if __name__=='__main__': main()
