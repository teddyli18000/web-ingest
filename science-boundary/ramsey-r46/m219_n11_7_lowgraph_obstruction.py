#!/usr/bin/env python3
"""Exact structural obstruction for m=219, degree sequence 11^7 12^18 13^9 14^2.

Solver-free verifier.  Dependencies: the already-certified no-lucky-d12 closure
(S(v)<=146 for d(v)=12), and the complete authenticated A26/B116 strata.
"""
from itertools import combinations
from collections import Counter
import argparse,json

A26=("JiQC@{}N`{?","JqPA@{}N`{?")
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
SEQ={11:7,12:18,13:9,14:2}
A_MIN={11:8,12:11,13:15,14:20}; A_MAX={11:26,12:29,13:32,14:35}
B_MIN={11:116,12:101,13:88,14:77}; B_MAX={11:132,12:122,13:114,14:107}

def g6(s):
 n=ord(s[0])-63;bits=[]
 for ch in s[1:]:
  x=ord(ch)-63;bits += [(x>>k)&1 for k in range(5,-1,-1)]
 adj=[0]*n;q=0
 for j in range(1,n):
  for i in range(j):
   if bits[q]:adj[i]|=1<<j;adj[j]|=1<<i
   q+=1
 return adj

def edges(g):return sum(x.bit_count() for x in g)//2
def degs(g):return [x.bit_count() for x in g]
def independent_sets(g,k):
 out=[]
 for S in combinations(range(len(g)),k):
  m=sum(1<<v for v in S)
  if all((g[v]&m)==0 for v in S):out.append(m)
 return out

def ex_k4(n):
 q,r=divmod(n,3);p=[q+(i<r) for i in range(3)]
 return sum(p[i]*p[j] for i in range(3) for j in range(i+1,3))
def s_interval(d,m=219):return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])
def distributions(total,limits,prefix=()):
 if len(limits)==1:
  if 0<=total<=limits[0]:yield prefix+(total,)
  return
 lo=max(0,total-sum(limits[1:]));hi=min(limits[0],total)
 for x in range(lo,hi+1):yield from distributions(total-x,limits[1:],prefix+(x,))

