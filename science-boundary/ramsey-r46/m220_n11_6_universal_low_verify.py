#!/usr/bin/env python3
"""Universal post-audit low-graph boundary for m=220 with six degree-11 vertices.

For a low vertex v put r(v)=t(v)-w(v)=132-S(v), where t is the number of
other degree-11 neighbours and w is the degree excess above 12 among higher
neighbours. Endpoint extrema give r>=2. Complete A25/A26/B116/B117 local
catalogues give pairwise restrictions on r=2,3 vertices. Exhausting all
unlabelled six-vertex K4-free low graphs then proves sum r >= 22.
"""
from __future__ import annotations
import argparse,collections,itertools,json
from pathlib import Path
import networkx as nx

HERE=Path(__file__).resolve().parent
A25D=HERE/'data/m219-r34-A25.g6'; A26D=HERE/'data/m219-r34-A26.g6'
B116D=HERE/'data/m219-r34-B116.g6'; B117D=HERE/'data/m219-r34-B117.g6'

def read(p):return [nx.from_graph6_bytes(s.encode()) for s in Path(p).read_text().splitlines() if s]
def k4free(G):return all(G.subgraph(S).number_of_edges()<6 for S in itertools.combinations(G.nodes(),4))
def indep(G,k):return [frozenset(S) for S in itertools.combinations(G.nodes(),k) if G.subgraph(S).number_of_edges()==0]

def bank(As):
 out=collections.defaultdict(list)
 for A in As:
  for k in (8,9):
   for S in itertools.combinations(A.nodes(),k):
    H=A.subgraph(S).copy();key=(k,tuple(sorted(dict(H.degree()).values())),H.number_of_edges(),nx.weisfeiler_lehman_graph_hash(H,iterations=3));out[key].append(H)
 return out

def embeds(H,B):
 key=(len(H),tuple(sorted(dict(H.degree()).values())),H.number_of_edges(),nx.weisfeiler_lehman_graph_hash(H,iterations=3))
 return any(nx.is_isomorphic(H,T) for T in B.get(key,()))

def catalogue_certificate(A25,A26,B116,B117):
 hit={}
 for name,As in [('A25',A25),('A26',A26)]:
  vals=[]
  for A in As:
   I5=indep(A,5);assert I5
   vals.append(next(k for k in range(12) if any(all(set(S)&T for T in I5) for S in itertools.combinations(A.nodes(),k))))
  hit[name]=vals
 assert hit['A25']==[2]*6 and hit['A26']==[2]*2
 BA25,BA26=bank(A25),bank(A26);stats={};detail={}
 for name,Bs in [('B116',B116),('B117',B117)]:
  rows=[]
  for bi,B in enumerate(Bs):
   for q in B:
    if B.degree(q)<=9:
     H=B.subgraph(list(B.neighbors(q))).copy();rows.append((bi,q,B.degree(q),embeds(H,BA25),embeds(H,BA26)))
  c=collections.Counter(x[0] for x in rows if x[3])
  stats[name]={'positions':len(rows),'A25_embeddings':sum(x[3] for x in rows),'A26_embeddings':sum(x[4] for x in rows),'max_A25_positions_per_B':max(c.values(),default=0),'min_degree':min(min(dict(B.degree()).values()) for B in Bs)}
  detail[name]=rows
 assert stats['B116']=={'positions':72,'A25_embeddings':1,'A26_embeddings':0,'max_A25_positions_per_B':1,'min_degree':8}
 assert stats['B117']['positions']==653 and stats['B117']['A25_embeddings']==27 and stats['B117']['A26_embeddings']==0 and stats['B117']['min_degree']==8
 only=[x for x in detail['B116'] if x[3]];assert len(only)==1 and only[0][2]==8
 return {'hitting_minima':hit,'stats':stats,'unique_B116_A25_position':{'B':only[0][0],'q':only[0][1],'dB':only[0][2]}}

