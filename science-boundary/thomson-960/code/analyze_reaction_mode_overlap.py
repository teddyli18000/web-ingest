#!/usr/bin/env python3
"""Project a labeled Thomson reaction displacement onto endpoint Hessian modes."""
from __future__ import annotations
import argparse,json,math,pathlib
import numpy as np
from scipy.sparse.linalg import eigsh
import diagnose_soft_modes as sm

N=960


def load(path):
    d=json.loads(pathlib.Path(path).read_text()); p=d.get('points') if isinstance(d,dict) else d
    if p is None or len(p)!=N: raise ValueError('expected 960 labeled points')
    x=np.asarray(p,float); return x/np.linalg.norm(x,axis=1)[:,None]


def reaction_physical(S,T):
    q=sm.xyz_to_vars(S); x,dth,dph=sm.vars_to_xyz(q)
    dot=np.clip(np.sum(S*T,axis=1),-1,1); a=np.arccos(dot); sa=np.sin(a)
    L=np.zeros_like(S); good=sa>1e-12
    L[good]=(a[good]/sa[good])[:,None]*(T[good]-dot[good,None]*S[good])
    bad=~good
    if np.any(bad):
        z=T[bad]-S[bad]; z-=np.sum(z*S[bad],axis=1)[:,None]*S[bad]; L[bad]=z
    sinth=np.maximum(np.sin(q.reshape(-1,2)[:,0]),1e-10)
    ephi=dph/sinth[:,None]
    y=np.column_stack([np.sum(L*dth,axis=1),np.sum(L*ephi,axis=1)]).ravel()
    Q=sm.rotation_basis(q); y-=Q@(Q.T@y)
    return q,y,Q


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('source_json'); ap.add_argument('target_json')
    ap.add_argument('--k',type=int,default=48); ap.add_argument('--fd-step',type=float,default=3e-6)
    ap.add_argument('--out',required=True); args=ap.parse_args()
    S=load(args.source_json); T=load(args.target_json); q,y,Q=reaction_physical(S,T)
    yn=float(np.linalg.norm(y)); u=y/yn
    H,raw,Qh,calls=sm.build_hessian(q,args.fd_step,1e6)
    rng=np.random.default_rng(20261030); v0=rng.normal(size=len(q)); v0-=Qh@(Qh.T@v0); v0/=np.linalg.norm(v0)
    vals,V=eigsh(H,k=args.k,which='SA',tol=1e-5,maxiter=1100,ncv=max(80,2*args.k+8),v0=v0)
    o=np.argsort(vals); vals=vals[o]; V=V[:,o]
    ovs=[]
    for j in range(V.shape[1]):
        v=V[:,j].copy(); v-=Qh@(Qh.T@v); v/=np.linalg.norm(v)
        ov=float(v@u); ovs.append(ov)
    power=np.asarray(ovs)**2; cum=np.cumsum(power)
    order=np.argsort(-power)
    rows=[{'mode':int(j),'eigenvalue':float(vals[j]),'overlap':float(ovs[j]),'power':float(power[j]),
           'cumulative_low_modes':float(cum[j])} for j in range(len(vals))]
    top=[rows[int(j)] for j in order[:min(16,len(order))]]
    print('reaction_norm',yn,'k',args.k,'captured_power',float(cum[-1]),flush=True)
    print('cum6',float(cum[min(5,len(cum)-1)]),'cum12',float(cum[min(11,len(cum)-1)]),
          'cum24',float(cum[min(23,len(cum)-1)]),flush=True)
    for r in top: print('TOP',r,flush=True)
    out={'reaction_norm':yn,'k':args.k,'eigenvalues':[float(v) for v in vals],
         'mode_rows':rows,'top_modes':top,'captured_power':float(cum[-1]),
         'cum6':float(cum[min(5,len(cum)-1)]),'cum12':float(cum[min(11,len(cum)-1)]),
         'cum24':float(cum[min(23,len(cum)-1)]),'hessian_gradient_calls':calls['n']}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__': main()
