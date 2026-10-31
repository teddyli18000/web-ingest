#!/usr/bin/env python3
"""Post-audit structural exclusion of four m=220,n11=6 degree sequences.

Let r(v)=t(v)-w(v)=132-S(v) for a degree-11 vertex, where t is its number
of degree-11 neighbours and w is the total degree excess above 12 among its
higher-degree neighbours.  At m=220 every degree-11 vertex has r>=2.

Key recursive lemma: two r=2 degree-11 vertices must be adjacent.  For an r=2
anchor v the local pair is one of the complete A26/B116 extrema.  If another
r=2 low q were a non-neighbour of v, then q lies in B.  Its A-column must hit
every independent 5-set of A26, so it has size at least 2 and d_B(q)<=9.
But q itself has A26 as its full neighbourhood, forcing B[N_B(q)] to embed
induced in A26.  Exhausting the complete two A26 and nine B116 types shows
this never occurs.  Thus the r=2 lows form a clique, hence at most three in a
K4-free graph.  With six lows, sum r>=3*2+3*3=15.

We then prove sum r<=14 for four structural degree sequences.  Three follow
from the global identity sum_v S(v)=sum_v d(v)^2 and endpoint upper bounds.
The fourth uses an explicit nonnegative-slack identity recorded below.
No withdrawn row-domain predicate is used.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
import networkx as nx
import m220_structure as base

HERE=Path(__file__).resolve().parent
A26D=HERE/'data/m219-r34-A26.g6'
B116D=HERE/'data/m219-r34-B116.g6'

def read_g6(p):
    return [nx.from_graph6_bytes(s.encode()) for s in Path(p).read_text().splitlines() if s]
def independent_sets(G,k):
    return [frozenset(S) for S in itertools.combinations(G.nodes(),k)
            if G.subgraph(S).number_of_edges()==0]
def induced_embeds(H,T):
    return any(nx.is_isomorphic(H,T.subgraph(S)) for S in itertools.combinations(T.nodes(),len(H)))

def recursive_r2_certificate(A26,B116):
    # Any B column in an A26/B116 gluing hits every A-independent 5-set.
    mins=[]
    for A in A26:
        I5=independent_sets(A,5); assert I5
        kmin=next(k for k in range(12)
                  if any(all(set(S)&T for T in I5) for S in itertools.combinations(A.nodes(),k)))
        mins.append(kmin)
    assert mins==[2,2]
    rows=[]
    for bi,B in enumerate(B116):
        for q in B:
            if B.degree(q)<=9:
                H=B.subgraph(list(B.neighbors(q))).copy()
                rows.append({'B':bi,'q':q,'dB':B.degree(q),
                             'embeds_A26':any(induced_embeds(H,A) for A in A26)})
    assert len(rows)==72 and not any(x['embeds_A26'] for x in rows)
    return {'A26_min_independent5_hitting_size':mins,
            'B116_vertices_degree_le9_checked':len(rows),
            'induced_A26_embedding_count':sum(x['embeds_A26'] for x in rows)}

def s_upper(d):
    hi=base.s_interval(d,220)[1]
    if d==12: hi=min(hi,147) # exact no-lucky-d12 closure at m=220
    return hi

def simple_R_upper(seq):
    total_s2=sum(n*d*d for d,n in seq.items())
    other_max=sum(n*s_upper(d) for d,n in seq.items() if d!=11)
    low_min=total_s2-other_max
    return 132*seq[11]-low_min, {'sum_d2':total_s2,'other_S_upper_sum':other_max,'low_S_lower':low_min}

def special_identity_certificate():
    # Degree sequence 11^6 12^20 13^8 14^1 16^1.
    # Edge-class variables e_ij.  On the degree-class handshake equations,
    #
    # 14-R = (2940-S12)+(1312-S13)+(178-S14)
    #        + e_11,16 + (8-e_13,16) + 2(1-e_14,16) - 8e_16,16,
    # and e_16,16=0 because the degree-16 class is a singleton.
    #
    # Verify the identity coefficient-by-coefficient after adding the zero
    # combination D11-12 D12-13 D13-14 D14-4 D16 of handshake equations.
    ds=(11,12,13,14,16); n={11:6,12:20,13:8,14:1,16:1}
    def add(A,B,c=1):
        z=A.copy()
        for k,v in B.items():z[k]=z.get(k,0)+c*v
        return {k:v for k,v in z.items() if v}
    def scale(A,c):return {k:c*v for k,v in A.items() if c*v}
    def edge(a,b):return {(min(a,b),max(a,b)):1}
    def degree_form(d):
        z={}
        for e in ds:
            p=(min(d,e),max(d,e)); z[p]=z.get(p,0)+(2 if e==d else 1)
        return z,-d*n[d]
    def S_form(d):
        z={}
        for e in ds:
            p=(min(d,e),max(d,e)); z[p]=z.get(p,0)+(2*d if e==d else e)
        return z,0
    def plus(F,G,c=1):return add(F[0],G[0],c),F[1]+c*G[1]
    R=(add(scale(edge(11,11),2),add(scale(edge(11,13),-1),add(scale(edge(11,14),-2),scale(edge(11,16),-4)))),0)
    lhs=scale(R[0],-1),14
    rhs=({},2940+1312+178+8+2)
    for d in (12,13,14):rhs=plus(rhs,(S_form(d)[0],0),-1)
    rhs=plus(rhs,(edge(11,16),0),1)
    rhs=plus(rhs,(edge(13,16),0),-1)
    rhs=plus(rhs,(edge(14,16),0),-2)
    rhs=plus(rhs,(edge(16,16),0),-8)
    diff=plus(rhs,lhs,-1)
    combo=({},0)
    for d,c in ((11,1),(12,-12),(13,-13),(14,-14),(16,-4)):
        combo=plus(combo,degree_form(d),c)
    assert diff==combo,(diff,combo)
    assert s_upper(12)==147 and s_upper(13)==164 and s_upper(14)==178
    return {'identity':'14-R=(2940-S12)+(1312-S13)+(178-S14)+e11_16+(8-e13_16)+2*(1-e14_16)-8e16_16, with e16_16=0',
            'handshake_zero_combination':'D11-12D12-13D13-14D14-4D16',
            'nonnegative_slacks':['2940-S12','1312-S13','178-S14','e11_16','8-e13_16','1-e14_16'],
            'R_upper':14}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--A26',type=Path,default=A26D);ap.add_argument('--B116',type=Path,default=B116D);ap.add_argument('--output',type=Path);a=ap.parse_args()
    A26=read_g6(a.A26); B116=read_g6(a.B116)
    assert len(A26)==2 and len(B116)==9
    assert all(len(A)==11 and A.number_of_edges()==26
               and all(A.subgraph(T).number_of_edges()<3 for T in itertools.combinations(A.nodes(),3))
               and not independent_sets(A,6) for A in A26)
    assert all(len(B)==24 and B.number_of_edges()==116
               and all(B.subgraph(T).number_of_edges()<6 for T in itertools.combinations(B.nodes(),4))
               and not independent_sets(B,5) for B in B116)
    cert=recursive_r2_certificate(A26,B116)
    data=base.reduce(); seqs=[]
    for row in data['survivors']:
        seq={int(k):v for k,v in row.items()}
        if seq.get(11)==6:seqs.append(seq)
    assert len(seqs)==14
    simple=[]
    for seq in seqs:
        ub,detail=simple_R_upper(seq)
        if ub<=14:simple.append((seq,ub,detail))
    assert len(simple)==3,[(s,u) for s,u,_ in simple]
    special={11:6,12:20,13:8,14:1,16:1}
    assert special in seqs and all(s!=special for s,_,_ in simple)
    sid=special_identity_certificate()
    rows=[]
    for seq,ub,detail in simple:
        rows.append({'degree_sequence':{str(k):v for k,v in sorted(seq.items())},'R_upper':ub,'upper_method':'global S-sum bound',**detail,'status':'UNSAT_by_R_bounds'})
    rows.append({'degree_sequence':{str(k):v for k,v in sorted(special.items())},'R_upper':14,'upper_method':'explicit nonnegative-slack identity','identity_certificate':sid,'status':'UNSAT_by_R_bounds'})
    R_lower=3*2+3*3; assert R_lower==15
    assert all(r['R_upper']<R_lower for r in rows)
    out={'campaign':'m220-n11-6-r2-clique-post-audit','edges':220,'n11':6,
         'r2_recursive_certificate':cert,
         'lemma':'Any two r=2 degree-11 vertices are adjacent; hence the r=2 set is a clique and has size at most 3 in a K4-free graph.',
         'R_lower':R_lower,'excluded_degree_sequence_count':len(rows),'excluded':rows,
         'soundness':'Uses only the complete A26/B116 catalogues, independent-5 column hitting, induced-neighbourhood consistency, endpoint S bounds, the already-certified d12 cap S<=147, degree-class handshake identities, and K4-freeness. It does not use the withdrawn row-domain predicate.',
         'conclusion':'Four of the fourteen m=220,n11=6 structural degree sequences are impossible.','all_unsat_for_listed_sequences':True}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({'excluded':len(rows),'R_lower':R_lower,'rows':[(r['degree_sequence'],r['R_upper']) for r in rows]},sort_keys=True))
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt)
if __name__=='__main__':main()
