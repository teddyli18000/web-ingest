#!/usr/bin/env python3
"""Exact structural exclusions for t=3,5,6 in the m=219 seq0 r=3 branch.

Hypothesis: a 36-vertex (4,6)-Ramsey graph with 219 edges and degree sequence
11^7 12^16 13^13.  For a degree-11 anchor v define
  t(v) = number of degree-11 neighbours,
  h(v) = number of degree-13 neighbours.
The endpoint identity and the A/B edge extrema imply t(v)-h(v) >= 3.
This verifier handles the branch t(v)-h(v)=3, where necessarily
A=N(v) is an e=26 R(3,6,11) graph and B is an e=116 R(4,5,24) graph.

It proves three subbranches impossible without the withdrawn row-CSP:
* t=3: an exact B-side class-label DP using only the necessary r>=3 inequality.
* t=5: exhaustive raw A-side local contexts + a transversal lemma.
* t=6: exhaustive raw A-side local contexts + the same transversal lemma.

Transversal lemma.  If H is K4-free on h vertices, every set meeting every
independent triple of H has size at least h-8.  Otherwise deleting at most
h-9 vertices leaves at least 9 vertices, still K4-free and with no independent
triple, contradicting R(3,4)=9.
"""
from __future__ import annotations
import argparse, json, math
from collections import Counter, defaultdict
from itertools import combinations, permutations
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
A_DEFAULT=HERE/'data/m219-r34-A26.g6'
B_DEFAULT=HERE/'data/m219-r34-B116.g6'

def read_g6(path:Path):
    return [nx.from_graph6_bytes(s.encode()) for s in path.read_text().splitlines() if s]

def k4_free(G):
    return all(G.subgraph(S).number_of_edges()<6 for S in combinations(G,4))

def no_independent(G,k):
    return all(G.subgraph(S).number_of_edges()>0 for S in combinations(G,k))

def induced_embeddings(A,L,T):
    k=len(T)
    for P in permutations(range(11),k):
        if all(A.has_edge(P[i],P[j])==L.has_edge(T[i],T[j])
               for i in range(k) for j in range(i+1,k)):
            yield P

def i5_sets(A):
    return [set(S) for S in combinations(range(11),5)
            if A.subgraph(S).number_of_edges()==0]

def hits_all(family,S):
    S=set(S)
    return all(S & Z for Z in family)

def t3_b_label_dp(B):
    """Count B-side low/high class assignments surviving a sound relaxation.

    B has 3 degree-11 and 13 degree-13 vertices (8 degree-12 vertices).
    For a B-low vertex q let l_B,h_B be its low/high neighbours inside B and
    x=11-d_B(q) its total A-cross degree.  Since d_B>=8, x<=3, so even in the
    most favourable case all x cross edges go to the three low A vertices.
    Necessarily
        l_B + x - h_B >= 3,
    i.e. h_B <= l_B + 8 - d_B(q).
    We enumerate the low triple and DP over high-label adjacency patterns.
    """
    n=24; total=0; lowsets=0
    for L in combinations(range(n),3):
        LS=set(L); caps=[]; bad=False
        for q in L:
            lB=sum(B.has_edge(q,u) for u in L if u!=q)
            cap=lB+8-B.degree(q)
            if cap<0: bad=True; break
            caps.append(cap)
        if bad: continue
        groups=Counter(tuple(int(B.has_edge(v,q)) for q in L)
                       for v in range(n) if v not in LS)
        states={(0,(0,0,0)):1}
        for pat,num in groups.items():
            nxt=defaultdict(int)
            for (cnt,z),ways in states.items():
                for take in range(num+1):
                    if cnt+take>13: break
                    zz=tuple(z[i]+take*pat[i] for i in range(3))
                    if any(zz[i]>caps[i] for i in range(3)): continue
                    nxt[(cnt+take,zz)] += ways*math.comb(num,take)
            states=nxt
            if not states: break
        ways=sum(w for (cnt,_),w in states.items() if cnt==13)
        if ways:
            lowsets+=1; total+=ways
    return lowsets,total

def min_independent_triple_capacity(A,P,residual):
    vals=[]
    for T in combinations(range(len(P)),3):
        if all(not A.has_edge(P[i],P[j]) for i,j in combinations(T,2)):
            vals.append(sum(residual[i] for i in T))
    return min(vals,default=999)

