#!/usr/bin/env python3
"""Continuous occupancy exchange on the common A/R N=961 hub.

The A add-rank3 size bounce reaches the same N=961 minimum as the live-R
add-rank0 bounce.  Hard deletion of hub particle 886 returns R, while deleting
the newly inserted A particle is the exact reverse candidate toward A.

This script replaces the discrete choice of which particle to remove by an
alchemical coordinate: all hub particles have unit charge except indices 886
and 960, whose charges are t and 1-t.  Thus the total charge stays 960 while
all 961 coordinates remain movable.  Intermediate fractional states are also
projected to genuine N=960 configurations by deleting either exchange particle
and fully relaxing the remaining 960 unit charges.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np

import search_live_size_bounce as sbounce
import search_size_beam as sbeam
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from search_learned_event_grammar import defect_signature


def parse_schedule(s):
    vals=[float(z) for z in s.split(',') if z.strip()]
    if len(vals)<2 or any(v<0 or v>1 for v in vals): raise ValueError('schedule must lie in [0,1]')
    inc=vals[-1]>vals[0]
    if inc and any(vals[i+1]<vals[i]-1e-14 for i in range(len(vals)-1)): raise ValueError('schedule not monotone')
    if not inc and any(vals[i+1]>vals[i]+1e-14 for i in range(len(vals)-1)): raise ValueError('schedule not monotone')
    return vals


def sig_json(x):
    sig=defect_signature(x)
    return {'coord':[[int(a),int(b)] for a,b in sig['coord']], 'twin_count':int(sig['twins']),
            'components':[list(map(int,t)) for t in sig['components']]}


def classify(e,live):
    refs={'R':live,'A':444368.3956862258,'B':444368.4029728613,'D':444368.41099308443,
          'e432':444368.4322496275}
    name,err=min(((n,abs(e-v)) for n,v in refs.items()),key=lambda z:z[1])
    return name if err<2e-6 else 'novel'


def project(x,delete_idx,live,maxiter):
    z=np.delete(x,int(delete_idx),axis=0)
    e,y,nit,ok=sbeam.stable_relax(z,maxiter)
    return {'delete_index':int(delete_idx),'energy':float(e),'delta_live':float(e-live),
            'class':classify(e,live),'signature':sig_json(y),'nit':int(nit),'success':bool(ok),
            'points':y.tolist()}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('A_json')
    ap.add_argument('--schedule',required=True)
    ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--hub-maxiter',type=int,default=3200); ap.add_argument('--weighted-maxiter',type=int,default=1800)
    ap.add_argument('--project-maxiter',type=int,default=3000)
    ap.add_argument('--project-values',default='0,.2,.35,.5,.65,.8,1')
    ap.add_argument('--out',required=True); args=ap.parse_args()

    meta,A=sbounce.load_points(pathlib.Path(args.A_json))
    if len(A)!=960: raise ValueError('expected A N=960 seed')
    vc=sbounce.voronoi_candidates(A); sel=vc[3]
    xstart=np.vstack([A,np.asarray(sel['point'])[None,:]])
    hub=sbounce.relax(xstart,args.hub_maxiter); x=np.asarray(hub['points'],float)
    if len(x)!=961: raise RuntimeError('failed to construct N961 hub')
    print('HUB','tri',sel['triangle'],'E961',f"{hub['energy']:.12f}",'nit',hub['nit'],'ok',hub['success'],flush=True)
    if abs(hub['energy']-445303.247369582)>5e-4:
        raise RuntimeError(f'unexpected N961 hub energy {hub["energy"]}')

    schedule=parse_schedule(args.schedule)
    pvals=[float(z) for z in args.project_values.split(',') if z.strip()]
    rows=[]; projections=[]
    for t in schedule:
        charges=np.ones(961,float); charges[886]=float(t); charges[960]=float(1.0-t)
        ew,x,nit,ok,msg,grms=stable_weighted_relax(x,charges,args.weighted_maxiter)
        active886=np.delete(x,886,axis=0); active960=np.delete(x,960,axis=0)
        row={'t':float(t),'q886':float(t),'q960':float(1-t),'weighted_energy':float(ew),
             'gradient_rms':float(grms),'nit':int(nit),'success':bool(ok),'message':str(msg),
             'sig_del886':sig_json(active886),'sig_del960':sig_json(active960)}
        rows.append(row)
        print('T',t,'Ew',f'{ew:.12f}','grms',f'{grms:.3g}','nit',nit,'ok',ok,
              'del886_tw',row['sig_del886']['twin_count'],'del960_tw',row['sig_del960']['twin_count'],flush=True)
        if any(abs(t-p)<1e-10 for p in pvals):
            for di in (886,960):
                pr=project(x,di,args.live_score,args.project_maxiter); pr['t']=float(t)
                projections.append(pr)
                print('PROJECT','t',t,'del',di,pr['class'],f"{pr['energy']:.12f}",
                      'dLive',f"{pr['delta_live']:+.9g}",'sig',pr['signature']['coord'],flush=True)

    best=min(projections,key=lambda r:r['energy']) if projections else None
    out={'live_score':float(args.live_score),'hub_energy':float(hub['energy']),'hub_triangle':sel['triangle'],
         'schedule':schedule,'rows':rows,'projections':projections,
         'best_projection':best}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best is not None and best['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH.json').write_text(json.dumps(best,separators=(',',':'))+'\n')

if __name__=='__main__': main()
