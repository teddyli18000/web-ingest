#!/usr/bin/env python3
"""Spatially split the >48-mode e432->B reaction residual around the short scar.

The e432->B reaction is broad-spectrum: the first 48 endpoint Hessian modes
capture only ~30.8% of its power, while the >48 residual alone crosses to B.
This script isolates that residual, then independently scales the part supported
near e432's unique short 5-7-5 scar and its complement before stable full relax.
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
from search_scar_core_elastic_split import graph,short_component,shell_mask

N=960


def first_modes(q,k,fd):
    H,raw,Q,calls=sm.build_hessian(q,fd,1e6)
    rng=np.random.default_rng(20261030)
    v0=rng.normal(size=len(q)); v0-=Q@(Q.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=k,which='SA',tol=1e-5,maxiter=1200,ncv=max(88,2*k+8),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    for j in range(V.shape[1]):
        V[:,j]-=Q@(Q.T@V[:,j]); V[:,j]/=np.linalg.norm(V[:,j])
    return vals,V,Q,calls['n']


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--k',type=int,default=48); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--shell',type=int,required=True); ap.add_argument('--decay',type=float,default=1.0)
    ap.add_argument('--core-scales',default='-0.6,0,0.35,0.55,0.70,0.85,1.0,1.2,1.5')
    ap.add_argument('--far-scales',default='-0.4,0,0.25,0.5,0.7,0.9,1.0,1.2')
    ap.add_argument('--maxiter',type=int,default=3400); ap.add_argument('--live-score',type=float,required=True)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    if args.k<48: raise ValueError('k must be >=48')

    S=load(args.source_json); T=load(args.target_json); q,y,Q0=reaction_physical(S,T)
    vals,V,Q,hcalls=first_modes(q,args.k,args.fd_step)
    proj=V@(V.T@y); residual=y-proj
    rn=float(np.linalg.norm(residual)); yn=float(np.linalg.norm(y)); residual_power=(rn/yn)**2
    adj,deg=graph(S); core=short_component(adj,deg); w,dist=shell_mask(adj,core,args.shell,args.decay)
    w2=np.repeat(w,2)
    rcore=residual*w2; rfar=residual*(1.0-w2)
    pc=float(np.dot(rcore,rcore)/(rn*rn)); pf=float(np.dot(rfar,rfar)/(rn*rn)); cross=float(2*np.dot(rcore,rfar)/(rn*rn))
    print('RESIDUAL_POWER',residual_power,'RMS',rn/math.sqrt(N),'SHELL',args.shell,'active',len(dist),
          'core_power',pc,'far_power',pf,'cross',cross,'core',core,flush=True)

    cs=[float(z) for z in args.core_scales.split(',') if z]; fs=[float(z) for z in args.far_scales.split(',') if z]
    rows=[]; saved=[]
    for a in cs:
        for b in fs:
            z=a*rcore+b*rfar; zn=float(np.linalg.norm(z))
            if zn<1e-15:
                continue
            amp=zn/math.sqrt(N)
            qs=sp.exp_perturb(q,z,amp); start,_=sm.fg(qs)
            e,raw,x,nit,ok,msg=stable_relax_q(qs,maxiter=args.maxiter); cc=tm.coord_counts(x)
            row={'shell':args.shell,'core_scale':a,'far_scale':b,'amp':amp,'start_energy':float(start),
                 'energy':float(e),'delta_live':float(e-args.live_score),'coord_counts':cc,
                 'nit':nit,'success':ok,'message':msg}
            rows.append(row)
            print('TRY shell',args.shell,'core',a,'far',b,'amp',amp,'E',f'{e:.12f}',
                  'dLive',f'{e-args.live_score:+.9g}','cc',cc,'nit',nit,flush=True)
            if e<args.live_score+0.18 and all(abs(e-s['energy'])>2e-6 or cc!=s['coord_counts'] for s in saved):
                saved.append({'energy':float(e),'delta_live':float(e-args.live_score),'coord_counts':cc,
                              'shell':args.shell,'core_scale':a,'far_scale':b,'amp':amp,'points':x.tolist()})
    saved.sort(key=lambda z:z['energy']); best=min(rows,key=lambda z:z['energy'])
    out={'source_energy':float(tm.raw_energy(S)),'target_energy':float(tm.raw_energy(T)),'live_score':args.live_score,
         'k':args.k,'eigenvalues':[float(v) for v in vals],'residual_power':residual_power,
         'residual_rms':rn/math.sqrt(N),'short_core':core,'short_core_degrees':[int(deg[i]) for i in core],
         'shell':args.shell,'active_vertices':len(dist),'core_residual_power':pc,'far_residual_power':pf,'cross_power':cross,
         'hessian_gradient_calls':hcalls,'rows':rows,'distinct_low_basins':saved[:24],
         'best_energy':best['energy'],'best_delta_live':best['delta_live']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if saved and saved[0]['energy']<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.candidate.json').write_text(json.dumps(saved[0],separators=(',',':'))+'\n')

if __name__=='__main__': main()
