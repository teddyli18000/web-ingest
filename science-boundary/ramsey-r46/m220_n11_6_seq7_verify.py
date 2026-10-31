#!/usr/bin/env python3
"""Sound post-audit exclusion of m=220 degree sequence 11^6 12^19 13^10 16.

Uses the complete A25/A26 and B116/B117 local catalogues plus exact low-graph
census.  No withdrawn row-domain predicate is used.
"""
from __future__ import annotations
import argparse,collections,itertools,json
from pathlib import Path
import networkx as nx
import m220_structure as base

HERE=Path(__file__).resolve().parent
A25D=HERE/'data/m219-r34-A25.g6'; A26D=HERE/'data/m219-r34-A26.g6'
B116D=HERE/'data/m219-r34-B116.g6'; B117D=HERE/'data/m219-r34-B117.g6'
SEQ={11:6,12:19,13:10,16:1}

def read(p):return [nx.from_graph6_bytes(s.encode()) for s in Path(p).read_text().splitlines() if s]
def k4free(G):return all(G.subgraph(S).number_of_edges()<6 for S in itertools.combinations(G.nodes(),4))
def indep(G,k):return [frozenset(S) for S in itertools.combinations(G.nodes(),k) if G.subgraph(S).number_of_edges()==0]

def make_induced_bank(As):
 bank=collections.defaultdict(list)
 for A in As:
  for k in (8,9):
   for S in itertools.combinations(A.nodes(),k):
    H=A.subgraph(S).copy();key=(k,tuple(sorted(dict(H.degree()).values())),H.number_of_edges())
    bank[key].append(H)
 return bank

def embeds_bank(H,bank):
 key=(len(H),tuple(sorted(dict(H.degree()).values())),H.number_of_edges())
 return any(nx.is_isomorphic(H,T) for T in bank.get(key,()))

def compatibility_certificate(A25,A26,B116,B117):
 hitmins=[]
 for fam,As in [('A25',A25),('A26',A26)]:
  vals=[]
  for A in As:
   I5=indep(A,5);assert I5
   vals.append(next(k for k in range(12) if any(all(set(S)&T for T in I5) for S in itertools.combinations(A.nodes(),k))))
  hitmins.append((fam,vals))
 assert all(set(vals)=={2} for _,vals in hitmins)
 banks={'A25':make_induced_bank(A25),'A26':make_induced_bank(A26)}
 stats={};detailed={}
 for name,Bs in [('B116',B116),('B117',B117)]:
  rows=[]
  for bi,B in enumerate(Bs):
   for q in B:
    if B.degree(q)<=9:
     H=B.subgraph(list(B.neighbors(q))).copy()
     rows.append({'B':bi,'q':q,'dB':B.degree(q),'A25':embeds_bank(H,banks['A25']),'A26':embeds_bank(H,banks['A26'])})
  stats[name]={'positions':len(rows),'A25_embeddings':sum(x['A25'] for x in rows),'A26_embeddings':sum(x['A26'] for x in rows),'max_A25_positions_per_B':max(collections.Counter(x['B'] for x in rows if x['A25']).values(),default=0)}
  detailed[name]=rows
 assert stats['B116']=={'positions':72,'A25_embeddings':1,'A26_embeddings':0,'max_A25_positions_per_B':1}
 assert stats['B117']['positions']==653 and stats['B117']['A25_embeddings']==27 and stats['B117']['A26_embeddings']==0
 exc=[x for x in detailed['B116'] if x['A25']];assert len(exc)==1 and exc[0]['dB']==8
 return {'hitting_minima':dict(hitmins),'embedding_stats':stats,'unique_B116_A25_position':exc[0]}

def low_patterns(R):
 out=[]
 for G in nx.graph_atlas_g():
  if len(G)!=6:continue
  L=nx.convert_node_labels_to_integers(G)
  if min(dict(L.degree()).values(),default=0)<2 or not k4free(L):continue
  ds=[L.degree(i) for i in range(6)]
  for r in itertools.product(*[range(2,d+1) for d in ds]):
   if sum(r)!=R:continue
   if any(((r[i]==2 and r[j]<=3) or (r[j]==2 and r[i]<=3)) and not L.has_edge(i,j) for i,j in itertools.combinations(range(6),2)):continue
   out.append((L,r))
 return out

