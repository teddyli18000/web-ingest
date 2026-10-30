#!/usr/bin/env python3
"""Test a two-step scar reconstruction where the second flip exists only after the first.

Unlike the earlier orbit0->orbit1 chain, both moves here are not independent
live-record glides.  Crossing the first orbit4 boundary changes the local
triangulation and creates the second legal Delaunay move.  We cross that newly
created move, adapt all other particles with both quads fixed, then jointly
release the eight involved vertices under decreasing spherical restraint.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter

import diagnose_soft_modes as sm
from search_from_seed_modes import load_seed,stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb,flipped
from search_e564_scaffolded_flip import fixed_relax
from search_scaffold_restraint_homotopy import restraint_relax,parse_schedule


def parse_quad(s):
    q=tuple(int(z) for z in s.split(','))
    if len(q)!=4: raise ValueError('quad must be u,v,a,b')
    return q


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('seed_json')
    ap.add_argument('--first-quad',required=True); ap.add_argument('--second-quad',required=True)
    ap.add_argument('--pattern',default='balanced')
    ap.add_argument('--first-multiplier',type=float,default=1.003); ap.add_argument('--second-multiplier',type=float,default=1.003)
    ap.add_argument('--schedule',default='100000,30000,10000,6000,4000,3000,2200,1600,1200,900,700,500,300,200,100,30,10,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=2400); ap.add_argument('--stage-maxiter',type=int,default=1800)
    ap.add_argument('--final-maxiter',type=int,default=4000); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    q1=parse_quad(args.first_quad); q2=parse_quad(args.second_quad)
    meta,x0=load_seed(pathlib.Path(args.seed_json)); E0,_=sm.fg(sm.xyz_to_vars(x0))
    t1=threshold(x0,q1,args.pattern)
    if t1 is None: raise RuntimeError('first flip has no finite threshold')
    x1=perturb(x0,q1,t1*args.first_multiplier,args.pattern)
    if not flipped(x1,q1): raise RuntimeError('failed first flip')
    t2=threshold(x1,q2,args.pattern)
    if t2 is None: raise RuntimeError('dependent second flip is not legal/finite after first')
    start=perturb(x1,q2,t2*args.second_multiplier,args.pattern)
    if not flipped(start,q1) or not flipped(start,q2): raise RuntimeError('failed to keep both flips after dependent crossing')
    qstart=sm.xyz_to_vars(start); Estart,_=sm.fg(qstart); fixed=sorted(set(q1)|set(q2))
    Efix,rawfix,qfix,xfix,nfix,okfix,msgfix=fixed_relax(qstart,fixed,args.fixed_maxiter)
    print('SEED',f'{E0:.12f}','T1',t1,'T2',t2,'START',f'{Estart:.12f}',counts(start),flush=True)
    print('FIXED',f'{Efix:.12f}','Q1',flipped(xfix,q1),'Q2',flipped(xfix,q2),'cc',counts(xfix),'nit',nfix,'ok',okfix,flush=True)

    target=xfix.copy(); q=qfix.copy(); rows=[]; last_both=None; first_lost=None
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,fixed,kappa,args.stage_maxiter)
        f1=bool(flipped(x,q1)); f2=bool(flipped(x,q2)); cc=counts(x)
        row={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),'raw_energy':float(raw),
             'first_flipped':f1,'second_flipped':f2,'both_flipped':bool(f1 and f2),'coord_counts':cc,
             'anchor_rms':arms,'penalty':pen,'nit':int(nit),'success':bool(ok),'message':str(msg)}
        rows.append(row)
        print('K',kappa,'E',f'{E:.12f}','dLive',f'{E-args.live_score:+.9g}','Q1',f1,'Q2',f2,
              'cc',cc,'anchor',f'{arms:.6g}','nit',nit,flush=True)
        if f1 and f2:
            last_both={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),'coord_counts':cc,
                       'anchor_rms':arms,'points':x.tolist()}
        elif first_lost is None:
            first_lost={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                        'first_flipped':f1,'second_flipped':f2,'coord_counts':cc,'anchor_rms':arms}

    Ef,rawf,xf,nf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter)
    final={'energy':float(Ef),'delta_live':float(Ef-args.live_score),'raw_energy':float(rawf),
           'first_flipped':bool(flipped(xf,q1)),'second_flipped':bool(flipped(xf,q2)),'coord_counts':counts(xf),
           'nit':int(nf),'success':bool(okf),'message':str(msgf),'points':xf.tolist()}
    print('FINAL',f'{Ef:.12f}','dLive',f'{Ef-args.live_score:+.9g}','Q1',final['first_flipped'],'Q2',final['second_flipped'],'cc',final['coord_counts'],flush=True)
    out={'seed_energy':float(E0),'first_quad':list(q1),'second_quad':list(q2),'pattern':args.pattern,
         'first_threshold':float(t1),'second_threshold':float(t2),'first_multiplier':args.first_multiplier,
         'second_multiplier':args.second_multiplier,'start_energy':float(Estart),'fixed_energy':float(Efix),
         'fixed_first_flipped':bool(flipped(xfix,q1)),'fixed_second_flipped':bool(flipped(xfix,q2)),
         'fixed_coord':counts(xfix),'schedule':parse_schedule(args.schedule),'rows':rows,
         'last_both_flipped_state':last_both,'first_lost_state':first_lost,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if final['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(final,separators=(',',':'))+'\n')

if __name__=='__main__': main()