def enumerate_t(Agraphs,target):
    """Enumerate raw A-side contexts for t=5 or t=6 and test transversal bound."""
    assert target in (5,6)
    threshold=(16-target)-8
    I5=[i5_sets(A) for A in Agraphs]
    root_occ=raw=0; cap_hist=Counter(); violations=[]
    for G in nx.graph_atlas_g():
        if len(G)!=7 or min(dict(G.degree()).values(),default=0)<3 or not k4_free(G):
            continue
        L=nx.convert_node_labels_to_integers(G)
        for v in L:
            if L.degree(v)!=target: continue
            T=list(L.neighbors(v)); U=[u for u in L if u!=v and u not in T]
            fixed_low_B_neighbours=None
            if target==5:
                q=U[0]
                if L.degree(q)!=3: continue
                fixed_low_B_neighbours=[i for i,x in enumerate(T) if L.has_edge(x,q)]
                if len(fixed_low_B_neighbours)!=3: continue
            root_occ+=1
            for ai,A in enumerate(Agraphs):
                for P in induced_embeddings(A,L,T):
                    if target==5:
                        N=[P[i] for i in fixed_low_B_neighbours]
                        if not hits_all(I5[ai],N): continue
                    caps=[L.degree(x)-3 for x in T]
                    remaining=[a for a in range(11) if a not in P]
                    for HA in combinations(remaining,target-3):
                        internal=[sum(A.has_edge(P[i],h) for h in HA)
                                  for i in range(target)]
                        if any(internal[i]>caps[i] for i in range(target)): continue
                        residual=[caps[i]-internal[i] for i in range(target)]
                        m=min_independent_triple_capacity(A,P,residual)
                        raw+=1; cap_hist[m]+=1
                        if m>=threshold:
                            violations.append({
                                'low_graph':nx.to_graph6_bytes(L,header=False).decode().strip(),
                                'root':v,'A_index':ai,'P':list(P),'HA':list(HA),
                                'residual_caps':residual,'min_independent_triple_capacity':m,
                                'required_upper_strictly_below':threshold,
                            })
    return {
        't':target,'root_occurrences':root_occ,'raw_contexts':raw,
        'high_B_count':16-target,'transversal_lower_bound':threshold,
        'min_capacity_histogram':{str(k):v for k,v in sorted(cap_hist.items())},
        'violations':violations,'all_excluded':not violations,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--A26',type=Path,default=A_DEFAULT)
    ap.add_argument('--B116',type=Path,default=B_DEFAULT)
    ap.add_argument('--output',type=Path)
    args=ap.parse_args()
    As=read_g6(args.A26); Bs=read_g6(args.B116)
    assert len(As)==2 and len(Bs)==9
    assert all(len(A)==11 and A.number_of_edges()==26 and all(A.subgraph(S).number_of_edges()<3 for S in combinations(A,3)) and no_independent(A,6) for A in As)
    assert all(len(B)==24 and B.number_of_edges()==116 and k4_free(B) and no_independent(B,5) for B in Bs)
    assert min(min(dict(B.degree()).values()) for B in Bs)>=8

    t3=[]
    for bi,B in enumerate(Bs):
        lowsets,assignments=t3_b_label_dp(B)
        t3.append({'B_index':bi,'surviving_low_triples':lowsets,'surviving_class_assignments':assignments})
    assert all(x['surviving_class_assignments']==0 for x in t3)

    t5=enumerate_t(As,5); t6=enumerate_t(As,6)
    assert t5['all_excluded'] and t5['raw_contexts']==13200
    assert t6['all_excluded'] and t6['raw_contexts']==19584
    out={
        'campaign':'m219-seq0-r3-t356-transversal',
        'degree_sequence':{'11':7,'12':16,'13':13},
        'edges':219,'branch':'degree-11 anchor with r=t-h=3',
        'fixed_local_strata':{'A':'R(3,6,11), e=26, 2 types','B':'R(4,5,24), e=116, 9 types'},
        'lemma':'For K4-free H on h vertices, a transversal of all independent triples has size >= h-8, by R(3,4)=9.',
        't3':{'B_label_relaxations':t3,'all_excluded':True},
        't5':t5,'t6':t6,
        'conclusion':'Within seq0 and r=3, t=3,5,6 are impossible; t=4 remains the only open t-layer.',
    }
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'
    print(text,end='')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
if __name__=='__main__': main()
