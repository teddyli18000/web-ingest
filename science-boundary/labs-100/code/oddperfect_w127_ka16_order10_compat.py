#!/usr/bin/env python3
"""Exact compatibility test between ka16 order-25 survivors and order-10 W127 cross+NGP profiles."""
import argparse, math, re

def decode(code):
    s=[]
    for _ in range(10):
        s.append(-5+2*(code%6)); code//=6
    return s

def orientation_count(v, code):
    s=decode(code); ways=1
    for r in range(5):
        vals=[v[i] for i in range(25) if i%5==r]
        fixed=sum(vals); z=vals.count(0)
        if s[r]+s[r+5] != 2*fixed: return 0
        diff=s[r]-s[r+5]
        if diff%2: return 0
        d=diff//2
        if abs(d)>z or ((d-z)&1): return 0
        ways*=math.comb(z,(z+d)//2)
    return ways

def parse_survivor(line):
    m=re.search(r'p=([0-9,\-]+) c=([0-9,\-]+)',line)
    if not m: raise ValueError(line)
    p=list(map(int,m.group(1).split(','))); c=list(map(int,m.group(2).split(',')))
    if len(p)!=25 or len(c)!=25: raise ValueError('bad survivor length')
    return p,c

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('ka16'); ap.add_argument('ngp10'); args=ap.parse_args()
    surv=[parse_survivor(x.strip()) for x in open(args.ka16) if x.strip()]
    prof=[tuple(map(int,x.split())) for x in open(args.ngp10) if x.strip()]
    print(f'ka16_projected_survivors={len(surv)}')
    print(f'order10_cross_ngp_profiles={len(prof)}')
    total=0
    for j,(p,c) in enumerate(surv,1):
        # Durable order-25 convention is c=x^13 q, hence q_i=c_(i+13).
        q=[c[(i+13)%25] for i in range(25)]
        hits=lifts=0
        for ca,cb in prof:
            wa=orientation_count(p,ca)
            if not wa: continue
            wb=orientation_count(q,cb)
            if not wb: continue
            hits+=1; lifts+=wa*wb
        print(f'survivor={j} compatible_profiles={hits} compatible_orientation_lifts={lifts}')
        total+=hits
    print(f'SUMMARY survivors={len(surv)} profiles={len(prof)} compatible_pairs={total}')
    if len(surv)!=4 or len(prof)!=4220: raise SystemExit('unexpected upstream count')
    if total: raise SystemExit('order10-compatible ka16 survivor exists')
if __name__=='__main__': main()
