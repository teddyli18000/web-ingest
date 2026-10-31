#!/usr/bin/env python3
"""Intervene on the remote-follower order after the known q1->q2->q3 scar walk.

The validated R->A route first performs the local history-dependent q1/q2/q3
reconstruction, then remote root glides soften and flip.  This experiment keeps
the local trigger fixed but deliberately changes the remote follower order.  It
therefore probes a different causal search space from deeper local scar-walk
beam search.
"""
from __future__ import annotations
import argparse, json, pathlib, math
from collections import Counter
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import stable_relax_q
from search_e564_defect_flip_parallel import topology, threshold, perturb
from search_e564_scaffolded_flip import fixed_relax
from search_scaffold_restraint_homotopy import restraint_relax, parse_schedule

Q3=(511,599,282,502)
LOCAL_SUPPORT={108,282,511,599,502}
FOLLOWERS={
    # natural R->A followers
    'o2':(79,134,323,35),
    'o3':(21,230,74,363),
    # strongest additional softened persistent root glide after q3
    'alt':(379,959,295,923),
    # two further softened persistent root glides, useful as controls
    'f4':(428,602,831,919),
    'f5':(319,699,283,615),
}

def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}

def edge(a,b): return (min(int(a),int(b)),max(int(a),int(b)))

def edge_state(x,q):
    _,ef=topology(x); es=set(ef); u,v,a,b=q
    return {'old':edge(u,v) in es,'new':edge(a,b) in es}

def classify(e,live):
    refs={'R':live,'A':444368.3956862258,'B':444368.4029728613,'D':444368.41099308443,
          'e432':444368.4322496275}
    name,err=min(((n,abs(e-v)) for n,v in refs.items()),key=lambda z:z[1])
    return name if err<2e-6 else 'novel'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('two_flip_result')
    ap.add_argument('--sequence',required=True,help='comma-separated follower names, e.g. alt,o3,o2')
    ap.add_argument('--q3-multiplier',type=float,default=1.04)
    ap.add_argument('--follower-multiplier',type=float,default=1.01)
    ap.add_argument('--schedule',default='100,70,50,30,20,10,5,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=2600); ap.add_argument('--stage-maxiter',type=int,default=2200)
    ap.add_argument('--final-maxiter',type=int,default=4800); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    seq=[s.strip() for s in args.sequence.split(',') if s.strip()]
    if not seq or any(s not in FOLLOWERS for s in seq): raise ValueError(f'bad sequence {seq}')

    rec=json.load(open(args.two_flip_result)); st=rec.get('last_both_flipped_state')
    if not st or 'points' not in st: raise RuntimeError('missing last_both_flipped_state.points')
    x0=np.asarray(st['points'],dtype=float)
    t3=threshold(x0,Q3,'balanced')
    if t3 is None or not math.isfinite(t3): raise RuntimeError('q3 unavailable')
    x=perturb(x0,Q3,float(t3)*args.q3_multiplier,'balanced')
    support=set(LOCAL_SUPPORT)
    E,raw,q,x,nit,ok,msg=fixed_relax(sm.xyz_to_vars(x),sorted(support),args.fixed_maxiter)
    rows=[{'kind':'q3-fixed','energy':float(E),'coord_counts':counts(x),'threshold':float(t3),
           'support':sorted(support)}]
    print('Q3','t',t3,'E',f'{E:.12f}','cc',counts(x),flush=True)

    applied=[]
    for name in seq:
        fq=FOLLOWERS[name]
        st0=edge_state(x,fq)
        t=threshold(x,fq,'balanced') if st0['old'] and not st0['new'] else None
        if t is None or not math.isfinite(t):
            rows.append({'kind':'follower-unavailable','name':name,'edge_state':st0,'coord_counts':counts(x)})
            print('UNAVAILABLE',name,st0,'cc',counts(x),flush=True)
            break
        xstart=perturb(x,fq,float(t)*args.follower_multiplier,'balanced')
        support.update(fq)
        E,raw,q,x,nit,ok,msg=fixed_relax(sm.xyz_to_vars(xstart),sorted(support),args.fixed_maxiter)
        st1=edge_state(x,fq)
        row={'kind':'follower-fixed','name':name,'threshold':float(t),'energy':float(E),
             'coord_counts':counts(x),'edge_state':st1,'support':sorted(support),'nit':int(nit),'success':bool(ok)}
        rows.append(row); applied.append(name)
        print('FOLLOW',name,'t',f'{t:.9g}','E',f'{E:.12f}','cc',counts(x),'edge',st1,flush=True)

    target=x.copy(); q=sm.xyz_to_vars(x); stages=[]
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,sorted(support),kappa,args.stage_maxiter)
        states={n:edge_state(x,FOLLOWERS[n]) for n in FOLLOWERS}
        row={'kappa':float(kappa),'energy':float(E),'delta_live':float(E-args.live_score),
             'coord_counts':counts(x),'anchor_rms':float(arms),'penalty':float(pen),
             'nit':int(nit),'success':bool(ok),'followers':states}
        stages.append(row)
        print('K',kappa,'E',f'{E:.12f}','dLive',f'{E-args.live_score:+.9g}','cc',counts(x),
              'states',{n:(z['old'],z['new']) for n,z in states.items()},flush=True)

    Ef,rawf,xf,nf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter)
    final={'energy':float(Ef),'raw_energy':float(rawf),'delta_live':float(Ef-args.live_score),
           'class':classify(Ef,args.live_score),'coord_counts':counts(xf),'nit':int(nf),'success':bool(okf),
           'message':str(msgf),'followers':{n:edge_state(xf,FOLLOWERS[n]) for n in FOLLOWERS},
           'points':xf.tolist()}
    print('FINAL',args.sequence,final['class'],f'{Ef:.12f}','dLive',f"{final['delta_live']:+.9g}",
          'cc',final['coord_counts'],flush=True)
    out={'sequence':seq,'applied':applied,'q3_threshold':float(t3),'rows':rows,'stages':stages,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if Ef<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH.json').write_text(json.dumps(final,separators=(',',':'))+'\n')

if __name__=='__main__': main()
