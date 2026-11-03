#!/usr/bin/env python3
"""Post-audit necessary condition for 220-edge (4,6,36), degree sequence
11^6 12^18 13^11 15. Uses published complete A32/B88 graph strata and the
already certified lower bound R=sum_(deg11 v)(132-S(v))>=22.
"""
import itertools
import json
from collections import Counter, defaultdict
import networkx as nx

# Complete R(3,6,13), 32-edge stratum: independently certified unique type.
A32 = "Ls`rbPgB_[ANC]"
# Complete R(4,5,22), 88-edge stratum from McKay r45extreme.tar.gz
# Archive SHA256: 9cfac9dbd1c209cfa342e5d5424df2a7a3fbb008ca00bf0a992e5bbe72b
B88 = [
    "U?`@?bGKdWSWRELSWk?fGtHUMVEuH@VP`}HA[Ui?",
    "U?`D@`gFCkIWwcbK\\CPVOdQWu[Cqsadm@ddCRPM?",
    "U?`@?bGpDcCY[PCyTahjgxobZG@tbAxIaMYGRY`?",
]

def independent(G, S):
    return not any(G.has_edge(u, v) for u, v in itertools.combinations(S, 2))

def validate(A, Bs):
    assert len(A) == 13 and A.number_of_edges() == 32
    assert sorted(dict(A.degree()).values()) == [4] + [5]*12
    assert not any(all(A.has_edge(u,v) for u,v in itertools.combinations(S,2))
                   for S in itertools.combinations(A,3))
    assert not any(independent(A,S) for S in itertools.combinations(A,6))
    assert len(Bs) == 3
    for B in Bs:
        assert len(B)==22 and B.number_of_edges()==88
        assert not any(all(B.has_edge(u,v) for u,v in itertools.combinations(S,2))
                       for S in itertools.combinations(B,4))
        assert not any(independent(B,S) for S in itertools.combinations(B,5))

def allowed_positions(A, B, buckets):
    """An extreme degree-13 vertex q in B has N_B(q) induced inside A32."""
    out=[]
    for q in B:
        H=B.subgraph(B.neighbors(q))
        key=(len(H), H.number_of_edges(), tuple(sorted(dict(H.degree()).values())))
        if any(nx.is_isomorphic(H,T) for T in buckets.get(key,())):
            out.append(q)
    return out

def main():
    A=nx.from_graph6_bytes(A32.encode())
    Bs=[nx.from_graph6_bytes(line.encode()) for line in B88]
    validate(A,Bs)
    # Isomorphism test #1: enumerated induced A subgraphs, with invariant
    # prefilter only (never used to declare a match).
    buckets=defaultdict(list)
    for k in range(7,10):
        for S in itertools.combinations(A,k):
            H=A.subgraph(S)
            key=(k,H.number_of_edges(),tuple(sorted(dict(H.degree()).values())))
            buckets[key].append(H)
    records=[]
    for i,B in enumerate(Bs):
        eligible=allowed_positions(A,B,buckets)
        # Independent check #2: VF2 induced-subgraph matcher, a distinct API.
        second=[q for q in B if nx.algorithms.isomorphism.GraphMatcher(
                 A,B.subgraph(B.neighbors(q))).subgraph_is_isomorphic()]
        assert eligible==second
        records.append({
            "b_ordinal":i, "eligible_vertices":eligible,
            "eligible_internal_degrees":[B.degree(q) for q in eligible],
            "eligible_induced_edges":sorted(map(list,B.subgraph(eligible).edges())),
            "degree_histogram":dict(sorted(Counter(dict(B.degree()).values()).items())),
        })
    assert [r["eligible_vertices"] for r in records]==[[8,9,12,15],[],[]]
    assert records[0]["eligible_internal_degrees"]==[7]*4
    assert records[0]["eligible_induced_edges"]==[[8,15],[9,12]]
    # Sum S(v) = sum d(v)^2 = 5402. For 11-vertices,
    # S(v)=132-r(v); certified R=sum r>=22. For d=12, S<=147,
    # for d=15, S<=189. Hence sum_(degree13)S >=1797.
    sq=6*11**2+18*12**2+11*13**2+15**2
    s13min=sq-(6*132-22)-18*147-189
    deficit=11*164-s13min
    assert (sq,s13min,deficit)==(5402,1797,7)
    # At most seven of the eleven 13-vertices can have S<164.
    # Among >=4 extreme vertices a K4-free graph has a nonedge.
    # For each such nonadjacent pair u,v, in B_v the vertex u must
    # be among the eligible sites above, forcing B_v=B88[0],
    # deg_Bv(u)=7 and |N(v) intersect N(u)|=13-7=6.
    out={
        "campaign":"m220-n11-6-seq4-b88-embedding-post-audit",
        "scope":"36 vertices, 220 edges, degree sequence 11^6 12^18 13^11 15",
        "catalogue_counts":{"A32":1,"B88":3},
        "B88_embedding_results":records,
        "S13_sum_lower_bound":s13min,
        "S13_deficit_upper_bound":deficit,
        "extreme13_count_lower_bound":11-deficit,
        "nonadjacent_extreme_pair":{
            "exists":True,"B_type_at_each_endpoint":0,
            "common_neighbor_count":6,"eligible_induced_pattern":"2K2"},
        "status":"necessary condition, NOT a complete seq4 exclusion",
        "soundness":"two independent induced-subgraph isomorphism APIs; no withdrawn row predicate or SAT."
    }
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
