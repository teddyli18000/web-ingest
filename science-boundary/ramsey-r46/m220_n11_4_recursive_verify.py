#!/usr/bin/env python3
"""Sound post-audit exclusion of the entire m=220, n11=4 layer.

No withdrawn row-domain predicate is used.  The proof combines the exact
m220 endpoint identity, complete A25/A26/B116 catalogues, recursive
neighbourhood consistency, and a final 8-vertex induced-subgraph check.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from itertools import combinations
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
A25_DEFAULT=HERE/'data/m219-r34-A25.g6'
A26_DEFAULT=HERE/'data/m219-r34-A26.g6'
B116_DEFAULT=HERE/'data/m219-r34-B116.g6'

def read_g6(p):
    return [nx.from_graph6_bytes(s.encode()) for s in Path(p).read_text().splitlines() if s]

def independent_sets(G,k):
    return [frozenset(S) for S in combinations(G.nodes(),k) if G.subgraph(S).number_of_edges()==0]

def triangle_free(G):
    return all(G.subgraph(S).number_of_edges()<3 for S in combinations(G.nodes(),3))

def local_need_profile(T,p):
    N=set(T.neighbors(p)); H=[h for h in T if h!=p and h not in N]
    return sorted(1+sum(T.has_edge(h,q) for q in N) for h in H)

def degree5_profiles(graphs):
    rows=[]
    for family,T in graphs:
        for p in T:
            if T.degree(p)!=5: continue
            need=local_need_profile(T,p)
            rows.append({'family':family,'edges':T.number_of_edges(),'vertex':p,
                         'needs':need,'need_ge5_count':sum(x>=5 for x in need)})
    assert rows and min(x['need_ge5_count'] for x in rows)>=2
    return rows

def hits_all_i5(A,S):
    return all(set(S)&T for T in independent_sets(A,5))

def unique_induced_types(graphs,k):
    out=[]
    for ti,T in enumerate(graphs):
        for S in combinations(T.nodes(),k):
            H=T.subgraph(S).copy()
            if not any(nx.is_isomorphic(H,X['graph']) for X in out):
                out.append({'type':ti,'vertices':list(S),'graph':H})
    return out

def main():
    ap=argparse.ArgumentParser();
    ap.add_argument('--A25',type=Path,default=A25_DEFAULT)
    ap.add_argument('--A26',type=Path,default=A26_DEFAULT)
    ap.add_argument('--B116',type=Path,default=B116_DEFAULT)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    A25=read_g6(a.A25); A26=read_g6(a.A26); B116=read_g6(a.B116)
    assert (len(A25),len(A26),len(B116))==(6,2,9)
    assert all(len(G)==11 and G.number_of_edges()==25 and triangle_free(G) and not independent_sets(G,6) for G in A25)
    assert all(len(G)==11 and G.number_of_edges()==26 and triangle_free(G) and not independent_sets(G,6) for G in A26)
    assert all(len(G)==24 and G.number_of_edges()==116 and independent_sets(G,4) and not independent_sets(G,5) for G in B116)

    low_graphs=[]
    atlas=[G for G in nx.graph_atlas_g() if len(G)==4]
    for G in atlas:
        if min(dict(G.degree()).values(),default=0)>=2 and G.number_of_edges()<6:
            low_graphs.append(nx.convert_node_labels_to_integers(G))
    uniq=[]
    for G in low_graphs:
        if not any(nx.is_isomorphic(G,H) for H in uniq): uniq.append(G)
    assert len(uniq)==2
    low_graph_summary=sorted((G.number_of_edges(),sorted(dict(G.degree()).values())) for G in uniq)
    assert low_graph_summary==[(4,[2,2,2,2]),(5,[2,2,3,3])]

    profiles=degree5_profiles([*(('A25',G) for G in A25),*(('A26',G) for G in A26)])
    assert all(min(dict(B.degree()).values())>=8 for B in B116)

    pair_rows=[]; exceptional=[]
    for ai,A in enumerate(A26):
        for u,v in combinations(A.nodes(),2):
            du,dv=A.degree(u),A.degree(v)
            if du!=5 and dv!=5:
                pair_rows.append({'A26_type':ai,'pair':[u,v],'degrees':sorted([du,dv]),'edge':A.has_edge(u,v)})
                exceptional.append((ai,u,v,A.has_edge(u,v)))
    assert pair_rows==[{'A26_type':0,'pair':[0,1],'degrees':[3,4],'edge':True}]

    ai,u,v,is_edge=exceptional[0]; A=A26[ai]
    assert is_edge
    assert not hits_all_i5(A,{u,v})
    thirds=[c for c in A if c not in (u,v) and hits_all_i5(A,{u,v,c})]
    assert thirds==[2,3,4,5,6]

    ind8=unique_induced_types(A26,8)
    assert len(ind8)==15
    q_checks=[]; degree8_total=0
    for bi,B in enumerate(B116):
        for q in B:
            if B.degree(q)!=8: continue
            degree8_total+=1
            H=B.subgraph(list(B.neighbors(q))).copy()
            matches=sum(nx.is_isomorphic(H,X['graph']) for X in ind8)
            q_checks.append({'B116_type':bi,'q':q,'neighbor_edges':H.number_of_edges(),
                             'neighbor_degree_sequence':sorted(dict(H.degree()).values()),
                             'A26_induced8_matches':matches})
            assert matches==0
    assert degree8_total==9

    profile_hist=Counter((x['family'],tuple(x['needs'])) for x in profiles)
    profile_hist_rows=[{'family':fam,'needs':list(needs),'count':cnt} for (fam,needs),cnt in sorted(profile_hist.items())]

    out={
      'campaign':'m220-n11-4-recursive-post-audit',
      'edges':220,'n11':4,
      'catalog_counts':{'A25':6,'A26':2,'B116':9},
      'low_graph_types':low_graph_summary,
      'degree5_recursive_profile_histogram':profile_hist_rows,
      'min_degree5_rows_requiring_capacity_ge5':min(x['need_ge5_count'] for x in profiles),
      'anchor_A26_non5_pairs':pair_rows,
      'exceptional_diamond':{
        'A26_type':ai,'low_edge':[u,v],'degrees':[A.degree(u),A.degree(v)],
        'pair_hits_all_I5':False,'third_vertices_that_complete_I5_hitting':thirds,
        'forced_q_cross_degree':3,'forced_q_B_degree':8,
        'A26_induced8_type_count':len(ind8),'degree8_q_candidates':degree8_total,
        'q_checks':q_checks},
      'soundness':'Uses endpoint r>=2, complete A25/A26/B116 catalogues, recursive neighbourhood consistency, exact I5 hitting, and induced-subgraph isomorphism only; no withdrawn row-domain predicate.',
      'conclusion':'No 220-edge R(4,6,36) graph can have exactly four degree-11 vertices.',
      'all_unsat':True}
    text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(text,end='')
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
if __name__=='__main__':main()
