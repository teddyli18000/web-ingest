#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,itertools
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
A25D=HERE/'data/m219-r34-A25.g6'
A26D=HERE/'data/m219-r34-A26.g6'
B116D=HERE/'data/m219-r34-B116.g6'

def read(p):
    return [nx.from_graph6_bytes(s.encode()) for s in Path(p).read_text().splitlines() if s]
def k4free(G):
    return all(G.subgraph(S).number_of_edges()<6 for S in itertools.combinations(G.nodes(),4))
def indep(G,k):
    return [frozenset(S) for S in itertools.combinations(G.nodes(),k) if G.subgraph(S).number_of_edges()==0]
def tri_free(G):
    return all(G.subgraph(S).number_of_edges()<3 for S in itertools.combinations(G.nodes(),3))
def isomorphic_subgraph(H,T):
    k=len(H)
    return any(nx.is_isomorphic(H,T.subgraph(S)) for S in itertools.combinations(T.nodes(),k))
def degree5_profiles(graphs):
    out=[]
    for fam,ti,T in graphs:
        for p in T:
            if T.degree(p)!=5: continue
            N=set(T.neighbors(p)); H=[h for h in T if h!=p and h not in N]
            needs=sorted(1+sum(T.has_edge(h,q) for q in N) for h in H)
            out.append((fam,ti,p,needs,sum(x>=5 for x in needs)))
    assert out and min(x[4] for x in out)>=2
    return out

