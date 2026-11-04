#!/usr/bin/env python3
"""Solver-free post-audit exclusion of m220 n11=6 seq1's x=e(13,13)=49 branch."""
import itertools
import json
from collections import defaultdict
import networkx as nx

LOW = {22: "Ep~o", 24: "EznW"}

def low_cover():
    out = {}
    for R, g6 in LOW.items():
        G = nx.from_graph6_bytes(g6.encode())
        assert len(G) == 6 and 2*G.number_of_edges() == R
        missing = list(nx.non_edges(G))
        assert all(not all(u in S or v in S for u,v in missing)
                   for S in itertools.combinations(G,2))
        assert not any(G.subgraph(S).number_of_edges() == 0
                       for S in itertools.combinations(G,3))
        out[str(R)] = {"low_middle_edges": 66-R, "minimum_low_cover": 3}
    return out

def cubic8():
    """Complete triangle-free 3-regular 8-vertex census, N(0) relabelled 1,2,3."""
    n=8; adj=[0]*n; deg=[0]*n
    for j in (1,2,3):
        adj[0]|=1<<j; adj[j]|=1; deg[0]+=1; deg[j]+=1
    count=0; reps=[]
    def rec(v):
        nonlocal count
        if v==n:
            assert all(d==3 for d in deg)
            count+=1
            G=nx.Graph(); G.add_nodes_from(range(n))
            G.add_edges_from((i,j) for i in range(n) for j in range(i+1,n)
                             if adj[i]>>j&1)
            if any(G.subgraph(S).number_of_edges()==0
                   for S in itertools.combinations(range(n),4)):
                return
            if not any(nx.is_isomorphic(G,Q) for Q in reps): reps.append(G)
            return
        need=3-deg[v]
        options=[w for w in range(v+1,n) if deg[w]<3 and not (adj[v]&adj[w])]
        for S in itertools.combinations(options,need):
            for w in S:
                adj[v]|=1<<w; adj[w]|=1<<v; deg[v]+=1; deg[w]+=1
            rec(v+1)
            for w in S:
                adj[v]^=1<<w; adj[w]^=1<<v; deg[v]-=1; deg[w]-=1
    rec(1)
    Wagner=nx.circulant_graph(8,[1,4])
    assert count==96 and len(reps)==1 and nx.is_isomorphic(reps[0],Wagner)
    return {"labelled_trianglefree_cubic":count,
            "alpha_le3_isomorphism_classes":len(reps)}, Wagner

def exact_gluing(F):
    """Complete 6x8 crossing-edge search: S=K3,3, T=complement Wagner."""
    T=nx.complement(F)
    assert len(T)==8 and T.number_of_edges()==16
    pairs=list(itertools.combinations(range(8),2))
    eT={(u,v) for u,v in pairs if T.has_edge(u,v)}
    nonT=set(pairs)-eT; full=255
    def independent(mask):
        return all(not (mask>>u&1 and mask>>v&1) for u,v in eT)
    def clique(mask):
        return all(not (mask>>u&1 and mask>>v&1) for u,v in nonT)
    rows=[]
    for S in itertools.combinations(range(8),4):
        mask=sum(1<<v for v in S)
        if any(T.subgraph(Q).number_of_edges()==3
               for Q in itertools.combinations(S,3)): continue
        outside=[v for v in range(8) if not mask>>v&1]
        if any(T.subgraph(Q).number_of_edges()==0
               for Q in itertools.combinations(outside,3)): continue
        rows.append(mask)
    assert len(rows)==38
    # Three same-side S vertices form an independent triple; each T vertex
    # must meet that side. Since each T vertex has three S-neighbors total,
    # both sides have column incidence 1 or 2.
    bycounts=defaultdict(list)
    for ids in itertools.combinations_with_replacement(range(len(rows)),3):
        triple=tuple(rows[i] for i in ids)
        cs=[sum((r>>v)&1 for r in triple) for v in range(8)]
        if min(cs)!=1 or max(cs)!=2: continue
        # Two same-side S vertices are nonadjacent. Their common T
        # nonneighbors must be a clique, else an independent 4-set forms.
        if any(not clique(full^(triple[i]|triple[j]))
               for i,j in itertools.combinations(range(3),2)): continue
        bycounts[sum((c-1)<<v for v,c in enumerate(cs))].append(triple)
    triples=sum(map(len,bycounts.values()))
    assert triples==388 and len(bycounts)==62
    pairs_tested=valid=0
    for signature, As in bycounts.items():
        for A in As:
            for B in bycounts.get(full^signature,()):
                pairs_tested+=1
                # Cross-side S vertices are adjacent. Their common T
                # neighbors must be independent, else a K4 forms.
                if all(independent(a&b) for a in A for b in B): valid+=1
    assert pairs_tested==2372 and valid==0
    return {"individual_cross_rows":len(rows),"same_side_triples":triples,
            "column_signatures":len(bycounts),
            "complementary_triple_pairs_tested":pairs_tested,
            "surviving_cross_gluings":valid}

def main():
    low=low_cover()
    cubic,F=cubic8()
    gluing=exact_gluing(F)
    # Six degree-11 lows (L), fourteen degree-13 highs (H),
    # sixteen degree-12 middles (M); L and H anticomplete.
    # x=e(H)=49 and S13<=163 force 7-regular H.
    # e(L,M)=66-R <=44<16*3, so some m in M meets <=2 lows.
    # Every low graph's missing edges require a vertex cover >=3;
    # thus m misses an independent pair in L. To avoid I6,
    # T=H\N_H(m) must have alpha<=2; S=N_H(m) is triangle-free
    # (otherwise m plus its neighboring triangle is a K4).
    # R(3,4)=9 forces 6<=q=|S|<=8.
    # With S trianglefree alpha<=3, max degree(S)<=3.
    # Complement(T) is trianglefree alpha<=3, max degree<=3.
    # As H is 7-regular, eT-eS=49-7q.
    # q7: eS<=10, eT>=11, but regularity requires eT=eS.
    # q8: eS<=12, eT>=6, yet regularity eT=eS-7<=5.
    # q6: eS<=9, eT>=16, eT=eS+7 => eS9, eT16.
    # Then S=K3,3 and complement(T) is triangle-free cubic alpha<=3;
    # its unique isomorphism type and exact crossing search are above.
    out={
        "campaign":"m220-n11-6-seq1-x49-partition-post-audit",
        "degree_sequence":{"11":6,"12":16,"13":14},"edges":220,
        "eliminated_class_matrices":[{"R":22,"x":49},{"R":24,"x":49}],
        "low_vertex_cover_and_capacity":low,
        "forced_middle_vertex_low_neighbors_max":2,
        "high_partition_size_range":[6,7,8],
        "q7_inequality":"eS<=10, eT>=11, regularity forces eS=eT",
        "q8_inequality":"eS<=12, eT>=6, regularity forces eT=eS-7<=5",
        "q6_forced":"S=K3,3, |S|=6, eS=9; T has 8 vertices and 16 edges",
        "cubic_T_complement_catalogue":cubic,
        "q6_exact_cross_gluing":gluing,
        "soundness":"Finite cubic census and exhaustive crossing-row cover; no SAT, MILP or withdrawn row CSP.",
        "status":"UNSAT_for_x49_only","x49_eliminated":True,
        "conclusion":"The x=49 class matrices in seq1, at R22 and R24, cannot extend to a 36-vertex (4,6)-graph."
    }
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
