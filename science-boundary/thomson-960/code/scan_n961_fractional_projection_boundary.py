#!/usr/bin/env python3
"""Locate the A/R projection boundary along the label960 fractional fade.

From the validated common N=961 hub, continuously reduce q_960 from 1 to 0
while all coordinates remain mobile.  At every requested lambda, delete label
960 from the *current fractional minimum* and fully repolish the remaining 960
unit charges.  Hard deletion at lambda=1 is A, while the adiabatic lambda->0
endpoint is R; this scan locates the bifurcation interval and preserves nearby
fractional states for subsequent occupancy x geometry searches.
"""
from __future__ import annotations
import argparse,json,pathlib
import numpy as np

from search_live_size_bounce import load_points,voronoi_candidates,relax as size_relax
from search_n972_mobile_fractional_homotopy import stable_weighted_relax
from search_size_beam import stable_relax
from search_learned_event_grammar import defect_signature

KNOWN={'R':None,'A':444368.3956862258,'B':444368.4029728613,'D':444368.41099308443}

def parse_schedule(s):
    v=[float(z) for z in s.split(',') if z.strip()]
    if not v or abs(v[0]-1)>1e-12 or abs(v[-1])>1e-12: raise ValueError('schedule must run 1 -> 0')
    if any(v[i+1]>v[i]+1e-14 for i in range(len(v)-1)): raise ValueError('schedule must be nonincreasing')
    return v

def sig_json(x):
    s=defect_signature(x)
    return {'coord':[[int(a),int(b)] for a,b in s['coord']], 'twins':int(s['twins']),
            'components':[list(map(int,t)) for t in s['components']]}

def classify(e,live):
    refs=dict(KNOWN); refs['R']=float(live)
    n,err=min(((k,abs(float(e)-v)) for k,v in refs.items()),key=lambda z:z[1])
    return n if err<2e-6 else 'novel'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('a_json'); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--schedule',default='1,.8,.6,.4,.25,.15,.1,.075,.06,.05,.04,.03,.025,.02,.015,.01,.007,.005,.003,.001,0')
    ap.add_argument('--weighted-maxiter',type=int,default=1800); ap.add_argument('--project-maxiter',type=int,default=4200)
    ap.add_argument('--out',required=True); args=ap.parse_args()

    _,a=load_points(pathlib.Path(args.a_json)); sel=voronoi_candidates(a)[3]
    hub=size_relax(np.vstack([a,np.asarray(sel['point'],float)[None,:]]),3200); x=np.asarray(hub['points'],float)
    if abs(hub['energy']-445303.247369582)>5e-4: raise RuntimeError(f'unexpected hub {hub["energy"]}')
    rows=[]; saved=[]; prev_class=None; transitions=[]
    for lam in parse_schedule(args.schedule):
        charges=np.ones(961,float); charges[960]=float(lam)
        ew,x,nit,ok,msg,grms=stable_weighted_relax(x,charges,args.weighted_maxiter)
        active=np.delete(x,960,axis=0)
        ep,z,nitp,okp=stable_relax(active,args.project_maxiter)
        cls=classify(ep,args.live_score); sig=sig_json(z)
        row={'lambda':float(lam),'weighted_energy':float(ew),'weighted_grms':float(grms),
             'weighted_nit':int(nit),'weighted_success':bool(ok),'projection_energy':float(ep),
             'projection_delta_live':float(ep-args.live_score),'projection_class':cls,
             'projection_signature':sig,'projection_nit':int(nitp),'projection_success':bool(okp)}
        rows.append(row)
        print('L',lam,'Ew',f'{ew:.12f}','grms',f'{grms:.3g}','P',cls,f'{ep:.12f}',
              'dLive',f'{ep-args.live_score:+.9g}','sig',sig['coord'],flush=True)
        if prev_class is not None and cls!=prev_class:
            transitions.append({'from':prev_class,'to':cls,'lambda_hi':float(rows[-2]['lambda']),'lambda_lo':float(lam)})
        prev_class=cls
        # Keep coordinates for all points near a class transition / low-lambda endpoint.
        if lam<=0.1 or cls not in ('A','R'):
            saved.append({'lambda':float(lam),'fractional_points':x.tolist(),'projection_points':z.tolist(),
                          'projection_class':cls,'projection_energy':float(ep),'weighted_energy':float(ew)})
    best=min(rows,key=lambda r:r['projection_energy'])
    out={'live_score':float(args.live_score),'hub_energy':float(hub['energy']),'hub_triangle':sel['triangle'],
         'rows':rows,'transitions':transitions,'saved_states':saved,'best':best}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best['projection_energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('projection below live; verify independently\n')

if __name__=='__main__': main()
