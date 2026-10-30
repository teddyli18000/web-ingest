#!/usr/bin/env python3
"""Exact structural obstruction for m=219, degree sequence 11^8 12^15 13^12 14.

The degree-class relaxation forces at least six r=3 low vertices. Weak B116
label DP gives their only possible low-graph complement degrees and local
relations. A direct solver-free enumeration of the 8-vertex low complement
with six marked r=3 vertices has zero survivors.
"""
from itertools import combinations,product
from collections import Counter
import argparse,json

A26=("JiQC@{}N`{?","JqPA@{}N`{?")
B116=("W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE","WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?","WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_","WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_","WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT","Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@","Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC")
SEQ={11:8,12:15,13:12,14:1};A_MIN={11:8,12:11,13:15,14:20};A_MAX={11:26,12:29,13:32,14:35};B_MIN={11:116,12:101,13:88,14:77};B_MAX={11:132,12:122,13:114,14:107}
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
 rec(0,[d*SEQ[d] for d in ds]);assert len(vals)==304 and max(vals)==26,(len(vals),max(vals));return vals
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
def residual_counts(t,z):
 y=t-3-2*z
 if y<0:return None
 a12=11-t-y-z
 if a12<0:return None
 a={11:t,12:a12,13:y,14:z};b={d:SEQ[d]-(d==11)-a[d] for d in SEQ}
 if min(b.values())<0:return None
 return tuple(b[11+e] for e in range(4))
def low_complement_enum():
 R=range(6);U=(6,7);RE=list(combinations(R,2));states=0;valid_R=0
 for mask in range(1<<15):
  h=[0]*8;dr=[0]*6;ok=True
  for i,(u,v) in enumerate(RE):
   if mask>>i&1:
    dr[u]+=1;dr[v]+=1
    if dr[u]>2 or dr[v]>2:ok=False;break
    h[u]|=1<<v;h[v]|=1<<u
  if not ok:continue
  if any(all(not(h[u]>>v&1) for u,v in combinations(S,2)) for S in combinations(R,4)):continue
  valid_R+=1;choices=[tuple(b for b in range(4) if b.bit_count()<=2-dr[r]) for r in R]
  for rows in product(*choices):
   g=h.copy()
   for r,b in enumerate(rows):
    for j,u in enumerate(U):
     if b>>j&1:g[r]|=1<<u;g[u]|=1<<r
   for uv in (0,1):
    q=g.copy();states+=1
    if uv:q[6]|=1<<7;q[7]|=1<<6
    if any(x.bit_count()>4 for x in q):continue
    good=True
    for r in R:
     N=[v for v in range(8) if q[r]>>v&1];d=len(N)
     if d>2:good=False;break
     if d==1 and q[N[0]].bit_count()!=4:good=False;break
     if d==2 and q[N[0]]>>N[1]&1:good=False;break
    if not good:continue
    if any(all(not(q[u]>>v&1) for u,v in combinations(S,2)) for S in combinations(range(8),4)):continue
    raise AssertionError(('low complement survivor',q))
 return valid_R,states
def main():
 p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();vals=class_relaxation();A=[g6(x) for x in A26];B=[g6(x) for x in B116]
 assert all(edges(x)==26 for x in A);taus=[transversal_number(x) for x in A];assert taus==[2,2];assert all(edges(x)==116 for x in B)
 minr3=8-(max(vals)-24);assert minr3==6;checks=[]
 for t in range(3,8):
  for z in range(2):
   bc=residual_counts(t,z)
   if bc is None:continue
   row=[]
   for bi,bg in enumerate(B):
    poss=weak_B_feasible(bg,bc)
    if poss:row.append({'b_ordinal':bi,'possible_low_sets':poss})
   checks.append({'t':t,'z14':z,'B_counts':bc,'survivors':row})
 for r in checks:
  if r['t']<5:assert not r['survivors'],r
  if r['t']==5:assert r['survivors']==[{'b_ordinal':1,'possible_low_sets':[(0,3)]}],r
  if r['t']==6:assert r['survivors']==[{'b_ordinal':1,'possible_low_sets':[(0,)]}],r
 assert degs(B[1])[0]==8 and (B[1][0]>>3)&1
 validR,states=low_complement_enum();out={'campaign':'m219-n11-8-r3-lowgraph-obstruction','degree_sequence':{'11':8,'12':15,'13':12,'14':1},'dependencies':{'no_lucky_d12':'certified closure implies S(v)<=146 for degree 12 in class relaxation','A26':'complete authenticated McKay stratum, 2 graphs; both I5 transversal number 2','B116':'complete authenticated McKay stratum, 9 graphs'},'class_relaxation_count':len(vals),'max_sum_r':max(vals),'minimum_forced_r3_vertices':minr3,'A26_transversal_numbers':taus,'r3_local_cases':checks,'low_complement_R_graphs_considered':validR,'low_complement_states_checked':states,'low_complement_survivors':0,'conclusion':'degree sequence 11^8 12^15 13^12 14^1 is impossible for an m=219 (4,6)-Ramsey graph'}
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({k:v for k,v in out.items() if k!='r3_local_cases'},sort_keys=True));
 if a.output:open(a.output,'w').write(text)
if __name__=='__main__':main()
