#!/usr/bin/env python3
"""Exact post-audit exclusion of m220 n11=6 seq5: 11^6 12^19 13^8 14^3.

Uses only the certified n11=6 low-graph R=22/24 boundary, degree-class
handshakes and S caps, plus the complete 3-member (4,5,22) edge-88 catalogue.
A six-vertex low component leaves <=3 anticomplete B88 vertices, forcing
S=164 degree-13 vertices to have one degree-14 neighbor. Class-edge totals
then rule out every degree sequence. No SAT or withdrawn row predicate.
"""
from collections import Counter
from itertools import combinations
import hashlib
import json
import networkx as nx

B88 = [
    'U?`@?bGKdWSWRELSWk?fGtHUMVEuH@VP`}HA[Ui?',
    'U?`D@`gFCkIWwcbK\\CPVOdQWu[Cqsadm@ddCRPM?',
    'U?`@?bGpDcCY[PCyTahjgxobZG@tbAxIaMYGRY`?',
]
LOW = {22: 'Ep~o', 24: 'EznW'}
B88_SHA256 = 'cdb6bbe20c73cd578590d57d896a343fceed76f5216d2a8524ccd1afd9559fb8'


def pack_low_graphs():
    ordered_bytes = ('\n'.join(B88)+'\n').encode('ascii')
    assert hashlib.sha256(ordered_bytes).hexdigest() == B88_SHA256
    Bs = [nx.from_graph6_bytes(s.encode()) for s in B88]
    assert len(Bs)==3 and all(len(B)==22 and B.number_of_edges()==88 for B in Bs)
    cert={}
    for R,code in LOW.items():
        L=nx.from_graph6_bytes(code.encode())
        assert len(L)==6 and L.number_of_edges()==R//2
        target_degrees=sorted(d for _,d in L.degree())
        rows=[]
        for b,B in enumerate(Bs):
            adjacency=[sum(1<<q for q in B.neighbors(v)) for v in B]
            hist_profile=Counter();hist_exact=Counter()
            for S in combinations(range(22),6):
                m=sum(1<<v for v in S)
                degrees=sorted((adjacency[v]&m).bit_count() for v in S)
                if degrees!=target_degrees:
                    continue
                q=sum((not (m>>w&1)) and (adjacency[w]&m)==0 for w in range(22))
                hist_profile[q]+=1
                if nx.is_isomorphic(B.subgraph(S),L):
                    hist_exact[q]+=1
            rows.append({'b_type':b,'profile_candidate_counts':dict(sorted(hist_profile.items())),
                         'exact_induced_copy_counts':dict(sorted(hist_exact.items())),
                         'maximum_anticomplete_vertices':max(hist_profile,default=-1)})
        cert[str(R)]=rows
    assert [x['maximum_anticomplete_vertices'] for x in cert['22']]==[3,2,2]
    assert [x['exact_induced_copy_counts'] for x in cert['24']]==[{}, {}, {}]
    return cert


def enumerate_class_matrices():
    rows=[]
    for R in (22,24):
        e11_12=66-R
        for x in range(29):          # e13_13
            for y in range(25):      # e13_14
                for z in range(4):   # e14_14
                    e12_13=104-2*x-y
                    e12_14=42-y-2*z
                    rem=228-e11_12-e12_13-e12_14
                    if e12_13<0 or e12_14<0 or rem<0 or rem%2:
                        continue
                    e12_12=rem//2
                    S12=11*e11_12+24*e12_12+13*e12_13+14*e12_14
                    S13=1248+2*x+2*y
                    S14=504+y+4*z
                    if not 132*19<=S12<=147*19:
                        continue
                    if not 143*8<=S13<=164*8:
                        continue
                    if not 154*3<=S14<=178*3:
                        continue
                    D=8*164-S13
                    assert D in (0,2,4,6)
                    t=8-D    # at least t of eight degree-13 vertices have S=164
                    # Each extreme vertex has exactly one degree-14 neighbor.
                    # For z=3, no vertex may join all three degree-14 vertices.
                    max_y=8+D if z==3 else 8+2*D
                    rows.append({'R':R,'x':x,'y':y,'z':z,'D':D,'extreme_min':t,
                                 'y_capacity':max_y,'gap':y-max_y})
    assert len(rows)==84
    assert Counter(r['R'] for r in rows)=={22:54,24:30}
    assert all(r['extreme_min']>=2 and r['gap']>0 for r in rows)
    assert min(r['gap'] for r in rows)==1
    return rows


def main():
    packing=pack_low_graphs()
    rows=enumerate_class_matrices()
    output={
        'campaign':'m220-n11-6-seq5-extreme-packing-post-audit',
        'degree_sequence':{'11':6,'12':19,'13':8,'14':3},
        'edges':220,
        'source':'complete McKay extreme-edge R(4,5,22) catalogue (e=88)',
        'B88_ordered_graph6_sha256':B88_SHA256,
        'low_graph_packings':packing,
        'candidate_class_matrices':len(rows),
        'candidate_by_low_R':dict(sorted(Counter(str(r['R']) for r in rows).items())),
        'minimum_capacity_contradiction_margin':min(r['gap'] for r in rows),
        'capacity_violations_by_low_R':dict(sorted(Counter(str(r['R']) for r in rows if r['gap']>0).items())),
        'class_matrix_results':rows,
        'local_lemma':(
            'For an extreme degree-13 vertex v (S(v)=164), write k for its '
            'number of degree-14 neighbors. No degree-11 vertex meets the '
            '13/14 classes at this low-graph boundary. The 13-class degree '
            'in H equals 8-2k, so v has exactly 2+k other high nonneighbors. '
            'The complete B88 list allows at most three vertices anticomplete '
            'to the six low vertices, hence k<=1; k=0 would require eight '
            'degree-13 neighbors although there are only seven others. Thus k=1.'),
        'global_lemma':(
            'D=8*164-S13 is the nonnegative integral deficit sum, so at least '
            '8-D degree-13 vertices are extreme. Counting edges to three '
            'degree-14 vertices gives y<=8+2D, improved to y<=8+D '
            'when those three form a triangle. Every one of the 84 class '
            'matrices violates its applicable bound.'),
        'status':'UNSAT_for_this_degree_sequence',
        'soundness':(
            'Degree-class handshake identities, post-audit universal low-graph '
            'orbits, exact S upper bounds, complete B88 graph6 stratum, and '
            'exhaustive induced six-set checks; never uses withdrawn tf() or SAT.')
    }
    print(json.dumps(output,indent=2,sort_keys=True))


if __name__=='__main__':
    main()
