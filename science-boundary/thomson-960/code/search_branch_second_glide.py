#!/usr/bin/env python3
"""Add a second same-scar glide while the soft orbit0 branch is still alive.

Input is the result JSON from search_samecount_flip_restraint_homotopy.py.
That run identifies a last restrained state where the first glide's new
Delaunay diagonal is still present.  Starting from those coordinates, cross a
second same-count glide on the same defect component, adapt with both quads
hard-fixed, then release both events together through a common spherical
restraint homotopy.

This directly tests the smallest nontrivial glide chain suggested by the live
record's one-flip graph, rather than enumerating arbitrary flip pairs.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb,flipped
from search_e564_scaffolded_flip import fixed_relax
from search_scaffold_restraint_homotopy import restraint_relax,parse_schedule


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def load_branch(path):
    d=json.loads(pathlib.Path(path).read_text())
    s=d.get('last_flipped_state')
    if not s or 'points' not in s:
        raise ValueError('branch JSON has no last_flipped_state with points')
    x=np.asarray(s['points'],float); x/=np.linalg.norm(x,axis=1)[:,None]
    q1=tuple(int(z) for z in d['quad'])
    return d,s,x,q1


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('branch_json')
    ap.add_argument('--second-quad',required=True,help='u,v,a,b')
    ap.add_argument('--pattern',default='balanced'); ap.add_argument('--multiplier',type=float,default=1.003)
    ap.add_argument('--schedule',default='6000,3000,1500,1000,700,500,300,200,100,30,10,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=2000); ap.add_argument('--stage-maxiter',type=int,default=1800)
    ap.add_argument('--final-maxiter',type=int,default=3800); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    bd,bs,x0,q1=load_branch(args.branch_json)
    q2=tuple(int(z) for z in args.second_quad.split(','))
    if len(q2)!=4: raise ValueError('second quad needs u,v,a,b')
    if not flipped(x0,q1): raise RuntimeError('first glide is not alive in supplied branch state')
    th=threshold(x0,q2,args.pattern)
    if th is None: raise RuntimeError('second glide has no finite crossing threshold on branch state')
    start=perturb(x0,q2,th*args.multiplier,args.pattern)
    if not flipped(start,q2): raise RuntimeError('failed to cross second glide')
    qstart=sm.xyz_to_vars(start); Estart,_=sm.fg(qstart)
    fixed=sorted(set(q1)|set(q2))
    Efix,rawfix,qfix,xfix,nfix,okfix,msgfix=fixed_relax(qstart,fixed,args.fixed_maxiter)
    print('BASE_K',bs.get('kappa'),'BASE_E',bs.get('energy'),'FIRST',q1,'SECOND',q2,
          'SECOND_THRESHOLD',th,flush=True)
    print('START',f'{Estart:.12f}','first',flipped(start,q1),'second',flipped(start,q2),'cc',counts(start),flush=True)
    print('FIXED',f'{Efix:.12f}','first',flipped(xfix,q1),'second',flipped(xfix,q2),'cc',counts(xfix),
          'nit',nfix,'ok',okfix,flush=True)

    target=xfix.copy(); q=qfix.copy(); rows=[]; last_both=None; first_lost=None
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,fixed,kappa,args.stage_maxiter)
        f1=bool(flipped(x,q1)); f2=bool(flipped(x,q2)); cc=counts(x)
        row={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),'raw_energy':float(raw),
             'first_flipped':f1,'second_flipped':f2,'both_flipped':bool(f1 and f2),'coord_counts':cc,
             'anchor_rms':arms,'penalty':pen,'nit':int(nit),'success':bool(ok),'message':str(msg)}
        rows.append(row)
        print('K',kappa,'E',f'{E:.12f}','dLive',f'{E-args.live_score:+.9g}',
              'first',f1,'second',f2,'cc',cc,'anchor',f'{arms:.6g}','nit',nit,flush=True)
        if f1 and f2:
            last_both={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                       'coord_counts':cc,'anchor_rms':arms,'points':x.tolist()}
        elif first_lost is None:
            first_lost={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                        'first_flipped':f1,'second_flipped':f2,'coord_counts':cc,'anchor_rms':arms}

    Ef,rawf,xf,nf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter)
    final={'energy':float(Ef),'delta_live':float(Ef-args.live_score),'raw_energy':float(rawf),
           'first_flipped':bool(flipped(xf,q1)),'second_flipped':bool(flipped(xf,q2)),
           'coord_counts':counts(xf),'nit':int(nf),'success':bool(okf),'message':str(msgf),'points':xf.tolist()}
    print('FINAL',f'{Ef:.12f}','dLive',f'{Ef-args.live_score:+.9g}','first',final['first_flipped'],
          'second',final['second_flipped'],'cc',final['coord_counts'],flush=True)
    out={'source_branch':args.branch_json,'source_branch_kappa':bs.get('kappa'),'source_branch_energy':bs.get('energy'),
         'first_quad':list(q1),'second_quad':list(q2),'pattern':args.pattern,'second_threshold':float(th),
         'multiplier':args.multiplier,'start_energy':float(Estart),'fixed_energy':float(Efix),
         'fixed_first_flipped':bool(flipped(xfix,q1)),'fixed_second_flipped':bool(flipped(xfix,q2)),
         'fixed_coord':counts(xfix),'schedule':parse_schedule(args.schedule),'rows':rows,
         'last_both_flipped_state':last_both,'first_lost_state':first_lost,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if final['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(final,separators=(',',':'))+'\n')

if __name__=='__main__': main()
