#!/usr/bin/env python3
"""Replay the pinned B-to-X saturating matching used by the multi-row reduction.

The bipartite graph has left side B (359 core rows), right side X=N disjoint A
disjoint D (367 points), and an edge a--x when a and x are confusable in C7^5.
A deterministic augmenting-path matcher is sufficient at this size and avoids
external graph libraries.  The script verifies a matching saturating all B,
the N/A/D partition, the O/H/V 367 transversals, and all 18 terminal wirings.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path
import bpz_joint_row_defects_maxsat as J

def independent(ring,S):
    L=sorted(S)
    return all(b not in ring.NB[a] for i,a in enumerate(L) for b in L[i+1:])

def matching(B,X,ring):
    L=sorted(B);R=set(X);mr={}
    def aug(a,seen):
        for x in sorted(ring.NB[a]&R):
            if x in seen:continue
            seen.add(x);old=mr.get(x)
            if old is None or aug(old,seen):mr[x]=a;return True
        return False
    for a in L:
        if not aug(a,set()):raise RuntimeError(('unsaturated row',a,len(mr)))
    ml={a:x for x,a in mr.items()}
    if len(ml)!=len(B):raise RuntimeError(('matching size',len(ml),len(B)))
    return ml

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();root=a.tan_root.resolve()
    _base,ring,B,fam=J.load_geometry(root);B=set(B);N=set(fam['N']);A=set(fam['A']);D=set(fam['D']);X=N|A|D
    if len(B)!=359 or (len(N),len(A),len(D),len(X))!=(322,19,26,367):raise RuntimeError(('profile',len(B),len(N),len(A),len(D),len(X)))
    if N&A or N&D or A&D:raise RuntimeError('N/A/D overlap')
    M=matching(B,X,ring)
    if len(set(M.values()))!=359 or any(x not in ring.NB[b] for b,x in M.items()):raise RuntimeError('matching replay')
    factor_hist=Counter('N' if x in N else ('A' if x in A else 'D') for x in M.values())
    trans={k:set(fam[k]) for k in ('O','H','V')}
    for k,T in trans.items():
        if len(T)!=8 or not independent(ring,T) or not independent(ring,B|T):raise RuntimeError(('transversal',k))
    # Verify the exact row-side factor/transversal wiring used by every terminal.
    checks=[]
    for q in ('O','H','V'):
        for r in ('O','H','V'):
            for orient in (0,1):
                P=J.terminal_periphery(fam,q,r,orient)
                sA,sD=(trans['H'],trans['V']) if orient==0 else (trans['V'],trans['H'])
                required={(x,t) for x in N for t in trans[q]}
                required|={(x,t) for x in A for t in sA}
                required|={(x,t) for x in D for t in sD}
                if not required<=P:raise RuntimeError(('row wiring',q,r,orient,len(required-P)))
                # Symmetric column wiring: r x N plus H/V x D/A according to orientation.
                if orient==0:
                    reqc={(t,x) for t in trans[r] for x in N}|{(t,x) for t in trans['H'] for x in D}|{(t,x) for t in trans['V'] for x in A}
                else:
                    reqc={(t,x) for t in trans[r] for x in N}|{(t,x) for t in trans['H'] for x in A}|{(t,x) for t in trans['V'] for x in D}
                if not reqc<=P:raise RuntimeError(('column wiring',q,r,orient,len(reqc-P)))
                checks.append((q,r,orient,len(required),len(reqc)))
    out={'method':'pinned-bpz-multirow-matching-audit','B_size':len(B),'X_size':len(X),'N_size':len(N),'A_size':len(A),'D_size':len(D),'matching_size':len(M),'matching_saturates_B':True,'matching_factor_histogram':dict(sorted(factor_hist.items())),'transversal_sizes':{k:len(v) for k,v in trans.items()},'terminal_configurations_checked':len(checks),'matching':[[b,M[b]] for b in sorted(M)]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='matching'},sort_keys=True))
if __name__=='__main__':main()
