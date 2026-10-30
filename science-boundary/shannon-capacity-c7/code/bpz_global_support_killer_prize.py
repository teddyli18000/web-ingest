#!/usr/bin/env python3
"""Exact all-k weak prize for arbitrary single-row BPZ support defects.

Select any pairwise nonconfusable set Y of five-dimensional outsiders with
nonempty support against the pinned 359-point core B.  Let C be the union of
all supports and H the union of BPZ private-pair killer colors.  This solves
exactly

    max |Y| - |C| - |H|.

The empty set gives value zero.  A nonpositive optimum closes every single-row
support-defect family under the existing conditional killer lower bound, without
fixing k or enumerating support types.  A positive optimum is only a promising
necessary-bound survivor and still requires the full 10D terminal-periphery
optimization before any breakthrough claim.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from bpz_joint_row_defects_maxsat import load_geometry
from bpz_irreducible_support_sat import conflict5,killer_mask

def solve(root:Path,solver:str):
    _base,ring,B,fam=load_geometry(root.resolve());B=set(B);owners=sorted(B);oi={b:i for i,b in enumerate(owners)}
    raw=json.loads((root/'data'/'base_c7.json').read_text());pairs=raw['private_pairs']
    candidates=[];supports=[];kmasks=[]
    for z in range(ring.n):
        if z in B:continue
        S=tuple(sorted(ring.NB[z]&B))
        if not S:continue
        candidates.append(z);supports.append(tuple(oi[b] for b in S));kmasks.append(killer_mask(z,pairs))
    n=len(candidates);m=len(owners);xidx={z:i for i,z in enumerate(candidates)};y0=n+1;c0=y0+m
    w=WCNF();conf=0;impl=0;kimpl=0
    candset=set(candidates)
    for i,z in enumerate(candidates):
        for q in ring.NB[z]&candset:
            j=xidx[q]
            if j>i:w.append([-(i+1),-(j+1)]);conf+=1
        for u in supports[i]:w.append([-(i+1),y0+u]);impl+=1
        km=kmasks[i]
        for j in range(8):
            if km>>j&1:w.append([-(i+1),c0+j]);kimpl+=1
    for i in range(n):w.append([i+1],weight=1)
    for j in range(m):w.append([-(y0+j)],weight=1)
    for j in range(8):w.append([-(c0+j)],weight=1)
    t=time.time()
    with RC2(w,solver=solver,adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('no RC2 model')
    pos={z for z in model if z>0};sel=[i for i in range(n) if i+1 in pos]
    Y=[candidates[i] for i in sel];C=set();km=0
    for i in sel:C.update(supports[i]);km|=kmasks[i]
    ysel={j for j in range(m) if y0+j in pos};csel={j for j in range(8) if c0+j in pos}
    if ysel!=C:raise RuntimeError(('owner drift',len(ysel),len(C)))
    actual_colors={j for j in range(8) if km>>j&1}
    if csel!=actual_colors:raise RuntimeError(('killer drift',csel,actual_colors))
    for ii,a in enumerate(Y):
        for b in Y[ii+1:]:
            if b in ring.NB[a]:raise RuntimeError(('conflict',a,b))
    objective=len(Y)-len(C)-len(actual_colors)
    if objective!=n-cost:raise RuntimeError(('objective',objective,n-cost))
    return {'method':'exact-global-support-killer-weak-prize','solver':solver,'seconds':time.time()-t,'candidate_count':n,'conflict_clauses':conf,'support_implications':impl,'killer_implications':kimpl,'selected_count':len(Y),'owner_count':len(C),'killer_count':len(actual_colors),'objective':objective,'selected':sorted(Y),'owners':[owners[i] for i in sorted(C)],'killer_colors':sorted(actual_colors)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--solver',default='g4');a=ap.parse_args()
    r=solve(a.tan_root,a.solver);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ('selected','owners')},sort_keys=True))
if __name__=='__main__':main()
