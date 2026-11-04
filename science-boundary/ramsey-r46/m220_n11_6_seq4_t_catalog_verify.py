#!/usr/bin/env python3
"""Independently certify the complete R(3,4,7/8) graph6 lists used by the C++ high-only proof.

NetworkX's graph atlas is complete through seven vertices. Enumerating all
128 possible neighborhoods of an eighth vertex extends that completeness to
8-vertex graphs, after isomorphism deduplication.
"""
from itertools import combinations
import json
import networkx as nx

SEVEN = ('Fhc?G', 'FPq?g', 'FhCKG', 'FHhGg', 'Fh_gg', 'FhEK_', 'FlO[O', 'FlgGg', 'FhUk_')
EIGHT = ('GPq?jG', 'GHhGm_', 'GlO[PK')
TRI = tuple(combinations(range(8), 3))
I4 = tuple(combinations(range(8), 4))

def valid_rows(a, n):
    if any((a[u]>>v&1) and (a[u]>>w&1) and (a[v]>>w&1)
           for u,v,w in TRI if w<n):
        return False
    if any(not((a[u]>>v&1) or (a[u]>>w&1) or (a[u]>>t&1)
                or (a[v]>>w&1) or (a[v]>>t&1) or (a[w]>>t&1))
           for u,v,w,t in I4 if t<n):
        return False
    return True

def rows(G):
    a=[0]*8
    for u,v in G.edges():
        a[u] |= 1<<v
        a[v] |= 1<<u
    return a

def to_graph(a,n):
    H=nx.Graph()
    H.add_nodes_from(range(n))
    H.add_edges_from((u,v) for u in range(n) for v in range(u+1,n) if a[u]>>v&1)
    return H

def main():
    a7=[nx.convert_node_labels_to_integers(G) for G in nx.graph_atlas_g() if len(G)==7]
    seven=[G for G in a7 if valid_rows(rows(G),7)]
    assert len(seven)==9
    assert {nx.to_graph6_bytes(G,header=False).decode().strip() for G in seven}==set(SEVEN)
    reps=[]
    for G in a7:
        a=rows(G)
        for mask in range(128):
            b=a.copy();b[7]=mask
            for u in range(7):
                if mask>>u&1:b[u] |= 1<<7
            if not valid_rows(b,8): continue
            H=to_graph(b,8)
            if not any(nx.is_isomorphic(H,R) for R in reps): reps.append(H)
    assert len(reps)==3
    standard=[nx.from_graph6_bytes(g.encode()) for g in EIGHT]
    assert all(valid_rows(rows(G),8) for G in standard)
    assert all(any(nx.is_isomorphic(G,H) for H in standard) for G in reps)
    assert all(any(nx.is_isomorphic(G,H) for H in reps) for G in standard)
    print(json.dumps({'R34_7_types':len(seven),'R34_8_types':len(reps),
                      'R34_7_graph6':list(SEVEN),'R34_8_graph6':list(EIGHT),
                      'independent_generation':'7-vertex atlas + all 2^7 eighth neighborhoods'},indent=2))
if __name__=='__main__':main()
