#!/usr/bin/env python3
"""Exact irreducibility audit for k-owner support clique-cover-gap cases.

For every cover-gap owner set C emitted by bpz_support_clique_cover_gap_census.py,
recompute alpha(Y_C) and, among all maximum independent sets, minimize the number
of reused deleted owners.  Intersection zero means a genuine outside-only raw
replacement; positive intersection exposes a reducible apparent defect.
"""
from __future__ import annotations
import argparse,json
from collections import Counter
from pathlib import Path

def conflict5(a,b):
    if a==b:return True
    for _ in range(5):
        x,y=a%7,b%7;a//=7;b//=7
        if (x-y)%7 not in (0,1,6):return False
    return True

def best_independent(pool,owners):
    n=len(pool);compat=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if not conflict5(pool[i],pool[j]):compat[i]|=1<<j;compat[j]|=1<<i
    best=-1;best_inter=10**9;witness=[]
    def rec(mask,chosen,hits):
        nonlocal best,best_inter,witness
        s=len(chosen);ub=s+mask.bit_count()
        if ub<best or (ub==best and hits>=best_inter):return
        if not mask:
            if s>best or (s==best and hits<best_inter):best=s;best_inter=hits;witness=[pool[i] for i in chosen]
            return
        mm=mask;pick=(mm&-mm).bit_length()-1;worst=-1
        while mm:
            b=mm&-mm;mm-=b;i=b.bit_length()-1;z=(mask&~(compat[i]|(1<<i))).bit_count()
            if z>worst:worst=z;pick=i
        rec(mask&compat[pick],chosen+[pick],hits+(pool[pick] in owners))
        rec(mask&~(1<<pick),chosen,hits)
    rec((1<<n)-1,[],0);return best,best_inter,sorted(witness)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('census_json',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();d=json.loads(a.census_json.read_text());k=int(d['k']);cases=d.get('cover_gap_cases',[])
    if len(cases)!=int(d.get('cover_gap_count',-1)):raise RuntimeError('schema/count')
    hist=Counter();ah=Counter();rows=[]
    for c in cases:
        owners=set(map(int,c['owners']));pool=list(map(int,c['pool']));al,inter,wit=best_independent(pool,owners)
        if al!=int(c['alpha']):raise RuntimeError(('alpha mismatch',sorted(owners),al,c['alpha']))
        hist[inter]+=1;ah[al]+=1;rows.append({'owners':sorted(owners),'pool_size':len(pool),'alpha':al,'min_owner_intersection_at_alpha':inter,'irreducible':inter==0,'raw_gain':al-k,'witness':wit})
    irr=[x for x in rows if x['irreducible']];pos=[x for x in irr if x['raw_gain']>0];neu=[x for x in irr if x['raw_gain']==0]
    out={'method':'exact-gap-max-independent-min-owner-intersection','k':k,'input_gap_cases':len(cases),'alpha_histogram':{str(x):y for x,y in sorted(ah.items())},'intersection_histogram':{str(x):y for x,y in sorted(hist.items())},'irreducible_count':len(irr),'irreducible_positive_count':len(pos),'irreducible_neutral_count':len(neu),'irreducible_positive':pos,'irreducible_neutral':neu,'cases':rows}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({x:y for x,y in out.items() if x!='cases'},sort_keys=True))
if __name__=='__main__':main()
