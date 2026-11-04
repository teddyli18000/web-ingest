#!/usr/bin/env python3
"""Sound post-audit class-edge reduction for m220,n11=6,seq5.

Scope: degree sequence 11^6 12^19 13^8 14^3. Enumerate every
8-point R(4,4) degree-13 induced graph by extending the complete
7-vertex graph atlas, then apply the certified extreme B88 2K2 rule.
The degree-14 attachment is relaxed to per-row cardinalities only.
"""
from collections import Counter
from functools import lru_cache
from itertools import combinations
import json
import networkx as nx

QUADS=tuple(tuple(combinations(S,2)) for S in combinations(range(8),4))

def ramsey44(a):
    return all(0 < sum(a[u]>>v&1 for u,v in P) < 6 for P in QUADS)

def matching_support(a, extreme):
    for v in range(8):
        if not extreme>>v&1:
            continue
        F=[u for u in range(8) if u!=v and extreme>>u&1 and not(a[v]>>u&1)]
        if len(F)>4:
            return False
        if len(F)<3:
            continue
        e=sum(a[u]>>w&1 for u,w in combinations(F,2))
        if len(F)==3 and e!=1:
            return False
        if len(F)==4 and (e!=2 or any(
            sum(a[u]>>w&1 for w in F if w!=u)!=1 for u in F)):
            return False
    return True

@lru_cache(None)
def compositions(k,n=8):
    if n==1:
        return ((k,),)
    return tuple((i,)+tail for i in range(k+1) for tail in compositions(k-i,n-1))

def class_matrices():
    records=[]
    for R,e1112 in ((22,44),(24,42)):
        for x in range(29):
            for y in range(25):
                for z in range(4):
                    a=104-2*x-y
                    b=42-y-2*z
                    q=228-e1112-a-b
                    if a<0 or b<0 or q<0 or q%2:
                        continue
                    p=q//2
                    S12=11*e1112+24*p+13*a+14*b
                    S13=1248+2*x+2*y
                    S14=504+y+4*z
                    if not 132*19<=S12<=147*19:
                        continue
                    if not 143*8<=S13<=164*8:
                        continue
                    if not 154*3<=S14<=178*3:
                        continue
                    D=1312-S13
                    assert D in (0,2,4,6)
                    records.append((R,x,y,z,D))
    assert Counter(r[0] for r in records)=={22:54,24:30}
    return records

def main():
    records=class_matrices()
    target={(x,y,D) for _,x,y,_,D in records}
    feasible=set()
    sampled=Counter()
    for G in nx.graph_atlas_g():
        if len(G)!=7:
            continue
        base=[0]*8
        for u,v in G.edges():
            base[u]|=1<<v
            base[v]|=1<<u
        for neighbor_mask in range(128):
            a=base.copy()
            a[7]=neighbor_mask
            for i in range(7):
                if neighbor_mask>>i&1:
                    a[i]|=1<<7
            if not ramsey44(a):
                continue
            ds=[v.bit_count() for v in a]
            x=sum(ds)//2
            odd=sum(d&1 for d in ds)
            for D in (0,2,4,6):
                if odd>D:
                    continue
                y=32-x-D//2
                if (x,y,D) not in target:
                    continue
                for more in compositions((D-odd)//2):
                    delta=[(d&1)+2*z for d,z in zip(ds,more)]
                    k=[(8-d-v)//2 for d,v in zip(ds,delta)]
                    if not all(0<=c<=3 for c in k):
                        continue
                    assert sum(k)==y
                    ext=sum(1<<i for i,d in enumerate(delta) if d==0)
                    sampled[(x,y,D)]+=1
                    if matching_support(a,ext):
                        feasible.add((x,y,D))
    passed=[r for r in records if (r[1],r[2],r[4]) in feasible]
    removed=[r for r in records if (r[1],r[2],r[4]) not in feasible]
    assert (len(records),len(removed),len(passed))==(84,50,34)
    assert Counter(r[4] for r in removed)=={0:40,2:8,4:2}
    assert Counter(r[0] for r in passed)=={22:24,24:10}
    out={
      'campaign':'m220-n11-6-seq5-b88-class-post-audit',
      'degree_sequence':{'11':6,'12':19,'13':8,'14':3},
      'input_class_matrices':len(records),
      'excluded_by_sound_relaxation':len(removed),
      'remaining_class_matrices':len(passed),
      'exclusions_by_D13':dict(sorted(Counter(r[4] for r in removed).items())),
      'remaining_by_low_R':dict(sorted(Counter(r[0] for r in passed).items())),
      'remaining_class_records':[{'R':R,'e13_13':x,'e13_14':y,'e14_14':z,'D13':D}
                                 for R,x,y,z,D in passed],
      'R44_8_source':'complete extension of the NetworkX 7-vertex atlas',
      'B88_rule':'nonadjacent extreme degree-13 vertices at each extreme anchor must induce an induced subgraph of 2K2',
      'soundness':'The 14-degree attachments are relaxed to independent per-13-vertex row counts; only necessary conditions are applied. No withdrawn tf predicate.',
      'conclusion':'50/84 class-edge matrices excluded; 34 remain. Not a full seq5 exclusion.'
    }
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
