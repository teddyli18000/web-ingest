#!/usr/bin/env python3
"""Replay the support<=2 owner-clique assignment certificate.

Let B be the pinned 359-point core factor.  Consider every five-dimensional
factor z outside B with nonempty support S(z)=N[z]∩B of size at most two.  We
assign z to one owner f(z) in S(z), requiring that all factors assigned to one
owner form a clique in the C7^5 confusability graph.

Singleton-support factors are forced.  A size-two support gives one Boolean
choice, and every pair of nonconfusable factors sharing an eligible owner gives
a 2-SAT clause forbidding their simultaneous assignment to that owner.  The
script solves this 2-SAT instance with a built-in SCC implementation and then
independently replays every owner clique.

The product consequence is documented in
results/outside-outside-support2-closure.md: assign (u,v) to core cell
(f(u),f(v)).  Two 10D candidates assigned to one cell conflict in both
coordinates, so an independent set injects into its touched core cells.
"""
from __future__ import annotations
import argparse,json,itertools
from collections import Counter,defaultdict
from pathlib import Path
import bpz_joint_row_defects_maxsat as J

def solve_2sat(n,clauses):
    g=[[] for _ in range(2*n)];gr=[[] for _ in range(2*n)]
    def node(l):return 2*(abs(l)-1)+(0 if l>0 else 1)
    def add(a,b):g[a].append(b);gr[b].append(a)
    for c in clauses:
        if len(c)==1:
            a=node(c[0]);add(a^1,a)
        elif len(c)==2:
            a,b=map(node,c);add(a^1,b);add(b^1,a)
        else:raise RuntimeError(('non-2sat clause',c))
    seen=[False]*(2*n);order=[]
    for s in range(2*n):
        if seen[s]:continue
        seen[s]=True;st=[(s,0)]
        while st:
            v,k=st[-1]
            if k<len(g[v]):
                w=g[v][k];st[-1]=(v,k+1)
                if not seen[w]:seen[w]=True;st.append((w,0))
            else:order.append(v);st.pop()
    comp=[-1]*(2*n);cid=0
    for s in reversed(order):
        if comp[s]>=0:continue
        comp[s]=cid;st=[s]
        while st:
            v=st.pop()
            for w in gr[v]:
                if comp[w]<0:comp[w]=cid;st.append(w)
        cid+=1
    if any(comp[2*i]==comp[2*i+1] for i in range(n)):return None,cid
    ans=[comp[2*i]>comp[2*i+1] for i in range(n)]
    def ok(c):
        return any((lit>0 and ans[abs(lit)-1]) or (lit<0 and not ans[abs(lit)-1]) for lit in c)
    if not all(ok(c) for c in clauses):ans=[not x for x in ans]
    if not all(ok(c) for c in clauses):raise RuntimeError('SCC assignment replay failed')
    return ans,cid

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();root=a.tan_root.resolve()
    _base,ring,B,fam=J.load_geometry(root);B=set(B)
    factors=[];support={}
    for z in range(ring.n):
        if z in B:continue
        S=tuple(sorted(ring.NB[z]&B))
        if 1<=len(S)<=2:factors.append(z);support[z]=S
    singleton=[z for z in factors if len(support[z])==1];binary=[z for z in factors if len(support[z])==2]
    if (len(factors),len(singleton),len(binary))!=(425,50,375):raise RuntimeError(('factor census',len(factors),len(singleton),len(binary)))
    vid={z:i for i,z in enumerate(binary)};eligible=defaultdict(list)
    for z in singleton:eligible[support[z][0]].append((z,None))
    for z in binary:
        x,y=support[z];eligible[x].append((z,False));eligible[y].append((z,True))
    def forbid(z,val):
        i=vid[z]+1
        return i if val is False else -i
    clauses=[];forced_bad=[]
    for owner,L in eligible.items():
        for i,(z,vz) in enumerate(L):
            for w,vw in L[i+1:]:
                if w in ring.NB[z]:continue
                if vz is None and vw is None:forced_bad.append((owner,z,w))
                elif vz is None:clauses.append((forbid(w,vw),))
                elif vw is None:clauses.append((forbid(z,vz),))
                else:clauses.append((forbid(z,vz),forbid(w,vw)))
    if forced_bad:raise RuntimeError(('forced singleton nonclique',forced_bad[:5]))
    assignment,scc=solve_2sat(len(binary),clauses)
    if assignment is None:raise RuntimeError('support<=2 owner-clique 2-SAT unexpectedly UNSAT')
    groups=defaultdict(list);chosen={}
    for z in singleton:chosen[z]=support[z][0];groups[chosen[z]].append(z)
    for z,val in zip(binary,assignment):chosen[z]=support[z][1 if val else 0];groups[chosen[z]].append(z)
    bad=[]
    for owner,L in groups.items():
        for i,z in enumerate(L):
            for w in L[i+1:]:
                if w not in ring.NB[z]:bad.append((owner,z,w))
    if bad:raise RuntimeError(('owner clique replay',bad[:5]))
    # Every assigned owner is genuinely in the exact support.
    if any(chosen[z] not in support[z] for z in factors):raise RuntimeError('assignment outside support')
    out={'method':'pinned-support-le2-owner-clique-2sat','factor_count':len(factors),'support1_factors':len(singleton),'support2_factors':len(binary),'boolean_variables':len(binary),'clauses':len(clauses),'unit_clauses':sum(len(c)==1 for c in clauses),'binary_clauses':sum(len(c)==2 for c in clauses),'scc_count':scc,'assigned_owner_groups':len(groups),'max_owner_group_size':max(map(len,groups.values())),'owner_group_size_histogram':{str(k):v for k,v in sorted(Counter(map(len,groups.values())).items())},'clique_replay_bad_pairs':0,'assignment':[[z,chosen[z]] for z in sorted(factors)]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='assignment'},sort_keys=True))
if __name__=='__main__':main()