def local_possible(L,v,cols,As):
 N=list(L.neighbors(v));hs=[m for w,m in cols if (m>>v)&1]
 sigs=[sum(1<<i for i,u in enumerate(N) if (m>>u)&1) for m in hs]
 for A in As:
  for P in itertools.permutations(A.nodes(),len(N)):
   if any(A.has_edge(P[i],P[j])!=L.has_edge(N[i],N[j]) for i,j in itertools.combinations(range(len(N)),2)):continue
   avail=[x for x in A if x not in P];cand=[]
   for sig in sigs:
    C=[x for x in avail if sum(1<<i for i,p in enumerate(P) if A.has_edge(x,p))==sig]
    if not C:break
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

def high_patterns(target):
 avail={1:10,4:1};T=sum(target);types=[]
 for w,n in avail.items():
  for m in range(1,64):
   vec=tuple(w if (m>>i)&1 else 0 for i in range(6))
   if sum(vec)<=T and all(vec[i]<=target[i] for i in range(6)):types.append((w,m,vec))
 out=[]
 def rec(st,rem,cnt,cols):
  if not any(rem):out.append(tuple(cols));return
  i=next(i for i,x in enumerate(rem) if x)
  for z in range(st,len(types)):
   w,m,vec=types[z]
   if not(m>>i&1) or cnt[w]>=avail[w] or any(vec[j]>rem[j] for j in range(6)):continue
   cnt[w]+=1;cols.append((w,m));rec(z,tuple(rem[j]-vec[j] for j in range(6)),cnt,cols);cols.pop();cnt[w]-=1
 rec(0,tuple(target),collections.Counter(),[]);return out

def A_side_survives(L,r,A25,A26):
 target=[L.degree(i)-r[i] for i in range(6)]
 for cols in high_patterns(target):
  ok=True
  for v in range(6):
   if r[v]==2:As=A26
   elif r[v]==3:As=A25+A26
   else:continue
   if not local_possible(L,v,cols,As):ok=False;break
  if ok:return True
 return False

def R_upper_certificate():
 ds=(11,12,13,16); n={11:6,12:19,13:10,16:1}
 def add(A,B,c=1):
  z=A.copy()
  for k,v in B.items():z[k]=z.get(k,0)+c*v
  return {k:v for k,v in z.items() if v}
 def scale(A,c):return {k:c*v for k,v in A.items() if c*v}
 def edge(a,b):return {(min(a,b),max(a,b)):1}
 def degree_form(d):
  z={}
  for e in ds:
   q=(min(d,e),max(d,e));z[q]=z.get(q,0)+(2 if e==d else 1)
  return z,-d*n[d]
 def S_form(d):
  z={}
  for e in ds:
   q=(min(d,e),max(d,e));z[q]=z.get(q,0)+(2*d if e==d else e)
  return z,0
 def plus(F,G,c=1):return add(F[0],G[0],c),F[1]+c*G[1]
 R=(add(scale(edge(11,11),2),add(scale(edge(11,13),-1),scale(edge(11,16),-4))),0)
 lhs=(scale(R[0],-1),19);rhs=({},2793+1640+10)
 rhs=plus(rhs,(S_form(12)[0],0),-1);rhs=plus(rhs,(S_form(13)[0],0),-1)
 rhs=plus(rhs,(edge(11,16),0));rhs=plus(rhs,(edge(13,16),0),-1);rhs=plus(rhs,(edge(16,16),0),-8)
 diff=plus(rhs,lhs,-1);combo=({},0)
 for d,c in ((11,1),(12,-12),(13,-13),(16,-4)):combo=plus(combo,degree_form(d),c)
 assert diff==combo,(diff,combo)
 assert min(base.s_interval(12,220)[1],147)==147 and base.s_interval(13,220)[1]==164
 assert (16-10)==6 and 6%2==0 and 2793%2==1
 return {'identity':'19-R=(2793-S12)+(1640-S13)+e11_16+(10-e13_16)-8e16_16, with e16_16=0','handshake_zero_combination':'D11-12D12-13D13-4D16','R_lp_upper':19,'equality_parity_contradiction':'R=19 forces S12=2793, e11_16=0, e13_16=10, e12_16=6; d12 handshake makes e11_12+e12_13 even but S12 parity makes it odd.','R_integer_upper':18}

