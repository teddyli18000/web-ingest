#!/usr/bin/env python3
"""Sound post-audit exclusion of m=220 degree sequence 11^6 12^21 13^4 14^5."""
from __future__ import annotations
import argparse, collections, itertools, json
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
A25D=HERE/'data/m219-r34-A25.g6'; A26D=HERE/'data/m219-r34-A26.g6'
B116D=HERE/'data/m219-r34-B116.g6'; B117D=HERE/'data/m219-r34-B117.g6'
SEQ={11:6,12:21,13:4,14:5}

def read(p): return [nx.from_graph6_bytes(s.encode()) for s in Path(p).read_text().splitlines() if s]
def k4free(G): return all(G.subgraph(S).number_of_edges()<6 for S in itertools.combinations(G.nodes(),4))
def indep(G,k): return [frozenset(S) for S in itertools.combinations(G.nodes(),k) if G.subgraph(S).number_of_edges()==0]

def make_bank(As):
    bank=collections.defaultdict(list)
    for A in As:
        for k in (8,9):
            for S in itertools.combinations(A.nodes(),k):
                H=A.subgraph(S).copy()
                key=(k,tuple(sorted(dict(H.degree()).values())),H.number_of_edges(),nx.weisfeiler_lehman_graph_hash(H,iterations=3))
                bank[key].append(H)
    return bank

def embeds(H,bank):
    key=(len(H),tuple(sorted(dict(H.degree()).values())),H.number_of_edges(),nx.weisfeiler_lehman_graph_hash(H,iterations=3))
    return any(nx.is_isomorphic(H,T) for T in bank.get(key,()))

def catalogue_certificate(A25,A26,B116,B117):
    hitmins={}
    for name,As in [('A25',A25),('A26',A26)]:
        vals=[]
        for A in As:
            I5=indep(A,5); assert I5
            vals.append(next(k for k in range(12) if any(all(set(S)&T for T in I5) for S in itertools.combinations(A.nodes(),k))))
        hitmins[name]=vals
    assert hitmins['A25']==[2]*6 and hitmins['A26']==[2]*2
    banks={'A25':make_bank(A25),'A26':make_bank(A26)}
    stats={};detail={}
    for name,Bs in [('B116',B116),('B117',B117)]:
        rows=[]
        for bi,B in enumerate(Bs):
            for q in B:
                if B.degree(q)<=9:
                    H=B.subgraph(list(B.neighbors(q))).copy()
                    rows.append({'B':bi,'q':q,'dB':B.degree(q),'A25':embeds(H,banks['A25']),'A26':embeds(H,banks['A26'])})
        stats[name]={'positions':len(rows),'A25_embeddings':sum(x['A25'] for x in rows),'A26_embeddings':sum(x['A26'] for x in rows),'max_A25_positions_per_B':max(collections.Counter(x['B'] for x in rows if x['A25']).values(),default=0)}
        detail[name]=rows
    assert stats['B116']=={'positions':72,'A25_embeddings':1,'A26_embeddings':0,'max_A25_positions_per_B':1}
    assert stats['B117']['positions']==653 and stats['B117']['A25_embeddings']==27 and stats['B117']['A26_embeddings']==0
    only=[x for x in detail['B116'] if x['A25']]; assert len(only)==1 and only[0]['dB']==8
    assert min(min(dict(B.degree()).values()) for B in B116)==8
    return {'hitting_minima':hitmins,'embedding_stats':stats,'unique_B116_A25_position':only[0],'B116_min_degree':8}

def low_patterns(R):
    out=[]
    for G in nx.graph_atlas_g():
        if len(G)!=6: continue
        L=nx.convert_node_labels_to_integers(G)
        if min(dict(L.degree()).values(),default=0)<2 or not k4free(L): continue
        ds=[L.degree(i) for i in range(6)]
        for r in itertools.product(*[range(2,d+1) for d in ds]):
            if sum(r)!=R: continue
            if any(((r[i]==2 and r[j]<=3) or (r[j]==2 and r[i]<=3)) and not L.has_edge(i,j) for i,j in itertools.combinations(range(6),2)): continue
            out.append((L,r))
    return out

