#!/usr/bin/env python3
"""Exact integer census for the odd-perfect (18,0), K=19 corner.

Definitions:
  d_r = C_(2r)/2, W = sum_{r=1}^{49} d_r^2.
  m = d_25 = K-25 = -6.
  U_r=(d_r+d_(50-r))/2, V_r=(d_r-d_(50-r))/2, r=1..24.
Then sum U=31 and W=36+2*sum(U^2+V^2).

This enumerates the only U multisets at W<=130 and every possible sorted
order-25 common-PAF multiset G_j=U_j+U_(25-j), j=1..12.
"""
from collections import Counter
from functools import lru_cache

N=24
SUM_U=31


def u_multisets(square_sum: int):
    vals=tuple(range(-6, 7))
    out=[]
    def rec(j,n,s,q,cnt):
        if j==len(vals):
            if n==N and s==SUM_U and q==square_sum:
                out.append(Counter({v:c for v,c in zip(vals,cnt) if c}))
            return
        v=vals[j]
        left=N-n
        for c in range(left+1):
            q2=q+c*v*v
            if q2>square_sum:
                break
            rec(j+1,n+c,s+c*v,q2,cnt+(c,))
    rec(0,0,0,0,())
    return out


def pair_sum_types(multiset: Counter):
    state=tuple(sorted(multiset.items()))
    @lru_cache(None)
    def f(st):
        c=dict(st)
        if not c:
            return {()}
        a=min(c)
        c[a]-=1
        if c[a]==0:
            del c[a]
        ans=set()
        for b in sorted(c):
            d=c.copy()
            d[b]-=1
            if d[b]==0:
                del d[b]
            for rest in f(tuple(sorted(d.items()))):
                ans.add(tuple(sorted((a+b,)+rest)))
        return ans
    return f(state)


def fmt(c):
    return ' '.join(f'{v}^{c[v]}' for v in sorted(c))


def main():
    u45=u_multisets(45)
    u47=u_multisets(47)
    assert u45 == [Counter({1:17,2:7})], u45
    assert set(tuple(sorted(c.items())) for c in u47) == {
        ((0,1),(1,15),(2,8)),
        ((1,18),(2,5),(3,1)),
    }, u47
    base=pair_sum_types(u45[0])
    alt=set()
    for c in u47:
        alt |= pair_sum_types(c)
    assert len(base)==4, len(base)
    assert len(alt)==12, len(alt)
    print('U45',fmt(u45[0]))
    print('BASE_G_TYPES',len(base))
    for x in sorted(base):
        print('G',fmt(Counter(x)))
    print('U47_TYPES',len(u47))
    for c in u47:
        print('U47',fmt(c))
    print('W130_ZERO_DEFECT_G_TYPES',len(alt))
    for x in sorted(alt):
        print('G',fmt(Counter(x)))


if __name__=='__main__':
    main()
