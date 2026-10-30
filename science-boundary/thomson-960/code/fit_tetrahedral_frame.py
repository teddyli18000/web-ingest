#!/usr/bin/env python3
"""Directly fit a canonical proper-tetrahedral rotation group to a point cloud.

This is a robust fallback for recovering the T frame of the historical N=972
Th Thomson minimum.  Rather than recovering one C2 and one C3 axis independently
and hoping they form a compatible pair, optimize a single SO(3) conjugation A:

    G(A) = { A R A^T : R in canonical T }.

The objective measures nearest-neighbor self-mapping error of the point cloud
under all nontrivial group elements.  Multiple random/Powell starts are cheap
relative to subsequent 960-point relaxations and avoid fragile axis pairing.
"""
from __future__ import annotations
import argparse, json, math, pathlib
import numpy as np
from scipy.optimize import differential_evolution, minimize
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation
from analyze_twinned_motif import load_xyz

G0=Rotation.create_group('T').as_matrix()


def frame(v): return Rotation.from_rotvec(np.asarray(v,float)).as_matrix()


def group_for(v):
    A=frame(v); return [A@R@A.T for R in G0]


def diagnostics(x,tree,v,subset=False):
    G=group_for(v); rms=[]; mx=[]; bij=[]
    ids=range(1,len(G)) if not subset else (1,2,3,4,5)
    for i in ids:
        d,p=tree.query(x@G[i].T,k=1)
        rms.append(float(np.sqrt(np.mean(d*d)))); mx.append(float(np.max(d)))
        bij.append(len(np.unique(p))==len(x))
    return max(rms),max(mx),all(bij),rms,mx


def objective(v,x,tree,subset=True):
    r,m,b,_,_=diagnostics(x,tree,v,subset=subset)
    return r+0.12*m


def fit(x,seed=97277,random_starts=14):
    tree=cKDTree(x); rng=np.random.default_rng(seed)
    # rotvec cube [-pi,pi]^3 over-parameterizes SO(3), but is robust for DE.
    de=differential_evolution(lambda v:objective(v,x,tree,True),[(-math.pi,math.pi)]*3,
                              seed=seed,popsize=12,maxiter=55,tol=1e-8,polish=False,workers=1)
    starts=[de.x,np.zeros(3)]
    starts += [Rotation.random(random_state=rng).as_rotvec() for _ in range(random_starts)]
    best=None
    for k,s in enumerate(starts):
        r=minimize(lambda v:objective(v,x,tree,False),s,method='Powell',
                   options={'maxiter':500,'xtol':1e-10,'ftol':1e-12})
        dr=diagnostics(x,tree,r.x,False); item=(dr[1],dr[0],not dr[2],float(r.fun),r.x.copy(),dr)
        print(f'FIT {k} fun={r.fun:.6g} rmsmax={dr[0]:.3e} max={dr[1]:.3e} bij={dr[2]} rotvec={r.x.tolist()}',flush=True)
        if best is None or item[:4]<best[:4]:best=item
    return best


def main():
    ap=argparse.ArgumentParser();ap.add_argument('xyz');ap.add_argument('--seed',type=int,default=97277);ap.add_argument('--out',required=True);args=ap.parse_args()
    x=load_xyz(args.xyz); b=fit(x,args.seed); _,_,_,fun,v,d=b; A=frame(v); G=group_for(v)
    out={'n':len(x),'objective':fun,'rotation_vector':v.tolist(),'frame':A.tolist(),
         'group':[R.tolist() for R in G],'rms_max':d[0],'max_error':d[1],'bijective':d[2],
         'element_rms':d[3],'element_max':d[4]}
    pathlib.Path(args.out).write_text(json.dumps(out,separators=(',',':'))+'\n')
    print('FINAL',out['rms_max'],out['max_error'],out['bijective'],flush=True)

if __name__=='__main__':main()
