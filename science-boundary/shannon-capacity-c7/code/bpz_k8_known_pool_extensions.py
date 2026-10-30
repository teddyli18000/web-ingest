#!/usr/bin/env python3
"""Reproduce exact k=8 positive support defects from the completed k6/k7 pools.

Inputs are the pinned BPZ base_c7.json plus completed k6/k7 cover-gap JSON and
the k7 irreducibility audit.  Candidate points are taken only from the union of
those already-audited complete pools, but their supports are recomputed exactly
against all 359 core owners B using the C7^5 confusability rule.  Each of the 12
genuine outside-only k7 7->8 witnesses is then tested against every known pool
candidate for a compatible ninth point whose full support union is exactly 8.

This is a reproducible lower-bound census inside the known k6/k7 pool universe,
not a complete k8 census.  The output also audits BPZ private-pair killer colors.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

def conflict5(a:int,b:int)->bool:
    if a==b:return True
    for _ in range(5):
        x,y=a%7,b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def support(z:int,B:set[int])->tuple[int,...]:
    return tuple(sorted(b for b in B if conflict5(z,b)))

def killer_mask(z:int,pairs:list[tuple[int,int]])->int:
    m=0
    for i,(a,b) in enumerate(pairs):
        if conflict5(z,a) and conflict5(z,b):m|=1<<i
    return m

def independent(S:list[int])->bool:
    return all(not conflict5(a,b) for i,a in enumerate(S) for b in S[i+1:])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('base_json',type=Path)
    ap.add_argument('k6_json',type=Path)
    ap.add_argument('k7_json',type=Path)
    ap.add_argument('k7_audit_json',type=Path)
    ap.add_argument('output',type=Path)
    a=ap.parse_args()
    raw=json.loads(a.base_json.read_text())
    pairs=[tuple(map(int,p)) for p in raw['private_pairs']]
    I=set(map(int,raw['I0']));B=I-{p[0] for p in pairs}
    if len(B)!=359:raise RuntimeError(('B',len(B)))
    k6=json.loads(a.k6_json.read_text());k7=json.loads(a.k7_json.read_text());audit=json.loads(a.k7_audit_json.read_text())
    if int(audit.get('irreducible_positive_count',-1))!=12:raise RuntimeError(('k7 irreducible drift',audit.get('irreducible_positive_count')))
    known=set()
    for d in (k6,k7):
        for r in d['cover_gap_cases']:known.update(map(int,r['pool']))
    known-=B
    exact_support={z:support(z,B) for z in sorted(known)}
    if any(not S for S in exact_support.values()):raise RuntimeError('zero-support point in audited nonzero pool union')
    hits=[]
    for ci,r in enumerate(audit['irreducible_positive']):
        W=sorted(map(int,r['witness']));owners=set(map(int,r['owners']))
        if len(W)!=8 or len(owners)!=7 or not independent(W):raise RuntimeError(('bad k7 witness',ci))
        wu=set().union(*(set(support(z,B)) for z in W))
        if wu!=owners:raise RuntimeError(('k7 support drift',ci,sorted(wu),sorted(owners)))
        for z,S in exact_support.items():
            if z in W or any(conflict5(z,w) for w in W):continue
            U=owners|set(S)
            if len(U)!=8:continue
            WW=sorted(W+[z])
            if not independent(WW):raise RuntimeError(('extension conflict',ci,z))
            km=0
            for q in WW:km|=killer_mask(q,pairs)
            hits.append({'case':ci,'z':z,'support':list(S),'owners':sorted(U),'witness':WW,'killer_mask':km,'killer_count':km.bit_count(),'killer_colors':[i for i in range(len(pairs)) if km>>i&1]})
    hist=Counter(h['killer_count'] for h in hits)
    out={'method':'exact-known-pool-k8-extension-census','scope':'union of completed k6/k7 complete support pools only; not a complete k8 census','B_size':len(B),'known_outside_pool_vertices':len(known),'k7_irreducible_witnesses':len(audit['irreducible_positive']),'extensions':len(hits),'killer_histogram':{str(k):v for k,v in sorted(hist.items())},'min_killer_count':min(hist) if hist else None,'hits':hits}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='hits'},sort_keys=True))
if __name__=='__main__':main()
