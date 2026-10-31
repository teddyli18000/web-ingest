#!/usr/bin/env python3
"""Search transverse geometric exits at an N961 fractional-occupancy boundary.

The label960 occupancy fade has a validated discontinuity in the N960 return:
hard deletion at lambda=1 reaches A, while adiabatic fading to lambda=0 reaches
R.  Once a projection scan brackets the A/R switch, reproduce a selected
fractional minimum on the same adiabatic branch, compute its true weighted
physical tangent Hessian, perturb along the lowest non-rigid modes, delete the
fractional particle, and fully repolish the remaining 960 unit charges.

This is deliberately a 2-D reformulation (occupancy x geometry), not a denser
one-dimensional lambda scan.
"""
from __future__ import annotations
import argparse,json,math,pathlib
from collections import Counter
import numpy as np
from scipy.sparse.linalg import LinearOperator,eigsh

import diagnose_soft_modes as sm
import search_soft_pair as sp
from search_live_size_bounce import load_points,voronoi_candidates,relax as size_relax
from search_n972_mobile_fractional_homotopy import stable_weighted_relax,weighted_terms_grad
from search_from_seed_modes import stable_relax_q
from search_e564_defect_flip_parallel import topology

KNOWN={'A':444368.3956862258,'B':444368.4029728613,'D':444368.41099308443,'e432':444368.4322496275}


def counts(x):
    d,_=topology(x); c=Counter(map(int,d)); return {str(k):int(v) for k,v in sorted(c.items())}


def classify(e,live):
    refs=dict(KNOWN); refs['R']=float(live)
    n,err=min(((k,abs(float(e)-v)) for k,v in refs.items()),key=lambda z:z[1])
    return n if err<2e-6 else 'novel'


def parse_schedule(s,target):
    vals=[float(z) for z in s.split(',') if z.strip()]
    if not vals or abs(vals[0]-1)>1e-12: raise ValueError('schedule must start at 1')
    if any(vals[i+1]>vals[i]+1e-14 for i in range(len(vals)-1)): raise ValueError('schedule must decrease')
    if all(abs(v-target)>1e-12 for v in vals): vals.append(float(target)); vals=sorted(vals,reverse=True)
    vals=[v for v in vals if v>=target-1e-12]
    if abs(vals[-1]-target)>1e-12: vals.append(float(target))
    return vals


