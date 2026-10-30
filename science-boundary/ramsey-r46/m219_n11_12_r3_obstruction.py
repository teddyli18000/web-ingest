#!/usr/bin/env python3
"""Exact solver-free obstruction for m=219, degree sequence 11^12 12^6 13^18.

Uses the same complete A26/B116 endpoint strata and weak B degree-label necessary
conditions as the certified n11=11 obstruction. The degree-class relaxation
forces every degree-11 vertex to have r(v)=132-S(v)=3; each possible local
B-count vector is one already eliminated by the complete B116 scan.
"""
from itertools import combinations
from collections import Counter
from math import comb
import argparse, json

B116=(
"W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE",
"WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?",
"WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_",
"WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_",
"WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@",
"Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC")
SEQ={11:12,12:6,13:18}
A_MIN={11:8,12:11,13:15,14:20,15:25,16:32,17:40}
A_MAX={11:26,12:29,13:32,14:35,15:37,16:40,17:42}
B_MIN={11:116,12:101,13:88,14:77,15:68,16:57,17:50}
B_MAX={11:132,12:122,13:114,14:107,15:100,16:92,17:85}

def g6(s):
    n=ord(s[0])-63; bits=[]
    for c in s[1:]:
        x=ord(c)-63; bits += [(x>>k)&1 for k in range(5,-1,-1)]
    g=[0]*n; q=0
    for j in range(1,n):
        for i in range(j):
            if bits[q]: g[i]|=1<<j; g[j]|=1<<i
            q+=1
    return g

def degs(g): return [x.bit_count() for x in g]
def edges(g): return sum(degs(g))//2

def ex_k4(n):
    q,r=divmod(n,3); p=[q+(i<r) for i in range(3)]
    return sum(p[i]*p[j] for i in range(3) for j in range(i+1,3))

def s_interval(d,m=219):
    return max(11*d,m+A_MIN[d]-B_MAX[d]), min(17*d,m+A_MAX[d]-B_MIN[d])

def distributions(total, limits, prefix=()):
    if len(limits)==1:
        if 0<=total<=limits[0]: yield prefix+(total,)
        return
    lo=max(0,total-sum(limits[1:])); hi=min(limits[0],total)
    for x in range(lo,hi+1):
        yield from distributions(total-x,limits[1:],prefix+(x,))