def allowed(L,r):
 for u,v in itertools.combinations(range(6),2):
  if not L.has_edge(u,v) and ((r[u]==2 and r[v]<=3) or (r[v]==2 and r[u]<=3)):return False
 for v in range(6):
  if r[v]==3 and sum(r[q]==3 and not L.has_edge(v,q) for q in range(6) if q!=v)>1:return False
 for u,v in itertools.combinations(range(6),2):
  if L.has_edge(u,v):continue
  common=len(set(L.neighbors(u))&set(L.neighbors(v)))
  if common>=4 and (r[u]<=3 or r[v]<=3):return False
 return True

def census():
 hist=collections.Counter();rows=[]
 for G in nx.graph_atlas_g():
  if len(G)!=6:continue
  L=nx.convert_node_labels_to_integers(G)
  if min(dict(L.degree()).values(),default=0)<2 or not k4free(L):continue
  ds=[L.degree(i) for i in range(6)]
  for r in itertools.product(*[range(2,d+1) for d in ds]):
   if not allowed(L,r):continue
   R=sum(r);hist[R]+=1;rows.append((L,r))
 return hist,rows

def labeled_orbits(rows):
 reps=[]
 for L,r in rows:
  G=L.copy();nx.set_node_attributes(G,{i:r[i] for i in G},'r')
  if any(nx.is_isomorphic(G,H,node_match=lambda a,b:a['r']==b['r']) for H,_ in reps):continue
  reps.append((G,r))
 return [(nx.to_graph6_bytes(G,header=False).decode().strip(),list(r)) for G,r in reps]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--A25',type=Path,default=A25D);ap.add_argument('--A26',type=Path,default=A26D);ap.add_argument('--B116',type=Path,default=B116D);ap.add_argument('--B117',type=Path,default=B117D);ap.add_argument('--output',type=Path);a=ap.parse_args()
 A25,A26,B116,B117=map(read,(a.A25,a.A26,a.B116,a.B117));assert (len(A25),len(A26),len(B116),len(B117))==(6,2,9,90)
 assert all(len(A)==11 and A.number_of_edges() in (25,26) for A in A25+A26);assert all(len(B)==24 and B.number_of_edges() in (116,117) for B in B116+B117)
 cert=catalogue_certificate(A25,A26,B116,B117);hist,rows=census()
 assert all(hist[R]==0 for R in range(12,22));assert hist[22]==1 and hist[23]==0 and hist[24]==1
 orbits={str(R):labeled_orbits([(L,r) for L,r in rows if sum(r)==R]) for R in sorted(hist)}
 assert orbits['22']==[('Ep~o',[4,3,4,3,4,4])]
 assert orbits['24']==[('EznW',[4,4,4,4,4,4])]
 out={'campaign':'m220-n11-6-universal-low-post-audit','edges':220,'n11':6,'catalogue_certificate':cert,'survivor_histogram':{str(k):v for k,v in sorted(hist.items())},'R_lower':22,'R23_impossible':True,'boundary_orbits':orbits,'lemmas':['r>=2 for every degree-11 vertex','an r2 vertex is adjacent to every r2/r3 vertex','an r3 vertex has at most one r3 non-neighbour','a nonedge incident to an r2/r3 vertex cannot have four common degree-11 neighbours because B116/B117 have minimum degree 8'],'soundness':'Complete frozen A25/A26/B116/B117 catalogues plus a complete graph-atlas census of unlabelled six-vertex graphs. No withdrawn row-domain predicate is used.','conclusion':'At m=220 with exactly six degree-11 vertices, sum r is at least 22; sum r=23 is also impossible. The unique R=22 boundary orbit is Ep~o with labels [4,3,4,3,4,4].'}
 txt=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({'R_lower':22,'R23':hist[23],'R22_orbits':orbits['22'],'R24_orbits':orbits['24']},sort_keys=True))
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(txt)
if __name__=='__main__':main()