def anchor_pair_feasible(L,v,A26):
    ns=list(L.neighbors(v)); assert len(ns)==2
    rel=L.has_edge(*ns); ts=[L.degree(x) for x in ns]
    count=0
    for A in A26:
        for a,b in itertools.permutations(A.nodes(),2):
            if A.has_edge(a,b)!=rel: continue
            # A low vertex with t<=3 has total high-degree excess w<=1. If it
            # were degree 5 inside another low vertex's A25/A26 neighbourhood,
            # the complete recursive profiles above would require at least two
            # outside neighbours with cross capacity >=5, impossible with w<=1.
            if ts[0]<=3 and A.degree(a)==5: continue
            if ts[1]<=3 and A.degree(b)==5: continue
            count+=1
    return count

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--A25',type=Path,default=A25D)
    ap.add_argument('--A26',type=Path,default=A26D)
    ap.add_argument('--B116',type=Path,default=B116D)
    ap.add_argument('--output',type=Path)
    a=ap.parse_args()
    A25,A26,B116=read(a.A25),read(a.A26),read(a.B116)
    assert (len(A25),len(A26),len(B116))==(6,2,9)
    assert all(len(G)==11 and G.number_of_edges()==25 and tri_free(G) and not indep(G,6) for G in A25)
    assert all(len(G)==11 and G.number_of_edges()==26 and tri_free(G) and not indep(G,6) for G in A26)
    assert all(len(G)==24 and G.number_of_edges()==116 and k4free(G) and indep(G,4) and not indep(G,5) for G in B116)

    # Recursive capacity lemma for degree-5 distinguished vertices in every
    # local A25/A26 type relevant when a degree-11 low has r=2 or 3.
    prof=degree5_profiles([*(('A25',i,G) for i,G in enumerate(A25)),
                           *(('A26',i,G) for i,G in enumerate(A26))])

    # Complete unlabeled census of the degree-11 induced graph when n11=5.
    lows=[]
    for G in nx.graph_atlas_g():
        if len(G)==5 and min(dict(G.degree()).values(),default=0)>=2 and k4free(G):
            lows.append(nx.convert_node_labels_to_integers(G))
    assert len(lows)==8
    low_summary=[{'g6':nx.to_graph6_bytes(G,header=False).decode().strip(),
                  'edges':G.number_of_edges(),'degrees':sorted(dict(G.degree()).values())} for G in lows]

    # Universal r=2 obstruction for a low vertex q lying in the B116 side of
    # another r=2 anchor.  A B-column hits every A-independent 5-set, hence has
    # size at least 2, so d_B(q)<=9. If t(q)=2 then r(q)=2 and N(q)=A26; thus
    # the graph induced by q's B-neighbours must embed in A26. None do.
    b_le9=[]
    for bi,B in enumerate(B116):
        for q in B:
            if B.degree(q)<=9:
                H=B.subgraph(list(B.neighbors(q))).copy()
                ok=any(isomorphic_subgraph(H,T) for T in A26)
                b_le9.append({'B':bi,'q':q,'dB':B.degree(q),'embeds_A26':ok})
    assert len(b_le9)==72 and not any(x['embeds_A26'] for x in b_le9)

    rows=[]
    # Seven of the eight low graph types contain a degree-2 anchor v. Then
    # r(v)=2 and its local pair is A26/B116.
    for G in lows:
        g6=nx.to_graph6_bytes(G,header=False).decode().strip()
        deg2=[v for v in G if G.degree(v)==2]
        if not deg2: continue
        killed=None; details={}
        # Four types already fail on the two low vertices inside A26.
        for v in deg2:
            c=anchor_pair_feasible(G,v,A26)
            if c==0:
                killed='anchor_pair_recursive_degree5'
                details={'anchor':v,'feasible_A26_low_pair_placements':0}
                break
        if killed is None:
            # In each of the remaining three types, at least one of the two
            # low vertices on the B side has t=2, so the universal induced-
            # neighbourhood A26 obstruction applies.
            v=deg2[0]; N=set(G.neighbors(v))
            Bloss=[x for x in G if x!=v and x not in N]
            tB=[G.degree(x) for x in Bloss]
            assert 2 in tB
            killed='B_low_t2_recursive_A26_embedding'
            details={'anchor':v,'B_low_vertices':Bloss,'B_low_degrees':tB,
                     'B_vertices_dB_le9_checked':len(b_le9)}
        rows.append({'g6':g6,'method':killed,**details})
    assert len(rows)==7

    # Last low graph: degree sequence 3,3,3,3,4. Choose a t=3 anchor v and its
    # unique low non-neighbour q. q is adjacent to all three low A vertices, so
    # its A-column has size >=3. Since every B116 has minimum degree 8, d_B(q)=8.
    G=next(G for G in lows if min(dict(G.degree()).values())==3)
    assert sorted(dict(G.degree()).values())==[3,3,3,3,4]
    v=next(x for x in G if G.degree(x)==3)
    N=set(G.neighbors(v)); q=next(x for x in G if x!=v and x not in N)
    assert G.degree(q)==3 and all(G.has_edge(q,x) for x in N)

    d8=[]
    for bi,B in enumerate(B116):
        for z in B:
            if B.degree(z)!=8: continue
            H=B.subgraph(list(B.neighbors(z))).copy()
            a26=any(isomorphic_subgraph(H,T) for T in A26)
            a25=any(isomorphic_subgraph(H,T) for T in A25)
            d8.append((bi,z,H,a25,a26))
    assert len(d8)==9 and not any(x[4] for x in d8)
    # Therefore q cannot have r=2. With t(q)=3 it has r=3 and its local A is
    # A25 or A26; A26 is already excluded, and only one B vertex embeds in A25.
    surv=[x for x in d8 if x[3]]
    assert [(x[0],x[1]) for x in surv]==[(1,0)]
    bi,z,H,_,_=surv[0]
    embeds=[]
    for ti,T in enumerate(A25):
        for S in itertools.combinations(T.nodes(),8):
            HH=T.subgraph(S)
            if not nx.is_isomorphic(H,HH): continue
            C=[x for x in T if x not in S]
            CC=T.subgraph(C)
            if CC.number_of_edges()!=2 or sorted(dict(CC.degree()).values())!=[1,1,2]:
                continue
            center=next(x for x in C if CC.degree(x)==2)
            leaves=[x for x in C if CC.degree(x)==1]
            embeds.append({'A25_type':ti,'subset':list(S),'complement':C,
                           'center_degree_in_A25':T.degree(center),
                           'leaf_degrees_in_A25':[T.degree(x) for x in leaves]})
    assert len(embeds)==45
    # The P3 leaves are t=3 lows. Every embedding makes at least one such leaf
    # degree 5, contradicting the recursive capacity lemma above.
    assert all(any(d==5 for d in e['leaf_degrees_in_A25']) for e in embeds)
    rows.append({'g6':nx.to_graph6_bytes(G,header=False).decode().strip(),
                 'method':'unique_d8_A25_embedding_then_t3_degree5_capacity',
                 'anchor':v,'B_low':q,'degree8_B_candidates':len(d8),
                 'A25_embedding_B_candidates':[[x[0],x[1]] for x in surv],
                 'A25_embeddings_checked':len(embeds),
                 'embeddings_with_t3_leaf_degree5':sum(any(d==5 for d in e['leaf_degrees_in_A25']) for e in embeds)})

    assert len(rows)==8
    out={'campaign':'m220-n11-5-recursive-post-audit','edges':220,'n11':5,
         'catalog_counts':{'A25':6,'A26':2,'B116':9},
         'low_graph_type_count':8,'low_graph_types':low_summary,
         'degree5_recursive_profile_count':len(prof),
         'min_degree5_profile_vertices_needing_capacity_ge5':min(x[4] for x in prof),
         'B116_degree_le9_vertex_count':len(b_le9),
         'B116_degree_le9_A26_embedding_count':sum(x['embeds_A26'] for x in b_le9),
         'coverage':rows,
         'soundness':'Uses only m220 r>=2, complete A25/A26/B116 catalogues, recursive neighbourhood consistency, independent-5 hitting necessity, and induced-subgraph isomorphism; no withdrawn row-domain predicate.',
         'conclusion':'No 220-edge R(4,6,36) graph can have exactly five degree-11 vertices.',
         'all_unsat':True}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(txt,end='')
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt)
if __name__=='__main__':main()
