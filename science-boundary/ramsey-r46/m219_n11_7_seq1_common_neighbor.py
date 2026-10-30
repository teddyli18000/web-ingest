#!/usr/bin/env python3
"""Exact solver-free exclusion of m=219 degree sequence 11^7 12^17 13^11 14.

The class-edge relaxation forces at least three r=3 degree-11 vertices, where
r(v)=t(v)-w(v)=132-S(v), t is the number of degree-11 neighbours, and w is the
weighted number of degree>=13 neighbours.  Certified B116 weak-label results
then constrain the low non-neighbours of every r=3 anchor.  Their internal B
degrees also bound how many common low neighbours they can have with the
anchor.  This file exhausts all 2^21 labelled graphs on the seven low vertices.
"""
from __future__ import annotations
import argparse, json
from itertools import combinations
from math import comb
from pathlib import Path

HERE=Path(__file__).resolve().parent
SEQ={11:7,12:17,13:11,14:1}
DEGS=(11,12,13,14)
A_MIN={11:8,12:11,13:15,14:20}
A_MAX={11:26,12:29,13:32,14:35}
B_MIN={11:116,12:101,13:88,14:77}
B_MAX={11:132,12:122,13:114,14:107}
B1_G6="WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?"

def g6(s):
 n=ord(s[0])-63; bits=[]
 for c in s[1:]:
  x=ord(c)-63; bits += [(x>>k)&1 for k in range(5,-1,-1)]
 g=[0]*n;q=0
 for j in range(1,n):
  for i in range(j):
   if bits[q]:g[i]|=1<<j;g[j]|=1<<i
   q+=1
 return g

def ex_k4(n):
 q,r=divmod(n,3);p=[q+(i<r) for i in range(3)]
 return sum(p[i]*p[j] for i in range(3) for j in range(i+1,3))

def s_interval(d,m=219):
 return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])

def distributions(total,limits,p=()):
 if len(limits)==1:
  if 0<=total<=limits[0]:yield p+(total,)
  return
 lo=max(0,total-sum(limits[1:]));hi=min(limits[0],total)
 for x in range(lo,hi+1):yield from distributions(total-x,limits[1:],p+(x,))

