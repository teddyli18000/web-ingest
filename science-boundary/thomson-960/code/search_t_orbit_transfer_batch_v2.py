#!/usr/bin/env python3
"""Robust entry point for exhaustive N972 -> N960 T-orbit transfer.

The first batch recovered one C2 and one C3 axis independently.  Although each
axis can be a good standalone symmetry direction, numerical axis recovery may
select a local minimum that does not yield a stable exact tetrahedral frame when
paired.  This wrapper recovers several symmetry-axis lines independently,
deduplicates them, tries all C2/C3 pairs, and chooses the exact canonical-T
conjugation with the best point-cloud validation.  The downstream exhaustive
orbit transfer/classification/release logic is unchanged.
"""
from __future__ import annotations
import math
import numpy as np

import search_t_orbit_transfer_batch as base

PI=math.pi
_ORIG=base.exact_t_group_from_axes


def _line_unique(rows, score, axis, tol=0.9995):
    axis=np.asarray(axis,float); axis/=np.linalg.norm(axis)
    for i,(s,a) in enumerate(rows):
        if abs(float(axis@a))>tol:
            if score<s: rows[i]=(score,axis)
            return
    rows.append((score,axis))


def robust_exact_t_group(x,n2_first,n3_first):
    c2=[]; c3=[]
    # Include the axes already paid for by base.main.
    s2=base.symmetry_objective([math.acos(np.clip(n2_first[2],-1,1)),math.atan2(n2_first[1],n2_first[0])],x,base.cKDTree(x),PI)
    s3=base.symmetry_objective([math.acos(np.clip(n3_first[2],-1,1)),math.atan2(n3_first[1],n3_first[0])],x,base.cKDTree(x),2*PI/3)
    _line_unique(c2,s2,n2_first); _line_unique(c3,s3,n3_first)
    # True T has three C2 axis lines and four C3 axis lines.  Multiple global
    # searches are cheap compared with the downstream orbit relaxations.
    for seed in range(97220,97232):
        if len(c2)<3:
            s,a=base.recover_axis(x,PI,seed); _line_unique(c2,s,a)
        if len(c3)<4:
            s,a=base.recover_axis(x,2*PI/3,seed+100); _line_unique(c3,s,a)
        if len(c2)>=3 and len(c3)>=4: break
    c2.sort(key=lambda t:t[0]); c3.sort(key=lambda t:t[0])
    print('C2_AXES',[(s,a.tolist()) for s,a in c2],flush=True)
    print('C3_AXES',[(s,a.tolist()) for s,a in c3],flush=True)
    best=None; errors=[]
    target=1/math.sqrt(3)
    # Prefer geometrically compatible pairs, but try all recovered lines.
    pairs=[]
    for s2,a2 in c2:
        for s3,a3 in c3:
            pairs.append((abs(abs(float(a2@a3))-target),s2+s3,a2,a3))
    pairs.sort(key=lambda t:(t[0],t[1]))
    for mismatch,score,a2,a3 in pairs:
        try:
            r=_ORIG(x,a2,a3)
            item=(r[2],r[3],mismatch,score,r)
            if best is None or item[:4]<best[:4]:best=item
        except Exception as e:
            errors.append((mismatch,score,repr(e)))
    if best is None:
        raise RuntimeError('no recovered C2/C3 pair produced a valid T frame; '+str(errors[:8]))
    print(f'T_FRAME selected max={best[0]:.3e} rmsmax={best[1]:.3e} angle_mismatch={best[2]:.3e} axis_score_sum={best[3]:.3e}',flush=True)
    return best[4]


base.exact_t_group_from_axes=robust_exact_t_group

if __name__=='__main__':
    base.main()
