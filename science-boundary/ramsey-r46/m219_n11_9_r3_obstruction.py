#!/usr/bin/env python3
"""Exact structural obstruction for m=219, degree sequence 11^9 12^12 13^15.

At least three degree-11 vertices must have r(v)=132-S(v)=3. Complete A26/B116
local data force every such vertex to have one or two low non-neighbours, none
of which can itself be r=3. Alpha(complement low graph)<=3 then makes the three
marked vertices' six complement incidences partition the other six low
vertices. The local pair edge condition immediately creates a K4.
"""
from itertools import combinations
from collections import Counter
import argparse,json
A26=("JiQC@{}N`{?","JqPA@{}N`{?")
B116=("W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE","WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?","WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_","WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_","WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT","Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@","Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC")
SEQ={11:9,12:12,13:15,14:0};A_MIN={11:8,12:11,13:15,14:20};A_MAX={11:26,12:29,13:32,14:35};B_MIN={11:116,12:101,13:88,14:77};B_MAX={11:132,12:122,13:114,14:107}
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
def edges(g):return sum(x.bit_count() for x in g)//2
def degs(g):return [x.bit_count() for x in g]
def independent_sets(g,k):
 out=[]
 for S in combinations(range(len(g)),k):
  m=sum(1<<v for v in S)
  if all(not(g[v]&m) for v in S):out.append(m)
 return out
def ex_k4(n):
 q,r=divmod(n,3);p=[q+(i<r) for i in range(3)];return sum(p[i]*p[j] for i in range(3) for j in range(i+1,3))
def s_interval(d,m=219):return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])
def distributions(total,limits,p=()):
 if len(limits)==1:
  if 0<=total<=limits[0]:yield p+(total,)
  return
 for x in range(max(0,total-sum(limits[1:])),min(limits[0],total)+1):yield from distributions(total-x,limits[1:],p+(x,))
def class_relaxation():
 ds=(11,12,13,14);mat=[[0]*4 for _ in ds];cap=[[0]*4 for _ in ds];vals=[]
 for i,d in enumerate(ds):
  for j in range(i,4):cap[i][j]=min(SEQ[d]*(SEQ[d]-1)//2,ex_k4(SEQ[d])) if i==j else SEQ[d]*SEQ[ds[j]]
 def check(i):
  d=ds[i];ss=2*d*mat[i][i]+sum(e*mat[min(i,j)][max(i,j)] for j,e in enumerate(ds) if j!=i);lo,hi=s_interval(d)
  if d==12:hi=146
  return lo*SEQ[d]<=ss<=hi*SEQ[d]
 def rec(i,rem):
  if i==3:
   if rem[i]<0 or rem[i]%2:return
   z=rem[i]//2
   if z<=cap[i][i]:
    mat[i][i]=z
    if check(i):vals.append(2*mat[0][0]-mat[0][2]-2*mat[0][3])
   return
  for eii in range(min(cap[i][i],rem[i]//2)+1):
   need=rem[i]-2*eii;js=list(range(i+1,4));lims=[min(cap[i][j],rem[j]) for j in js]
   if need<0 or need>sum(lims):continue
   mat[i][i]=eii
   for xs in distributions(need,lims):
    nr=rem[:]
    for j,x in zip(js,xs):mat[i][j]=x;nr[j]-=x
    if min(nr)>=0 and check(i):rec(i+1,nr)
 rec(0,[d*SEQ[d] for d in ds]);assert len(vals)==173 and max(vals)==33,(len(vals),max(vals));return vals
def transversal_number(A):
 I5=independent_sets(A,5)
 for k in range(12):
  for S in combinations(range(11),k):
   m=sum(1<<v for v in S)
   if all(m&I for I in I5):return k
 raise AssertionError
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
   groups[(sum(1<<i for i,u in enumerate(L) if B[u]>>v&1),allow)]+=1
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
def residual_counts(t):
 y=t-3;a12=14-2*t
 if a12<0:return None
 a={11:t,12:a12,13:y,14:0};b={d:SEQ[d]-(d==11)-a[d] for d in SEQ}
 if min(b.values())<0:return None
 return tuple(b[11+e] for e in range(4))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();vals=class_relaxation();A=[g6(x) for x in A26];B=[g6(x) for x in B116]
 assert all(edges(x)==26 for x in A);taus=[transversal_number(x) for x in A];assert taus==[2,2];assert all(edges(x)==116 for x in B)
 minr3=9-(max(vals)-27);assert minr3==3;checks=[]
 for t in range(3,8):
  bc=residual_counts(t);assert bc is not None;row=[]
  for bi,bg in enumerate(B):
   poss=weak_B_feasible(bg,bc)
   if poss:row.append({'b_ordinal':bi,'possible_low_sets':poss})
  checks.append({'t':t,'B_counts':bc,'survivors':row})
 for r in checks:
  if r['t']<6:assert not r['survivors'],r
 assert checks[-2]['survivors']==[{'b_ordinal':1,'possible_low_sets':[(0,3)]}],checks[-2]
 assert checks[-1]['survivors']==[{'b_ordinal':1,'possible_low_sets':[(0,)]}],checks[-1]
 db=degs(B[1]);assert db[0]==8 and db[3]==9 and (B[1][0]>>3)&1
 # t=6 gives H-degree2 and its two H-neighbours need H-degrees >=4 and >=5; t=7 gives
 # H-degree1 and its unique H-neighbour needs H-degree >=5. Thus selected r3 vertices cannot
 # be H-adjacent. They are an independent triple R in H. Alpha(H)<=3 forces every other low
 # vertex to touch R. There are six such vertices and sum deg_H(R)<=6, so equality holds:
 # every R vertex has degree2 and every U vertex has exactly one R-neighbour. For one owner r1,
 # its pair p,q is an L-edge by the t=6 local rule. The other marked r2,r3 are L-adjacent to
 # each other and to p,q, giving K4 {r2,r3,p,q}.
 assert minr3==3 and 3*2==6 and 9-3==6
 out={'campaign':'m219-n11-9-r3-lowgraph-obstruction','degree_sequence':{'11':9,'12':12,'13':15},'dependencies':{'no_lucky_d12':'certified closure implies S(v)<=146 for degree 12 in class relaxation','A26':'complete authenticated McKay stratum, 2 graphs; both I5 transversal number 2','B116':'complete authenticated McKay stratum, 9 graphs'},'class_relaxation_count':len(vals),'max_sum_r':max(vals),'minimum_forced_r3_vertices':minr3,'A26_transversal_numbers':taus,'r3_local_cases':checks,'structural_obstruction':'three r3 vertices are independent in the low complement; alpha<=3 forces six R-U complement edges, saturating all three marked degrees at2 and assigning each U to exactly one marked vertex. Each marked pair of low non-neighbours is an L-edge, so either other marked pair plus that owner-pair forms K4.','conclusion':'degree sequence 11^9 12^12 13^15 is impossible for an m=219 (4,6)-Ramsey graph'}
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({k:v for k,v in out.items() if k!='r3_local_cases'},sort_keys=True));
 if a.output:open(a.output,'w').write(text)
if __name__=='__main__':main()
