#!/usr/bin/env python3
"""Construct independent C7^10 codes by optimizing *actual* row/column fibers.

Given a 367-point five-dimensional parent I, fixed private-pair deletions R,
and a translated 367-point auxiliary X, retain B×B for B=I-R.
For every auxiliary x, independently select row and column endpoints from
the COMPLETE five-dimensional safe pool E={e:N[e]∩I ⊆ R}.
All same-fiber and row/column cross-conflicts are encoded exactly as MILP.
The returned candidate is replayed independently; if it exceeds the Few
Shots p004 baseline, it is also materialized as certificate.json.
"""
import argparse,itertools,json,time
from pathlib import Path
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

P=(1,7,49,343,2401)
U=7**5
D=tuple(tuple(v//p%7 for p in P) for v in range(U))
OFF=tuple(itertools.product((-1,0,1),repeat=5))

def clash(a,b):
    return all((u-v)%7 in (0,1,6) for u,v in zip(D[a],D[b]))

def neighborhood(v):
    x=D[v]
    return (sum((x[i]+z[i])%7*P[i] for i in range(5)) for z in OFF)

def independent(S):
    return len(S)==len(set(S)) and all(
        not clash(a,b) for i,a in enumerate(S) for b in S[i+1:])

def transform(S,delta):
    return [sum((D[x][i]+delta[i])%7*P[i] for i in range(5)) for x in S]

def optimize(parent,near,seconds,aux_swaps=()):
    I=[int(v) for v in parent.read_text().split()]
    assert len(I)==367 and independent(I)
    case=json.loads(near.read_text())["best"]
    pairs=case["pairs"]
    R={a for a,b in pairs};t=len(R);B=set(I)-R
    assert len(R)==len(pairs) and len(B)==367-t
    X=transform(I,case["delta"])
    for old,new in aux_swaps:
        assert old in X and new not in X
        X[X.index(old)]=new
    assert len(X)==367 and independent(X)
    # Exact owner supports; do not artificially restrict endpoints to PH/PV.
    supp=[set() for _ in range(U)]
    for a in I:
        for e in neighborhood(a):
            supp[e].add(a)
    E=[e for e in range(U) if supp[e] and supp[e]<=R]
    assert all(not clash(e,b) for e in E for b in B)
    hit=np.array([[clash(e,x) for e in E] for x in X],dtype=bool)
    active=np.flatnonzero(hit.any(axis=1))
    aset=set(map(int,active))
    a=len(active);m=len(E);n=2*a*m
    def h(i,k):return i*m+k
    def v(i,k):return a*m+i*m+k
    row=[];col=[];constraints=0
    def edge(x,y):
        nonlocal constraints
        row.extend((constraints,constraints))
        col.extend((x,y))
        constraints+=1
    intra=[(i,j) for i,e in enumerate(E) for j,f in enumerate(E)
           if j>i and clash(e,f)]
    for i in range(a):
        for j,k in intra:
            edge(h(i,j),h(i,k))
            edge(v(i,j),v(i,k))
    cross=0
    for ii,i in enumerate(active):
        vk=np.flatnonzero(hit[i])
        for jj,j in enumerate(active):
            hk=np.flatnonzero(hit[j])
            for k in hk:
                for l in vk:
                    edge(h(ii,int(k)),v(jj,int(l)))
                    cross+=1
    A=coo_matrix((np.ones(len(row)),(row,col)),shape=(constraints,n)).tocsr()
    begin=time.monotonic()
    sol=milp(-np.ones(n),integrality=np.ones(n),
             bounds=Bounds(np.zeros(n),np.ones(n)),
             constraints=LinearConstraint(A,-np.inf,np.ones(constraints)),
             options={"time_limit":seconds,"mip_rel_gap":0})
    stats={"method":"full-safe-endpoint-direct-10D-MILP",
           "port_count":t,"safe_endpoint_count":m,
           "active_auxiliary":a,"inert_auxiliary":367-a,
           "variables":n,"constraints":constraints,
           "cross_constraints":cross,"solver_status":int(sol.status),
           "elapsed_seconds":round(time.monotonic()-begin,3)}
    if sol.x is None:return stats,None
    sel=sol.x
    H={};V={}
    for ii,i in enumerate(active):
        H[X[i]]=[E[k] for k in range(m) if sel[h(ii,k)]>.5]
        V[X[i]]=[E[k] for k in range(m) if sel[v(ii,k)]>.5]
    for i,x in enumerate(X):
        if i not in aset:
            H[x]=sorted(R);V[x]=sorted(R)
    # Independent, direct ten-dimensional certificate replay.
    assert all(independent(z) for z in itertools.chain(H.values(),V.values()))
    assert all(not(any(clash(e,y) for e in H[x]) and
                   any(clash(x,f) for f in V[y]))
               for x in X for y in X)
    points={(a,b) for a in B for b in B}
    points.update((e,x) for x in X for e in H[x])
    points.update((x,e) for x in X for e in V[x])
    expected=len(B)**2+sum(len(H[x])+len(V[x]) for x in X)
    assert len(points)==expected
    assert expected==len(B)**2+2*t*(367-a)+round(-sol.fun)
    stats.update({"score":expected,"gain_over_record":expected-134753,
                  "candidate":expected>134753,
                  "mip_gap":float(sol.mip_gap) if sol.mip_gap is not None else None,
                  "best_bound":float(sol.mip_dual_bound) if sol.mip_dual_bound is not None else None})
    return stats,sorted("".join(map(str,D[x]+D[y])) for x,y in points)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("parent_ids",type=Path)
    p.add_argument("near_miss",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--seconds",type=float,default=120)
    p.add_argument("--aux-swap",default="",help="old:new 5D point replacement after translation")
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    swaps=[tuple(map(int,pair.split(":"))) for pair in args.aux_swap.split(",") if pair]
    stats,words=optimize(args.parent_ids,args.near_miss,args.seconds,swaps)
    stats["auxiliary_swaps"]=[list(x) for x in swaps]
    (args.output/"status.json").write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n")
    if words is not None:
        data=json.dumps({"points":words},separators=(",",":"))+"\n"
        (args.output/"best_certificate.json").write_text(data)
        if stats["candidate"]:
            (args.output/"certificate.json").write_text(data)
    print("FINAL",json.dumps(stats,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
