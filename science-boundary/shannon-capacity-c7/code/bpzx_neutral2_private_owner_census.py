#!/usr/bin/env python3
"""Exhaust neutral 2-for-2 neighbors of BPZ-X and count private owners.

The public BPZ-X C7^5 independent set has 367 points and 10 distinct owners of
private neighbours.  All public 1-for-1 private-swap components have already
been exhausted without reaching 11 owners.  A neutral 2-for-2 move need not
factor through two legal 1-for-1 moves, so it can reach a different component.

For every outside vertex we compute its conflict support against BPZ-X.  A
2-for-2 neighbor must add two compatible vertices whose union of supports has
size at most two; after cancelling degenerate re-additions this is generated
exactly by support-1 and support-2 groups.  Every resulting 367-set is replayed
for independence, deduplicated, and scored by number of distinct private owners.
"""
import argparse,json,sys
from itertools import combinations
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bpz_t10_aux_translation_fft as t10


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('tan_root',type=Path); ap.add_argument('status',type=Path); args=ap.parse_args()
    sys.path.insert(0,str(args.tan_root.resolve())); from shannon.certificates import Ring
    raw=json.loads((args.tan_root/'data'/'base_c7.json').read_text()); X=sorted(map(int,raw['X']))
    ring=Ring(t10.D); digits=tuple(ring.decode(v) for v in range(t10.U)); nb=[sum(1<<z for z in ring.NB[v]) for v in range(t10.U)]
    if len(X)!=367 or not t10.independent(X,digits): raise RuntimeError('BPZ-X invalid')
    xset=set(X)

    support=[0]*t10.U
    for i,u in enumerate(X):
        bit=1<<i
        for v in ring.NB[u]: support[v]|=bit
    one={}; two={}
    for v,s in enumerate(support):
        if v in xset: continue
        bc=s.bit_count()
        if bc==1:
            i=(s&-s).bit_length()-1; one.setdefault(i,[]).append(v)
        elif bc==2:
            ids=[i for i in range(len(X)) if (s>>i)&1]
            two.setdefault((ids[0],ids[1]),[]).append(v)

    ownerpairs=set(two)
    for a,b in combinations(sorted(one),2): ownerpairs.add((a,b))
    seen=set(); legal=0; pair_trials=0; max_pool=0
    basebits=sum(1<<z for z in X); basepp=t10.private(basebits,nb); baseowners=len({a for a,q in basepp})
    bestowners=baseowners; bestpairs=len(basepp); best=[]; hist={}

    for a,b in sorted(ownerpairs):
        pool=sorted(set(one.get(a,[])+one.get(b,[])+two.get((a,b),[])))
        max_pool=max(max_pool,len(pool))
        for u,v in combinations(pool,2):
            pair_trials+=1
            if t10.conflict(u,v,digits): continue
            Y=list(X); Y[a]=u; Y[b]=v
            if len(set(Y))!=367: continue
            key=tuple(sorted(Y))
            if key in seen: continue
            seen.add(key)
            if not t10.independent(key,digits): raise RuntimeError('neutral2 replay failed')
            legal+=1
            bits=sum(1<<z for z in key); pp=t10.private(bits,nb); owners=len({p for p,q in pp})
            hist[str(owners)]=hist.get(str(owners),0)+1
            rec={'remove_indices':[a,b],'remove_points':[X[a],X[b]],'add':[u,v],'private_owners':owners,'private_pairs':len(pp)}
            if owners>bestowners:
                bestowners=owners; bestpairs=len(pp); best=[rec]
            elif owners==bestowners:
                bestpairs=max(bestpairs,len(pp))
                if len(best)<50: best.append(rec)

    status={
        'method':'bpz-X-exact-neutral2-private-owner-census',
        'base_private_owners':baseowners,
        'base_private_pairs':len(basepp),
        'support1_owner_groups':len(one),
        'support2_owner_pairs':len(two),
        'owner_pairs_generated':len(ownerpairs),
        'max_candidate_pool':max_pool,
        'candidate_pairs_tested':pair_trials,
        'legal_distinct_neutral2_states':legal,
        'private_owner_histogram':hist,
        'max_private_owners':bestowners,
        'max_private_pairs_at_max_owner_level':bestpairs,
        't11_state_exists':bestowners>=11,
        'best_states':best,
    }
    args.status.parent.mkdir(parents=True,exist_ok=True); args.status.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n'); print(json.dumps(status,sort_keys=True))

if __name__=='__main__': main()
