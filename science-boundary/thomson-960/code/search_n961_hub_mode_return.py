#!/usr/bin/env python3
"""Search N=960 return basins from soft deformations of the shared A/R N=961 hub.

The A- and R-centered size-bounce campaigns meet at the same N=961 minimum.
Direct deletion from that minimum is strongly funneled: deleting label 886 is
the special low-energy exit back to record R, while almost all other deletions
go to a 23-dislocation layer.  This script changes the representation rather
than enumerating more deletions: it deforms the shared N=961 hub along its true
low physical Hessian modes, then performs the special deletion 886 before
relaxing in N=960.  A low side exit would therefore be a genuine branch of the
shared size-space interface rather than another greedy deletion index.
"""
from __future__ import annotations
import argparse,json,math,pathlib
from collections import Counter
import numpy as np
from scipy.sparse.linalg import eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_from_seed_modes import stable_relax_q
from search_live_size_bounce import load_points,voronoi_candidates,relax as size_relax
from search_e564_defect_flip_parallel import topology

KNOWN={'R':444368.3924061973,'A':444368.3956862258,'B':444368.4029728613,
       'D':444368.41099308443,'e432':444368.4322496275}


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def classify(e):
    n,err=min(((k,abs(float(e)-v)) for k,v in KNOWN.items()),key=lambda z:z[1])
    return n if err<2e-6 else 'novel'


def reproduce_hub(a_json,rank,maxiter):
    _,a=load_points(pathlib.Path(a_json))
    vc=voronoi_candidates(a); sel=vc[rank]
    xstart=np.vstack([a,np.asarray(sel['point'],float)[None,:]])
    rr=size_relax(xstart,maxiter); x=rr['points']
    return sel,rr,x


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('a_json')
    ap.add_argument('--rank',type=int,default=3); ap.add_argument('--delete-index',type=int,default=886)
    ap.add_argument('--modes',default='0,1,2'); ap.add_argument('--amps',default='.004,.008,.014,.022,.035')
    ap.add_argument('--k',type=int,default=10); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--hub-maxiter',type=int,default=3200); ap.add_argument('--return-maxiter',type=int,default=3600)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()

    sel,hub_rec,xhub=reproduce_hub(args.a_json,args.rank,args.hub_maxiter)
    if len(xhub)!=961: raise RuntimeError('hub reproduction did not yield N=961')
    print('HUB','tri',sel['triangle'],'E',f"{hub_rec['energy']:.12f}",'cc',counts(xhub),
          'del',args.delete_index,flush=True)
    # Guard against silently drifting to a different N961 minimum.
    if abs(float(hub_rec['energy'])-445303.247369582)>2e-5:
        raise RuntimeError(f"unexpected N961 hub energy {hub_rec['energy']}")

    q0=sm.xyz_to_vars(xhub); H,raw_hy,Qrot,calls=sm.build_hessian(q0,args.fd_step,1e6)
    modes=[int(z) for z in args.modes.split(',') if z.strip()]; amps=[float(z) for z in args.amps.split(',') if z.strip()]
    k=max(args.k,max(modes)+1)
    rng=np.random.default_rng(961886); v0=rng.normal(size=len(q0)); v0-=Qrot@(Qrot.T@v0)
    vals,V=eigsh(H,k=k,which='SA',tol=2e-5,maxiter=800,ncv=max(40,3*k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    print('LAMBDAS',[float(v) for v in vals],flush=True)

    rows=[]; saved=[]
    for m in modes:
        d=V[:,m].copy(); d-=Qrot@(Qrot.T@d); d/=np.linalg.norm(d)
        for sign in (-1,1):
            for amp in amps:
                qp=sp.exp_perturb(q0,d*sign,amp); xp,_,_=sm.vars_to_xyz(qp)
                if args.delete_index<0 or args.delete_index>=len(xp): raise IndexError(args.delete_index)
                x960=np.delete(xp,args.delete_index,axis=0)
                e,raw,y,nit,ok,msg=stable_relax_q(sm.xyz_to_vars(x960),maxiter=args.return_maxiter)
                rec={'mode':m,'eigenvalue':float(vals[m]),'sign':sign,'amp':amp,
                     'energy':float(e),'raw_energy':float(raw),'delta_live':float(e-args.live_score),
                     'class':classify(e),'coord_counts':counts(y),'nit':int(nit),'success':bool(ok),'message':str(msg)}
                rows.append(rec)
                print('RETURN','m',m,'lam',f'{vals[m]:.8g}','s',sign,'a',amp,
                      rec['class'],f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}',rec['coord_counts'],flush=True)
                if rec['class']=='novel' or e<args.live_score+0.02:
                    rr=dict(rec); rr['points']=y.tolist(); saved.append(rr)
    rows.sort(key=lambda r:r['energy']); saved.sort(key=lambda r:r['energy'])
    distinct=[]
    for r in saved:
        if any(abs(r['energy']-z['energy'])<2e-7 and r['coord_counts']==z['coord_counts'] for z in distinct): continue
        distinct.append(r)
        if len(distinct)>=12: break
    best=rows[0]['energy'] if rows else float('inf')
    out={'live_score':args.live_score,'hub_energy':float(hub_rec['energy']),'hub_triangle':sel['triangle'],
         'hub_coord_counts':counts(xhub),'delete_index':args.delete_index,'modes':modes,'amps':amps,
         'eigenvalues':[float(v) for v in vals],'hessian_gradient_calls':calls['n'],
         'rows':rows,'saved_distinct':distinct,'best_energy':float(best),'best_delta_live':float(best-args.live_score)}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('N961 hub mode return candidate below live; verify independently\n')

if __name__=='__main__': main()
