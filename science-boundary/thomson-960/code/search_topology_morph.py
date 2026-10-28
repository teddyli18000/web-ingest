#!/usr/bin/env python3
"""Continuous topology morph between the merged D2 and live p007 minima.

Align the 20-dislocation D2 configuration to the 24-dislocation live record by
multi-start ICP/Kabsch, solve a one-to-one Hungarian point correspondence, then
interpolate every matched point along the unit-sphere geodesic at several t.
Each morph is fully relaxed with a stable termwise energy-difference objective.

Unlike cut-and-splice, this path has no seam or duplicate-point pathology. The
relaxation may create/annihilate dislocation pairs as the morph crosses a
structural instability, so intermediate t values can reveal topologies absent
from either endpoint.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re

import numpy as np
from scipy.optimize import linear_sum_assignment, minimize
from scipy.spatial import cKDTree, ConvexHull
from scipy.spatial.transform import Rotation

N=960
PI=math.pi
D2_REL=pathlib.Path("problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json")


def cert_xyz(path):
    raw=json.loads(pathlib.Path(path).read_text())
    x=np.array([[a/d,b/d,c/d] for a,b,c,d in raw["points"]],float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def find_live(root):
    best=None
    for md in (root/"problems/p007-thomson-problem/shots").glob("*/*/SHOT.md"):
        m=re.search(r'^claimed_score\s*=\s*"([0-9.]+)"',md.read_text(),re.M)
        if m:
            item=(float(m.group(1)),md.parent)
            if best is None or item[0]<best[0]: best=item
    if best is None: raise RuntimeError("no merged p007 shot")
    return best


def kabsch(P,Q):
    U,S,Vt=np.linalg.svd(P.T@Q); R=U@Vt
    if np.linalg.det(R)<0: U[:,-1]*=-1; R=U@Vt
    return R


def icp(B,A,rng,starts=12,iters=15):
    tree=cKDTree(A); best=None
    seeds=[np.eye(3)]+[Rotation.random(random_state=rng).as_matrix() for _ in range(starts-1)]
    for R0 in seeds:
        R=R0.copy(); last=1e9
        for _ in range(iters):
            Y=B@R; dist,idx=tree.query(Y,k=1); R=R@kabsch(Y,A[idx])
            rms=float(np.sqrt(np.mean(dist*dist)))
            if abs(last-rms)<1e-11: break
            last=rms
        Y=B@R; dist,_=tree.query(Y,k=1); rms=float(np.sqrt(np.mean(dist*dist)))
        if best is None or rms<best[0]: best=(rms,R,Y)
    return best


def geodesic(A,B,t):
    dot=np.clip(np.sum(A*B,axis=1),-1,1); ang=np.arccos(dot); s=np.sin(ang)
    X=np.empty_like(A); small=s<1e-10
    X[small]=(1-t)*A[small]+t*B[small]
    ns=~small
    X[ns]=(np.sin((1-t)*ang[ns])/s[ns])[:,None]*A[ns]+(np.sin(t*ang[ns])/s[ns])[:,None]*B[ns]
    return X/np.linalg.norm(X,axis=1)[:,None]


def xyz_to_vars(x):
    return np.column_stack([np.arccos(np.clip(x[:,2],-1,1)),np.arctan2(x[:,1],x[:,0])]).ravel()


def vars_to_xyz(v):
    a=v.reshape(-1,2); th,ph=a[:,0],a[:,1]
    st,ct=np.sin(th),np.cos(th); cp,sp=np.cos(ph),np.sin(ph)
    x=np.column_stack([st*cp,st*sp,ct]); dth=np.column_stack([ct*cp,ct*sp,-st]); dph=np.column_stack([-st*sp,st*cp,np.zeros_like(st)])
    return x,dth,dph


def pair_terms_grad(v):
    x,dth,dph=vars_to_xyz(v); dots=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0); ga=w@x
    gt=np.sum(ga*dth,axis=1); gp=np.sum(ga*dph,axis=1)
    return inv[np.triu_indices(N,1)],np.column_stack([gt,gp]).ravel(),x


def raw_energy(x):
    d=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*d,1e-300); np.fill_diagonal(r2,np.inf)
    return float(np.sum(np.triu(1/np.sqrt(r2),1),dtype=np.longdouble))


def relax(x0,maxiter=1900):
    q0=xyz_to_vars(x0); ref,_,_=pair_terms_grad(q0); ref=np.asarray(ref,dtype=np.longdouble); E0=float(np.sum(ref,dtype=np.longdouble))
    def fg(v):
        t,g,_=pair_terms_grad(v); return float(np.sum(np.asarray(t,dtype=np.longdouble)-ref,dtype=np.longdouble)),g
    bounds=[(1e-8,PI-1e-8),(None,None)]*N
    r=minimize(fg,q0,jac=True,method='L-BFGS-B',bounds=bounds,
               options={'maxiter':maxiter,'gtol':1e-9,'ftol':1e-15,'maxls':80,'maxcor':40})
    delta,_=fg(r.x); x,_,_=vars_to_xyz(r.x)
    return E0+delta,x,int(r.nit),bool(r.success)


def coord_counts(x):
    h=ConvexHull(x); nbr=[set() for _ in range(N)]
    for tri in h.simplices:
        a,b,c=map(int,tri); nbr[a].update((b,c)); nbr[b].update((a,c)); nbr[c].update((a,b))
    deg=np.array([len(s) for s in nbr])
    return {str(k):int(np.sum(deg==k)) for k in sorted(set(map(int,deg)))}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('few_shots'); ap.add_argument('--seed',type=int,default=5011); ap.add_argument('--out',required=True)
    args=ap.parse_args(); root=pathlib.Path(args.few_shots); rng=np.random.default_rng(args.seed)
    live_score,live_dir=find_live(root); A=cert_xyz(live_dir/'certificate.json'); B=cert_xyz(root/D2_REL)
    rms,R,Ba=icp(B,A,rng)
    # Hungarian assignment on squared chord distances.
    cost=np.maximum(0.0,2-2*np.clip(A@Ba.T,-1,1))
    ia,ib=linear_sum_assignment(cost); assert np.array_equal(ia,np.arange(N))
    Bm=Ba[ib]; match_rms=float(np.sqrt(np.mean(np.sum((A-Bm)**2,axis=1))))
    print(f'live={live_score:.10f} icp_nn_rms={rms:.6g} hungarian_rms={match_rms:.6g}',flush=True)
    ts=[0.12,0.20,0.30,0.40,0.50,0.60,0.70,0.80,0.88]
    rows=[]; best=1e99; bestx=None
    for t in ts:
        X=geodesic(A,Bm,t); start=raw_energy(X); E,Y,nit,ok=relax(X); cc=coord_counts(Y) if E<live_score+0.2 else None
        row={'t':t,'start_energy':start,'energy':E,'delta_vs_live':E-live_score,'nit':nit,'success':ok,'coord_counts':cc}
        rows.append(row); print(f't={t:.2f} start={start:.9f} E={E:.12f} dlive={E-live_score:+.9g} nit={nit} coord={cc}',flush=True)
        if E<best: best=E; bestx=Y.copy()
    out={'seed':args.seed,'live_score':live_score,'live_shot':str(live_dir.relative_to(root)),'icp_nn_rms':rms,'hungarian_rms':match_rms,
         'rows':rows,'best_float_energy':best,'best_delta_vs_live':best-live_score,
         'best_points':bestx.tolist() if best<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__': main()
