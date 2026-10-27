#!/usr/bin/env python3
"""Exhaust every one-for-one independent-set neighbour of the BPZ C7^5 base.

The fixed BPZ I has exactly eight private alternatives.  Replacing an owner by
its private alternative gives every one-swap independent 367-set neighbour
(unless a zero-conflict outside point existed, which is checked and rejected).
For each neighbour, solve the full Definition-2 oriented-pair problem exactly
and ask for t >= 9.  A hit materializes the corresponding 134770-point Gao
product for the Few Shots verifier.
"""

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

from pysat.solvers import Minicard

Q=7; D=5; U=Q**D; N=367; TARGET=9; TARGET_SCORE=N*N+TARGET*TARGET


def conflict(a,b,digits):
    return all((x-y)%Q in (0,1,Q-1) for x,y in zip(digits[a],digits[b]))


def indep(vals,digits):
    v=list(vals)
    return all(not conflict(a,b,digits) for a,b in combinations(v,2))


def private_candidates(I, ring):
    out=[]; zero=[]
    for q in range(U):
        if q in I: continue
        hits=[z for z in ring.NB[q] if z in I]
        if not hits: zero.append(q)
        elif len(hits)==1: out.append((hits[0],q))
    return out,zero


def solve_t9(I,X,ring,digits,xmask):
    priv,zero=private_candidates(I,ring)
    opts=[]; selfbad=0
    for r,q in priv:
        if xmask[r]&xmask[q]: selfbad+=1; continue
        opts.append((r,q,r,q,0)); opts.append((r,q,q,r,1))
    m=len(opts)
    if m < 2*TARGET:
        return None,{"private_candidates":len(priv),"private_owners":len({r for r,_ in priv}),"zero_conflict":len(zero),"oriented_options":m,"self_invalid":selfbad,"incompatible_pairs":None}
    s=Minicard(); inc=0
    for i,(ri,qi,hi,vi,si) in enumerate(opts):
        for j in range(i+1,m):
            rj,qj,hj,vj,sj=opts[j]
            bad=(ri==rj or conflict(hi,hj,digits) or conflict(vi,vj,digits)
                 or bool(xmask[hi]&xmask[vj]) or bool(xmask[hj]&xmask[vi]))
            if bad:
                s.add_clause([-(i+1),-(j+1)]); inc+=1
    s.add_atmost([-(i+1) for i in range(m)],m-TARGET)
    sat=s.solve(); model=s.get_model() if sat else None; s.delete()
    chosen=None
    if sat:
        pos={z for z in model if z>0}
        ii=[i for i in range(m) if i+1 in pos][:TARGET]
        if len(ii)!=TARGET: raise RuntimeError("short SAT model")
        chosen=[opts[i] for i in ii]
    return chosen,{"private_candidates":len(priv),"private_owners":len({r for r,_ in priv}),"zero_conflict":len(zero),"oriented_options":m,"self_invalid":selfbad,"incompatible_pairs":inc}


def build(I,X,chosen,ring,digits):
    owners=[z[0] for z in chosen]; PH=[z[2] for z in chosen]; PV=[z[3] for z in chosen]
    if len(set(owners))!=TARGET or not indep(PH,digits) or not indep(PV,digits): raise RuntimeError("bad chosen transversals")
    R=set(owners); B=set(I)-R
    NH=set().union(*(ring.NB[h] for h in PH)); NV=set().union(*(ring.NB[v] for v in PV))
    if set(X)&NH&NV: raise RuntimeError("X double-hit")
    X0=set(X)-(NH|NV); XH=set(X)&NH; XV=set(X)&NV
    pairs=set()
    for A,C in ((B,B),(R,X0),(set(PH),XH),(set(PV),XV),(X0,R),(XH,set(PV)),(XV,set(PH))):
        for a in A:
            for c in C:pairs.add((a,c))
    if len(pairs)!=TARGET_SCORE: raise RuntimeError(f"score {len(pairs)}")
    def p10(ab):
        ds=ring.decode(ab[0])+ring.decode(ab[1]); return ''.join(map(str,ds))
    return sorted(p10(z) for z in pairs),owners,PH,PV,(len(X0),len(XH),len(XV))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('output',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    root=args.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import Ring
    raw=json.loads((root/'data'/'base_c7.json').read_text());I0=set(map(int,raw['I0']));X=set(map(int,raw['X']))
    ring=Ring(D);digits=tuple(ring.decode(v) for v in range(U))
    if len(I0)!=N or len(X)!=N or not indep(I0,digits) or not indep(X,digits):raise RuntimeError('base drift')
    xmask=[0]*U
    for xi,x in enumerate(sorted(X)):
        bit=1<<xi
        for v in ring.NB[x]:xmask[v]|=bit
    initial,zero=private_candidates(I0,ring)
    if zero: raise RuntimeError(f'base has {len(zero)} direct-add points')
    if len(initial)!=8:raise RuntimeError(f'expected 8 base private candidates, got {len(initial)}')
    rows=[];winner=None
    for r,q in initial:
        I=set(I0);I.remove(r);I.add(q)
        if len(I)!=N or not indep(I,digits):raise RuntimeError('invalid one-swap neighbour')
        chosen,stats=solve_t9(I,X,ring,digits,xmask)
        row={"remove":r,"add":q,"sat_t9":chosen is not None,**stats};rows.append(row)
        print('STATE',json.dumps(row,sort_keys=True),flush=True)
        if chosen is not None and winner is None:winner=(r,q,I,chosen)
    status={"method":"bpz-definition2-exact-one-swap-t9","states":len(rows),"rows":rows,"candidate":winner is not None}
    args.status.parent.mkdir(parents=True,exist_ok=True)
    if winner is None:
        status['score']=N*N+8*8;args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('NONE',json.dumps(status,sort_keys=True),flush=True);return
    r,q,I,chosen=winner;points,owners,PH,PV,xpart=build(I,X,chosen,ring,digits)
    status.update({"score":len(points),"winning_swap":{"remove":r,"add":q},"owners":owners,"PH":PH,"PV":PV,"X_partition":{"X0":xpart[0],"XH":xpart[1],"XV":xpart[2]}})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({"points":points},separators=(',',':'))+'\n');args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps(status,sort_keys=True),flush=True)

if __name__=='__main__':main()
