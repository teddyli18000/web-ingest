#!/usr/bin/env python3
"""Jointly continue two live-record glide events on different scar triplets.

The soft live-local orbit0 and orbit4 one-glide interfaces are both novel with
respect to the known A/B routes, yet each heals when released alone.  Cross one
representative from each orbit independently just beyond its exact Delaunay
threshold, adapt the remaining 952 particles with both quads fixed, then replace
both hard constraints by a common spherical harmonic restraint and decrease its
stiffness continuously.  Track each Delaunay diagonal separately.

Three C3-relative phases of the orbit4 representative are tested by the workflow;
this script handles one phase.
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


def parse_quad(s):
    q=tuple(int(z) for z in s.split(','))
    if len(q)!=4: raise ValueError('quad must be u,v,a,b')
    return q


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--quad-a',required=True); ap.add_argument('--quad-b',required=True)
    ap.add_argument('--pattern',default='balanced')
    ap.add_argument('--multiplier-a',type=float,default=1.003); ap.add_argument('--multiplier-b',type=float,default=1.003)
    ap.add_argument('--schedule',default='100000,30000,10000,6000,4000,3000,2200,1600,1200,900,700,500,300,200,100,30,10,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=2200); ap.add_argument('--stage-maxiter',type=int,default=1800)
    ap.add_argument('--final-maxiter',type=int,default=4000); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    qa=parse_quad(args.quad_a); qb=parse_quad(args.quad_b)
    if set(qa)&set(qb): raise ValueError('paired quads must be vertex-disjoint')
    meta,x0=load_seed(pathlib.Path(args.seed_json)); E0,_=sm.fg(sm.xyz_to_vars(x0))
    ta=threshold(x0,qa,args.pattern); tb=threshold(x0,qb,args.pattern)
    if ta is None or tb is None: raise RuntimeError(f'finite thresholds required: {ta} {tb}')
    # Quads are disjoint, so sequential perturbation preserves the first crossing.
    start=perturb(x0,qa,ta*args.multiplier_a,args.pattern)
    start=perturb(start,qb,tb*args.multiplier_b,args.pattern)
    if not flipped(start,qa) or not flipped(start,qb):
        raise RuntimeError('failed to cross both requested Delaunay boundaries')
    qstart=sm.xyz_to_vars(start); Estart,_=sm.fg(qstart); fixed=sorted(set(qa)|set(qb))
    Efix,rawfix,qfix,xfix,nfix,okfix,msgfix=fixed_relax(qstart,fixed,args.fixed_maxiter)
    print('SEED',f'{E0:.12f}','THRESHOLDS',ta,tb,'START',f'{Estart:.12f}',counts(start),flush=True)
    print('FIXED',f'{Efix:.12f}','A',flipped(xfix,qa),'B',flipped(xfix,qb),'cc',counts(xfix),'nit',nfix,'ok',okfix,flush=True)

    target=xfix.copy(); q=qfix.copy(); rows=[]; last_both=None; first_lost=None
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,fixed,kappa,args.stage_maxiter)
        fa=bool(flipped(x,qa)); fb=bool(flipped(x,qb)); cc=counts(x)
        row={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),'raw_energy':float(raw),
             'a_flipped':fa,'b_flipped':fb,'both_flipped':bool(fa and fb),'coord_counts':cc,
             'anchor_rms':arms,'penalty':pen,'nit':int(nit),'success':bool(ok),'message':str(msg)}
        rows.append(row)
        print('K',kappa,'E',f'{E:.12f}','dLive',f'{E-args.live_score:+.9g}','A',fa,'B',fb,
              'cc',cc,'anchor',f'{arms:.6g}','nit',nit,flush=True)
        if fa and fb:
            last_both={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                       'coord_counts':cc,'anchor_rms':arms,'points':x.tolist()}
        elif first_lost is None:
            first_lost={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                        'a_flipped':fa,'b_flipped':fb,'coord_counts':cc,'anchor_rms':arms}

    Ef,rawf,xf,nf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter)
    final={'energy':float(Ef),'delta_live':float(Ef-args.live_score),'raw_energy':float(rawf),
           'a_flipped':bool(flipped(xf,qa)),'b_flipped':bool(flipped(xf,qb)),'coord_counts':counts(xf),
           'nit':int(nf),'success':bool(okf),'message':str(msgf),'points':xf.tolist()}
    print('FINAL',f'{Ef:.12f}','dLive',f'{Ef-args.live_score:+.9g}','A',final['a_flipped'],'B',final['b_flipped'],'cc',final['coord_counts'],flush=True)
    out={'seed_energy':float(E0),'quad_a':list(qa),'quad_b':list(qb),'pattern':args.pattern,
         'threshold_a':float(ta),'threshold_b':float(tb),'multiplier_a':args.multiplier_a,'multiplier_b':args.multiplier_b,
         'start_energy':float(Estart),'fixed_energy':float(Efix),'fixed_a_flipped':bool(flipped(xfix,qa)),
         'fixed_b_flipped':bool(flipped(xfix,qb)),'fixed_coord':counts(xfix),'schedule':parse_schedule(args.schedule),
         'rows':rows,'last_both_flipped_state':last_both,'first_lost_state':first_lost,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if final['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(final,separators=(',',':'))+'\n')

if __name__=='__main__': main()
