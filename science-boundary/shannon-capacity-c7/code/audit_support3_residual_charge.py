#!/usr/bin/env python3
"""Audit the charge-separation premise in the first support3 residual reduction.

The residual script keeps all exception-containing candidates and only those
regular×regular candidates whose assigned owner cell lies in the exception
footprint K.  Omitted regular candidates are intended to be charged injectively
to assigned cells outside K.

For that argument to be valid as stated, an omitted selected candidate's charge
cell must not already be activated by a retained selected regular candidate.
This audit searches for a two-candidate counterexample to that separation:

  q=(u,v) omitted because m(q)=(f(u),f(v)) is outside K;
  r=(x,y) retained because m(r) is inside K;
  q and r are independent in C7^5 strong-square;
  nevertheless m(q) lies in S(x)×S(y), so r already deletes q's charge cell.

Finding one does not itself produce a positive-prize construction, but it
invalidates the simple disjoint-charge proof and means a negative residual
optimum cannot be promoted to a full-family closure without a stronger argument.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from bpz_support3_first_mus_residual_prize import build_support2_assignment,EXCEPTIONS
import bpz_joint_row_defects_maxsat as J

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();root=a.tan_root.resolve()
    _base,ring,B,_fam=J.load_geometry(root);B=set(B)
    regular,support,fmap=build_support2_assignment(ring,B)
    for z in EXCEPTIONS:support[z]=tuple(sorted(ring.NB[z]&B))
    factors=regular+list(EXCEPTIONS)
    K=set()
    for e in EXCEPTIONS:
        for u in factors:
            for aa in support[e]:
                for bb in support[u]:K.add((aa,bb));K.add((bb,aa))
    retained=[];omitted=[]
    for u in regular:
        for v in regular:
            m=(fmap[u],fmap[v])
            (retained if m in K else omitted).append((u,v,m))
    # Index retained candidates by every core cell their support rectangle touches.
    bycell={}
    for x,y,mr in retained:
        for aa in support[x]:
            for bb in support[y]:bycell.setdefault((aa,bb),[]).append((x,y,mr))
    witness=None;checks=0
    for u,v,m in omitted:
        for x,y,mr in bycell.get(m,()):
            checks+=1
            # Product conflict iff both coordinates conflict.
            if x in ring.NB[u] and y in ring.NB[v]:continue
            witness={'omitted':[u,v],'omitted_charge':list(m),'omitted_support':[list(support[u]),list(support[v])],'retained':[x,y],'retained_assigned_cell':list(mr),'retained_support':[list(support[x]),list(support[y])],'charge_in_retained_rectangle':True,'pair_independent':True}
            break
        if witness:break
    out={'method':'audit-support3-residual-charge-separation','regular_factors':len(regular),'exceptions':list(EXCEPTIONS),'exception_footprint_cells':len(K),'retained_regular_pairs':len(retained),'omitted_regular_pairs':len(omitted),'candidate_pair_checks':checks,'charge_separation_counterexample':witness is not None,'witness':witness}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
