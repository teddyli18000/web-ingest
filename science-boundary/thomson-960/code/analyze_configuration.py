#!/usr/bin/env python3
"""Structural diagnostics for an N=960 Thomson floating configuration.

Reads JSON containing `points` (or a raw xyz list), normalizes to S^2, computes
spherical Delaunay connectivity via the 3-D convex hull, coordination-number
counts/defect charge, and approximate low-order rotational symmetries using
nearest-neighbor set matching.
"""
from __future__ import annotations
import argparse, json, math, pathlib
from collections import Counter
import numpy as np
from scipy.spatial import ConvexHull, cKDTree


def load(path):
    d=json.loads(pathlib.Path(path).read_text())
    p=d.get('points') if isinstance(d,dict) else d
    if p is None: raise ValueError('no points')
    x=np.asarray(p,float); x/=np.linalg.norm(x,axis=1)[:,None]
    return x


def axis_rotation(axis,angle):
    a=np.asarray(axis,float); a/=np.linalg.norm(a)
    x,y,z=a; c=math.cos(angle); s=math.sin(angle); C=1-c
    return np.array([[c+x*x*C,x*y*C-z*s,x*z*C+y*s],
                     [y*x*C+z*s,c+y*y*C,y*z*C-x*s],
                     [z*x*C-y*s,z*y*C+x*s,c+z*z*C]])


def match_rotation(x,R):
    y=x@R.T; tree=cKDTree(x); d,idx=tree.query(y,k=1)
    unique=len(np.unique(idx))==len(x)
    return float(np.sqrt(np.mean(d*d))),float(np.max(d)),unique


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); args=ap.parse_args()
    x=load(args.input); n=len(x)
    hull=ConvexHull(x)
    nbr=[set() for _ in range(n)]
    for tri in hull.simplices:
        a,b,c=map(int,tri)
        nbr[a].update((b,c)); nbr[b].update((a,c)); nbr[c].update((a,b))
    deg=np.array([len(s) for s in nbr])
    counts=Counter(map(int,deg))
    charge=int(np.sum(6-deg))
    print('n',n,'hull_faces',len(hull.simplices),'coord_counts',dict(sorted(counts.items())),'sum_6_minus_z',charge)
    defects=np.where(deg!=6)[0]
    print('defect_vertices',len(defects),'five',int(np.sum(deg==5)),'seven',int(np.sum(deg==7)),
          'other',int(np.sum((deg!=5)&(deg!=6)&(deg!=7))))
    # inertia axes are useful candidates for residual rotational symmetries
    C=x.T@x; vals,vecs=np.linalg.eigh(C)
    print('second_moment_eigenvalues',' '.join(f'{v:.12f}' for v in vals))
    axes=[('x',(1,0,0)),('y',(0,1,0)),('z',(0,0,1))]
    axes += [(f'eig{i}',vecs[:,i]) for i in range(3)]
    for name,a in axes:
        for k in (2,3,4,5,6):
            rms,mx,uniq=match_rotation(x,axis_rotation(a,2*math.pi/k))
            if rms<1e-3:
                print(f'sym_candidate axis={name} order={k} rms={rms:.6e} max={mx:.6e} bijective={uniq}')

if __name__=='__main__': main()
