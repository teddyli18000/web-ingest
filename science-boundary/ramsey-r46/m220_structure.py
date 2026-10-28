#!/usr/bin/env python3
"""Exact necessary structural reduction for a hypothetical 220-edge R(4,6,36) graph.

For v with degree d, A=N(v), B=V\(A union {v}), and S(v)=sum_{u in N(v)}d(u),
we use S=m+e(A)-e(B), complete R(3,6,d) edge extrema and exact R(4,5,35-d)
extrema.  Summing S(v) gives sum d(v)^2, so degree-count vectors are exhausted.

The already-closed lucky-d12 pair is A29/B101.  For m=220 it has S=148, so
no hypothetical graph may have a degree-12 vertex with S>=148; equivalently
we impose the rigorous cap S12<=147.

For degree 11, the endpoint extrema give S11<=130. Relative to eleven degree-12
neighbours (sum 132), every d11 vertex needs t-w>=2, where t is its number of
d11 neighbours and w is the total degree excess above 12 among higher-degree
neighbours. Thus n11=1 or 2 is impossible. If n11=3, every d11 vertex must be
adjacent to the other two, with w=0 and all remaining nine neighbours degree12.
Hence S11=130 and e(B)-e(A)=90, forcing the exact extreme pair A26/B116.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path

DEGREES=tuple(range(11,18))
A_MIN={11:8,12:11,13:15,14:20,15:25,16:32,17:40}
A_MAX={11:26,12:29,13:32,14:35,15:37,16:40,17:42}
B_MIN={11:116,12:101,13:88,14:77,15:68,16:57,17:50}
B_MAX={11:132,12:122,13:114,14:107,15:100,16:92,17:85}

def compositions(total,k,prefix=()):
    if k==1:
        yield prefix+(total,);return
    for x in range(total+1):yield from compositions(total-x,k-1,prefix+(x,))

def s_interval(d,m=220):
    return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])

def as_dict(ns):return {str(d):n for n,d in zip(ns,DEGREES) if n}

def aggregate(m=220):
    out=[]
    for ns in compositions(36,len(DEGREES)):
        if sum(n*d for n,d in zip(ns,DEGREES))!=2*m:continue
        s2=sum(n*d*d for n,d in zip(ns,DEGREES));lo=hi=0
        for n,d in zip(ns,DEGREES):
            a,b=s_interval(d,m)
            if d==12:b=min(b,m-73) # lucky-d12 A29/B101 is already exact-UNSAT
            lo+=n*a;hi+=n*b
        if lo<=s2<=hi:out.append(ns)
    return out

def reduce():
    raw=aggregate();assert len(raw)==179,len(raw)
    killed=[];surv=[]
    for ns in raw:
        if ns[0] in (1,2):
            killed.append({'degree_sequence':as_dict(ns),'reason':'S11<=130 requires at least two d11 neighbours after accounting for nonnegative high-degree excess'})
        else:surv.append(ns)
    assert len(surv)==144,len(surv)
    n3=[as_dict(x) for x in surv if x[0]==3];assert len(n3)==16,len(n3)
    return {'edges':220,'aggregate_vector_count':len(raw),'aggregate_vectors':[as_dict(x) for x in raw],
            'killed_n11_1_2_count':len(killed),'killed_n11_1_2':killed,
            'survivor_count':len(surv),'survivors':[as_dict(x) for x in surv],
            'n11_eq_3':{'degree_sequence_count':len(n3),'degree_sequences':n3,'induced_L':'K3',
                       'S11':130,'degree11_neighbours_per_anchor':2,'degree12_neighbours_per_anchor':9,
                       'degree11_to_higher_edges':0,'forced_A_edges':26,'forced_B_edges':116,
                       'complete_A26_types':2,'complete_B116_types':9},
            's_intervals':{str(d):list(s_interval(d)) for d in DEGREES},
            'degree12_upper_after_no_lucky_d12':147,
            'interpretation':'necessary exact structural reduction only; survivors are not claimed realizable'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);a=ap.parse_args();d=reduce()
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'aggregate':d['aggregate_vector_count'],'survivors':d['survivor_count'],'n11_eq_3':d['n11_eq_3']['degree_sequence_count']},sort_keys=True))
if __name__=='__main__':main()
