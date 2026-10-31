#!/usr/bin/env python3
"""Continuous occupancy exits from the shared A/R N=961 hub.

A and R reach the same relaxed N=961 minimum, but hard deletion of different
labels selects different N=960 exits: the originally inserted label 960 is the
natural A-side reverse, while deletion of remote scar point 886 returns record
R.  Replace the discrete deletion by a continuous charge fade of one selected
particle while all 961 coordinates remain mobile.  At lambda=0 the faded point
decouples exactly and is removed before an ordinary N=960 repolish.
"""
from __future__ import annotations
import argparse,json,pathlib
from collections import Counter
import numpy as np

from search_live_size_bounce import load_points,voronoi_candidates,relax as size_relax
from search_from_seed_modes import stable_relax_q
from search_e564_defect_flip_parallel import topology
from search_learned_event_grammar import defect_signature
import diagnose_soft_modes as sm
import search_n972_mobile_fractional_homotopy as mob

KNOWN={'R':444368.3924061973,'A':444368.3956862258,'B':444368.4029728613,
       'D':444368.41099308443,'e432':444368.4322496275}


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def sig(x):
    s=defect_signature(x); return {'coord':[[int(a),int(b)] for a,b in s['coord']],
        'twin_count':int(s['twins']),'components':[list(map(int,t)) for t in s['components']]}


def classify(e):
    n,err=min(((k,abs(float(e)-v)) for k,v in KNOWN.items()),key=lambda z:z[1])
    return n if err<2e-6 else 'novel'


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('a_json'); ap.add_argument('--rank',type=int,default=3)
    ap.add_argument('--fade-index',type=int,required=True)
    ap.add_argument('--schedule',default='1,.85,.7,.58,.48,.38,.29,.21,.14,.09,.05,.025,.01,.003,0')
    ap.add_argument('--maxiter',type=int,default=1800); ap.add_argument('--final-maxiter',type=int,default=4200)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    _,a=load_points(pathlib.Path(args.a_json)); vc=voronoi_candidates(a); sel=vc[args.rank]
    first=size_relax(np.vstack([a,np.asarray(sel['point'])[None,:]]),3200); x=first['points']
    if len(x)!=961: raise RuntimeError('hub reproduction failed')
    if abs(float(first['energy'])-445303.247369582)>2e-5: raise RuntimeError(f'unexpected hub {first["energy"]}')
    if not (0<=args.fade_index<len(x)): raise IndexError(args.fade_index)
    schedule=mob.parse_schedule(args.schedule); parent=x.copy(); rows=[]
    print('HUB',f"{first['energy']:.12f}",'tri',sel['triangle'],'fade',args.fade_index,'cc',counts(x),flush=True)
    for lam in schedule:
        charges=np.ones(len(x),float); charges[args.fade_index]=float(lam)
        E,x,nit,ok,msg,grms=mob.stable_weighted_relax(x,charges,args.maxiter)
        active=np.delete(x,args.fade_index,axis=0)
        row={'lambda':lam,'weighted_energy':float(E),'gradient_rms':grms,'nit':nit,'success':ok,'message':msg,
             'active_signature':sig(active),'active_rms_from_hub':mob.angular_rms(active,np.delete(parent,args.fade_index,axis=0)),
             'faded_displacement':float(np.arccos(np.clip(np.dot(x[args.fade_index],parent[args.fade_index]),-1.0,1.0)))}
        rows.append(row)
        print('L',lam,'Ew',f'{E:.12f}','grms',f'{grms:.3g}','twins',row['active_signature']['twin_count'],
              'coord',row['active_signature']['coord'],'active_rms',f"{row['active_rms_from_hub']:.6g}",
              'fade_move',f"{row['faded_displacement']:.6g}",flush=True)
    x960=np.delete(x,args.fade_index,axis=0)
    e,raw,y,nit,ok,msg=stable_relax_q(sm.xyz_to_vars(x960),maxiter=args.final_maxiter)
    final={'energy':float(e),'raw_energy':float(raw),'delta_live':float(e-args.live_score),'class':classify(e),
           'coord_counts':counts(y),'signature':sig(y),'nit':int(nit),'success':bool(ok),'message':str(msg),'points':y.tolist()}
    print('FINAL',final['class'],f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}',final['coord_counts'],
          'twins',final['signature']['twin_count'],flush=True)
    out={'live_score':args.live_score,'hub_energy':float(first['energy']),'hub_triangle':sel['triangle'],
         'fade_index':args.fade_index,'schedule':schedule,'rows':rows,'final':final}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if e<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('fractional N961 exit below live; verify independently\n')

if __name__=='__main__': main()
