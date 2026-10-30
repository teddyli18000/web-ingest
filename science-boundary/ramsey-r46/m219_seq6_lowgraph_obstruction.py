#!/usr/bin/env python3
"""Exact structural obstruction for m=219, degree sequence 11^9 12^13 13^13 14.

This is a solver-free finite verifier.  It depends on the already-certified
no-lucky-degree-12 closure (hence S(v)<=146 for d(v)=12) and on completeness of
McKay's two A26 and nine B116 extremal catalog strata, embedded below.

Outline.
  1. An exact degree-class relaxation gives sum r(v)=27 over the nine
     degree-11 vertices, where r(v)=132-S(v)>=3.  Hence every low vertex has
     r=3.  For a low anchor v, if t is its number of low neighbours and w the
     weighted number of high neighbours, t-w=3.  Also e(A)=26,e(B)=116.
  2. Both A26 types have I5 transversal number 2, so every B vertex has at
     least two cross-neighbours in A.  For a low B vertex, r=3 means total
     neighbour excess over degree 11 is 8; therefore its internal-B excess is
     at most 8.  Exact DP over the nine B116 graphs rules out t=3,4,5.
  3. Thus the nine low vertices induce a K4-free graph of minimum degree >=6.
     Turan equality forces K_{3,3,3}; every low anchor has t=6 and its two low
     non-neighbours are nonadjacent.
  4. The same weak B-label DP for t=6 leaves only B116 ordinal 1 and, in both
     possible residual degree counts, uniquely forces the two low B vertices
     to be {0,3}.  But 0--3 is an edge in that B graph: contradiction.
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
SEQ={11:9,12:13,13:13,14:1}
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
  if d==12:hi=146 # from certified no-lucky-d12 closure
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
 assert len(vals)==87 and set(vals)=={27},(len(vals),set(vals))
 return vals

def transversal_number(A):
 I5=independent_sets(A,5)
 for k in range(12):
  for S in combinations(range(11),k):
   m=sum(1<<v for v in S)
   if all(m&I for I in I5):return k
 raise AssertionError

def residual_B_counts(t,z):
 # r=3 gives w=t-3=y+2z, where y=#degree13 and z=#degree14 neighbours of the anchor.
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
 """Return all possible low-vertex sets in a deliberately weak necessary system.

 Vertices are labelled by final degree excess e=D-11.  Cross degree must be >=2
 because tau(A)=2.  If e=0 then, since r=3, internal-B neighbour excess <=8.
 We omit the exact cross contribution and all Ramsey cross constraints.
 """
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

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output');a=ap.parse_args()
 vals=class_relaxation()
 A=[g6(s) for s in A26];B=[g6(s) for s in B116]
 assert all(len(x)==11 and edges(x)==26 for x in A)
 taus=[transversal_number(x) for x in A];assert taus==[2,2],taus
 assert all(len(x)==24 and edges(x)==116 for x in B)
 rows=[];low_t_cases=[]
 for t in (3,4,5):
  for z in (0,1):
   bc=residual_B_counts(t,z)
   if bc is None:continue
   low_t_cases.append({'t':t,'z14':z,'B_counts':bc})
   for bi,bg in enumerate(B):
    poss,n=weak_B_feasible(bg,bc);rows.append({'stage':'t<=5','t':t,'z14':z,'B_counts':bc,'b_ordinal':bi,'possible_low_sets':poss,'dp_states':n})
    assert not poss,(t,z,bi,poss)
 # Therefore every low vertex has t>=6.  The low graph has 9 vertices, is K4-free,
 # and has >=27 edges; Turan ex(9,K4)=27, so equality gives K3,3,3 and t=6 everywhere.
 assert ex_k4(9)==27
 t6=[]
 for z in (0,1):
  bc=residual_B_counts(6,z);assert bc is not None
  for bi,bg in enumerate(B):
   poss,n=weak_B_feasible(bg,bc);t6.append({'t':6,'z14':z,'B_counts':bc,'b_ordinal':bi,'possible_low_sets':poss,'dp_states':n})
 survivors=[r for r in t6 if r['possible_low_sets']]
 assert len(survivors)==2,survivors
 assert all(r['b_ordinal']==1 and r['possible_low_sets']==[(0,3)] for r in survivors),survivors
 assert (B[1][0]>>3)&1 # contradiction: the two same-part low vertices must be nonadjacent in K3,3,3.
 out={
  'campaign':'m219-seq6-lowgraph-obstruction',
  'degree_sequence':{'11':9,'12':13,'13':13,'14':1},
  'dependencies':{
   'no_lucky_d12':'certified closure implies S(v)<=146 for degree 12 in class relaxation',
   'A26':'complete authenticated McKay stratum, 2 graphs; both have I5 transversal number 2',
   'B116':'complete authenticated McKay stratum, 9 graphs'
  },
  'class_relaxation_count':len(vals),'sum_r_values':sorted(set(vals)),'all_degree11_r3':True,
  'A26_transversal_numbers':taus,
  't_le_5_cases':low_t_cases,'t_le_5_checks':rows,
  'derived_low_graph':'K4-free on 9 vertices with minimum degree >=6; Turan equality forces K3,3,3',
  't6_checks':t6,
  't6_survivors':survivors,
  'final_obstruction':'both t=6 residual cases force B116 ordinal 1 and low B vertices {0,3}, but edge (0,3) is present; in K3,3,3 these are the anchor same-part mates and must be nonadjacent',
  'conclusion':'degree sequence 11^9 12^13 13^13 14^1 is impossible for an m=219 (4,6)-Ramsey graph'
 }
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(text,end='')
 if a.output:open(a.output,'w').write(text)
if __name__=='__main__':main()
