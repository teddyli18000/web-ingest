#!/usr/bin/env python3
"""Exact ALL 7^4 relative-translation compatibility census of dense C7^5 slices.

For 4D projected patterns A,B and a relative shift delta of B, incompatibility
means some a-b-delta lies in {-1,0,1}^4. Hence the set of forbidden deltas
is exactly union_{a in A,b in B} N4[a-b]. Computing this bitset avoids
enumerating translated high-dimensional graph edges for 2401 shifts.

The maximum-weight cycle on base patterns with edges whenever *any* relative
translation works is a rigorous upper bound for the full independently
translated slice-template family (it relaxes the cyclic phase-sum condition).
A value <=367 would globally exclude all 7^4 layer phases in this family.
"""
from __future__ import annotations
import argparse,collections,itertools,json,time
from pathlib import Path
from c7p5_slice_stitch_dp import gather,NBITS
from c7p5_two_layer_repair import digits5,proj,N4

ALL=(1<<N4)-1
DIG4=tuple(tuple((v//(7**k))%7 for k in range(4)) for v in range(N4))

def diff(a,b):
    da,db=DIG4[a],DIG4[b]
    return sum(((da[k]-db[k])%7)*7**k for k in range(4))

def base_templates(seeds,axis):
    patterns=[]
    for lay in range(7):
        by={}
        for name,S in seeds:
            Q=tuple(sorted(proj(v,axis) for v in S if digits5(v)[axis]==lay))
            by.setdefault(Q,name)
        patterns.append([{'q':q,'size':len(q),'source':name} for q,name in by.items()])
    return patterns

def allow_mask(A,B):
    bad=0
    for a in A:
        for b in B:
            bad|=NBITS[diff(a,b)]
            if bad==ALL:return 0
    return ALL^bad

def relaxed_cycle(T,adj):
    best=(-1,None)
    for start,t in enumerate(T[0]):
        dp={start:(t['size'],(start,))}
        for k in range(6):
            nxt={}
            for i,(value,path) in dp.items():
                for j in adj[k][i]:
                    z=value+T[k+1][j]['size']
                    if j not in nxt or z>nxt[j][0]:
                        nxt[j]=(z,path+(j,))
            dp=nxt
            if not dp:break
        for j,(z,path) in dp.items():
            if start in adj[6][j] and z>best[0]:
                best=(z,path)
    return best

def run(seeds,axis):
    T=base_templates(seeds,axis)
    adj=[];details=[];hist=collections.Counter()
    has_shift=0;total=0
    for k in range(7):
        E=[[] for _ in T[k]]
        for i,A in enumerate(T[k]):
            for j,B in enumerate(T[(k+1)%7]):
                mask=allow_mask(A['q'],B['q'])
                total+=1
                size=mask.bit_count()
                hist[size]+=1
                if not size:continue
                E[i].append(j)
                if mask&~1:has_shift+=1
                details.append({'boundary':k,'from':i,'to':j,'allowed_count':size,
                                'allowed_delta': [v for v in range(N4) if mask>>v&1]})
        adj.append(E)
    (upper,path)=relaxed_cycle(T,adj)
    if path is None:raise RuntimeError(('no baseline path',axis))
    trace=[{'layer':k,'size':T[k][path[k]]['size'],'source':T[k][path[k]]['source']} for k in range(7)]
    return {'axis':axis,'source_count':len(seeds),'template_count_by_layer':[len(p) for p in T],
            'boundary_pairs_tested':total,'allowed_pairs':len(details),
            'allowed_nonzero_shift_pairs':has_shift,
            'allowed_count_histogram':{str(k):v for k,v in sorted(hist.items())},
            'relaxed_cycle_upper_score':upper,'closed_full_shift_family':upper<=367,
            'relaxed_best_path':trace,'compatible_pair_details':details}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('tan',type=Path);p.add_argument('family',type=Path)
    p.add_argument('result',type=Path);p.add_argument('--axis',type=int,required=True)
    a=p.parse_args()
    t=time.monotonic()
    seeds=gather(json.loads(a.tan.read_text()),json.loads(a.family.read_text()))
    out=run(seeds,a.axis)
    out['seconds']=time.monotonic()-t
    a.result.parent.mkdir(parents=True,exist_ok=True)
    a.result.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='compatible_pair_details'},sort_keys=True),flush=True)

if __name__=='__main__':main()
