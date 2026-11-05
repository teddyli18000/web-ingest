#!/usr/bin/env python3
"""Complete all-affine aperiodic audit of O58/K28 3-overlap Q survivors.

Inputs are the full uncapped compressed and fibre transcripts. Every Q-support
image is joined to all matching signed compressed AGL images. The negacyclic
fibre sign gauge is unfolded (both global signs), then all 500 induced
simultaneous cyclic/negacyclic affine transforms are scored at original N=100.
"""
import argparse
import re
from collections import Counter, defaultdict
from math import gcd

N = 25
UNITS = [a for a in range(1, N) if gcd(a, N) == 1]
MASKS = [0] + [(1 << (100-k)) - 1 for k in range(1,100)]


def score(s):
    bits = sum(1 << j for j,v in enumerate(s) if v == 1)
    energy = odd = even = 0
    for k in range(1,100):
        distance = ((bits ^ (bits >> k)) & MASKS[k]).bit_count()
        cor = 100-k-2*distance
        e = cor*cor
        energy += e
        if k % 2: odd += e
        else: even += e
    return energy, odd, even


def parse_compressed(path):
    compressed = []
    for line in open(path, encoding="utf-8"):
        if not line.startswith("HIT "):
            continue
        p,c = line.split(" p=")[1].strip().split("|c=")
        p = tuple(map(int,p.split(",")))
        c = tuple(map(int,c.split(",")))
        assert len(p)==len(c)==25 and sum(p)==sum(c)==1
        compressed.append((p,c))
    return compressed


def parse_fibre(path):
    hits = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("QHIT "):
            hits.append({k:int(v) for k,v in re.findall(r"(\w+)=(-?\d+)",line)})
    return hits


def periodic_image(p,c,a,b):
    pp=[0]*25;cc=[0]*25
    for i in range(25):
        j=(a*i+b)%25
        pp[j]=p[i];cc[j]=c[i]
    return tuple(pp),tuple(cc)


def support_key(p,c):
    return (
        sum(1 << i for i in range(25) if p[i]==0),
        sum(1 << i for i in range(25) if c[i]==0)
    )


def fibres(hit):
    alpha=[(1 if hit["amask"]>>i&1 else -1) if hit["as"]>>i&1 else 0 for i in range(25)]
    gamma=[(1 if hit["gmask"]>>i&1 else -1) if hit["gs"]>>i&1 else 0 for i in range(25)]
    assert sum(v*v for v in alpha+gamma)==22
    return alpha,gamma


def neg_star(a,b):
    out=[0]*25
    for i in range(25):
        for j in range(25):
            exp=i-j
            value=a[i]*b[j]
            if exp<0:
                exp+=25
                value=-value
            out[exp]+=value
    return out


def transform(p,c,alpha,gamma,a,b):
    odd_a=a if a%2 else a+25
    pp=[0]*25;cc=[0]*25;aa=[0]*25;gg=[0]*25
    for i in range(25):
        j=(a*i+b)%25
        pp[j]=p[i]
        cc[j]=c[i]
        exponent=odd_a*i+b
        sign=-1 if (exponent//25)%2 else 1
        aa[j]=alpha[i]*sign
        gg[j]=gamma[i]*sign
    return pp,cc,aa,gg


def interleave(p,c,alpha,gamma):
    q=[c[(i+13)%25] for i in range(25)]
    beta=[gamma[i+13] if i<12 else -gamma[i-12] for i in range(25)]
    A=[p[i]+alpha[i] for i in range(25)]+[p[i]-alpha[i] for i in range(25)]
    B=[q[i]+beta[i] for i in range(25)]+[q[i]-beta[i] for i in range(25)]
    assert all(v in (-1,1) for v in A+B)
    assert sum(A)==sum(B)==2
    return [v for x in zip(A,B) for v in x]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("compressed")
    ap.add_argument("fibre")
    args=ap.parse_args()
    compressed=parse_compressed(args.compressed)
    qhits=parse_fibre(args.fibre)
    assert len(compressed)==53
    assert len(qhits)==34
    needed={(h["as"],h["gs"]) for h in qhits}
    matching=defaultdict(set)
    for p,c in compressed:
        for a in UNITS:
            for b in range(25):
                pp,cc=periodic_image(p,c,a,b)
                key=support_key(pp,cc)
                if key in needed:
                    matching[key].add((pp,cc))
    assert len(matching)==5 and all(matching[key] for key in needed)

    paired=transforms=odd58=0
    minE=(10**9,None)
    minO=(10**9,None)
    O_hist=Counter()
    for h in qhits:
        alpha,gamma=fibres(h)
        assert neg_star(alpha,gamma)==neg_star(gamma,alpha)
        for p,c in matching[(h["as"],h["gs"])]:
            SG=sum(sum(p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25] for i in range(25))**2 for r in range(1,13))
            if SG+h["sh"]>120:
                continue
            paired+=1
            for sign in (1,-1):
                aa=[sign*v for v in alpha]
                gg=[sign*v for v in gamma]
                for a in UNITS:
                    for b in range(25):
                        pp,cc,at,gt=transform(p,c,aa,gg,a,b)
                        s=interleave(pp,cc,at,gt)
                        E,O,V=score(s)
                        assert O>=58
                        if O==58:odd58+=1
                        transforms+=1
                        O_hist[O]+=1
                        if E<minE[0]:minE=(E,("".join("+" if v==1 else "-" for v in s),O,V,SG,h["sh"],a,b))
                        if O<minO[0]:minO=(O,(E,"".join("+" if v==1 else "-" for v in s),a,b))
    assert (paired,transforms,odd58,minE[0],minO[0])==(66,66000,0,1310,154)
    s=[1 if v=="+" else -1 for v in minE[1][0]]
    corr=[sum(s[i]*s[i+k] for i in range(100-k)) for k in range(1,100)]
    assert sum(v*v for v in corr)==minE[0]
    assert sum(v*v for k,v in enumerate(corr,1) if k%2)==minE[1][1]
    print("K28_FULL_AFFINE_AUDIT compressed=53 QHIT=34 mapped_Q=66 transforms=66000 O58=0 minE=1310 minO=154")
    print("BEST_E_SEQUENCE",minE[1])
    print("MIN_O_SEQUENCE",minO)
    print("LOW_ODD_HIST",sorted(O_hist.items())[:15])


if __name__=="__main__":
    main()
