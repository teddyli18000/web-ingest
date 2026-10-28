#!/usr/bin/env python3
"""Necessary half-sum classes for low odd-energy LABS-100 layers.

This is not a feasibility solver. It exactly enumerates the possible aggregate
odd-pair defect arithmetic for O=50+8D, reduces parity-half sums by the
standard LABS symmetries, then applies rigorous z=1 and z=i integer-square
lower bounds to discard classes that cannot meet a requested total target.
"""
from __future__ import annotations
import argparse, math

def pair_dt(max_d:int):
    out={d:set() for d in range(max_d+1)}
    lim=int(math.sqrt(4*max_d+1))+3
    for t in range(-int(math.sqrt(max_d))-1,int(math.sqrt(max_d))+2):
        for u in range(-lim,lim+1):
            if u%2==0: continue
            d=t*t+(u*u-1)//4
            if 0<=d<=max_d: out[d].add(t)
    return out

def possible_abs_P(D:int):
    opts=pair_dt(D); states={(0,0)}
    for _ in range(25):
        nxt=set()
        for d0,p0 in states:
            for d,ts in opts.items():
                if d0+d>D: continue
                for t in ts: nxt.add((d0+d,p0+t))
        states=nxt
    return sorted({abs(p) for d,p in states if d==D})

def alt_sums(total:int):
    out=[]
    for alt in range(-50,51,2):
        if (total+alt)%2 or (total-alt)%2: continue
        u=(total+alt)//2; v=(total-alt)//2
        if abs(u)<=25 and abs(v)<=25 and u%2 and v%2: out.append(alt)
    return out

def min_integer_square_sum(n:int,total:int):
    q,r=divmod(abs(total),n)
    return (n-r)*q*q+r*(q+1)*(q+1)

def even_lower_bound(a:int,b:int):
    S=(a*a+b*b-100)//2
    best=None; witness=None
    for aa in alt_sums(a):
        for bb in alt_sums(b):
            T=(aa*aa+bb*bb-100)//2
            if (S+T)%2 or (S-T)%2: continue
            se=(S+T)//2; so=(S-T)//2
            if se%2 or so%2: continue
            # r=1..49: 24 even r and 25 odd r; every C_{2r} is even.
            q=4*(min_integer_square_sum(24,se//2)+min_integer_square_sum(25,so//2))
            if best is None or q<best:
                best=q; witness=(aa,bb,S,T,se,so)
    if best is None: raise RuntimeError('no alternating-sum realization')
    return best,witness

def half_classes(P:int):
    if P==0: return [(0,b) for b in range(0,51,2)]
    out=[]
    for a in range(2,51,2):
        for b in range(a,51,2):
            if a*b==4*P: out.append((a,b))
    return out

def classes(D:int,target:int):
    O=50+8*D; budget=target-O; ans=[]
    if budget<0:return O,budget,ans
    for P in possible_abs_P(D):
        for a,b in half_classes(P):
            lb,w=even_lower_bound(a,b)
            if lb<=budget: ans.append((P,a,b,lb,w))
    return O,budget,ans

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('D',type=int); ap.add_argument('--target',type=int,default=574)
    args=ap.parse_args(); O,budget,ans=classes(args.D,args.target)
    print(f'D={args.D} odd_energy={O} even_budget={budget} classes={len(ans)}')
    for P,a,b,lb,w in ans:
        print(f'P={P:2d} a={a:2d} b={b:2d} even_lb={lb:3d} alt_witness={w[0]},{w[1]}')
if __name__=='__main__':main()
