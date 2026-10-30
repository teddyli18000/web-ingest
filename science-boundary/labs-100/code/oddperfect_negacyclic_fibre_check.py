#!/usr/bin/env python3
"""Exact algebra/regression for the order-25 periodic/negacyclic fibre split.

For length-50 binary A,B write
 A=(1+x^25)p+(1-x^25)alpha,
 B=(1+x^25)q+(1-x^25)beta.
The odd-periodic cross polynomial F=A B* + x B A* in Z[x]/(x^50-1)
splits exactly as
 F=2(1+x^25)F_+ + 2(1-x^25)F_-,
where F_+=p q* + x q p* mod (x^25-1), and
F_-=alpha beta* + x beta alpha* mod (x^25+1).

With gamma=x^13 beta in the negacyclic quotient, F_-=0 iff
 alpha gamma* - gamma alpha*=0 mod (x^25+1).
"""
from __future__ import annotations
import argparse, random

INCUMBENT = "++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-"

def red_exp(e,n,neg):
    q,r=divmod(e,n)
    return r, (-1 if neg and (q&1) else 1)

def starprod(a,b,neg=False):
    n=len(a); out=[0]*n
    for i,x in enumerate(a):
        if not x: continue
        for j,y in enumerate(b):
            if not y: continue
            r,s=red_exp(i-j,n,neg); out[r]+=x*y*s
    return out

def xmul(a,neg=False):
    return [(-a[-1] if neg else a[-1]), *a[:-1]]

def add(a,b,scale_b=1): return [x+scale_b*y for x,y in zip(a,b)]

def split25(a):
    assert len(a)==50
    p=[(a[i]+a[i+25])//2 for i in range(25)]
    alpha=[(a[i]-a[i+25])//2 for i in range(25)]
    return p,alpha

def shift(a,k,neg=False):
    n=len(a); out=[0]*n
    for i,x in enumerate(a):
        r,s=red_exp(i+k,n,neg); out[r]+=x*s
    return out

def cross(a,b,neg=False):
    return add(starprod(a,b,neg),xmul(starprod(b,a,neg),neg))

def decompose(A,B):
    p,alpha=split25(A); q,beta=split25(B)
    F=cross(A,B,False)
    Fp=cross(p,q,False)
    Fm=cross(alpha,beta,True)
    rhs=[2*(Fp[i]+Fm[i]) for i in range(25)] + [2*(Fp[i]-Fm[i]) for i in range(25)]
    gamma=shift(beta,13,True)
    Fg=add(starprod(alpha,gamma,True),starprod(gamma,alpha,True),-1)
    # Fm = x^13 Fg in the negacyclic quotient.
    shifted=shift(Fg,13,True)
    return F,Fp,Fm,Fg,rhs,shifted

def seq(text): return [1 if c=='+' else -1 for c in text.strip()]

def energy(s):
    E=0
    for k in range(1,len(s)):
        c=sum(s[i]*s[i+k] for i in range(len(s)-k)); E+=c*c
    return E

def regress():
    s=seq(INCUMBENT); A=s[0::2]; B=s[1::2]
    F,Fp,Fm,Fg,rhs,shifted=decompose(A,B)
    assert energy(s)==578
    assert F==rhs
    assert not any(F) and not any(Fp) and not any(Fm) and not any(Fg)
    assert Fm==shifted
    rng=random.Random(20261030)
    for _ in range(32):
        A=[rng.choice((-1,1)) for _ in range(50)]
        B=[rng.choice((-1,1)) for _ in range(50)]
        F,Fp,Fm,Fg,rhs,shifted=decompose(A,B)
        assert F==rhs
        assert Fm==shifted
    print('REGRESSION_OK random_decompositions=32 incumbent_E=578 periodic_zero=1 negacyclic_zero=1 gamma_zero=1')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--regress',action='store_true'); ap.add_argument('--sequence')
    a=ap.parse_args()
    if a.regress: regress(); return
    if not a.sequence: ap.error('use --regress or --sequence <100-char +/- string>')
    s=seq(a.sequence); assert len(s)==100
    F,Fp,Fm,Fg,rhs,shifted=decompose(s[0::2],s[1::2])
    print('E',energy(s),'odd_periodic_cross_max',max(map(abs,F)),'periodic25_max',max(map(abs,Fp)),'negacyclic25_max',max(map(abs,Fm)),'gamma_max',max(map(abs,Fg)))
    assert F==rhs and Fm==shifted
if __name__=='__main__': main()