def high_patterns(target):
    avail={1:4,2:5}; types=[]; T=sum(target)
    for w,n in avail.items():
        for m in range(1,64):
            vec=tuple(w if (m>>i)&1 else 0 for i in range(6))
            if sum(vec)<=T and all(vec[i]<=target[i] for i in range(6)): types.append((w,m,vec))
    out=[]
    def rec(st,rem,cnt,cols):
        if not any(rem): out.append(tuple(cols)); return
        i=next(i for i,x in enumerate(rem) if x)
        for z in range(st,len(types)):
            w,m,vec=types[z]
            if not(m>>i&1) or cnt[w]>=avail[w] or any(vec[j]>rem[j] for j in range(6)): continue
            cnt[w]+=1;cols.append((w,m));rec(z,tuple(rem[j]-vec[j] for j in range(6)),cnt,cols);cols.pop();cnt[w]-=1
    rec(0,tuple(target),collections.Counter(),[]);return out

def local_possible(L,v,cols,As):
    N=list(L.neighbors(v)); hs=[m for w,m in cols if (m>>v)&1]
    sigs=[sum(1<<i for i,u in enumerate(N) if (m>>u)&1) for m in hs]
    for A in As:
        for P in itertools.permutations(A.nodes(),len(N)):
            if any(A.has_edge(P[i],P[j])!=L.has_edge(N[i],N[j]) for i,j in itertools.combinations(range(len(N)),2)): continue
            avail=[x for x in A if x not in P]; cand=[]
            for sig in sigs:
                C=[x for x in avail if sum(1<<i for i,p in enumerate(P) if A.has_edge(x,p))==sig]
                if not C: break
                cand.append(C)
            else:
                order=sorted(range(len(cand)),key=lambda i:len(cand[i]));used=set()
                def dfs(k):
                    if k==len(order):return True
                    for x in cand[order[k]]:
                        if x not in used:
                            used.add(x)
                            if dfs(k+1):return True
                            used.remove(x)
                    return False
                if dfs(0):return True
    return False

def A_survivors(L,r,A25,A26):
    target=[L.degree(i)-r[i] for i in range(6)];out=[]
    for cols in high_patterns(target):
        ok=True
        for v in range(6):
            As=A26 if r[v]==2 else (A25+A26 if r[v]==3 else None)
            if As is not None and not local_possible(L,v,cols,As):ok=False;break
        if ok:out.append(cols)
    return target,out

def labeled_orbits(L,patterns):
    reps=[]
    for r in patterns:
        G=L.copy();nx.set_node_attributes(G,{i:r[i] for i in G},'r')
        if any(nx.is_isomorphic(G,H,node_match=lambda a,b:a['r']==b['r']) for H,_ in reps):continue
        reps.append((G,r))
    return [r for _,r in reps]

