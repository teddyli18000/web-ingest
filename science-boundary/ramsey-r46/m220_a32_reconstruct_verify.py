#!/usr/bin/env python3
"""Reconstruct the extreme R(3,6,13), e=32 local graph from R(3,5,8).

This is a finite exact lemma used in the m=220 R(4,6,36) analysis.

If A is triangle-free on 13 vertices, alpha(A)<=5 and e(A)=32, the 2026
catalogue profile inequality 3q<=346+e plus convexity forces degree sequence
5^12 4^1. Let x be the unique degree-4 vertex, N=N_A(x), and let M be the
8 non-neighbours of x. Then N is independent, A[M] is an R(3,5,8) graph,
e(A[M])=12, every n in N has exactly 4 neighbours in M, and every m in M has
cross degree 5-d_M(m). Enumerating the complete 179-graph R(3,5,8)
catalogue and these 4x8 incidence matrices yields one isomorphism type.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
DEFAULT=HERE/'data/r35_8.g6'

def independent(G,S): return G.subgraph(S).number_of_edges()==0

def valid_r358(G):
    return len(G)==8 and not any(G.subgraph(S).number_of_edges()==3 for S in itertools.combinations(G,3)) \
        and not any(independent(G,S) for S in itertools.combinations(G,5))

def alpha_le5(G): return not any(independent(G,S) for S in itertools.combinations(G,6))

def make_A(M,masks):
    G=nx.Graph();G.add_nodes_from(range(13));G.add_edges_from((0,i) for i in range(1,5))
    G.add_edges_from((5+u,5+v) for u,v in M.edges())
    for i,mask in enumerate(masks,1):
        G.add_edges_from((i,5+j) for j in range(8) if mask>>j&1)
    return G

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--catalog',type=Path,default=DEFAULT);ap.add_argument('--output',type=Path);a=ap.parse_args()
    raw=a.catalog.read_bytes();lines=[s.strip() for s in raw.decode('ascii').splitlines() if s.strip()]
    graphs=[nx.convert_node_labels_to_integers(nx.from_graph6_bytes(s.encode())) for s in lines]
    assert len(graphs)==179
    assert all(valid_r358(G) for G in graphs)
    Ms=[G for G in graphs if G.number_of_edges()==12];assert len(Ms)==15
    candidates=[];stats=[]
    for mi,M in enumerate(Ms):
        target=[5-M.degree(j) for j in range(8)];assert sum(target)==16
        allowed=[sum(1<<j for j in S) for S in itertools.combinations(range(8),4) if independent(M,S)]
        raw_count=good_count=0
        for inds in itertools.combinations_with_replacement(range(len(allowed)),4):
            sums=[0]*8
            for ii in inds:
                mask=allowed[ii]
                for j in range(8): sums[j]+=(mask>>j)&1
            if sums!=target: continue
            raw_count+=1;A=make_A(M,[allowed[ii] for ii in inds])
            assert A.number_of_edges()==32 and sorted(dict(A.degree()).values())==[4]+[5]*12
            assert not any(A.subgraph(S).number_of_edges()==3 for S in itertools.combinations(A,3))
            if not alpha_le5(A): continue
            good_count+=1;candidates.append(A)
        stats.append({'M_ordinal':mi,'M_degree_sequence':sorted(dict(M.degree()).values()),
                      'independent_4_rows':len(allowed),'degree_feasible_row_multisets':raw_count,
                      'alpha5_row_multisets':good_count})
    reps=[]
    for G in candidates:
        if not any(nx.is_isomorphic(G,H) for H in reps): reps.append(G)
    assert len(candidates)==1 and len(reps)==1
    A=reps[0];g6=nx.to_graph6_bytes(A,header=False).decode().strip();assert g6=='Ls`rbPgB_[ANC]'
    x=next(v for v,d in A.degree() if d==4)
    aut_count=sum(1 for _ in nx.algorithms.isomorphism.GraphMatcher(A,A).isomorphisms_iter())
    local_degree_hist={}
    for _,d in A.degree(): local_degree_hist[d]=local_degree_hist.get(d,0)+1
    assert local_degree_hist=={4:1,5:12} or local_degree_hist=={5:12,4:1}
    out={'campaign':'m220-a32-reconstruction-post-audit','source':'Brendan McKay complete R(3,5,8) catalogue',
         'source_url':'https://users.cecs.anu.edu.au/~bdm/data/r35_8.g6','catalog_sha256':hashlib.sha256(raw).hexdigest(),
         'catalog_count':len(graphs),'e12_core_count':len(Ms),'candidate_row_multisets':len(candidates),
         'A32_isomorphism_type_count':len(reps),'A32_graph6':g6,'degree_sequence':sorted(dict(A.degree()).values()),
         'automorphism_group_order':aut_count,'unique_degree4_vertex':x,'local_degree_histogram':local_degree_hist,
         'core_stats':stats,
         'soundness':'Finite reconstruction from the complete R(3,5,8) catalogue; only degree equations, triangle-freeness, alpha<=5, and graph isomorphism are used. No row-domain CSP or SAT result is used.',
         'conclusion':'The R(3,6,13) edge-32 stratum has a single isomorphism type with degree sequence 5^12 4^1. Hence for an ambient vertex v with this neighborhood, exactly one incident edge vu has ambient codegree 4 and the other twelve have ambient codegree 5.'}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(txt,end='')
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt)
if __name__=='__main__':main()