def class_matrices():
 ds=list(DEGS);k=len(ds);M=[[0]*k for _ in range(k)];cap=[[0]*k for _ in range(k)];out=[]
 for i,d in enumerate(ds):
  for j in range(i,k):
   cap[i][j]=min(comb(SEQ[d],2),ex_k4(SEQ[d])) if i==j else SEQ[d]*SEQ[ds[j]]
 def check(i):
  d=ds[i];ss=2*d*M[i][i]+sum(e*M[min(i,j)][max(i,j)] for j,e in enumerate(ds) if j!=i)
  lo,hi=s_interval(d)
  if d==12:hi=min(hi,146)
  return lo*SEQ[d]<=ss<=hi*SEQ[d]
 def rec(i,rem):
  if i==k-1:
   if rem[i]<0 or rem[i]%2:return
   z=rem[i]//2
   if z>cap[i][i]:return
   M[i][i]=z
   if check(i):out.append([row[:] for row in M])
   return
  for eii in range(min(cap[i][i],rem[i]//2)+1):
   need=rem[i]-2*eii;js=list(range(i+1,k));lims=[min(cap[i][j],rem[j]) for j in js]
   if need<0 or need>sum(lims):continue
   M[i][i]=eii
   for xs in distributions(need,lims):
    nr=rem[:]
    for j,x in zip(js,xs):M[i][j]=x;nr[j]-=x
    if min(nr)>=0 and check(i):rec(i+1,nr)
 rec(0,[d*SEQ[d] for d in ds])
 return out

def certified_local_rules():
 # Reuse independently certified complete B116 weak-label scans from n11=8.
 d=json.loads((HERE/'results/m219-n11-8-r3-lowgraph-obstruction.json').read_text())
 rows={(tuple(r['B_counts']),r['t'],r['z14']):r for r in d['r3_local_cases']}
 assert rows[((2,11,10,1),5,0)]['survivors']==[{'b_ordinal':1,'possible_low_sets':[[0,3]]}]
 assert rows[((1,13,9,1),6,0)]['survivors']==[{'b_ordinal':1,'possible_low_sets':[[0]]}]
 assert rows[((1,12,11,0),6,1)]['survivors']==[{'b_ordinal':1,'possible_low_sets':[[0]]}]
 # The same B-count vectors arise here one unit lower in t because n11=7 rather than 8.
 B=g6(B1_G6);deg=[x.bit_count() for x in B]
 assert deg[0]==8 and deg[3]==9 and ((B[0]>>3)&1)
 return {'pair_positions':[0,3],'pair_internal_degrees':[8,9],'singleton_position':0,'singleton_internal_degree':8}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);a=ap.parse_args()
 mats=class_matrices();assert len(mats)==446,len(mats)
 allowed={}
 for M in mats:
  eLL,e13,e14=M[0][0],M[0][2],M[0][3];R=2*eLL-e13-2*e14
  allowed.setdefault(eLL,set()).add((e13,e14,R))
 assert max(R for vals in allowed.values() for _,_,R in vals)==25
 # If fewer than three vertices had r=3, sum r >= 2*3+5*4 = 26.
 rules=certified_local_rules()
 E=list(combinations(range(7),2));ei={e:i for i,e in enumerate(E)}
 inc=[0]*7
 for i,(u,v) in enumerate(E):inc[u]|=1<<i;inc[v]|=1<<i
 k4=[]
 for S in combinations(range(7),4):
  q=0
  for u,v in combinations(S,2):q|=1<<ei[(min(u,v),max(u,v))]
  k4.append(q)
 baseline=0;survivors=0;by_edges={}
 for mask in range(1<<21):
  eLL=mask.bit_count()
  if eLL not in allowed:continue
  dl=[(mask&inc[v]).bit_count() for v in range(7)]
  if min(dl)<3:continue
  if any(mask&q==q for q in k4):continue
  baseline+=1;by_edges[eLL]=by_edges.get(eLL,0)+1
  adj=[0]*7
  for i,(u,v) in enumerate(E):
   if mask>>i&1:adj[u]|=1<<v;adj[v]|=1<<u
  graph_ok=False
  for e13,e14,R in allowed[eLL]:
   states={(0,0,0)}
   for v,t in enumerate(dl):
    opts=[]
    for z in (0,1):
     for y in range(0,12-t-z):
      r=t-y-2*z
      if r<3:continue
      if r==3:
       U=[u for u in range(7) if u!=v and not ((adj[v]>>u)&1)]
       T=adj[v]
       if t==3:continue
       if t==4:
        # r=3 forces z=0 and B-low set {0,3}; their A-cross degrees are 3 and 2.
        if z or len(U)!=2 or not ((adj[U[0]]>>U[1])&1):continue
        c=[(adj[u]&T).bit_count() for u in U]
        if not ((c[0]<=3 and c[1]<=2) or (c[1]<=3 and c[0]<=2)):continue
       elif t==5:
        # The unique B-low vertex is B1 position 0, internal degree 8, so A-cross degree 3.
        if len(U)!=1 or (adj[U[0]]&T).bit_count()>3:continue
       elif t==6:
        if U:continue
       else:continue
      opts.append((y,z,r))
    nxt=set()
    for sy,sz,sr in states:
     for y,z,r in opts:
      if sy+y<=e13 and sz+z<=e14 and sr+r<=R:nxt.add((sy+y,sz+z,sr+r))
    states=nxt
    if not states:break
   if (e13,e14,R) in states:
    graph_ok=True;break
  if graph_ok:survivors+=1
 assert baseline==91647,baseline
 assert survivors==0,survivors
 out={
  'campaign':'m219-n11-7-seq1-common-neighbor-obstruction',
  'degree_sequence':{'11':7,'12':17,'13':11,'14':1},
  'class_edge_matrix_count':len(mats),
  'max_sum_r':25,
  'minimum_forced_r3_vertices':3,
  'labelled_low_graph_universe':1<<21,
  'labelled_low_graphs_after_delta3_K4free_and_edge_stratum':baseline,
  'baseline_by_low_edge_count':{str(k):v for k,v in sorted(by_edges.items())},
  'certified_B116_rule':rules,
  'survivors_after_exact_low_incidence_DP_and_common_neighbor_capacity':survivors,
  'conclusion':'degree sequence 11^7 12^17 13^11 14 is impossible for an m=219 (4,6)-Ramsey graph'}
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({k:v for k,v in out.items() if k!='baseline_by_low_edge_count'},sort_keys=True))
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text)
if __name__=='__main__':main()
