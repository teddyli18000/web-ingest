#!/usr/bin/env python3
"""Continue the live-record dependent reconstruction through a newly legal third flip.

Starts from last_both_flipped_state of the two-flip homotopy (typically the
1.04, kappa=100 state), crosses a third Delaunay boundary that does not exist at
the live record, adapts the remaining particles with the local support fixed,
and releases the reconstructed support under a common spherical restraint.
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


def parse_quad(s):
    q=tuple(int(z) for z in s.split(','))
    if len(q)!=4: raise ValueError('quad must be u,v,a,b')
    return q


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def edge_signature(x):
    _,ef=topology(x); edges=set(ef)
    def has(a,b): return (min(a,b),max(a,b)) in edges
    # q1: 108-282 -> 511-599; q2: 108-511 -> 502-599;
    # q3: 511-599 -> 282-502.
    return {
      'old_q1_108_282':has(108,282), 'old_q2_108_511':has(108,511),
      'bridge_511_599':has(511,599), 'q2_new_502_599':has(502,599),
      'q3_new_282_502':has(282,502)}


def chain_ok(sig):
    return (not sig['old_q1_108_282'] and not sig['old_q2_108_511'] and
            not sig['bridge_511_599'] and sig['q2_new_502_599'] and sig['q3_new_282_502'])


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('two_flip_result')
    ap.add_argument('--third-quad',default='511,599,282,502')
    ap.add_argument('--third-multiplier',type=float,default=1.002)
    ap.add_argument('--pattern',default='balanced')
    ap.add_argument('--schedule',default='30000,10000,6000,4000,3000,2200,1600,1200,900,700,500,300,200,100,70,50,30,20,10,5,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=2600); ap.add_argument('--stage-maxiter',type=int,default=2000)
    ap.add_argument('--final-maxiter',type=int,default=4500); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    rec=json.load(open(args.two_flip_result)); st=rec.get('last_both_flipped_state')
    if not st or 'points' not in st: raise RuntimeError('two-flip result lacks last_both_flipped_state.points')
    x0=np.asarray(st['points'],dtype=float); q3=parse_quad(args.third_quad)
    E0,_=sm.fg(sm.xyz_to_vars(x0)); t3=threshold(x0,q3,args.pattern)
    if t3 is None: raise RuntimeError('third flip is not legal/finite at seed state')
    start=perturb(x0,q3,t3*args.third_multiplier,args.pattern)
    if not flipped(start,q3): raise RuntimeError('failed third flip')
    qstart=sm.xyz_to_vars(start); Estart,_=sm.fg(qstart)
    fixed=sorted(set([108,282,511,599,502]))
    Efix,rawfix,qfix,xfix,nfix,okfix,msgfix=fixed_relax(qstart,fixed,args.fixed_maxiter)
    print('SEED_K',st.get('kappa'),'SEED_E',f'{E0:.12f}','T3',t3,'START',f'{Estart:.12f}',counts(start),edge_signature(start),flush=True)
    print('FIXED',f'{Efix:.12f}','cc',counts(xfix),'sig',edge_signature(xfix),'nit',nfix,'ok',okfix,flush=True)
    target=xfix.copy(); q=qfix.copy(); rows=[]; last_chain=None; first_lost=None
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,fixed,kappa,args.stage_maxiter)
        sig=edge_signature(x); good=chain_ok(sig); cc=counts(x)
        row={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),'raw_energy':float(raw),
             'chain_ok':bool(good),'signature':sig,'coord_counts':cc,'anchor_rms':arms,'penalty':pen,
             'nit':int(nit),'success':bool(ok),'message':str(msg)}
        rows.append(row)
        print('K',kappa,'E',f'{E:.12f}','dLive',f'{E-args.live_score:+.9g}','CHAIN',good,'sig',sig,
              'cc',cc,'anchor',f'{arms:.6g}','nit',nit,flush=True)
        if good:
            last_chain={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                        'coord_counts':cc,'signature':sig,'anchor_rms':arms,'points':x.tolist()}
        elif first_lost is None:
            first_lost={'kappa':kappa,'energy':float(E),'delta_live':float(E-args.live_score),
                        'coord_counts':cc,'signature':sig,'anchor_rms':arms}
    Ef,rawf,xf,nf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter); fsig=edge_signature(xf)
    final={'energy':float(Ef),'delta_live':float(Ef-args.live_score),'raw_energy':float(rawf),'chain_ok':chain_ok(fsig),
           'signature':fsig,'coord_counts':counts(xf),'nit':int(nf),'success':bool(okf),'message':str(msgf),'points':xf.tolist()}
    print('FINAL',f'{Ef:.12f}','dLive',f'{Ef-args.live_score:+.9g}','CHAIN',final['chain_ok'],'sig',fsig,'cc',final['coord_counts'],flush=True)
    out={'source_kappa':st.get('kappa'),'source_energy':float(E0),'third_quad':list(q3),'third_threshold':float(t3),
         'third_multiplier':args.third_multiplier,'start_energy':float(Estart),'fixed_energy':float(Efix),
         'fixed_signature':edge_signature(xfix),'fixed_coord':counts(xfix),'rows':rows,
         'last_chain_state':last_chain,'first_lost_state':first_lost,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if final['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(final,separators=(',',':'))+'\n')

if __name__=='__main__': main()
