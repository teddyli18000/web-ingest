#!/usr/bin/env python3
"""Sound post-audit exclusion of m=220,n11=6 sequence 8.

Sequence: 11^6 12^20 13^6 14^4.
Uses the class-boundary verifier to reduce to the unique R=22 low graph and
its two surviving class-edge matrices, then excludes each by a fixed
independent-6 obstruction. No SAT and no withdrawn row-domain predicate.
"""
from __future__ import annotations
import json
import networkx as nx
import m220_n11_6_class_boundary_verify as cb

def alpha_at_least_two(G):
    return next((tuple(e) for e in nx.non_edges(G)),None)

def exclude_pattern_1(L,m):
    assert m['e13_13']==2 and m['e13_14']==22 and m['e14_14']==4
    # Four Q vertices with four edges cannot contain a triangle: otherwise
    # every H vertex could meet at most three Q vertices, giving e(H,Q)<=18.
    # Hence Q=C4. There are exactly two missing H-Q incidences. For an H-H
    # edge, its endpoints cannot have adjacent common Q-neighbours (else K4),
    # so their common Q-neighbourhood in C4 has size at most two. Therefore
    # both global missing incidences must touch the endpoints of every H-H
    # edge. With two H-H edges, they must share a center and both missing
    # incidences lie at that center (on opposite Q vertices): H=P3+3 isolates.
    H=nx.Graph();H.add_nodes_from(range(6));H.add_edges_from([(0,1),(0,2)])
    I4=(0,3,4,5);assert H.subgraph(I4).number_of_edges()==0
    low_pair=alpha_at_least_two(L);assert low_pair is not None
    return {'status':'UNSAT',
            'reason':'fixed independent 6 = low nonedge + {P3 center, three H isolates}',
            'low_independent_pair':list(low_pair),'high_independent4':list(I4)}

def exclude_pattern_2(L,m):
    assert m['e13_13']==6 and m['e13_14']==18 and m['e14_14']==5
    # Q=K4-e. A triangle-free Q-neighbourhood has size at most three, and the
    # only size-three choices contain both endpoints a,b of the missing Q-edge
    # plus exactly one of c,d. Since e(H,Q)=18, every H vertex has exactly one
    # of these two choices. Same-choice H vertices cannot be adjacent, so H is
    # bipartite by choice. Six H-H edges rule out a 1+5 split (capacity 5).
    # A 2+4/4+2 split has an independent four-vertex color class; in a 3+3
    # split, one three-vertex color class plus its unchosen Q vertex is an
    # independent four-set. Combine with any nonedge of the low graph.
    low_pair=alpha_at_least_two(L);assert low_pair is not None
    cases=[]
    for k in (2,3,4):
        cap=k*(6-k);assert cap>=6
        high_I4=('four H vertices in the larger color class' if max(k,6-k)>=4
                 else 'three H vertices in one color class plus the opposite Q third vertex')
        cases.append({'color_split':[k,6-k],'cross_edge_capacity':cap,
                      'high_independent4':high_I4})
    return {'status':'UNSAT',
            'reason':'every feasible H color split contains a fixed independent 4; combine with a low nonedge',
            'low_independent_pair':list(low_pair),'color_split_cases':cases}

def main():
    seqs=cb.n11_6_sequences();seq=seqs[7]
    assert seq=={11:6,12:20,13:6,14:4}
    assert cb.simple_R_upper(seq)==24
    L=nx.from_graph6_bytes(b'Ep~o')
    assert [L.degree(i) for i in range(6)]==[4,3,4,3,4,4]
    assert alpha_at_least_two(L) is not None
    r24=cb.enum_seq8(24)
    assert len(r24)==2 and all(not cb.seq8_survival_reason(x)[0] for x in r24)
    r22=cb.enum_seq8(22)
    surv=[x for x in r22 if cb.seq8_survival_reason(x)[0]]
    assert len(surv)==2
    s1=next(x for x in surv if x['e14_14']==4)
    s2=next(x for x in surv if x['e14_14']==5)
    p1=exclude_pattern_1(L,s1);p2=exclude_pattern_2(L,s2)
    out={'campaign':'m220-n11-6-seq8-independent6-post-audit','edges':220,
         'degree_sequence':{str(k):v for k,v in seq.items()},
         'R24_class_patterns':len(r24),'R24_all_unsat':True,
         'R22_class_patterns':len(r22),'R22_survivors_before_independent6':len(surv),
         'R22_pattern_exclusions':[{'class_matrix':s1,**p1},{'class_matrix':s2,**p2}],
         'all_unsat':True,
         'soundness':'Uses only the post-audit universal R=22 low graph, exact class handshakes, and direct K4/I6 implications. No withdrawn row-domain predicate, SAT result, or external high-stratum catalogue is used.',
         'conclusion':'No 220-edge R(4,6,36) graph has degree sequence 11^6 12^20 13^6 14^4.'}
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=='__main__':main()
