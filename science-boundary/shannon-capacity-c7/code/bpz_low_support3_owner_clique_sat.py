#!/usr/bin/env python3
"""Exact owner-clique list-assignment SAT for all nonempty supports of size <=3.

For every 5D factor z outside the pinned 359-point core B with
1 <= |S(z)| <= 3, choose one owner f(z) in S(z).  For every owner b, all factors
assigned to b must form a clique in the C7^5 confusability graph.

If SAT, the product injection used for the support<=2 closure extends verbatim:
(u,v) -> (f(u),f(v)) injects every independent outside-outside set into its
mandatory deleted core cells, so all candidates whose two supports are <=3 have
nonpositive raw core gain.

If UNSAT, selector assumptions expose a factor-level UNSAT core identifying the
first obstruction to that injection strategy.
"""
from __future__ import annotations
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
from pysat.solvers import Solver
import bpz_joint_row_defects_maxsat as J


def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--solver',default='g4');a=ap.parse_args();root=a.tan_root.resolve()
    _base,ring,B,_fam=J.load_geometry(root);B=set(B)
    factors=[];support={}
    byk=Counter()
    for z in range(ring.n):
        if z in B:continue
        S=tuple(sorted(ring.NB[z]&B))
        if 1<=len(S)<=3:
            factors.append(z);support[z]=S;byk[len(S)]+=1
    # Variable x[z,b] means factor z is assigned to eligible owner b.
    var={};rev={};nextv=1
    for z in factors:
        for b in support[z]:
            var[(z,b)]=nextv;rev[nextv]=(z,b);nextv+=1
    selector={};selrev={}
    for z in factors:
        selector[z]=nextv;selrev[nextv]=z;nextv+=1
    clauses=[];atleast=0;atmost=0;conflict_clauses=0
    # Selector-guarded at-least-one; at-most-one can remain unconditional since
    # inactive factors may simply set all assignment variables false.
    for z in factors:
        xs=[var[(z,b)] for b in support[z]]
        clauses.append([-selector[z]]+xs);atleast+=1
        for i in range(len(xs)):
            for j in range(i+1,len(xs)):
                clauses.append([-xs[i],-xs[j]]);atmost+=1
    eligible=defaultdict(list)
    for z in factors:
        for b in support[z]:eligible[b].append(z)
    owner_pair_checks=0
    for b,L in eligible.items():
        for i,z in enumerate(L):
            for w in L[i+1:]:
                owner_pair_checks+=1
                if w in ring.NB[z]:continue
                clauses.append([-var[(z,b)],-var[(w,b)]]);conflict_clauses+=1
    assumptions=[selector[z] for z in factors]
    with Solver(name=a.solver,bootstrap_with=clauses) as s:
        sat=s.solve(assumptions=assumptions)
        model=s.get_model() if sat else None
        core=s.get_core() if not sat else None
    out={'method':'support-le3-owner-clique-list-sat','solver':a.solver,'factor_count':len(factors),'support_histogram':{str(k):v for k,v in sorted(byk.items())},'assignment_variables':len(var),'selector_variables':len(selector),'clauses':len(clauses),'atleast_clauses':atleast,'atmost_clauses':atmost,'owner_conflict_clauses':conflict_clauses,'owner_pair_checks':owner_pair_checks,'sat':bool(sat)}
    if sat:
        pos={x for x in model if x>0};chosen={};groups=defaultdict(list)
        for z in factors:
            owners=[b for b in support[z] if var[(z,b)] in pos]
            if len(owners)!=1:raise RuntimeError(('assignment cardinality',z,owners))
            chosen[z]=owners[0];groups[owners[0]].append(z)
        bad=[]
        for b,L in groups.items():
            for i,z in enumerate(L):
                for w in L[i+1:]:
                    if w not in ring.NB[z]:bad.append((b,z,w))
        if bad:raise RuntimeError(('clique replay',bad[:5]))
        out.update({'assigned_owner_groups':len(groups),'max_owner_group_size':max(map(len,groups.values())) if groups else 0,'owner_group_size_histogram':{str(k):v for k,v in sorted(Counter(map(len,groups.values())).items())},'clique_replay_bad_pairs':0,'assignment':[[z,chosen[z]] for z in sorted(factors)]})
    else:
        core=core or []
        core_factors=sorted(selrev[abs(l)] for l in core if abs(l) in selrev)
        out.update({'unsat_core_selector_count':len(core_factors),'unsat_core_factors':[{'z':z,'support':list(support[z])} for z in core_factors]})
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('assignment','unsat_core_factors')},sort_keys=True))
    if not sat:print(json.dumps({'unsat_core_preview':out['unsat_core_factors'][:30]},sort_keys=True))
if __name__=='__main__':main()
