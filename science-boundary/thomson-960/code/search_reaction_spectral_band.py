#!/usr/bin/env python3
"""Search spectral bands of a *known physical reaction field* around a Thomson minimum.

For a labeled source/target pair, form the exact spherical log-map reaction at
source, project it onto the source physical-tangent Hessian eigenbasis, and
isolate a requested spectral band.  Perturb along that band at multiples of its
native RMS amplitude and fully relax.  This differs from blind high-mode scans:
the directions are the portions of the actual topology-changing event carried
by specific frequency ranges.
"""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
import search_topology_morph as tm
from search_from_seed_modes import stable_relax_q
from analyze_reaction_mode_overlap import load,reaction_physical

N=960


def modes(q,k,fd):
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    rng=np.random.default_rng(20261030)
    v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=1200,ncv=max(88,2*k+8),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    for j in range(V.shape[1]):
        V[:,j]-=Q@(Q.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    return vals,V,Q,calls['n']


def component(name,y,V):
    c=V.T@y
    p=lambda a,b: V[:,a:b]@c[a:b]
    p12=p(0,12); p24=p(0,24); p48=V@c
    if name=='low12': return p12
    if name=='mid12_24': return p(12,24)
    if name=='high24_48': return p(24,48)
    if name=='captured48': return p48
    if name=='residual48': return y-p48
    if name=='no_low12': return y-p12
    if name=='no_low24': return y-p24
    raise ValueError(name)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--band',required=True,choices=['low12','mid12_24','high24_48','captured48','residual48','no_low12','no_low24'])
    ap.add_argument('--k',type=int,default=48); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--scales',default='-1.5,-1.0,-0.65,0.45,0.70,0.90,1.05,1.20,1.45,1.80')
    ap.add_argument('--maxiter',type=int,default=3000); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    if args.k<48: raise ValueError('k must be >=48')

    S=load(args.source_json); T=load(args.target_json)
    q,y,Q0=reaction_physical(S,T); vals,V,Q,hcalls=modes(q,args.k,args.fd_step)
    b=component(args.band,y,V); bn=float(np.linalg.norm(b)); yn=float(np.linalg.norm(y))
    if bn<1e-12: raise RuntimeError('band has negligible norm')
    native=bn/math.sqrt(N); power=(bn/yn)**2
    print('BAND',args.band,'native_rms',native,'power',power,'reaction_rms',yn/math.sqrt(N),flush=True)
    rows=[]; saved=[]
    for scale in [float(z) for z in args.scales.split(',') if z]:
        amp=abs(scale)*native; direction=b if scale>=0 else -b
        qs=sp.exp_perturb(q,direction,amp)
        start,_=sm.fg(qs)
        e,raw,x,nit,ok,msg=stable_relax_q(qs,maxiter=args.maxiter)
        cc=tm.coord_counts(x)
        row={'band':args.band,'scale':scale,'native_rms':native,'amp':amp,'start_energy':float(start),
             'energy':float(e),'delta_live':float(e-args.live_score),'coord_counts':cc,
             'nit':nit,'success':ok,'message':msg}
        rows.append(row)
        print('TRY',args.band,'scale',scale,'amp',amp,'start',f'{start:.9f}','E',f'{e:.12f}',
              'dLive',f'{e-args.live_score:+.9g}','cc',cc,'nit',nit,flush=True)
        if e<args.live_score+0.20 and all(abs(e-z['energy'])>2e-6 or cc!=z['coord_counts'] for z in saved):
            saved.append({'energy':float(e),'delta_live':float(e-args.live_score),'coord_counts':cc,
                          'band':args.band,'scale':scale,'amp':amp,'points':x.tolist()})
    saved.sort(key=lambda z:z['energy']); best=min(rows,key=lambda z:z['energy'])
    out={'band':args.band,'source_energy':float(tm.raw_energy(S)),'target_energy':float(tm.raw_energy(T)),
         'live_score':args.live_score,'reaction_norm':yn,'reaction_rms':yn/math.sqrt(N),
         'band_norm':bn,'band_native_rms':native,'band_power':power,
         'eigenvalues':[float(v) for v in vals],'hessian_gradient_calls':hcalls,
         'rows':rows,'distinct_low_basins':saved[:20],
         'best_energy':best['energy'],'best_delta_live':best['delta_live']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved and saved[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
