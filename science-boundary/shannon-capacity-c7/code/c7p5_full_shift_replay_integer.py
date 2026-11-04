#!/usr/bin/env python3
"""Independent integer-convolution replay of all C7p5 slice phase exclusions.

Uses *no* delta-neighborhood bitset machinery from c7p5_full_shift_compatibility.
A 4D difference histogram over all pairs of words is convolved successively
with the cyclic [1,1,1] stencil in each coordinate using NumPy integer rolls.
The resulting array counts every 4D conflict for each of the 2401 relative
translations. Zeros are exactly the permitted shifts.
"""
from __future__ import annotations
import argparse,collections,itertools,json,time
from pathlib import Path
import numpy as np

def dec5(v):
    return tuple((v//(7**k))%7 for k in range(5))

def independent5(S):
    L=[dec5(v) for v in S]
    return len(L)==len(set(S)) and all(
        not all((a[k]-b[k])%7 in (0,1,6) for k in range(5))
        for i,a in enumerate(L) for b in L[i+1:])

def build(raw,fam,axis):
    sources=[('I0',raw['I0']),('X',raw['X'])]
    sources.extend((f'F{i}',L) for i,L in enumerate(fam['states']))
    assert len(sources)==38
    out=[{} for _ in range(7)]
    for name,S in sources:
        assert len(S)==367 and independent5(S)
        group=[[] for _ in range(7)]
        for v in S:
            d=dec5(v)
            group[d[axis]].append(tuple(d[i] for i in range(5) if i!=axis))
        for lay,Q in enumerate(group):
            q=tuple(sorted(Q))
            out[lay].setdefault(q,name)
    return [[(q,name,len(q)) for q,name in D.items()] for D in out]

def coverage(A,B):
    d=np.zeros((7,7,7,7),dtype=np.int32)
    for a in A:
        for b in B:
            d[tuple((a[k]-b[k])%7 for k in range(4))]+=1
    for k in range(4):
        d=np.roll(d,1,axis=k)+d+np.roll(d,-1,axis=k)
    return d

def cycle_bound(T,edges):
    best=-1
    for start in range(len(T[0])):
        dp={start:T[0][start][2]}
        for k in range(6):
            nd={}
            for i,val in dp.items():
                for j in edges[k][i]:
                    z=val+T[k+1][j][2]
                    if z>nd.get(j,-1):nd[j]=z
            dp=nd
            if not dp:break
        for j,val in dp.items():
            if start in edges[6][j]:best=max(best,val)
    return best

def main():
    p=argparse.ArgumentParser()
    p.add_argument('bpz',type=Path);p.add_argument('family',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    raw=json.loads(a.bpz.read_text());fam=json.loads(a.family.read_text())
    start=time.monotonic();rows=[]
    for axis in range(5):
        T=build(raw,fam,axis)
        hist=collections.Counter();E=[];nonzero=0;maxconf=0
        for k in range(7):
            row=[[] for _ in T[k]]
            for i,(A,_,_) in enumerate(T[k]):
                for j,(B,_,_) in enumerate(T[(k+1)%7]):
                    d=coverage(A,B)
                    permitted=np.argwhere(d==0)
                    n=len(permitted);hist[n]+=1
                    if n:
                        row[i].append(j)
                        nonzero+=sum(any(int(c) for c in r) for r in permitted)
                    maxconf=max(maxconf,int(d.max()))
            E.append(row)
        upper=cycle_bound(T,E)
        out={'axis':axis,'template_counts':[len(L) for L in T],
             'pair_count':sum(hist.values()),'permitted_phase_histogram':{str(k):v for k,v in sorted(hist.items())},
             'nonzero_permitted_relative_phases':nonzero,'relaxed_cycle_upper':upper,
             'closed_all_independent_slice_translations':upper<=367}
        rows.append(out)
        print(json.dumps(out,sort_keys=True),flush=True)
    assert all(r['closed_all_independent_slice_translations'] for r in rows)
    result={'method':'independent-full-relative-translation-integer-convolution',
            'source_sets':38,'relative_phase_space':2401,
            'total_base_pairs':sum(r['pair_count'] for r in rows),
            'total_nonzero_permitted_phases':sum(r['nonzero_permitted_relative_phases'] for r in rows),
            'all_axes_upper_at_most_367':all(r['relaxed_cycle_upper']<=367 for r in rows),
            'wall_seconds':time.monotonic()-start,'axes':rows}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps({k:v for k,v in result.items() if k!='axes'},sort_keys=True),flush=True)

if __name__=='__main__':main()
