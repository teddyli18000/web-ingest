#!/usr/bin/env python3
"""Continue a same-count Delaunay glide from a fixed scaffold to zero restraint.

For live-record glide moves the coordination counts are identical before and
after the flip, so branch identity must be tracked by the Delaunay diagonal,
not by 5/6/7 counts.  Start just beyond an exact flip threshold, adapt all
other particles with the quad fixed, then replace the hard constraint by a
spherical harmonic restraint and decrease its stiffness continuously.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed,stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb,flipped
from search_e564_scaffolded_flip import fixed_relax
from search_scaffold_restraint_homotopy import restraint_relax,parse_schedule


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json'); ap.add_argument('--quad',required=True)
    ap.add_argument('--pattern',default='balanced'); ap.add_argument('--multiplier',type=float,default=1.003)
    ap.add_argument('--schedule',default='3000,1000,300,100,30,10,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=1800); ap.add_argument('--stage-maxiter',type=int,default=1800)
    ap.add_argument('--final-maxiter',type=int,default=3600); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    quad=tuple(int(z) for z in args.quad.split(','))
    if len(quad)!=4: raise ValueError('quad needs u,v,a,b')
    meta,x0=load_seed(pathlib.Path(args.seed_json)); q0=sm.xyz_to_vars(x0); E0,_=sm.fg(q0)
    th=threshold(x0,quad,args.pattern)
    if th is None: raise RuntimeError('requested flip has no finite threshold')
    start=perturb(x0,quad,th*args.multiplier,args.pattern); qstart=sm.xyz_to_vars(start); Es,_=sm.fg(qstart)
    Efix,rawfix,qfix,xfix,nfix,okfix,msgfix=fixed_relax(qstart,list(quad),args.fixed_maxiter)
    print('SEED',f'{E0:.12f}','threshold',th,'start',f'{Es:.12f}','start_flipped',flipped(start,quad),flush=True)
    print('FIXED',f'{Efix:.12f}','flipped',flipped(xfix,quad),'cc',counts(xfix),'nit',nfix,'ok',okfix,flush=True)
    target=xfix.copy(); q=qfix.copy(); rows=[]; last_flipped=None; first_healed=None
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,quad,kappa,args.stage_maxiter)
        isflip=bool(flipped(x,quad)); cc=counts(x)
        row={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),'raw_energy':float(raw),
             'flipped':isflip,'coord_counts':cc,'anchor_rms':arms,'penalty':pen,'nit':nit,'success':ok,'message':msg}
        rows.append(row)
        print('K',kappa,'E',f'{E:.12f}','dLive',f'{E-args.live_score:+.9g}','flipped',isflip,
              'cc',cc,'anchor',f'{arms:.6g}','nit',nit,'ok',ok,flush=True)
        if isflip: last_flipped={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                                 'coord_counts':cc,'anchor_rms':arms,'points':x.tolist()}
        elif first_healed is None: first_healed={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                                                 'coord_counts':cc,'anchor_rms':arms}
    Ef,rawf,xf,nf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter)
    final={'energy':float(Ef),'delta_live':float(Ef-args.live_score),'raw_energy':float(rawf),
           'flipped':bool(flipped(xf,quad)),'coord_counts':counts(xf),'nit':int(nf),'success':bool(okf),
           'message':str(msgf),'points':xf.tolist()}
    print('FINAL',f'{Ef:.12f}','dLive',f'{Ef-args.live_score:+.9g}','flipped',final['flipped'],'cc',final['coord_counts'],flush=True)
    out={'seed_energy':float(E0),'quad':list(quad),'pattern':args.pattern,'threshold':float(th),'multiplier':args.multiplier,
         'start_energy':float(Es),'fixed_energy':float(Efix),'fixed_flipped':bool(flipped(xfix,quad)),
         'fixed_coord':counts(xfix),'schedule':parse_schedule(args.schedule),'rows':rows,
         'last_flipped_state':last_flipped,'first_healed_state':first_healed,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if final['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(final,separators=(',',':'))+'\n')

if __name__=='__main__': main()