def weighted_hessian(q0,charges,fd_step,rot_penalty):
    n=len(q0); scale=sm.physical_scale(q0); invs=1.0/scale; Qrot=sm.rotation_basis(q0); calls={'n':0}
    def grad(q): return weighted_terms_grad(q,charges)[1]
    def raw_hy(y):
        yn=float(np.linalg.norm(y))
        if yn==0: return np.zeros_like(y)
        u=np.asarray(y,float)/yn; dq=invs*u
        gp=grad(q0+fd_step*dq); gm=grad(q0-fd_step*dq); calls['n']+=2
        hq=(gp-gm)*(yn/(2*fd_step))
        return invs*hq
    def mv(y):
        y=np.asarray(y,float); z=raw_hy(y); return z+rot_penalty*(Qrot@(Qrot.T@y))
    return LinearOperator((n,n),matvec=mv,dtype=float),raw_hy,Qrot,calls


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('a_json'); ap.add_argument('--lambda-value',type=float,required=True)
    ap.add_argument('--schedule',default='1,.8,.6,.4,.25,.15,.1,.075,.06,.05,.04,.03,.025,.02,.015,.01,.007,.005,.003,.001,0')
    ap.add_argument('--modes',default='0,1,2,3'); ap.add_argument('--amps',default='.0015,.003,.006,.012,.02')
    ap.add_argument('--k',type=int,default=8); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--weighted-maxiter',type=int,default=1800); ap.add_argument('--return-maxiter',type=int,default=4200)
    ap.add_argument('--live-score',type=float,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    lam=float(args.lambda_value)
    if not (0<=lam<=1): raise ValueError(lam)

    _,a=load_points(pathlib.Path(args.a_json)); sel=voronoi_candidates(a)[3]
    hub=size_relax(np.vstack([a,np.asarray(sel['point'],float)[None,:]]),3200); x=np.asarray(hub['points'],float)
    if abs(hub['energy']-445303.247369582)>5e-4: raise RuntimeError(f'unexpected hub {hub["energy"]}')
    trace=[]
    for lv in parse_schedule(args.schedule,lam):
        charges=np.ones(961,float); charges[960]=lv
        ew,x,nit,ok,msg,grms=stable_weighted_relax(x,charges,args.weighted_maxiter)
        trace.append({'lambda':lv,'energy':float(ew),'grms':float(grms),'nit':int(nit),'success':bool(ok)})
        print('CONT','L',lv,'Ew',f'{ew:.12f}','grms',f'{grms:.3g}','nit',nit,'ok',ok,flush=True)
    q0=sm.xyz_to_vars(x); charges=np.ones(961,float); charges[960]=lam
    # Baseline genuine N960 projection.
    eb,rawb,yb,nitb,okb,msgb=stable_relax_q(sm.xyz_to_vars(np.delete(x,960,axis=0)),maxiter=args.return_maxiter)
    base={'energy':float(eb),'delta_live':float(eb-args.live_score),'class':classify(eb,args.live_score),
          'coord_counts':counts(yb),'nit':int(nitb),'success':bool(okb),'message':str(msgb)}
    print('BASE',base['class'],f'{eb:.12f}','dLive',f"{base['delta_live']:+.9g}",base['coord_counts'],flush=True)

    H,raw_hy,Qrot,calls=weighted_hessian(q0,charges,args.fd_step,1e6)
    modes=[int(z) for z in args.modes.split(',') if z.strip()]; amps=[float(z) for z in args.amps.split(',') if z.strip()]
    k=max(args.k,max(modes)+1); rng=np.random.default_rng(961000+int(round(lam*1e6)))
    v0=rng.normal(size=len(q0)); v0-=Qrot@(Qrot.T@v0)
    vals,V=eigsh(H,k=k,which='SA',tol=2e-5,maxiter=800,ncv=max(40,3*k),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    print('LAMBDAS',[float(v) for v in vals],flush=True)
    rows=[]; saved=[]
    for m in modes:
        d=V[:,m].copy(); d-=Qrot@(Qrot.T@d); d/=np.linalg.norm(d)
        for sign in (-1,1):
            for amp in amps:
                qp=sp.exp_perturb(q0,d*sign,amp); xp,_,_=sm.vars_to_xyz(qp)
                e,raw,y,nit,ok,msg=stable_relax_q(sm.xyz_to_vars(np.delete(xp,960,axis=0)),maxiter=args.return_maxiter)
                rec={'mode':m,'eigenvalue':float(vals[m]),'sign':sign,'amp':amp,'energy':float(e),
                     'delta_live':float(e-args.live_score),'class':classify(e,args.live_score),
                     'coord_counts':counts(y),'nit':int(nit),'success':bool(ok),'message':str(msg)}
                rows.append(rec)
                print('RETURN','m',m,'eig',f'{vals[m]:.8g}','s',sign,'a',amp,rec['class'],
                      f'{e:.12f}','dLive',f'{e-args.live_score:+.9g}',rec['coord_counts'],flush=True)
                if rec['class']=='novel' or e<args.live_score+0.02:
                    rr=dict(rec); rr['points']=y.tolist(); saved.append(rr)
    rows.sort(key=lambda r:r['energy']); saved.sort(key=lambda r:r['energy'])
    distinct=[]
    for r in saved:
        if any(abs(r['energy']-z['energy'])<2e-7 and r['coord_counts']==z['coord_counts'] for z in distinct): continue
        distinct.append(r)
        if len(distinct)>=12: break
    best=min([base['energy']]+[r['energy'] for r in rows])
    out={'live_score':float(args.live_score),'lambda':lam,'hub_energy':float(hub['energy']),'hub_triangle':sel['triangle'],
         'continuation_trace':trace,'baseline':base,'eigenvalues':[float(v) for v in vals],
         'modes':modes,'amps':amps,'hessian_gradient_calls':calls['n'],'rows':rows,'saved_distinct':distinct,
         'best_energy':float(best),'best_delta_live':float(best-args.live_score),
         'fractional_points':x.tolist()}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    if best<args.live_score-2e-7:
        pathlib.Path(str(args.out)+'.BREAKTHROUGH').write_text('fractional boundary transverse candidate below live; verify independently\n')

if __name__=='__main__': main()
