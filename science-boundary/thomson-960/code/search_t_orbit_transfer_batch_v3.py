#!/usr/bin/env python3
"""Direct-frame fallback for exhaustive N972 -> N960 T-orbit transfer.

Overrides the fragile axis-pair step in search_t_orbit_transfer_batch with a
single SO(3) fit of the canonical proper-tetrahedral group to the N=972 point
cloud. Downstream orbit enumeration, relaxation, Hessian classification, and
portal release are exactly the base batch implementation.
"""
from __future__ import annotations
import numpy as np
from scipy.spatial import cKDTree

import search_t_orbit_transfer_batch as base
from fit_tetrahedral_frame import fit, frame, group_for


def direct_group(x,n2_unused,n3_unused):
    best=fit(x,seed=97331,random_starts=8)
    _,_,_,fun,v,d=best
    G=group_for(v);tree=cKDTree(x);perms=[];worst=0.0;rmax=0.0
    for R in G:
        dist,p=tree.query(x@R.T,k=1)
        if len(np.unique(p))!=len(x):
            raise RuntimeError('direct fitted T frame is not bijective')
        perms.append(np.asarray(p,int));worst=max(worst,float(np.max(dist)))
        rmax=max(rmax,float(np.sqrt(np.mean(dist*dist))))
    if worst>2e-3:
        raise RuntimeError(f'direct T fit validation too poor: max={worst:.3e}, rms={rmax:.3e}, fit={fun:.3e}')
    A=frame(v)
    # Axis values are diagnostic-only in the base return shape.
    return G,perms,worst,rmax,A,np.array([1.,0.,0.]),np.array([1.,1.,1.])/np.sqrt(3.)

base.exact_t_group_from_axes=direct_group

if __name__=='__main__':
    base.main()
