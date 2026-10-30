#!/usr/bin/env python3
"""Dependency-free exact check of the W127 order-25 shard ka=24,kc=2.

The proof has two cases for the two nonzero positions of c.

If their difference d is a unit mod 25, the cross equation forces
p=x^d p*, i.e. reflection symmetry.  Since p has support 24 and sum 10, it
has 17 +1s, 7 -1s and one zero.  The unique zero must be the reflection fixed
point, leaving +/- entries in equal-position pairs; 17 and 7 cannot both be
odd.  Contradiction.

If gcd(d,25)=5, affine/unit symmetries normalize c=delta_0-delta_5.  The cross
equation implies g=p-x^5 p* is invariant under shift 5.  Enumerating the tiny
coefficient possibilities under support(p)=24 and sum(p)=10 leaves exactly 28
p sequences.  Every one has combined cyclic PAF at shift 5 equal to 14 or 18,
whereas W127 requires every nonzero combined PAF to be in {2,3,4}.
"""
from itertools import product
from collections import Counter

V=(-1,0,1)
N=25

def paf(x,r):
    return sum(x[i]*x[(i+r)%N] for i in range(N))

def options(h):
    return [(a,b) for a in V for b in V if a-b==h]

def main():
    # R(i)=5-i is the reflection in p-x^5 p*.
    R=lambda i:(5-i)%N
    seen=set(); pairs=[]; fixed=[]
    for i in range(N):
        if i in seen: continue
        j=R(i)
        if i==j:
            fixed.append(i); seen.add(i)
        else:
            pairs.append((i,j)); seen.add(i); seen.add(j)
    assert fixed==[15]

    p0=[]; p14=[]; p23=[]
    for i,j in pairs:
        ri,rj=i%5,j%5
        if ri==rj==0: p0.append((i,j))
        elif {ri,rj}=={1,4}: p14.append((i,j) if ri==1 else (j,i))
        elif {ri,rj}=={2,3}: p23.append((i,j) if ri==2 else (j,i))
        else: raise AssertionError((i,j))
    assert len(p0)==2 and len(p14)==5 and len(p23)==5

    candidates=[]
    # g_i=p_i-p_(5-i) is constant on each residue class mod 5.
    # h_0=0 and h_-r=-h_r.  Enumerate h_1,h_2 exactly.
    for h1 in range(-2,3):
      for h2 in range(-2,3):
        o1,o2=options(h1),options(h2)
        for z0 in V:
          for z1 in V:
            for f in V:
              base=[None]*N
              base[p0[0][0]]=base[p0[0][1]]=z0
              base[p0[1][0]]=base[p0[1][1]]=z1
              base[15]=f
              for q1 in product(o1,repeat=5):
                a=base.copy()
                for (i,j),(u,v) in zip(p14,q1): a[i]=u; a[j]=v
                for q2 in product(o2,repeat=5):
                  p=a.copy()
                  for (i,j),(u,v) in zip(p23,q2): p[i]=u; p[j]=v
                  if p.count(0)==1 and sum(p)==10:
                    candidates.append(tuple(p))

    candidates=sorted(set(candidates))
    assert len(candidates)==28, len(candidates)

    c=[0]*N; c[0]=1; c[5]=-1
    vals=Counter()
    survivors=[]
    for p in candidates:
        # Independent cross check in Z[x]/(x^25-1).
        for r in range(N):
            cross=sum(p[i]*c[(i-r)%N] + c[i]*p[(i-r)%N] for i in range(N))
            assert cross==0, (r,cross,p)
        k5=paf(p,5)+paf(c,5)
        vals[k5]+=1
        K=[paf(p,r)+paf(c,r) for r in range(1,13)]
        if all(v in (2,3,4) for v in K) and sum(K)==37:
            survivors.append((p,K))

    print('KA24_GCD5_CANDIDATES',len(candidates))
    print('KA24_SHIFT5_VALUES',dict(sorted(vals.items())))
    print('KA24_W127_SURVIVORS',len(survivors))
    assert vals==Counter({14:20,18:8}), vals
    assert not survivors
    print('EXACT_RESULT W127_ORDER25_KA24_INFEASIBLE')

if __name__=='__main__':
    main()
