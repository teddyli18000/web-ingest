#!/usr/bin/env python3
"""Sound post-audit exclusion for a low-edge part of m=220,n11=6.

Scope: degree sequence 11^6 12^22 13^2 14^6, and the induced graph L on the
six degree-11 vertices has 8, 9, or 10 edges.

The proof uses only exact finite catalogues A26=R(3,6,11) with 26 edges and
B116=R(4,5,24) with 116 edges, integer degree-class identities, induced
subgraph consistency, and independent-5 hitting necessities.  It does NOT use
the withdrawn row-domain triangle-free predicate.
"""
from __future__ import annotations
import argparse, collections, functools, itertools, json
from math import comb
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
A26D=HERE/'data/m219-r34-A26.g6'
B116D=HERE/'data/m219-r34-B116.g6'

SEQ={11:6,12:22,13:2,14:6}
DS=tuple(sorted(SEQ))
A_MIN={11:8,12:11,13:15,14:20}
A_MAX={11:26,12:29,13:32,14:35}
B_MIN={11:116,12:101,13:88,14:77}
B_MAX={11:132,12:122,13:114,14:107}
HIGH_WEIGHTS=(1,1,2,2,2,2,2,2) # two d13 and six d14 vertices

def read_g6(path):
    return [nx.from_graph6_bytes(s.encode()) for s in Path(path).read_text().splitlines() if s]

def k4free(G):
    return all(G.subgraph(S).number_of_edges()<6 for S in itertools.combinations(G.nodes(),4))

def indep_sets(G,k):
    return [frozenset(S) for S in itertools.combinations(G.nodes(),k)
            if G.subgraph(S).number_of_edges()==0]

def ex_k4(n):
    q,r=divmod(n,3); parts=[q+(i<r) for i in range(3)]
    return sum(parts[i]*parts[j] for i in range(3) for j in range(i+1,3))

def s_interval(d,m=220):
    return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])

def distributions(total,limits,prefix=()):
    if len(limits)==1:
        if 0<=total<=limits[0]: yield prefix+(total,)
        return
    lo=max(0,total-sum(limits[1:])); hi=min(limits[0],total)
    for x in range(lo,hi+1): yield from distributions(total-x,limits[1:],prefix+(x,))

