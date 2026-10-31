#!/usr/bin/env python3
"""Sound post-audit exclusion of m=220,n11=6 sequence 6.

Sequence 11^6 12^19 13^9 14 15. The class-boundary verifier leaves six
R=22 class-edge matrices. Five die from high-subgraph alpha/K4 conditions;
the sixth dies by an exact 3+3+3 partition argument.
"""
from __future__ import annotations
import itertools,json,networkx as nx
import m220_n11_6_class_boundary_verify as cb

def three_edge_complement_lemma():
    """K6 minus three edges is K4-free only for a perfect-matching deletion."""
    V=range(6);E=list(itertools.combinations(V,2));checked=0
    for F in itertools.combinations(E,3):
        G=nx.Graph();G.add_nodes_from(V);G.add_edges_from(F);checked+=1
        matching=len({v for e in F for v in e})==6
        has_i4=any(G.subgraph(S).number_of_edges()==0 for S in itertools.combinations(V,4))
        assert matching or has_i4
    assert checked==455
    return checked

def main():
    seq=cb.n11_6_sequences()[5]
    assert seq=={11:6,12:19,13:9,14:1,15:1}
    L=nx.from_graph6_bytes(b'Ep~o');low_pair=next(iter(nx.non_edges(L)))
    mats=cb.enum_seq6(22);assert len(mats)==6 and cb.enum_seq6(24)==[]
    rows=[]
    for i,m in enumerate(mats):
        Hq=m['e13_14'];Hp=m['e13_15'];qp=m['e14_15']
        if i in (0,1):
            assert Hq==9
            rows.append({'index':i,'status':'UNSAT',
              'reason':'d14 is adjacent to all nine d13 vertices, so the d13 graph is triangle-free; R(3,4)=9 gives an independent 4 in the high graph'})
            continue
        if i in (2,3,4):
            assert qp==1
            common_lower=9-((9-Hq)+(9-Hp));assert common_lower>=4
            rows.append({'index':i,'status':'UNSAT','common_d13_neighbor_lower_bound':common_lower,
              'reason':'adjacent d14,d15 vertices have at least four common d13 neighbours; these common neighbours must be independent to avoid K4, contradicting high-subgraph alpha<=3'})
            continue
        assert i==5 and (Hq,Hp,qp)==(6,6,1)
        assert m['e13_13']==21 and m['S13']==1476==9*164
        # Missing d13-neighbour sets A,B of d14,d15 each have size 3. Their
        # common d13-neighbour set C is independent because d14-d15 is an edge.
        # alpha(high)<=3 and inclusion-exclusion force A,B disjoint and |C|=3.
        degA,degB,degC=5,6,3
        # S(h)=164 = 156+d_H+2*I(d14)+3*I(d15).
        # Thus d_H=5 on A, 6 on B, 3 on C.
        eAB6=m['e13_13']-3*degC;assert eAB6==12
        checked=three_edge_complement_lemma()
        # C is independent. Its total H-degree is 9, leaving 12 edges in the
        # six-vertex A∪B graph. K4-freeness makes this K6 minus a perfect
        # matching. Hence every A/B vertex has four neighbours within A∪B,
        # so A has one C-neighbour each and B has two.
        cdegA=degA-4;cdegB=degB-4;assert (cdegA,cdegB)==(1,2)
        # d15 is adjacent to all A∪C and d14 to all B∪C, so both induced
        # graphs are triangle-free. The perfect matching contains one missing
        # AA edge and one missing BB edge, hence H[B]=P3. Adjacent B endpoints
        # each have a 2-subset of the 3-set C as neighbours; those 2-subsets
        # must intersect, creating a forbidden triangle in B∪C.
        rows.append({'index':i,'status':'UNSAT','partition_sizes':{'A':3,'B':3,'C':3},
          'H_internal_degrees':{'A':degA,'B':degB,'C':degC},
          'edges_in_AunionB':eAB6,'missing_edge_lemma_cases_checked':checked,
          'C_neighbours_per_A':cdegA,'C_neighbours_per_B':cdegB,
          'reason':'H[A∪B]=K6 minus a perfect matching; H[B]=P3, but adjacent B vertices each meet 2 of the 3 C vertices, forcing a triangle in B∪C and hence a K4 with d14'})
    assert all(r['status']=='UNSAT' for r in rows)
    out={'campaign':'m220-n11-6-seq6-high-post-audit','edges':220,
      'degree_sequence':{str(k):v for k,v in seq.items()},
      'R24_class_matrix_count':0,'R22_class_matrix_count':len(mats),
      'R22_exclusions':rows,'all_unsat':True,'low_independent_pair':list(low_pair),
      'soundness':'Uses only the post-audit R=22 low boundary, exact class handshakes, endpoint S caps, R(3,4)=9, and finite K4/I6 arguments. No withdrawn row-domain predicate or SAT result is used.',
      'conclusion':'No 220-edge R(4,6,36) graph has degree sequence 11^6 12^19 13^9 14 15.'}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
