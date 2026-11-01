#!/usr/bin/env python3
"""Regression for the paired odd-correlation defect projection at N=100.

For odd-lag correlations D_r=C_(2r+1), r=0..49, define
    z_r=(D_r+D_(49-r))/4, r=0..24.
The script checks the exact arithmetic identities and the order-25 periodic /
negacyclic channel split used in the O=58 reformulation.
"""
from __future__ import annotations
import random

INCUMBENT='++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-'
N=25

def odd_corrs(s):
    return [sum(s[i]*s[i+2*r+1] for i in range(100-(2*r+1))) for r in range(50)]

def decomp(x):
    return ([(x[i]+x[i+25])//2 for i in range(N)],
            [(x[i]-x[i+25])//2 for i in range(N)])

def shift13_cyclic(q):
    c=[0]*N
    for i,v in enumerate(q): c[(i+13)%N]=v
    return c

def shift13_negacyclic(beta):
    g=[0]*N
    for i,v in enumerate(beta):
        e=i+13
        if e<N: g[e]=v
        else: g[e-N]=-v
    return g

def periodic_cross(p,c):
    return [sum(p[i]*c[(i-r)%N]+c[i]*p[(i-r)%N] for i in range(N)) for r in range(N)]

def negacyclic_comm(alpha,gamma):
    f=[0]*N
    def add(e,v):
        if e>=0: f[e]+=v
        else: f[e+N]-=v
    for i,a in enumerate(alpha):
        if not a: continue
        for j,g in enumerate(gamma):
            if not g: continue
            add(i-j,a*g)
            add(j-i,-g*a)
    return f

def check(s):
    A=s[::2]; B=s[1::2]
    D=odd_corrs(s)
    nums=[D[r]+D[49-r] for r in range(N)]
    assert all(x%4==0 for x in nums)
    z=[x//4 for x in nums]
    O=sum(x*x for x in D)
    lb=50+8*sum(x*x for x in z)
    assert O>=lb and (O-lb)%16==0
    assert sum(A)*sum(B)==4*sum(z)

    p,alpha=decomp(A); q,beta=decomp(B)
    c=shift13_cyclic(q); gamma=shift13_negacyclic(beta)
    P=periodic_cross(p,c); M=negacyclic_comm(alpha,gamma)
    assert P[0]==2*z[12]
    assert M[0]==0
    for r in range(1,13):
        assert P[r]==z[12+r]+z[12-r]
        assert M[r]==z[12+r]-z[12-r]
    # In this reduced coefficient convention both channels repeat under
    # r -> 25-r.  The sign distinguishing the two z coordinates is already
    # carried by M_r in the independent range r=1..12.
    for r in range(1,13):
        assert P[25-r]==P[r]
        assert M[25-r]==M[r]
    return O,z,P,M

def main():
    inc=[1 if x=='+' else -1 for x in INCUMBENT]
    O,z,P,M=check(inc)
    assert O==50 and not any(z) and not any(P) and not any(M)
    rng=random.Random(100058)
    for _ in range(500):
        check([rng.choice((-1,1)) for _ in range(100)])
    print('ODD_DEFECT_PROJECTION_REGRESSION_OK samples=501 incumbent_odd_energy=50')

if __name__=='__main__': main()
