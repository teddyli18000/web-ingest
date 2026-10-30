#!/usr/bin/env python3
"""Exact minimum exception set for the support<=3 owner-clique injection.

Among all five-dimensional factors z outside the pinned 359-point core B with
1 <= |S(z)=N[z]∩B| <= 3, retain the largest possible subset admitting an owner
assignment f(z)∈S(z) such that every owner fiber is a clique in C7^5.

This is the global version of the support<=3 list-SAT obstruction.  A selector
s_z activates factor z. Assignment variables x_{z,b} are allowed only when s_z
is active. Hard constraints enforce exactly one eligible owner for each active
factor and forbid two nonconfusable factors from sharing an owner. Soft unit
clauses [s_z] of weight one maximize the number of retained factors. Thus RC2
computes the exact minimum number of exceptions needed to recover the product
injection.

The returned assignment is independently replayed.  The exception set is the
right kernel for a subsequent injection-based ten-dimensional residual prize
model: regular×regular points remain chargeable injectively, so only candidates
whose assigned core cell overlaps an exception footprint need explicit search.
"""
from __future__ import annotations
import argparse,json,time
from collections import Counter,defaultdict
from pathlib import Path
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
import bpz_joint_row_defects_maxsat as J

PINNED_COMMIT='c753408492dde92a239708986d16c15dbf6c3235'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--solver',default='g4');a=ap.parse_args();root=a.tan_root.resolve()
    _base,ring,B,_fam=J.load_geometry(root);B=set(B)
    factors=[];support={};hist=Counter()
    for z in range(ring.n):
        if z in B:continue
        S=tuple(sorted(ring.NB[z]&B))
        if 1<=len(S)<=3:factors.append(z);support[z]=S;hist[len(S)]+=1
    if (hist[1],hist[2],hist[3],len(factors))!=(50,375,1581,2006):raise RuntimeError(('census',hist,len(factors)))
    # Variables.
    x={};nextv=1
    for z in factors:
        for b in support[z]:x[(z,b)]=nextv;nextv+=1
    s={}
    for z in factors:s[z]=nextv;nextv+=1
    w=WCNF();atleast=atmost=links=conflicts=0
    for z in factors:
        xs=[x[(z,b)] for b in support[z]]
        # Active factor must choose >=1 owner.
        w.append([-s[z]]+xs);atleast+=1
        # Assignment implies active, making inactive factors truly absent.
        for v in xs:w.append([-v,s[z]]);links+=1
        # At most one owner.
        for i in range(len(xs)):
            for j in range(i+1,len(xs)):w.append([-xs[i],-xs[j]]);atmost+=1
        w.append([s[z]],weight=1)
    eligible=defaultdict(list)
    for z in factors:
        for b in support[z]:eligible[b].append(z)
    pair_checks=0
    for b,L in eligible.items():
        for i,z in enumerate(L):
            for q in L[i+1:]:
                pair_checks+=1
                if q in ring.NB[z]:continue
                w.append([-x[(z,b)],-x[(q,b)]]);conflicts+=1
    t=time.time()
    with RC2(w,solver=a.solver,adapt=True,exhaust=True,incr=True,verbose=0) as rc2:
        model=rc2.compute();cost=rc2.cost
    if model is None:raise RuntimeError('RC2 returned no model')
    pos={v for v in model if v>0}
    active=[z for z in factors if s[z] in pos];exceptions=[z for z in factors if s[z] not in pos]
    if len(exceptions)!=cost:raise RuntimeError(('cost mismatch',len(exceptions),cost))
    chosen={};groups=defaultdict(list)
    for z in active:
        owners=[b for b in support[z] if x[(z,b)] in pos]
        if len(owners)!=1:raise RuntimeError(('assignment cardinality',z,owners))
        chosen[z]=owners[0];groups[owners[0]].append(z)
    # Exact replay.
    bad=[]
    for b,L in groups.items():
        for i,z in enumerate(L):
            for q in L[i+1:]:
                if q not in ring.NB[z]:bad.append((b,z,q))
    if bad:raise RuntimeError(('clique replay',bad[:5]))
    if any(chosen[z] not in support[z] for z in active):raise RuntimeError('owner outside support')
    eh=Counter(len(support[z]) for z in exceptions)
    owner_union=sorted(set().union(*(set(support[z]) for z in exceptions))) if exceptions else []
    out={'method':'exact-support-le3-min-exceptions-owner-clique-maxsat','source_commit':PINNED_COMMIT,'solver':a.solver,'factor_count':len(factors),'support_histogram':{str(k):v for k,v in sorted(hist.items())},'assignment_variables':len(x),'selector_variables':len(s),'hard_clauses':atleast+links+atmost+conflicts,'atleast_clauses':atleast,'assignment_selector_links':links,'atmost_clauses':atmost,'owner_conflict_clauses':conflicts,'owner_pair_checks':pair_checks,'minimum_exceptions':len(exceptions),'retained_factors':len(active),'exception_support_histogram':{str(k):v for k,v in sorted(eh.items())},'exception_owner_union_size':len(owner_union),'exception_owner_union':owner_union,'exceptions':[{'z':z,'support':list(support[z])} for z in sorted(exceptions)],'assigned_owner_groups':len(groups),'max_owner_group_size':max(map(len,groups.values())) if groups else 0,'owner_group_size_histogram':{str(k):v for k,v in sorted(Counter(map(len,groups.values())).items())},'seconds':time.time()-t,'clique_replay_bad_pairs':0,'assignment':[[z,chosen[z]] for z in sorted(active)]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('assignment','exceptions','exception_owner_union')},sort_keys=True));print(json.dumps({'exceptions':out['exceptions'],'exception_owner_union':owner_union},sort_keys=True))
if __name__=='__main__':main()
