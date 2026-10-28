#!/usr/bin/env python3
"""One-cycle oscillating-size basin search starting from the live p007 record.

Implements the key neighboring-size idea of Amore & Wales (2026) directly from
Few Shots' current best N=960 configuration:

  down: 960 -> several relaxed N=959 deletions -> Voronoi insertions -> N=960
  up:   960 -> Voronoi insertions -> several relaxed N=961 states -> deletions -> N=960

Insertion candidates are spherical Voronoi vertices, obtained as outward normals
of convex-hull triangular facets. Removal candidates are ranked by individual
Coulomb contribution. Each candidate is fully relaxed without symmetry.

Requires numpy/scipy.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import ConvexHull

P007 = pathlib.Path("problems/p007-thomson-problem")
PI = math.pi


def find_live(root: pathlib.Path):
    best = None
    for md in (root / P007 / "shots").glob("*/*/SHOT.md"):
        m = re.search(r'^claimed_score\s*=\s*"([0-9.]+)"', md.read_text(), re.M)
        if not m:
            continue
        item = (float(m.group(1)), md.parent)
        if best is None or item[0] < best[0]:
            best = item
    if best is None:
        raise RuntimeError("no merged p007 shot")
    return best


def load_cert(path: pathlib.Path) -> np.ndarray:
    raw = json.loads(path.read_text())
    x = np.array([[a/d, b/d, c/d] for a,b,c,d in raw["points"]], dtype=float)
    return x / np.linalg.norm(x, axis=1)[:,None]


def xyz_to_vars(x):
    th = np.arccos(np.clip(x[:,2], -1, 1))
    ph = np.arctan2(x[:,1], x[:,0])
    return np.column_stack([th,ph]).ravel()


def vars_to_xyz(v):
    a = v.reshape(-1,2)
    th, ph = a[:,0], a[:,1]
    st, ct = np.sin(th), np.cos(th)
    cp, sp = np.cos(ph), np.sin(ph)
    x = np.column_stack([st*cp, st*sp, ct])
    dth = np.column_stack([ct*cp, ct*sp, -st])
    dph = np.column_stack([-st*sp, st*cp, np.zeros_like(st)])
    return x, dth, dph


def energy_contrib(x):
    dots = np.clip(x @ x.T, -1.0, 1.0)
    r2 = np.maximum(2.0 - 2.0*dots, 1e-300)
    np.fill_diagonal(r2, np.inf)
    inv = 1.0 / np.sqrt(r2)
    return float(np.sum(np.triu(inv,1))), np.sum(inv,axis=1)


def fg(v):
    x, dth, dph = vars_to_xyz(v)
    dots = np.clip(x @ x.T, -1.0, 1.0)
    r2 = np.maximum(2.0 - 2.0*dots, 1e-300)
    np.fill_diagonal(r2, np.inf)
    inv = 1.0/np.sqrt(r2)
    f = float(np.sum(np.triu(inv,1)))
    w = inv/r2
    np.fill_diagonal(w,0.0)
    gc = w @ x - np.sum(w,axis=1)[:,None]*x
    gt = np.sum(gc*dth,axis=1)
    gp = np.sum(gc*dph,axis=1)
    return f, np.column_stack([gt,gp]).ravel()


def relax(x, maxiter=900):
    v0 = xyz_to_vars(x)
    bounds = [(1e-8,PI-1e-8),(None,None)]*len(x)
    res = minimize(fg, v0, jac=True, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter":maxiter,"gtol":3e-9,"ftol":1e-15,
                            "maxls":40,"maxcor":20})
    y,_,_ = vars_to_xyz(res.x)
    return float(res.fun), y, int(res.nit), bool(res.success)


def insertion_sites(x):
    hull = ConvexHull(x)
    sites=[]
    for tri in hull.simplices:
        a,b,c=x[tri]
        n=np.cross(b-a,c-a)
        nn=np.linalg.norm(n)
        if nn < 1e-14:
            continue
        n=n/nn
        if float(n @ a) < 0:
            n=-n
        sites.append(n)
    y=np.array(sites)
    # Rank all spherical Voronoi vertices by potential of the inserted charge.
    vals=[]
    for lo in range(0,len(y),300):
        z=y[lo:lo+300]
        dots=np.clip(z @ x.T,-1.0,1.0)
        vals.extend(np.sum(1.0/np.sqrt(np.maximum(2.0-2.0*dots,1e-15)),axis=1))
    return y, np.asarray(vals)


def top_removals(x,p):
    _,c=energy_contrib(x)
    return np.argsort(c)[-p:][::-1], c


def first_leg_down(x,p):
    ids,c=top_removals(x,p)
    out=[]
    for rank,j in enumerate(ids):
        y=np.delete(x,int(j),axis=0)
        e,z,nit,ok=relax(y)
        print(f"down1 rank={rank} removed={j} contrib={c[j]:.9f} E959={e:.12f} nit={nit} ok={ok}",flush=True)
        out.append((e,z,rank,int(j)))
    return sorted(out,key=lambda q:q[0])


def first_leg_up(x,p):
    sites,vals=insertion_sites(x)
    ids=np.argsort(vals)[:p]
    out=[]
    for rank,j in enumerate(ids):
        y=np.vstack([x,sites[j]])
        e,z,nit,ok=relax(y)
        print(f"up1 rank={rank} site={j} potential={vals[j]:.9f} E961={e:.12f} nit={nit} ok={ok}",flush=True)
        out.append((e,z,rank,int(j)))
    return sorted(out,key=lambda q:q[0])


def return_from_959(state,p,label):
    e959,x,_,_=state
    sites,vals=insertion_sites(x)
    ids=np.argsort(vals)[:p]
    out=[]
    for rank,j in enumerate(ids):
        y=np.vstack([x,sites[j]])
        e,z,nit,ok=relax(y,1200)
        print(f"down2 {label} rank={rank} site={j} potential={vals[j]:.9f} E960={e:.12f} nit={nit} ok={ok}",flush=True)
        out.append((e,z,{"parent_e":e959,"return_rank":rank,"site":int(j)}))
    return out


def return_from_961(state,p,label):
    e961,x,_,_=state
    ids,c=top_removals(x,p)
    out=[]
    for rank,j in enumerate(ids):
        y=np.delete(x,int(j),axis=0)
        e,z,nit,ok=relax(y,1200)
        print(f"up2 {label} rank={rank} removed={j} contrib={c[j]:.9f} E960={e:.12f} nit={nit} ok={ok}",flush=True)
        out.append((e,z,{"parent_e":e961,"return_rank":rank,"removed":int(j)}))
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("few_shots")
    ap.add_argument("--route",choices=["down","up"],required=True)
    ap.add_argument("--p",type=int,default=5)
    ap.add_argument("--parents",type=int,default=2)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    root=pathlib.Path(args.few_shots)
    live_score,shot=find_live(root)
    x=load_cert(shot/"certificate.json")
    e0,x0,nit,ok=relax(x,600)
    print(f"live={shot.relative_to(root)} verifier={live_score:.10f} polished={e0:.12f} nit={nit} ok={ok}",flush=True)

    candidates=[]
    if args.route=="down":
        first=first_leg_down(x0,args.p)
        for k,state in enumerate(first[:args.parents]):
            candidates += return_from_959(state,args.p,f"parent={k}")
    else:
        first=first_leg_up(x0,args.p)
        for k,state in enumerate(first[:args.parents]):
            candidates += return_from_961(state,args.p,f"parent={k}")

    candidates.sort(key=lambda q:q[0])
    best_e,best_x,meta=candidates[0]
    improvement=e0-best_e
    print(f"BEST route={args.route} E960={best_e:.12f} improvement={improvement:.12g}",flush=True)
    data={"route":args.route,"p":args.p,"parents":args.parents,
          "live_score":live_score,"polished_live_energy":e0,
          "best_float_energy":best_e,"improvement":improvement,
          "meta":meta,
          "best_points":best_x.tolist() if improvement > 2e-7 else None}
    pathlib.Path(args.out).write_text(json.dumps(data,indent=2)+"\n")

if __name__=="__main__":
    main()
