#!/usr/bin/env python3
"""Audit the pinned-data hypotheses behind the arbitrary single-row reduction.

The mathematical reduction is documented in results/single-row-core-release-reduction.md.
This checker verifies only the construction-specific finite facts:
- B has 359 points; N=X0 has 322 and every B point meets N in its closed C7^5 neighborhood;
- O,H,V are three 8-point independent transversals, each completely nonconfusable with B;
- B union each transversal is therefore a 367-point independent set;
- every pinned terminal row periphery contains N x q for q in {O,H,V}, and the
  corresponding column statement holds symmetrically.
"""
from __future__ import annotations
import argparse,json,sys
from collections import Counter
from pathlib import Path
import bpz_joint_row_defects_maxsat as J

def independent(ring,S):
    L=sorted(S)
    for i,a in enumerate(L):
        for b in L[i+1:]:
            if b in ring.NB[a]:return False
    return True

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();root=a.tan_root.resolve()
    base,ring,B,fam=J.load_geometry(root);B=set(B);N=set(fam['N']);A=set(fam['A']);D=set(fam['D']);X=N|A|D
    if len(B)!=359 or len(N)!=322 or len(A)!=19 or len(D)!=26 or len(X)!=367:raise RuntimeError(('profile',len(B),len(N),len(A),len(D),len(X)))
    if (N&A) or (N&D) or (A&D):raise RuntimeError('N/A/D overlap')
    deg=Counter(len(ring.NB[b]&N) for b in B)
    if not deg or min(deg)<=0:raise RuntimeError(('B-to-N zero neighbor',dict(deg)))
    trans={k:set(fam[k]) for k in ('O','H','V')};trows={}
    for name,T in trans.items():
        if len(T)!=8 or not independent(ring,T):raise RuntimeError(('transversal',name,len(T)))
        bad=[(b,t) for b in B for t in T if t in ring.NB[b]]
        if bad:raise RuntimeError(('not safe from B',name,bad[:5]))
        if len(B|T)!=367 or not independent(ring,B|T):raise RuntimeError(('B+T',name))
        trows[name]={'size':len(T),'independent':True,'safe_from_B':True,'B_union_size':len(B|T)}
    # Construction-level terminal containment check.  r is irrelevant to row moves,
    # but test all public q/r/orientation choices to guard against wiring drift.
    terminal_checks=0
    for q in ('O','H','V'):
        for r in ('O','H','V'):
            for orient in (0,1):
                P=J.terminal_periphery(fam,q,r,orient)
                if len(P)!=5872:raise RuntimeError(('P size',q,r,orient,len(P)))
                need={(x,t) for x in N for t in trans[q]}
                if not need<=P:raise RuntimeError(('missing N x q',q,r,orient,len(need-P)))
                # Column-side symmetric block r x N.
                needc={(t,x) for t in trans[r] for x in N}
                if not needc<=P:raise RuntimeError(('missing r x N',q,r,orient,len(needc-P)))
                terminal_checks+=1
    out={'method':'pinned-bpz-single-row-reduction-audit','B_size':len(B),'N_size':len(N),'A_size':len(A),'D_size':len(D),'X_partition_size':len(X),'B_to_N_neighbor_histogram':{str(k):v for k,v in sorted(deg.items())},'min_B_to_N_neighbors':min(deg),'max_B_to_N_neighbors':max(deg),'transversals':trows,'terminal_configurations_checked':terminal_checks,'terminal_size':5872,'row_block':'N x q','column_block':'r x N'}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