def class_matrices():
    """Enumerate all necessary degree-class edge matrices for SEQ."""
    ds=list(DS); k=len(ds); M=[[0]*k for _ in ds]; cap=[[0]*k for _ in ds]; out=[]
    for i,d in enumerate(ds):
        for j in range(i,k):
            cap[i][j]=min(comb(SEQ[d],2),ex_k4(SEQ[d])) if i==j else SEQ[d]*SEQ[ds[j]]
    def check(i):
        d=ds[i]
        ss=2*d*M[i][i]+sum(e*M[min(i,j)][max(i,j)] for j,e in enumerate(ds) if j!=i)
        lo,hi=s_interval(d)
        if d==12: hi=min(hi,147) # no-lucky-d12 closure at m=220
        return lo*SEQ[d] <= ss <= hi*SEQ[d]
    def rec(i,rem):
        if i==k-1:
            if rem[i]<0 or rem[i]%2:return
            z=rem[i]//2
            if z>cap[i][i]:return
            M[i][i]=z
            if check(i): out.append(tuple(tuple(M[a][b] for b in range(k)) for a in range(k)))
            return
        for eii in range(min(cap[i][i],rem[i]//2)+1):
            M[i][i]=eii; need=rem[i]-2*eii; js=list(range(i+1,k))
            lims=[min(cap[i][j],rem[j]) for j in js]
            if need<0 or need>sum(lims):continue
            for xs in distributions(need,lims):
                nr=rem[:]
                for j,x in zip(js,xs): M[i][j]=x; nr[j]-=x
                if min(nr)>=0 and check(i): rec(i+1,nr)
    rec(0,[d*SEQ[d] for d in ds])
    return out

def low_graphs():
    out=[]
    for G in nx.graph_atlas_g():
        if len(G)!=6:continue
        G=nx.convert_node_labels_to_integers(G)
        if min(dict(G.degree()).values(),default=0)<2 or not k4free(G):continue
        if G.number_of_edges() in (8,9,10):out.append(G)
    return out

def isomorphic_induced(H,T):
    return any(nx.is_isomorphic(H,T.subgraph(S)) for S in itertools.combinations(T.nodes(),len(H)))

def universal_degree2_B_obstruction(A26,B116):
    rows=[]
    for bi,B in enumerate(B116):
        for q in B:
            if B.degree(q)<=9:
                H=B.subgraph(list(B.neighbors(q))).copy()
                rows.append((bi,q,B.degree(q),any(isomorphic_induced(H,A) for A in A26)))
    assert len(rows)==72 and not any(x[3] for x in rows)
    return rows

def allowed_local_signatures(L,v,A26):
    N=list(L.neighbors(v)); allowed=collections.defaultdict(set)
    for A in A26:
        for P in itertools.permutations(A.nodes(),len(N)):
            if any(A.has_edge(P[i],P[j]) != L.has_edge(N[i],N[j])
                   for i,j in itertools.combinations(range(len(N)),2)):continue
            rem=[q for q in A if q not in P]
            for hcount in range(4):
                for Q in itertools.combinations(rem,hcount):
                    masks=tuple(sorted(sum(1<<i for i,p in enumerate(P) if A.has_edge(q,p)) for q in Q))
                    allowed[hcount].add(masks)
    return N,allowed

def row_options(target):
    return [frozenset(S) for r in range(len(HIGH_WEIGHTS)+1)
            for S in itertools.combinations(range(len(HIGH_WEIGHTS)),r)
            if sum(HIGH_WEIGHTS[h] for h in S)==target]

def canon_rows(rows):
    return tuple(sorted((HIGH_WEIGHTS[h],sum(1<<v for v,S in enumerate(rows) if h in S))
                        for h in range(len(HIGH_WEIGHTS))))

def enumerate_A_incidence(L,A26):
    sig=[allowed_local_signatures(L,v,A26) for v in range(6)]
    opts=[row_options(L.degree(v)-2) for v in range(6)]
    order=sorted(range(6),key=lambda v:len(opts[v])); rows=[None]*6; sols=set()
    def check(v):
        if rows[v] is None or any(rows[u] is None for u in L.neighbors(v)):return True
        N,allow=sig[v]
        masks=tuple(sorted(sum(1<<i for i,u in enumerate(N) if h in rows[u]) for h in rows[v]))
        return masks in allow[len(rows[v])]
    def dfs(pos):
        if pos==6:sols.add(canon_rows(rows));return
        v=order[pos]
        for S in opts[v]:
            rows[v]=S
            if check(v) and all(check(u) for u in L.neighbors(v)):dfs(pos+1)
            rows[v]=None
    dfs(0); return sols

def B_capacity_anchor(L,canon,v,B116):
    """Relaxed B116 class/signature feasibility for one r=2 anchor."""
    Q=[q for q in range(6) if q!=v and not L.has_edge(v,q)]
    Alow=list(L.neighbors(v))
    HA=[h for h,(_,m) in enumerate(canon) if (m>>v)&1]
    HB=[h for h in range(len(canon)) if h not in HA]
    req=collections.Counter()
    for h in HB:
        m=canon[h][1]
        req[sum(1<<i for i,q in enumerate(Q) if (m>>q)&1)]+=1
    for B in B116:
        for P in itertools.permutations(B.nodes(),len(Q)):
            if any(B.has_edge(P[i],P[j]) != L.has_edge(Q[i],Q[j])
                   for i,j in itertools.combinations(range(len(Q)),2)):continue
            ok=True
            for i,q in enumerate(Q):
                p=P[i]
                if B.degree(p)>9:ok=False;break # every A26-column hits I5, so size>=2
                known=sum(L.has_edge(q,u) for u in Alow)+sum((canon[h][1]>>q)&1 for h in HA)
                if known>11-B.degree(p):ok=False;break
            if not ok:continue
            used=set(P);cap=collections.Counter();must=collections.Counter()
            for z in B:
                if z in used:continue
                s=sum(1<<i for i,p in enumerate(P) if B.has_edge(z,p)); cap[s]+=1
                if B.degree(z)==11:must[s]+=1 # d12 mid would have only one A-neighbour
            if all(must[s]<=req[s]<=cap[s] for s in set(cap)|set(req)|set(must)):return True
    return False

def B_capacity_pattern(L,canon,B116):
    return all(B_capacity_anchor(L,canon,v,B116) for v in range(6))

def A_contexts(L,canon,v,A26):
    N=list(L.neighbors(v)); HA=[h for h,(_,m) in enumerate(canon) if (m>>v)&1]; out=[]
    for ai,A in enumerate(A26):
        for P in itertools.permutations(A.nodes(),len(N)):
            if any(A.has_edge(P[i],P[j]) != L.has_edge(N[i],N[j])
                   for i,j in itertools.combinations(range(len(N)),2)):continue
            rem=[x for x in A if x not in P]
            for Hnodes in itertools.permutations(rem,len(HA)):
                ok=True
                for h,node in zip(HA,Hnodes):
                    m=canon[h][1]
                    for i,u in enumerate(N):
                        if A.has_edge(node,P[i]) != bool((m>>u)&1):ok=False;break
                    if not ok:break
                if ok:out.append((ai,tuple(P),tuple(HA),tuple(Hnodes)))
    return out

def matching_covers(cand,forced):
    G=nx.Graph()
    for h,vs in cand.items():
        G.add_node(('h',h),bipartite=0)
        for z in vs:G.add_edge(('h',h),('b',z),weight=1000+(z in forced))
    M=nx.max_weight_matching(G,maxcardinality=True,weight='weight')
    if len(M)!=len(cand):return False
    matched=set()
    for x,y in M:
        if x[0]=='b':x,y=y,x
        if x[0]=='h':matched.add(y[1])
    return forced<=matched

def exact_unary_anchor(L,canon,v,A26,B116,I5):
    """Necessary exact one-column completion, still relaxing pairwise columns."""
    N=list(L.neighbors(v)); Q=[q for q in range(6) if q!=v and q not in N]
    HA=[h for h,(_,m) in enumerate(canon) if (m>>v)&1]; HB=[h for h in range(len(canon)) if h not in HA]
    @functools.lru_cache(None)
    def hit(ai,k,incmask,excmask):
        if incmask&excmask:return False
        inc=[x for x in range(11) if incmask>>x&1]
        if len(inc)>k or k>11:return False
        avail=[x for x in range(11) if not(incmask>>x&1) and not(excmask>>x&1)]
        for E in itertools.combinations(avail,k-len(inc)):
            S=frozenset(inc+list(E))
            if all(S&T for T in I5[ai]):return True
        return False
    def unary(ai,P,HAids,Hnodes,kind,item,dglob,bdeg):
        k=dglob-bdeg
        if not 0<=k<=11:return False
        inc=exc=0
        if kind=='low':
            q=item
            for i,u in enumerate(N):
                if L.has_edge(q,u):inc|=1<<P[i]
                else:exc|=1<<P[i]
            for h,node in zip(HAids,Hnodes):
                if (canon[h][1]>>q)&1:inc|=1<<node
                else:exc|=1<<node
        elif kind=='high':
            m=canon[item][1]
            for i,u in enumerate(N):
                if (m>>u)&1:inc|=1<<P[i]
                else:exc|=1<<P[i]
        return hit(ai,k,inc,exc)
    for ai,P,HAids,Hnodes in A_contexts(L,canon,v,A26):
        for B in B116:
            for BP in itertools.permutations(B.nodes(),len(Q)):
                if any(B.has_edge(BP[i],BP[j]) != L.has_edge(Q[i],Q[j])
                       for i,j in itertools.combinations(range(len(Q)),2)):continue
                if any(not unary(ai,P,HAids,Hnodes,'low',q,11,B.degree(BP[i])) for i,q in enumerate(Q)):continue
                used=set(BP);cand={};ok=True
                for h in HB:
                    sig=tuple(bool((canon[h][1]>>q)&1) for q in Q); dglob=12+canon[h][0]
                    V=[z for z in B if z not in used
                       and tuple(B.has_edge(z,BP[i]) for i in range(len(Q)))==sig
                       and unary(ai,P,HAids,Hnodes,'high',h,dglob,B.degree(z))]
                    if not V:ok=False;break
                    cand[h]=V
                if not ok:continue
                forced={z for z in B if z not in used and not unary(ai,P,HAids,Hnodes,'mid',None,12,B.degree(z))}
                if len(forced)<=len(HB) and matching_covers(cand,forced):return True
    return False

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--A26',type=Path,default=A26D);ap.add_argument('--B116',type=Path,default=B116D);ap.add_argument('--output',type=Path);a=ap.parse_args()
    A26=read_g6(a.A26);B116=read_g6(a.B116)
    assert len(A26)==2 and len(B116)==9
    assert all(len(A)==11 and A.number_of_edges()==26
               and all(A.subgraph(S).number_of_edges()<3 for S in itertools.combinations(A.nodes(),3))
               and not indep_sets(A,6) for A in A26)
    assert all(len(B)==24 and B.number_of_edges()==116 and k4free(B) and not indep_sets(B,5) for B in B116)
    I5=[indep_sets(A,5) for A in A26]
    assert all(I5) and all(not any(all(v in S for S in fam) for v in A26[i]) for i,fam in enumerate(I5))

    mats=class_matrices(); assert len(mats)==17
    class_rows=[]
    for M in mats:
        ell=M[0][0]; R=2*ell-M[0][2]-2*M[0][3]
        class_rows.append({'eLL':ell,'sum_r':R})
    hist=collections.Counter((x['eLL'],x['sum_r']) for x in class_rows)
    assert all(R==12 for (ell,R),cnt in hist.items() if ell in (8,9,10))

    degree2_certificate=universal_degree2_B_obstruction(A26,B116)
    lows=low_graphs();assert len(lows)==31
    stage=[]; survivors=[]
    for L in lows:
        g6=nx.to_graph6_bytes(L,header=False).decode().strip(); rec={'g6':g6,'edges':L.number_of_edges(),'degrees':sorted(dict(L.degree()).values())}
        if min(dict(L.degree()).values())==2:
            rec['status']='UNSAT';rec['reason']='all vertices r=2; choose an r=2 anchor nonadjacent to a degree-2 low q, then the universal B116->A26 recursive obstruction applies';stage.append(rec);continue
        sols=enumerate_A_incidence(L,A26);rec['A_incidence_orbits']=len(sols)
        if not sols:
            rec['status']='UNSAT';rec['reason']='no globally consistent low-high incidence survives all six A26 local signatures';stage.append(rec);continue
        bs=[c for c in sols if B_capacity_pattern(L,c,B116)];rec['B_capacity_survivors']=len(bs)
        if not bs:
            rec['status']='UNSAT';rec['reason']='no incidence pattern survives B116 low/high signature capacities and column-size>=2 necessity';stage.append(rec);continue
        rec['status']='OPEN_AFTER_CAPACITY';rec['capacity_patterns']=[[[w,m] for w,m in c] for c in sorted(bs)];stage.append(rec);survivors.append((L,bs,rec))
    assert [(r['g6'],r['B_capacity_survivors']) for r in stage if r['status']=='OPEN_AFTER_CAPACITY']==[('EzNG',1)]
    L,bs,rec=survivors[0];canon=bs[0]
    unary=[exact_unary_anchor(L,canon,v,A26,B116,I5) for v in range(6)]
    rec['exact_unary_anchor_feasible']=unary
    assert unary==[True,True,True,True,False,False]
    rec['status']='UNSAT';rec['reason']='the unique remaining incidence pattern has no exact independent-5-hitting column completion for anchors 4 and 5'

    assert all(r['status']=='UNSAT' for r in stage)
    out={'campaign':'m220-n11-6-seq14-lowedge-post-audit','edges':220,'degree_sequence':{str(k):v for k,v in SEQ.items()},
         'scope':'induced degree-11 graph has 8, 9, or 10 edges','class_matrix_count':len(mats),
         'class_matrix_eLL_sumr_histogram':{f'{e},{r}':c for (e,r),c in sorted(hist.items())},
         'forced_fact':'for e(L)=8,9,10 every feasible class matrix has sum r=12, so all six degree-11 vertices have r=2 and local pair A26/B116',
         'low_graph_type_count':len(lows),'degree2_recursive_check_count':len(degree2_certificate),
         'coverage':stage,
         'soundness':'No withdrawn row-domain tf() predicate is used. Every filter is necessary: exact degree-class identities; complete A26/B116 catalogues; recursive induced-neighbourhood consistency; exact low/high incidence forced by r=2; and independent-5 hitting for individual A-B columns. Pairwise and higher column constraints are omitted, so the final searches are relaxations.',
         'conclusion':'This degree sequence has no 220-edge R(4,6,36) realization whose six degree-11 vertices induce 8, 9, or 10 edges.',
         'all_unsat':True}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({'all_unsat':True,'low_types':len(lows),'stage_open':sum(r['status']!='UNSAT' for r in stage),'hist':out['class_matrix_eLL_sumr_histogram']},sort_keys=True))
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt)
if __name__=='__main__':main()
