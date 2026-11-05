#!/usr/bin/env python3
"""Exact AGL(1,25)/GF(2) support enumeration for O58 K24 overlap1.

Normalized compression norms (kp,kc)=(11,13), union23 sites, overlap T
one site and holes Z two sites. F=T union Z has size3. Mod2 centered
periodic cross equation is P F*+F P*=0. Emit all valid (F,T,P) masks.
"""
from itertools import combinations
from math import gcd
import argparse

N=25
ALL=(1<<N)-1
UNITS=[a for a in range(1,N) if gcd(a,N)==1]


def triple_orbits():
    seen=set()
    reps=[]
    for triple in combinations(range(N),3):
        F=frozenset(triple)
        if F in seen:
            continue
        orbit={frozenset((a*i+b)%N for i in F) for a in UNITS for b in range(N)}
        seen.update(orbit)
        reps.append(F)
    assert len(reps)==6 and len(seen)==2300
    return reps


def supports(F,T):
    positions=[i for i in range(N) if i not in F]
    rows=[]
    for r in range(1,13):
        row=0
        rhs=0
        for j in positions:
            if ((j+r)%N in F)!=((j-r)%N in F):
                row|=1<<j
        for j in T:
            rhs^=((j+r)%N in F)!=((j-r)%N in F)
        rows.append([row,rhs])

    pivot=[]
    rank=0
    for j in positions:
        q=next((r for r in range(rank,12) if rows[r][0]>>j&1),None)
        if q is None:
            continue
        rows[q],rows[rank]=rows[rank],rows[q]
        for r in range(12):
            if r!=rank and rows[r][0]>>j&1:
                rows[r][0]^=rows[rank][0]
                rows[r][1]^=rows[rank][1]
        pivot.append(j)
        rank+=1
    if any(rhs for _,rhs in rows[rank:]):
        return []

    free=[j for j in positions if j not in pivot]
    base=sum(1<<j for i,j in enumerate(pivot) if rows[i][1])
    Tmask=sum(1<<j for j in T)
    Fmask=sum(1<<j for j in F)
    base|=Tmask
    result=[]
    for setting in range(1<<len(free)):
        P=base
        for k,j in enumerate(free):
            if setting>>k&1:
                P^=1<<j
                for r,p in enumerate(pivot):
                    if rows[r][0]>>j&1:
                        P^=1<<p
        if P.bit_count()!=11:
            continue
        C=P^(ALL^Fmask)
        assert C.bit_count()==13 and (P&C)==Tmask
        for r in range(1,13):
            h=sum(
                (P>>i&1)*(C>>((i+r)%N)&1)
                +(C>>i&1)*(P>>((i+r)%N)&1)
                for i in range(N)
            )&1
            assert h==0
        result.append((Fmask,Tmask,P))
    return result


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("out")
    args=ap.parse_args()
    counts=[]
    with open(args.out,"w",encoding="utf-8") as file:
        for F in triple_orbits():
            family=[]
            for t in F:
                family+=supports(F,{t})
            counts.append(len(family))
            for masks in family:
                file.write(",".join(map(str,masks))+"\n")
            print("F3_CENTER_CLASS",sorted(F),"support_pairs=",len(family))
    assert counts==[462,961,948,961,948,462],counts
    assert sum(counts)==4742
    print("F3_K24_OVERLAP1_COMPLETE orbits=6 support_pairs=4742")


if __name__=="__main__":
    main()