def labeled_orbits(L,patterns):
 reps=[]
 for r in patterns:
  G=L.copy();nx.set_node_attributes(G,{i:r[i] for i in G},'r')
  if any(nx.is_isomorphic(G,H,node_match=lambda a,b:a['r']==b['r']) for H,_ in reps):continue
  reps.append((G,r))
 return [r for _,r in reps]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--A25',type=Path,default=A25D);ap.add_argument('--A26',type=Path,default=A26D);ap.add_argument('--B116',type=Path,default=B116D);ap.add_argument('--B117',type=Path,default=B117D);ap.add_argument('--output',type=Path);a=ap.parse_args()
 A25,A26,B116,B117=map(read,(a.A25,a.A26,a.B116,a.B117));assert (len(A25),len(A26),len(B116),len(B117))==(6,2,9,90)
 cert=compatibility_certificate(A25,A26,B116,B117); upper=R_upper_certificate()
 surv=[{int(k):v for k,v in row.items()} for row in base.reduce()['survivors']];assert SEQ in surv
 p17=low_patterns(17);assert len(p17)==4;r17=[]
 for L,r in p17:
  ok=A_side_survives(L,r,A25,A26);r17.append({'g6':nx.to_graph6_bytes(L,header=False).decode().strip(),'r':list(r),'A_side_survives':ok})
 assert not any(x['A_side_survives'] for x in r17)
 p18=low_patterns(18);assert len(p18)==43;p18b=[]
 for L,r in p18:
  if all(sum(1 for q in range(6) if q!=v and r[q]==3 and not L.has_edge(v,q))<=1 for v in range(6) if r[v]==3):p18b.append((L,r))
 assert len(p18b)==27 and {nx.to_graph6_bytes(L,header=False).decode().strip() for L,_ in p18b}=={'EznW'}
 L=p18b[0][0]; reps=labeled_orbits(L,[r for _,r in p18b]);assert len(reps)==4
 orbit_rows=[];last=None
 for r in reps:
  badpairs=[(u,v) for u,v in itertools.combinations(range(6),2) if r[u]==r[v]==3 and not L.has_edge(u,v)]
  if badpairs:
   assert all(len(set(L.neighbors(u))&set(L.neighbors(v)))==4 for u,v in badpairs)
   orbit_rows.append({'r':list(r),'status':'UNSAT','reason':'r3-r3 nonedge has four common low neighbours but unique B116 A25-compatible position has cross degree 3'})
  else:
   assert sorted(r)==[2,2,2,4,4,4];last=r;ok=A_side_survives(L,r,A25,A26)
   orbit_rows.append({'r':list(r),'status':'OPEN' if ok else 'UNSAT','reason':'A26 local high-incidence compatibility' if not ok else 'survives'})
 assert last is not None and not A_side_survives(L,last,A25,A26);assert all(x['status']=='UNSAT' for x in orbit_rows)
 out={'campaign':'m220-n11-6-seq7-post-audit','edges':220,'degree_sequence':{str(k):v for k,v in SEQ.items()},'R_upper_certificate':upper,'R_lower_from_r23_adjacency':17,'catalog_compatibility':cert,'R17':{'pattern_count':len(p17),'rows':r17,'all_unsat':True},'R18':{'raw_pattern_count':len(p18),'after_r3_nonneighbor_capacity':len(p18b),'low_graph':'EznW = K6 minus a perfect matching','orbit_count':len(reps),'orbits':orbit_rows,'all_unsat':True},'soundness':'All catalogue checks are complete for the frozen A25/A26/B116/B117 strata. Local A tests omit high-high constraints and all B-side constraints except the explicitly proved induced-neighbourhood compatibility, so they are relaxations. No withdrawn row-domain predicate is used.','conclusion':'No 220-edge R(4,6,36) graph has degree sequence 11^6 12^19 13^10 16.','all_unsat':True}
 txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({'all_unsat':True,'R17':len(p17),'R18_raw':len(p18),'R18_orbits':len(reps)},sort_keys=True))
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt)
if __name__=='__main__':main()