def class_relaxation():
 ds=(11,12,13,14);k=4;mat=[[0]*k for _ in range(k)];cap=[[0]*k for _ in range(k)]
 for i,d in enumerate(ds):
  for j in range(i,k):
   e=ds[j];cap[i][j]=min(SEQ[d]*(SEQ[d]-1)//2,ex_k4(SEQ[d])) if i==j else SEQ[d]*SEQ[e]
 rem0=[d*SEQ[d] for d in ds];vals=[]
 def check(i):
  d=ds[i];ss=2*d*mat[i][i]+sum(e*mat[min(i,j)][max(i,j)] for j,e in enumerate(ds) if j!=i)
  lo,hi=s_interval(d)
  if d==12:hi=146
  return lo*SEQ[d]<=ss<=hi*SEQ[d]
 def rec(i,rem):
  if i==k-1:
   if rem[i]<0 or rem[i]%2:return
   z=rem[i]//2
   if z>cap[i][i]:return
   mat[i][i]=z
   if not check(i):return
   vals.append(2*mat[0][0]-mat[0][2]-2*mat[0][3]);return
  for eii in range(min(cap[i][i],rem[i]//2)+1):
   need=rem[i]-2*eii;future=range(i+1,k);limits=[min(cap[i][j],rem[j]) for j in future]
   if need<0 or need>sum(limits):continue
   mat[i][i]=eii
   for xs in distributions(need,limits):
    nr=rem[:]
    for j,x in zip(future,xs):mat[i][j]=x;nr[j]-=x
    if min(nr)>=0 and check(i):rec(i+1,nr)
 rec(0,rem0)
 assert len(vals)==26 and set(vals)=={21},(len(vals),set(vals))
 return vals

def transversal_number(A):
 I5=independent_sets(A,5)
 for k in range(12):
  for S in combinations(range(11),k):
   m=sum(1<<v for v in S)
   if all(m&I for I in I5):return k
 raise AssertionError

def residual_B_counts(t,z):
 # r=3 => w=t-3=y+2z, z=#degree14 neighbours, y=#degree13 neighbours.
 y=t-3-2*z
 if y<0:return None
 a12=11-t-y-z
 if a12<0:return None
 a={11:t,12:a12,13:y,14:z}
 b={d:SEQ[d]-(1 if d==11 else 0)-a[d] for d in SEQ}
 if min(b.values())<0 or sum(b.values())!=24:return None
 return tuple(b[11+e] for e in range(4))

def compositions(n,allowed):
 for n1 in range(n+1):
  if n1 and 1 not in allowed:continue
  for n2 in range(n-n1+1):
   if n2 and 2 not in allowed:continue
   n3=n-n1-n2
   if n3 and 3 not in allowed:continue
   yield n1,n2,n3

def weak_B_feasible(B,bc):
 db=degs(B);n=24;nlow=bc[0]
 cand=[v for v,d in enumerate(db) if 11-d>=2]
 possible=[];states_seen=0
 for Lt in combinations(cand,nlow):
  L=list(Lt);LS=set(L);groups=Counter();bad=False
  for v in range(n):
   if v in LS:continue
   allow=tuple(e for e in (1,2,3) if bc[e]>0 and 11+e-db[v]>=2)
   if not allow:bad=True;break
   mask=sum(1<<i for i,u in enumerate(L) if (B[u]>>v)&1)
   groups[(mask,allow)]+=1
  if bad:continue
  states={(0,0,0,tuple(0 for _ in L))}
  for (mask,allow),num in groups.items():
   nxt=set()
   for c1,c2,c3,sums in states:
    for n1,n2,n3 in compositions(num,allow):
     nc=(c1+n1,c2+n2,c3+n3)
     if any(nc[i]>bc[i+1] for i in range(3)):continue
     add=n1+2*n2+3*n3;ns=tuple(sums[i]+(add if (mask>>i)&1 else 0) for i in range(len(L)))
     if any(x>8 for x in ns):continue
     nxt.add((nc[0],nc[1],nc[2],ns))
   states=nxt;states_seen+=len(states)
   if not states:break
  if any((c1,c2,c3)==tuple(bc[1:]) for c1,c2,c3,s in states):possible.append(tuple(Lt))
 return possible,states_seen

def maxdeg2_component_types(n=7):
 comps=[('P',k) for k in range(1,n+1)]+[('C',k) for k in range(4,n+1)]
 def alpha(c):
  typ,k=c;return (k+1)//2 if typ=='P' else k//2
 out=set()
 def rec(rem,start,chosen):
  if rem==0:
   if sum(alpha(c) for c in chosen)<=3:out.add(tuple(chosen))
   return
  for i in range(start,len(comps)):
   c=comps[i]
   if c[1]<=rem:rec(rem-c[1],i,chosen+[c])
 rec(n,0,[])
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output');a=ap.parse_args()
 vals=class_relaxation();A=[g6(s) for s in A26];B=[g6(s) for s in B116]
 assert all(len(x)==11 and edges(x)==26 for x in A)
 taus=[transversal_number(x) for x in A];assert taus==[2,2]
 assert all(len(x)==24 and edges(x)==116 for x in B)
 checks=[]
 for t in range(3,7):
  for z in range(3):
   bc=residual_B_counts(t,z)
   if bc is None:continue
   for bi,bg in enumerate(B):
    poss,n=weak_B_feasible(bg,bc)
    checks.append({'t':t,'z14':z,'B_counts':bc,'b_ordinal':bi,'possible_low_sets':poss,'dp_states':n})
 # t=3 impossible -> min degree of low graph >=4.
 t3=[r for r in checks if r['t']==3];assert t3 and all(not r['possible_low_sets'] for r in t3)
 # For t=4, every possible pair of low B vertices is an edge in B (= edge in low graph).
 t4=[r for r in checks if r['t']==4];assert any(r['possible_low_sets'] for r in t4)
 for r in t4:
  bg=B[r['b_ordinal']]
  for u,v in r['possible_low_sets']:assert (bg[u]>>v)&1,(r,u,v)
 # Complement H of low graph: Delta(H)<=2; preceding rule makes H triangle-free;
 # K4-free low graph means alpha(H)<=3.  Enumerate component types.
 types=maxdeg2_component_types(7)
 expected={(('C',7),),(('P',2),('C',5))}
 # canonical component list uses P entries before C due comps order, so normalize by sorted tuple.
 norm={tuple(sorted(x)) for x in types};exp={tuple(sorted(x)) for x in expected}
 assert norm==exp,(norm,exp)
 # t=5: both residual cases force B1 and the sole low B vertex 0, which has degree 8.
 t5=[r for r in checks if r['t']==5];sur5=[r for r in t5 if r['possible_low_sets']]
 assert len(sur5)==2,sur5
 assert all(r['b_ordinal']==1 and r['possible_low_sets']==[(0,)] for r in sur5),sur5
 assert degs(B[1])[0]==8
 # If H=C5+K2, K2 endpoints are nonadjacent lows with five common low neighbours.
 # Anchoring one endpoint, the other is B1 vertex0, so its cross degree (=mu) is 11-8=3 <5.
 assert 11-degs(B[1])[0]==3
 # If H=C7, each low nonedge has at least three common low neighbours, so each of the two
 # low B vertices must have B-internal degree <=8.  No t=4 surviving pair has both <=8.
 for r in t4:
  db=degs(B[r['b_ordinal']])
  for u,v in r['possible_low_sets']:assert not (db[u]<=8 and db[v]<=8),(r,u,v,db[u],db[v])
 out={
  'campaign':'m219-n11-7-lowgraph-obstruction','degree_sequence':{'11':7,'12':18,'13':9,'14':2},
  'dependencies':{'no_lucky_d12':'certified closure implies S(v)<=146 for degree 12 in class relaxation','A26':'complete authenticated McKay stratum, 2 graphs; both I5 transversal number 2','B116':'complete authenticated McKay stratum, 9 graphs'},
  'class_relaxation_count':len(vals),'sum_r_values':sorted(set(vals)),'all_degree11_r3':True,'A26_transversal_numbers':taus,
  'weak_B_checks':checks,
  'derived_complement_types':[list(map(list,x)) for x in sorted(norm)],
  'C5_plus_K2_obstruction':'K2 endpoints have 5 common low neighbours, but t=5 forces B1 vertex0 with cross/common degree 3',
  'C7_obstruction':'each low nonedge has >=3 common low neighbours, requiring both low B vertices to have internal degree <=8; every t=4 weak survivor pair has at least one endpoint of internal degree >=9',
  'conclusion':'degree sequence 11^7 12^18 13^9 14^2 is impossible for an m=219 (4,6)-Ramsey graph'
 }
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({k:v for k,v in out.items() if k!='weak_B_checks'},sort_keys=True))
 if a.output:open(a.output,'w').write(text)
if __name__=='__main__':main()
