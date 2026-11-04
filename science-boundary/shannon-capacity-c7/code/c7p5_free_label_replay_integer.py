#!/usr/bin/env python3
"""Independent exact integer-convolution replay of all free-label C7p5 slice pairs.

Distinct full 4D source templates from ALL original symbol layers can now
occupy ANY target 5D coordinate-symbol layer. For each ordered template pair
we compute, independently of bitset OR exclusion, every one of the 2401
relative phases using exact integer difference histograms and separable
cyclic 3-neighborhood convolutions. A 7-step maximum-weight cycle then
upper-bounds every phase-consistent free-label reconstruction.
"""
from __future__ import annotations
import argparse,collections,json,time
from pathlib import Path
import numpy as np
from c7p5_full_shift_replay_integer import build,coverage,cycle_bound

def main():
    p=argparse.ArgumentParser()
    p.add_argument('bpz',type=Path);p.add_argument('family',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args()
    raw=json.loads(a.bpz.read_text());fam=json.loads(a.family.read_text())
    t=time.monotonic();out=[]
    for axis in range(5):
        T=build(raw,fam,axis)
        pool={}
        for L in T:
            for Q,name,size in L:pool.setdefault(Q,(Q,name,size))
        U=list(pool.values());E=[[] for _ in U]
        hist=collections.Counter();nonzero=0
        for i,(A,_,_) in enumerate(U):
            for j,(B,_,_) in enumerate(U):
                P=coverage(A,B)
                candidates=np.argwhere(P==0)
                n=len(candidates);hist[n]+=1
                if n:
                    E[i].append(j)
                    nonzero+=sum(any(int(x) for x in d) for d in candidates)
        upper=cycle_bound([U]*7,[E]*7)
        row={'axis':axis,'distinct_templates':len(U),'ordered_template_pairs':len(U)**2,
             'compatible_ordered_pairs':sum(map(len,E)),
             'permitted_shift_histogram':{str(k):v for k,v in sorted(hist.items())},
             'nonzero_permitted_shift_count':nonzero,
             'relaxed_cycle_upper':upper,'full_phase_family_closed':upper<=367}
        out.append(row)
        print(json.dumps(row,sort_keys=True),flush=True)
    result={'method':'independent-integer-convolution-full-free-label-slice-census',
            'total_ordered_pairs':sum(x['ordered_template_pairs'] for x in out),
            'total_compatible_pairs':sum(x['compatible_ordered_pairs'] for x in out),
            'total_nonzero_permitted_shifts':sum(x['nonzero_permitted_shift_count'] for x in out),
            'closed_all_axes':all(x['full_phase_family_closed'] for x in out),
            'seconds':time.monotonic()-t,'axes':out}
    assert result['closed_all_axes']
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps({k:v for k,v in result.items() if k!='axes'},sort_keys=True),flush=True)

if __name__=='__main__':main()
