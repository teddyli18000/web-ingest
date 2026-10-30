#!/usr/bin/env python3
"""Diagnose remote follower-glide softening along the known dependent R->A scar walk.

Replays q3 from the q1+q2 kappa=100 state and records, at every restraint
stage, whether the two remote R->A follower glides (orbit2/orbit3) are already
flipped and, while they are still legal in the R orientation, their balanced
Delaunay crossing thresholds.  The goal is to test whether local history-
dependent scar motion predicts the later spontaneous cross-scar cascade.
"""
from __future__ import annotations
import argparse,json,pathlib,math
from collections import Counter
import numpy as np

import diagnose_soft_modes as sm
from search_from_seed_modes import stable_relax_q
from search_e564_defect_flip_parallel import topology,threshold,perturb,flipped
from search_e564_scaffolded_flip import fixed_relax
from search_scaffold_restraint_homotopy import restraint_relax,parse_schedule

Q3=(511,599,282,502)
FOLLOWERS={
    'orbit2':(79,134,323,35),   # delete (79,134), add (35,323)
    'orbit3':(21,230,74,363),   # delete (21,230), add (74,363)
}


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def edge_set(x):
    _,ef=topology(x); return set(ef)


def edge(a,b): return (min(int(a),int(b)),max(int(a),int(b)))


def follower_state(x,q):
    u,v,a,b=q; es=edge_set(x)
    old=edge(u,v); new=edge(a,b)
    old_has=old in es; new_has=new in es
    t=None
    if old_has and not new_has:
        try:
            z=threshold(x,q,'balanced')
            if z is not None and math.isfinite(z): t=float(z)
        except Exception:
            t=None
    return {'old_edge':list(old),'new_edge':list(new),'old_present':old_has,
            'new_present':new_has,'flipped':bool(new_has and not old_has),'threshold':t}


def snapshot(label,kappa,x,E,live):
    f={name:follower_state(x,q) for name,q in FOLLOWERS.items()}
    row={'label':label,'kappa':kappa,'energy':float(E),'delta_live':float(E-live),
         'coord_counts':counts(x),'followers':f}
    print('SNAP',label,'K',kappa,'E',f'{E:.12f}','dLive',f'{E-live:+.9g}',
          'o2',f['orbit2'],'o3',f['orbit3'],flush=True)
    return row


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('two_flip_result')
    ap.add_argument('--third-multiplier',type=float,default=1.04)
    ap.add_argument('--schedule',default='100,70,50,30,20,10,5,3,1,0.3,0.1,0.03,0.01,0.003,0.001,0')
    ap.add_argument('--fixed-maxiter',type=int,default=2600); ap.add_argument('--stage-maxiter',type=int,default=2200)
    ap.add_argument('--final-maxiter',type=int,default=4500); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    rec=json.load(open(args.two_flip_result)); st=rec.get('last_both_flipped_state')
    if not st or 'points' not in st: raise RuntimeError('two-flip result lacks last_both_flipped_state.points')
    x0=np.asarray(st['points'],dtype=float); E0,_=sm.fg(sm.xyz_to_vars(x0))
    rows=[snapshot('two-flip-source',st.get('kappa'),x0,E0,args.live_score)]

    t3=threshold(x0,Q3,'balanced')
    if t3 is None or not math.isfinite(t3): raise RuntimeError('q3 unavailable')
    start=perturb(x0,Q3,float(t3)*args.third_multiplier,'balanced')
    qstart=sm.xyz_to_vars(start); Estart,_=sm.fg(qstart)
    rows.append(snapshot('q3-crossed',None,start,Estart,args.live_score))

    fixed=sorted({108,282,511,599,502})
    Efix,rawfix,qfix,xfix,nfix,okfix,msgfix=fixed_relax(qstart,fixed,args.fixed_maxiter)
    rows.append(snapshot('q3-fixed',None,xfix,Efix,args.live_score))
    print('Q3',t3,'fixed',Efix,'nit',nfix,'ok',okfix,flush=True)

    target=xfix.copy(); q=qfix.copy()
    for kappa in parse_schedule(args.schedule):
        E,raw,q,x,nit,ok,msg,arms,pen=restraint_relax(q,target,fixed,kappa,args.stage_maxiter)
        row=snapshot('restraint',kappa,x,E,args.live_score)
        row.update({'anchor_rms':float(arms),'penalty':float(pen),'nit':int(nit),'success':bool(ok)})
        rows.append(row)

    Ef,rawf,xf,nf,okf,msgf=stable_relax_q(q,maxiter=args.final_maxiter)
    final=snapshot('final-free',None,xf,Ef,args.live_score)
    final.update({'raw_energy':float(rawf),'nit':int(nf),'success':bool(okf),'message':str(msgf),'points':xf.tolist()})

    # Summarize the last pre-flip threshold seen for each follower and the first stage where it flips.
    summary={}
    for name in FOLLOWERS:
        vals=[(r.get('kappa'),r['followers'][name]['threshold']) for r in rows if r['followers'][name]['threshold'] is not None]
        flipped_rows=[r for r in rows if r['followers'][name]['flipped']]
        summary[name]={'threshold_trace':vals,
                       'min_preflip_threshold':None if not vals else min(v for _,v in vals),
                       'first_flipped_label':None if not flipped_rows else flipped_rows[0]['label'],
                       'first_flipped_kappa':None if not flipped_rows else flipped_rows[0].get('kappa')}
    out={'source_kappa':st.get('kappa'),'source_energy':float(E0),'q3_threshold':float(t3),
         'third_multiplier':args.third_multiplier,'rows':rows,'summary':summary,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('SUMMARY',summary,flush=True)

if __name__=='__main__': main()