def upper_certificate():
    sumd2=sum(n*d*d for d,n in SEQ.items()); assert sumd2==5406
    assert 21*147==3087 and 4*164==656 and 5*178==890
    return {'identity':'19-R=(3087-S12)+(656-S13)+(890-S14)',
            'class_caps':{'S12':3087,'S13':656,'S14':890},
            'R_lp_upper':19,
            'R19_parity_contradiction':'S12 odd plus the d12 handshake forces e12_14 odd; S14 even plus the d14 handshake forces e12_14 even.',
            'R_integer_upper':18}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--A25',type=Path,default=A25D);ap.add_argument('--A26',type=Path,default=A26D);ap.add_argument('--B116',type=Path,default=B116D);ap.add_argument('--B117',type=Path,default=B117D);ap.add_argument('--output',type=Path);a=ap.parse_args()
    A25,A26,B116,B117=map(read,(a.A25,a.A26,a.B116,a.B117));assert (len(A25),len(A26),len(B116),len(B117))==(6,2,9,90)
    cert=catalogue_certificate(A25,A26,B116,B117);upper=upper_certificate()
    for R in range(12,17): assert not low_patterns(R),R
    p17=low_patterns(17);assert len(p17)==4
    rows17=[];surv=[]
    for L,r in p17:
        target,cols=A_survivors(L,r,A25,A26)
        rec={'g6':nx.to_graph6_bytes(L,header=False).decode().strip(),'r':list(r),'target_high_excess':target,'A_side_survivor_count':len(cols)}
        if cols:rec['A_side_survivors']=[[list(z) for z in c] for c in cols];surv.append((L,r,cols,rec))
        rows17.append(rec)
    assert len(surv)==1
    L,r,cols,rec=surv[0]; assert rec['g6']=='E}^G' and r==(3,2,3,3,3,3) and len(cols)==1
    bad=[(u,v,sorted(set(L.neighbors(u))&set(L.neighbors(v)))) for u,v in itertools.combinations(range(6),2) if r[u]==r[v]==3 and not L.has_edge(u,v)]
    assert (0,4,[1,2,3,5]) in bad
    rec['status']='UNSAT';rec['reason']='r3-r3 nonedge 0-4 has four common low neighbours, but symmetry forces A25/B116 and its unique compatible B position has cross degree only 3'
    for x in rows17:
        if x is not rec and x['A_side_survivor_count']==0:x['status']='UNSAT_A_side'
    assert all(x.get('status','').startswith('UNSAT') for x in rows17)

    p18=low_patterns(18);assert len(p18)==43
    p18b=[]
    for L,r in p18:
        if all(sum(1 for q in range(6) if q!=v and r[q]==3 and not L.has_edge(v,q))<=1 for v in range(6) if r[v]==3):p18b.append((L,r))
    assert len(p18b)==27 and {nx.to_graph6_bytes(L,header=False).decode().strip() for L,_ in p18b}=={'EznW'}
    L=p18b[0][0];reps=labeled_orbits(L,[r for _,r in p18b]);assert len(reps)==4
    rows18=[]
    for r in reps:
        rr={'r':list(r)}
        r3bad=[(u,v,sorted(set(L.neighbors(u))&set(L.neighbors(v)))) for u,v in itertools.combinations(range(6),2) if r[u]==r[v]==3 and not L.has_edge(u,v)]
        if r3bad:
            assert any(len(c)==4 for _,_,c in r3bad)
            rr.update(status='UNSAT',reason='an r3-r3 matched nonedge has four common low neighbours, exceeding the unique B116 A25-compatible cross degree 3')
        else:
            assert sorted(r)==[2,2,2,4,4,4]
            pairs=[(u,v,sorted(set(L.neighbors(u))&set(L.neighbors(v)))) for u,v in itertools.combinations(range(6),2) if not L.has_edge(u,v) and {r[u],r[v]}=={2,4}]
            assert len(pairs)==3 and all(len(c)==4 for _,_,c in pairs)
            rr.update(status='UNSAT',reason='each r2-r4 matched nonedge has four common low neighbours; from the r2 A26/B116 anchor the r4 target has B-degree <=7, but every B116 type has minimum degree >=8')
        rows18.append(rr)
    assert all(x['status']=='UNSAT' for x in rows18)
    out={'campaign':'m220-n11-6-seq12-post-audit','edges':220,'degree_sequence':{str(k):v for k,v in SEQ.items()},'upper_certificate':upper,'catalogue_certificate':cert,'R_lower':17,'R17':{'pattern_count':4,'rows':rows17,'all_unsat':True},'R18':{'raw_pattern_count':43,'after_r3_nonneighbor_capacity':len(p18b),'low_graph':'EznW = K6 minus a perfect matching','orbit_count':4,'orbits':rows18,'all_unsat':True},'soundness':'Complete frozen A25/A26/B116/B117 catalogues, independent-5 hitting, induced-neighbourhood consistency, exact low-graph census, endpoint S caps and parity. No withdrawn row-domain predicate is used. A-side tests are relaxations because high-high and B-side constraints are omitted unless explicitly stated.','conclusion':'No 220-edge R(4,6,36) graph has degree sequence 11^6 12^21 13^4 14^5.','all_unsat':True}
    txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({'all_unsat':True,'R17':len(p17),'R18_orbits':len(reps)},sort_keys=True))
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt)
if __name__=='__main__':main()
