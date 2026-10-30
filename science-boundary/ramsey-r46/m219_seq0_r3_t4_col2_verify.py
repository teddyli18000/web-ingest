#!/usr/bin/env python3
"""Sound solver-free/CSP exclusion of the t=4 subbranch of m=219 seq0, r=3.

Hypothesis: a 36-vertex (4,6)-Ramsey graph with 219 edges and degree
sequence 11^7 12^16 13^13.  Choose a degree-11 anchor v with
r(v)=t(v)-h(v)=3 and t(v)=4.  Then h(v)=1, A=N(v) is one of the two
R(3,6,11) graphs with 26 edges, and B is one of the nine R(4,5,24)
graphs with 116 edges.  B contains exactly 2 global-degree-11 vertices,
10 degree-12 vertices and 12 degree-13 vertices.

The verifier uses only necessary conditions, never the withdrawn row-domain
tf() predicate.

1. For each possible pair Q of low B vertices and each high set H of size 12,
   r(q)>=3 implies
       h_B(q) <= l_B(q) + (11-d_B(q)) - 3 = l_B(q)+8-d_B(q).
   We exhaust every Q,H satisfying this relaxed inequality.
2. In either A26 type, the independent 5-sets have empty total intersection.
   Therefore every B vertex must have at least two A-neighbours: a size-1
   column cannot hit every independent 5-set of A.  This eliminates every
   relaxed B-label context except three contexts on one B116 graph.
3. In each remaining context, restrict attention to B vertices whose exact
   A-cross degree is 2.  Their column is therefore one of the size-2 hitting
   sets of all independent 5-sets of A.  We solve the following relaxation:
     * if bb' is a B-edge, C_b intersect C_b' is independent in A (no K4);
     * if bb' is a B-nonedge, C_b union C_b' hits every independent 4-set of A;
     * for an independent B-triple, the three-column union hits every
       independent 3-set of A.
   All other columns, row-degree equations, and higher mixed constraints are
   omitted.  Hence UNSAT of this relaxation rigorously excludes a real gluing.
"""
from __future__ import annotations
import argparse, json
from collections import Counter
from itertools import combinations
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
A_DEFAULT=HERE/'data/m219-r34-A26.g6'
B_DEFAULT=HERE/'data/m219-r34-B116.g6'

def read_g6(path:Path):
    return [nx.from_graph6_bytes(s.encode()) for s in path.read_text().splitlines() if s]

def independent_sets(G,k):
    return [frozenset(S) for S in combinations(G.nodes(),k)
            if G.subgraph(S).number_of_edges()==0]

def hitting_sets(G,k,target_family):
    return [frozenset(S) for S in combinations(G.nodes(),k)
            if all(set(S)&T for T in target_family)]

def high_sets_for_pair(B,Q):
    """Enumerate every 12-high labeling surviving the sound low-q relaxation."""
    Q=tuple(Q); rem=[v for v in B if v not in Q]
    caps=[]
    for q in Q:
        lB=sum(B.has_edge(q,u) for u in Q if u!=q)
        caps.append(lB+8-B.degree(q))
    if min(caps)<0:
        return []
    pats=[tuple(int(B.has_edge(v,q)) for q in Q) for v in rem]
    out=[]
    def rec(i,need,c0,c1,sel):
        if need==0:
            out.append(tuple(sel)); return
        if len(rem)-i<need:
            return
        p0,p1=pats[i]
        if c0+p0<=caps[0] and c1+p1<=caps[1]:
            sel.append(rem[i]); rec(i+1,need-1,c0+p0,c1+p1,sel); sel.pop()
        rec(i+1,need,c0,c1,sel)
    rec(0,12,0,0,[])
    return out

def relaxed_label_contexts(Bs):
    rows=[]
    for bi,B in enumerate(Bs):
        for Q in combinations(range(24),2):
            for H in high_sets_for_pair(B,Q):
                rows.append((bi,tuple(Q),tuple(H)))
    return rows

def cross_degrees(B,Q,H):
    Q=set(Q); H=set(H); out=[]
    for b in range(24):
        gd=11 if b in Q else (13 if b in H else 12)
        out.append(gd-B.degree(b))
    return out

