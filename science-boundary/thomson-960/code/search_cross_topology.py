#!/usr/bin/env python3
"""Cross low-energy N=960 Thomson minima with different defect topologies.

Parent B is the merged 20-dislocation D2 Few Shots shot. Parent A is either the
live merged p007 record (24 dislocations, C3) or our durable symmetry-broken
+0.003280 24-dislocation neighbor.  We align B to A by multi-start ICP/Kabsch,
generate Deaven-Ho-like spherical cut-and-splice children at several population
fractions, screen out seam collisions and high raw energies, then fully relax
only the best candidates using a stable termwise energy-difference objective.

This intentionally tests topology-changing/global scar recombination rather
than the same-topology soft-mode basin graph already explored.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

import diagnose_soft_modes as sm

N=960
PI=math.pi
D2_REL=pathlib.Path("problems/p007-thomson-problem/shots/Abreto/thomson960-d2-ga/certificate.json")


def cert_xyz(path: pathlib.Path):
    raw=json.loads(path.read_text())
    x=np.array([[a/d,b/d,c/d] for a,b,c,d in raw["points"]],float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def json_xyz(path: pathlib.Path):
    raw=json.loads(path.read_text())
    pts=raw.get("points") if isinstance(raw,dict) else raw
    x=np.asarray(pts,float)
    return x/np.linalg.norm(x,axis=1)[:,None]


def find_live(root: pathlib.Path):
    best=None
    for md in (root/"problems/p007-thomson-problem/shots").glob("*/*/SHOT.md"):
        m=re.search(r'^claimed_score\s*=\s*"([0-9.]+)"',md.read_text(),re.M)
        if m:
            item=(float(m.group(1)),md.parent)
            if best is None or item[0]<best[0]: best=item
    if best is None: raise RuntimeError("no merged p007 shot")
    return best


def kabsch(P,Q):
    """Return row-vector rotation R minimizing ||P R - Q||."""
    H=P.T@Q
    U,S,Vt=np.linalg.svd(H)
    R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1
        R=U@Vt
    return R


def icp_align(B,A,rng,starts=8,iters=12):
    tree=cKDTree(A)
    seeds=[np.eye(3)]+[Rotation.random(random_state=rng).as_matrix() for _ in range(starts-1)]
    best=None
    for R0 in seeds:
        R=R0.copy()
        last=1e9
        for _ in range(iters):
            Y=B@R
            dist,idx=tree.query(Y,k=1)
            Rinc=kabsch(Y,A[idx])
            R=R@Rinc
            rms=float(np.sqrt(np.mean(dist*dist)))
            if abs(last-rms)<1e-10: break
            last=rms
        Y=B@R; dist,idx=tree.query(Y,k=1)
        rms=float(np.sqrt(np.mean(dist*dist)))
        if best is None or rms<best[0]: best=(rms,R,Y)
    return best


def xyz_to_vars(x):
    return np.column_stack([np.arccos(np.clip(x[:,2],-1,1)),np.arctan2(x[:,1],x[:,0])]).ravel()


def vars_to_xyz(v):
    a=v.reshape(-1,2); th,ph=a[:,0],a[:,1]
    st,ct=np.sin(th),np.cos(th); cp,sp=np.cos(ph),np.sin(ph)
    x=np.column_stack([st*cp,st*sp,ct])
    dth=np.column_stack([ct*cp,ct*sp,-st])
    dph=np.column_stack([-st*sp,st*cp,np.zeros_like(st)])
    return x,dth,dph


def pair_terms_grad(v):
    x,dth,dph=vars_to_xyz(v)
    dots=np.clip(x@x.T,-1,1)
    r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    inv=1/np.sqrt(r2); w=inv/r2; np.fill_diagonal(w,0)
    ga=w@x
    gt=np.sum(ga*dth,axis=1); gp=np.sum(ga*dph,axis=1)
    iu=np.triu_indices(N,1)
    return inv[iu],np.column_stack([gt,gp]).ravel(),x


def raw_energy_xyz(x):
    dots=np.clip(x@x.T,-1,1); r2=np.maximum(2-2*dots,1e-300); np.fill_diagonal(r2,np.inf)
    return float(np.sum(np.triu(1/np.sqrt(r2),1),dtype=np.longdouble))


def min_pair_chord(x):
    dots=x@x.T; np.fill_diagonal(dots,-1)
    return math.sqrt(max(0.0,2-2*float(np.max(dots))))


def stable_relax(x0,maxiter=1700):
    q0=xyz_to_vars(x0); ref,_,_=pair_terms_grad(q0)
    ref_ld=np.asarray(ref,dtype=np.longdouble)
    Eref=float(np.sum(ref_ld,dtype=np.longdouble))
    def fg(v):
        t,g,_=pair_terms_grad(v)
        delta=np.sum(np.asarray(t,dtype=np.longdouble)-ref_ld,dtype=np.longdouble)
        return float(delta),g
    bounds=[(1e-8,PI-1e-8),(None,None)]*N
    res=minimize(fg,q0,jac=True,method="L-BFGS-B",bounds=bounds,
                 options={"maxiter":maxiter,"gtol":1e-9,"ftol":1e-15,"maxls":70,"maxcor":40})
    delta,_=fg(res.x); x,_,_=vars_to_xyz(res.x)
    return Eref+delta,x,int(res.nit),bool(res.success)


def coord_counts(x):
    # Lightweight approximate coordination via convex hull only for final low children.
    try:
        from scipy.spatial import ConvexHull
        hull=ConvexHull(x); nbr=[set() for _ in range(N)]
        for tri in hull.simplices:
            a,b,c=map(int,tri); nbr[a].update((b,c)); nbr[b].update((a,c)); nbr[c].update((a,b))
        deg=np.array([len(s) for s in nbr])
        return {str(k):int(np.sum(deg==k)) for k in sorted(set(map(int,deg)))}
    except Exception:
        return None


def make_child(A,B,n,k):
    pa=A@n; pb=B@n
    ia=np.argpartition(pa,-k)[-k:]
    ib=np.argpartition(pb,N-k-1)[:N-k]
    return np.vstack([A[ia],B[ib]])


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots")
    ap.add_argument("--parent-a",choices=["record","neighbor"],default="record")
    ap.add_argument("--neighbor-json")
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--screen",type=int,default=64)
    ap.add_argument("--relax-top",type=int,default=4)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    root=pathlib.Path(args.few_shots); rng=np.random.default_rng(args.seed)
    live_score,live_dir=find_live(root)
    if args.parent_a=="record": A=cert_xyz(live_dir/"certificate.json")
    else:
        if not args.neighbor_json: raise ValueError("--neighbor-json required")
        A=json_xyz(pathlib.Path(args.neighbor_json))
    B=cert_xyz(root/D2_REL)
    icp_rms,R,Ba=icp_align(B,A,rng)
    print(f"live_score={live_score:.10f} A={args.parent_a} d2_icp_rms={icp_rms:.6g}",flush=True)

    safe=[]
    ks=np.array([280,320,360,400,440,480,520,560,600,640,680])
    for i in range(args.screen):
        n=rng.normal(size=3); n/=np.linalg.norm(n); k=int(rng.choice(ks))
        child=make_child(A,Ba,n,k); md=min_pair_chord(child)
        if md<0.055: continue
        E=raw_energy_xyz(child)
        safe.append((E,md,i,k,n.tolist()))
    safe.sort(key=lambda z:z[0])
    print(f"screened={args.screen} safe={len(safe)}",flush=True)
    for z in safe[:min(10,len(safe))]: print(f"screen E={z[0]:.9f} md={z[1]:.5f} i={z[2]} k={z[3]}",flush=True)

    rows=[]; best_e=1e99; best_x=None
    for rank,z in enumerate(safe[:args.relax_top]):
        E0,md,i,k,nlist=z; x=make_child(A,Ba,np.asarray(nlist),k)
        E,y,nit,ok=stable_relax(x)
        cc=coord_counts(y) if E<live_score+0.1 else None
        row={"rank":rank,"screen_index":i,"k_from_A":k,"start_energy":E0,"min_pair":md,
             "energy":E,"delta_vs_live":E-live_score,"nit":nit,"success":ok,"coord_counts":cc}
        rows.append(row)
        print(f"relax rank={rank} k={k} E={E:.12f} dlive={E-live_score:+.9g} nit={nit} coord={cc}",flush=True)
        if E<best_e: best_e=E; best_x=y.copy()

    out={"parent_a":args.parent_a,"seed":args.seed,"live_score":live_score,
         "live_shot":str(live_dir.relative_to(root)),"d2_icp_rms":icp_rms,
         "screened":args.screen,"safe_count":len(safe),"rows":rows,
         "best_float_energy":best_e,"best_delta_vs_live":best_e-live_score,
         "best_points":best_x.tolist() if best_x is not None and best_e<live_score-2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(out,indent=2)+"\n")

if __name__=="__main__": main()
