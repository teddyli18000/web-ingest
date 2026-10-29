#!/usr/bin/env python3
"""POST-UNSEAL ONLY. Audit which hidden Nagata edges were even discoverable.

This module is never imported by the candidate selectors. Compare old-parent
union, actual Concorde LP supports and k-nearest geometric edges against
the 5,757,191 held-out tour. Reports are diagnostic, NOT trained features.
"""
import argparse,importlib.util,json,os
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.spatial import cKDTree

def readtour(path):
    s=Path(path).read_text().splitlines()
    i=next(i for i,l in enumerate(s) if l.strip()=='TOUR_SECTION')
    a=[]
    for line in s[i+1:]:
        for z in line.split():
            if z in ('-1','EOF'):return [q-1 for q in a]
            a.append(int(z))
    raise ValueError(path)
def E(a,b):return (a,b) if a<b else (b,a)
def edges(t):return {E(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def main():
    p=argparse.ArgumentParser()
    for x in ('reference','hidden','parents','lps','output'):p.add_argument('--'+x,required=True)
    a=p.parse_args()
    t=readtour(a.reference);target=[int(x)-1 for x in json.loads(Path(a.hidden).read_text())['tour']]
    assert len(t)==len(target)==100000
    base=edges(t);nagata=edges(target)
    hist=set(base)
    for fn in json.loads(Path(a.parents).read_text()).values():
        tour=readtour(fn)
        assert len(tour)==len(t)
        hist.update(edges(tour))
    missing=nagata-base
    novel=nagata-hist
    assert len(missing)==2687
    assert len(novel)>=1000
    snaps={}
    for name,path in json.loads(Path(a.lps).read_text()).items():
        vals={}
        with open(path) as f:
            n,m=map(int,f.readline().split());assert n==len(t)
            for line in f:
                u,v,x=line.split()
                u=int(u);v=int(v);x=float(x)
                if x>1e-5:vals[E(u,v)]=x
        snaps[name]=vals
    comp={}
    for title,s in (('nagata_only_unseen_in_any_historical_tour',novel),
                    ('hidden_difference_from_reference',missing)):
        row={'edge_count':len(s),'historical_parent_union_coverage':len(s&hist)}
        for name,vals in snaps.items():
            row[name]={'LP_positive':sum(e in vals for e in s),
                       'LP_fractional':sum(e in vals and vals[e]<1-1e-5 for e in s),
                       'LP_integral_one':sum(vals.get(e,0)>=1-1e-5 for e in s)}
        row['LP_positive_any_snapshot']=sum(any(e in v for v in snaps.values()) for e in s)
        row['LP_fraction_any_snapshot']=sum(any(e in v and v[e]<1-1e-5 for v in snaps.values()) for e in s)
        row['LP_positive_all_three']=sum(all(e in v for v in snaps.values()) for e in s)
        comp[title]=row
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    tree=cKDTree(np.column_stack((xs,ys)))
    ranks=(4,8,16,32,64)
    pointset=set(x for e in novel for x in e)
    neighbors={}
    for u in pointset:
        near=tree.query([xs[u],ys[u]],k=65)[1]
        neighbors[u]={int(city):rank for rank,city in enumerate(near)}
    geo={str(k):sum((neighbors[u].get(w,999)<=k or neighbors[w].get(u,999)<=k) for u,w in novel) for k in ranks}
    report={'reference_len':5757199,'hidden_len':5757191,
           'old_parent_union_count':len(hist),
           'hidden_unique_vs_reference':len(missing),
           'hidden_edges_absent_all_old_parents':len(novel),
           'coverage':comp,'novel_target_edge_nearest_neighbor_rank':geo,
           'caveat':'This audit uses the hidden target after the blind runs concluded. NEVER feed these target-derived statistics or edges into candidate selection on this split; use only to form pre-registered hypotheses for OTHER instances or future held-outs.'}
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