def col2_unsat(A,B,cd):
    I5=independent_sets(A,5)
    I4=independent_sets(A,4)
    I3=independent_sets(A,3)
    domain=hitting_sets(A,2,I5)
    V=[b for b in range(24) if cd[b]==2]
    D={b:list(domain) for b in V}

    def indep_A(S):
        return A.subgraph(S).number_of_edges()==0
    def pair_ok(b,X,c,Y):
        if B.has_edge(b,c):
            return indep_A(set(X)&set(Y))
        U=set(X)|set(Y)
        return all(U&T for T in I4)

    comp={}
    for b,c in combinations(V,2):
        comp[(b,c)]={X:frozenset(Y for Y in D[c] if pair_ok(b,X,c,Y))
                     for X in D[b]}

    assigned={}; nodes=0; max_depth=0
    def candidates(b):
        out=[]
        for X in D[b]:
            ok=True
            for c,Y in assigned.items():
                if b<c:
                    if Y not in comp[(b,c)][X]: ok=False; break
                else:
                    if X not in comp[(c,b)][Y]: ok=False; break
            if ok: out.append(X)
        return out

    def dfs():
        nonlocal nodes,max_depth
        nodes+=1; max_depth=max(max_depth,len(assigned))
        if len(assigned)==len(V):
            return True
        best=None; C=None
        for b in V:
            if b in assigned: continue
            cc=candidates(b)
            if not cc: return False
            if C is None or len(cc)<len(C):
                best,C=b,cc
        for X in C:
            assigned[best]=X
            ok=True
            others=[v for v in assigned if v!=best]
            for b,c in combinations(others,2):
                if (not B.has_edge(best,b) and not B.has_edge(best,c)
                        and not B.has_edge(b,c)):
                    U=set(X)|set(assigned[b])|set(assigned[c])
                    if any(not (U&T) for T in I3):
                        ok=False; break
            if ok and dfs():
                return True
            del assigned[best]
        return False

    sat=dfs()
    return {'status':'SAT' if sat else 'UNSAT','nodes':nodes,'max_depth':max_depth,
            'column_count':len(V),'domain_size':len(domain)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--A26',type=Path,default=A_DEFAULT); ap.add_argument('--B116',type=Path,default=B_DEFAULT); ap.add_argument('--output',type=Path); args=ap.parse_args()
    As=read_g6(args.A26); Bs=read_g6(args.B116)
    assert len(As)==2 and len(Bs)==9
    for A in As:
        assert len(A)==11 and A.number_of_edges()==26
        assert all(A.subgraph(S).number_of_edges()<3 for S in combinations(A,3))
        I5=independent_sets(A,5)
        assert I5 and not set.intersection(*(set(S) for S in I5))
        assert not hitting_sets(A,1,I5)

    contexts=relaxed_label_contexts(Bs)
    assert len(contexts)==1499, len(contexts)
    by_B=Counter(bi for bi,_,_ in contexts)
    assert by_B==Counter({4:1496,1:3}),by_B

    min2=[]; killed=Counter()
    for bi,Q,H in contexts:
        cd=cross_degrees(Bs[bi],Q,H)
        if min(cd)>=2:
            min2.append((bi,Q,H,cd))
        else:
            killed[bi]+=1
    assert len(min2)==3 and all(x[0]==1 for x in min2)
    assert killed==Counter({4:1496})

    runs=[]
    for ai,A in enumerate(As):
        for ci,(bi,Q,H,cd) in enumerate(min2):
            r=col2_unsat(A,Bs[bi],cd)
            r.update({'A_index':ai,'B_index':bi,'context_index':ci,
                      'low_B':list(Q),'high_B':list(H),
                      'cross_degree_histogram':dict(sorted(Counter(cd).items()))})
            runs.append(r)
    assert all(r['status']=='UNSAT' for r in runs),runs
    assert [r['column_count'] for r in runs]==[12,11,11,12,11,11]

    out={'campaign':'m219-seq0-r3-t4-col2','edges':219,
         'degree_sequence':{'11':7,'12':16,'13':13},
         'branch':'degree-11 anchor with r=t-h=3 and t=4',
         'catalog_counts':{'A26':len(As),'B116':len(Bs)},
         'relaxed_B_label_context_count':len(contexts),
         'relaxed_B_label_contexts_by_B_index':dict(sorted(by_B.items())),
         'killed_by_column_min2':dict(sorted(killed.items())),
         'remaining_B_label_context_count':len(min2),
         'col2_runs':runs,
         'soundness':'The B-label enumeration is a relaxation of r(q)>=3. Every real column must hit all A-independent 5-sets. The final CSP keeps only constraints necessary for K4/I6 avoidance on exact size-2 columns; omitted constraints only enlarge the search space.',
         'conclusion':'The t=4 subbranch is impossible for both A26 types and every B116 type/degree labeling allowed by the sound relaxation.'}
    text=json.dumps(out,indent=2,sort_keys=True)+'\n'; print(text,end='')
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
if __name__=='__main__':main()
