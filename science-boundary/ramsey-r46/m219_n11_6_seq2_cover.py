#!/usr/bin/env python3
from itertools import combinations
from collections import Counter
from math import comb
import json,argparse
B116=(
"W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE",
"WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?",
"WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_",
"WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_",
"WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@",
"Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC")
SEQ={11:6,12:20,13:8,14:2};A_MIN={11:8,12:11,13:15,14:20};A_MAX={11:26,12:29,13:32,14:35};B_MIN={11:116,12:101,13:88,14:77};B_MAX={11:132,12:122,13:114,14:107}
def g6(s):
 n=ord(s[0])-63;bits=[]
 for c in s[1:]:
  x=ord(c)-63;bits += [(x>>k)&1 for k in range(5,-1,-1)]
 g=[0]*n;q=0
 for j in range(1,n):
  for i in range(j):
   if bits[q]:g[i]|=1<<j;g[j]|=1<<i
   q+=1
 return g
def degs(g):return [x.bit_count() for x in g]
def edge(g,u,v):return (g[u]>>v)&1
def s_interval(d,m=219):return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])
def exk4(n):
 q,r=divmod(n,3);p=[q+(i<r) for i in range(3)];return sum(p[i]*p[j] for i in range(3) for j in range(i+1,3))
def distr(total,lims,p=()):
 if len(lims)==1:
  if 0<=total<=lims[0]:yield p+(total,)
  return
 for x in range(max(0,total-sum(lims[1:])),min(lims[0],total)+1):yield from distr(total-x,lims[1:],p+(x,))
def class_relaxation():
 ds=sorted(SEQ);k=len(ds);M=[[0]*k for _ in range(k)];cap=[[0]*k for _ in range(k)];vals=[]
 for i,d in enumerate(ds):
  for j in range(i,k):cap[i][j]=min(comb(SEQ[d],2),exk4(SEQ[d])) if i==j else SEQ[d]*SEQ[ds[j]]
 def check(i):
  d=ds[i];ss=2*d*M[i][i]+sum(e*M[min(i,j)][max(i,j)] for j,e in enumerate(ds) if j!=i);lo,hi=s_interval(d);hi=min(hi,146) if d==12 else hi
  return lo*SEQ[d]<=ss<=hi*SEQ[d]
 def rec(i,rem):
  if i==k-1:
   if rem[i]<0 or rem[i]%2:return
   z=rem[i]//2
   if z<=cap[i][i]:
    M[i][i]=z
    if check(i):vals.append(2*M[0][0]-M[0][2]-2*M[0][3])
   return
  for eii in range(min(cap[i][i],rem[i]//2)+1):
   need=rem[i]-2*eii;js=list(range(i+1,k));lims=[min(cap[i][j],rem[j]) for j in js]
   if need<0 or need>sum(lims):continue
   M[i][i]=eii
   for xs in distr(need,lims):
    nr=rem[:]
    for j,x in zip(js,xs):M[i][j]=x;nr[j]-=x
    if min(nr)>=0 and check(i):rec(i+1,nr)
 rec(0,[d*SEQ[d] for d in ds]);return vals
def compositions(n,allow):
 for a in range(n+1):
  if a and 1 not in allow:continue
  for b in range(n-a+1):
   if b and 2 not in allow:continue
   c=n-a-b
   if not c or 3 in allow:yield a,b,c
def weak_B_feasible(B,bc):
 db=degs(B);nl=bc[0];cand=[v for v,d in enumerate(db) if 11-d>=2];poss=[]
 for Lt in combinations(cand,nl):
  L=list(Lt);LS=set(L);groups=Counter();bad=False
  for v in range(24):
   if v in LS:continue
   allow=tuple(e for e in (1,2,3) if bc[e] and 11+e-db[v]>=2)
   if not allow:bad=True;break
   groups[(sum(1<<i for i,u in enumerate(L) if edge(B,u,v)),allow)]+=1
  if bad:continue
  st={(0,0,0,tuple(0 for _ in L))}
  for (mask,allow),num in groups.items():
   nx=set()
   for c1,c2,c3,sums in st:
    for n1,n2,n3 in compositions(num,allow):
     nc=(c1+n1,c2+n2,c3+n3)
     if any(nc[i]>bc[i+1] for i in range(3)):continue
     add=n1+2*n2+3*n3;ns=tuple(sums[i]+(add if mask>>i&1 else 0) for i in range(len(L)))
     if any(x>8 for x in ns):continue
     nx.add((nc[0],nc[1],nc[2],ns))
   st=nx
   if not st:break
  if any((a,b,c)==tuple(bc[1:]) for a,b,c,s in st):poss.append(tuple(Lt))
 return poss
def main():
 p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();vals=class_relaxation();assert len(vals)==54 and max(vals)==20 and min(vals)==18,(len(vals),min(vals),max(vals));min_r3=24-max(vals);assert min_r3==4
 expected={0:[(0,5),(1,6),(2,4),(3,7)],1:[(0,3),(4,5)],5:[(0,2),(0,3),(1,5),(1,6),(2,7),(3,7),(4,5),(4,6)],6:[(0,2),(0,3),(1,5),(1,6),(2,7),(3,7),(4,5),(4,6)],7:[(0,2),(0,3),(1,5),(1,6),(2,7),(3,7),(4,5),(4,6)],8:[(0,1),(0,2),(1,3),(2,3),(4,6),(4,7),(5,6),(5,7)]};rows=[];total=0
 for bi,B in enumerate(map(g6,B116)):
  ps=weak_B_feasible(B,(2,12,8,2))
  if ps:
   assert ps==expected[bi],(bi,ps,expected.get(bi));assert all(edge(B,*uv) for uv in ps);rows.append({'b_ordinal':bi,'pairs':[list(x) for x in ps]});total+=len(ps)
 assert set(expected)=={r['b_ordinal'] for r in rows} and total==38
 out={'campaign':'m219-n11-6-seq2-cover','degree_sequence':{'11':6,'12':20,'13':8,'14':2},'class_relaxation_count':len(vals),'sum_r_values':sorted(set(vals)),'max_sum_r':max(vals),'minimum_forced_r3_vertices':min_r3,'weak_B_counts':[2,12,8,2],'weak_B_survivors':rows,'unordered_low_pairs':38,'ordered_low_pairs':76,'all_surviving_low_pairs_are_B_edges':True,'low_graph_dependency':'results/m219-n11-6-lowgraph-cover.json: adjacent low-B pair condition leaves exactly five non-K222 low types / six degree-3 anchor orbits','conclusion':'The third n11=6 sequence needs at least four r=3 low vertices. Any degree-3 low anchor has A26/B116 local strata and one of exactly 38 unordered (76 ordered) B-low pairs, all adjacent; these are the complete pair cases consumed by m219_n11_6_seq2_fixedlow_csp.cpp.'}
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({k:v for k,v in out.items() if k!='weak_B_survivors'},sort_keys=True));
 if a.output:open(a.output,'w').write(text)
if __name__=='__main__':main()