def class_relaxation(seq):
    ds=sorted(seq); k=len(ds); mat=[[0]*k for _ in range(k)]
    cap=[[0]*k for _ in range(k)]
    for i,d in enumerate(ds):
        for j in range(i,k):
            e=ds[j]
            cap[i][j]=min(comb(seq[d],2),ex_k4(seq[d])) if i==j else seq[d]*seq[e]
    rem0=[d*seq[d] for d in ds]; vals=[]
    def check(i):
        d=ds[i]; ss=2*d*mat[i][i]
        for j,e in enumerate(ds):
            if j!=i: ss += e*mat[min(i,j)][max(i,j)]
        lo,hi=s_interval(d)
        if d==12: hi=146
        return lo*seq[d] <= ss <= hi*seq[d]
    def rec(i,rem):
        if i==k-1:
            if rem[i]<0 or rem[i]%2: return
            z=rem[i]//2
            if z>cap[i][i]: return
            mat[i][i]=z
            if not check(i): return
            i11=ds.index(11)
            R=2*mat[i11][i11]
            for j,d in enumerate(ds):
                if d>=13: R-=(d-12)*mat[min(i11,j)][max(i11,j)]
            vals.append(R); return
        for eii in range(min(cap[i][i],rem[i]//2)+1):
            need=rem[i]-2*eii; future=list(range(i+1,k))
            limits=[min(cap[i][j],rem[j]) for j in future]
            if need<0 or need>sum(limits): continue
            mat[i][i]=eii
            for xs in distributions(need,limits):
                nr=rem[:]
                for j,x in zip(future,xs): mat[i][j]=x; nr[j]-=x
                if min(nr)>=0 and check(i): rec(i+1,nr)
    rec(0,rem0)
    return vals

def compositions(n,allowed):
    for a in range(n+1):
        if a and 1 not in allowed: continue
        for b in range(n-a+1):
            if b and 2 not in allowed: continue
            c=n-a-b
            if not c or 3 in allowed: yield a,b,c

def weak_B_feasible(B,bc):
    db=degs(B); nl=bc[0]
    cand=[v for v,d in enumerate(db) if 11-d>=2]
    possible=[]; states_seen=0
    for Lt in combinations(cand,nl):
        L=list(Lt); LS=set(L); groups=Counter(); bad=False
        for v in range(24):
            if v in LS: continue
            allow=tuple(e for e in (1,2,3) if bc[e] and 11+e-db[v]>=2)
            if not allow: bad=True; break
            mask=sum(1<<i for i,u in enumerate(L) if (B[u]>>v)&1)
            groups[(mask,allow)]+=1
        if bad: continue
        states={(0,0,0,tuple(0 for _ in L))}
        for (mask,allow),num in groups.items():
            nxt=set()
            for c1,c2,c3,sums in states:
                for n1,n2,n3 in compositions(num,allow):
                    nc=(c1+n1,c2+n2,c3+n3)
                    if any(nc[i]>bc[i+1] for i in range(3)): continue
                    add=n1+2*n2+3*n3
                    ns=tuple(sums[i]+(add if mask>>i&1 else 0) for i in range(len(L)))
                    if any(x>8 for x in ns): continue
                    nxt.add((nc[0],nc[1],nc[2],ns))
            states=nxt; states_seen+=len(states)
            if not states: break
        if any((a,b,c)==tuple(bc[1:]) for a,b,c,s in states): possible.append(tuple(Lt))
    return possible,states_seen

def residual_counts(t):
    # r=t-w=3. Here w=#degree13 neighbours; a12=11-t-w=14-2t.
    w=t-3; a12=14-2*t
    if w<0 or a12<0: return None
    b11=SEQ[11]-1-t; b12=SEQ[12]-a12; b13=SEQ[13]-w
    if min(b11,b12,b13)<0: return None
    return (b11,b12,b13,0)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output'); a=ap.parse_args()
    vals=class_relaxation(SEQ)
    assert vals and max(vals)==36, (len(vals), min(vals), max(vals))
    assert max(vals)==3*SEQ[11]
    Bg=[g6(x) for x in B116]; assert all(len(g)==24 and edges(g)==116 for g in Bg)
    checks=[]
    expected=[(7,0,17,0),(6,2,16,0),(5,4,15,0),(4,6,14,0)]
    got=[]
    for t in range(4,8):
        bc=residual_counts(t); got.append(bc)
        row={'t':t,'B_counts':bc,'B116_types_checked':len(Bg),'feasible_B_types':[]}
        for bi,B in enumerate(Bg):
            poss,n=weak_B_feasible(B,bc)
            if poss: row['feasible_B_types'].append({'b_ordinal':bi,'possible_low_sets':poss,'dp_states':n})
        assert not row['feasible_B_types'], row
        checks.append(row)
    assert got==expected, got
    assert residual_counts(3) is None and residual_counts(8) is None
    out={
      'campaign':'m219-n11-12-r3-obstruction',
      'degree_sequence':{'11':12,'12':6,'13':18},
      'class_relaxation_count':len(vals),
      'max_sum_r':max(vals),
      'forced_r3_vertices':12,
      'dependencies':{
        'B116':'complete authenticated McKay stratum, 9 graph6 records copied from certified n11=11 verifier',
        'no_lucky_d12':'certified closure implies S(v)<=146 for degree 12 in class relaxation'},
      'r3_local_cases':checks,
      'conclusion':'all 12 degree-11 vertices are forced to r=3, but every possible local B116 degree-label pattern fails; degree sequence impossible'}
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'
    print(json.dumps({k:v for k,v in out.items() if k!='r3_local_cases'},sort_keys=True))
    if a.output: open(a.output,'w').write(text)
if __name__=='__main__': main()
