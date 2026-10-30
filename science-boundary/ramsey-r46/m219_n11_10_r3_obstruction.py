#!/usr/bin/env python3
"""Exact structural obstruction for m=219, degree sequence 11^10 12^10 13^16.

The class relaxation forces at least six r=3 degree-11 vertices. Exact weak
B116 label DP forces every r=3 vertex to have seven low neighbours and its two
low non-neighbours adjacent. A six-vertex marked-set argument in the
complement of the low graph then contradicts alpha<=3.
"""
from itertools import combinations
from collections import Counter
import argparse,json
A26=("JiQC@{}N`{?","JqPA@{}N`{?")
B116=("W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE","WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?","WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_","WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_","WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT","Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA","Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@","Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC")
SEQ={11:10,12:10,13:16,14:0};A_MIN={11:8,12:11,13:15,14:20};A_MAX={11:26,12:29,13:32,14:35};B_MIN={11:116,12:101,13:88,14:77};B_MAX={11:132,12:122,13:114,14:107}
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
 rec(0,[d*SEQ[d] for d in ds]);assert len(vals)==76 and max(vals)==34,(len(vals),max(vals));return vals
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
 db=degs(B);nl=bc[0];cand=[v for v,d in enumerate(db) if 11-d>=2];poss=[];seen=0
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
   st=nx;seen+=len(st)
   if not st:break
  if any((a,b,c)==tuple(bc[1:]) for a,b,c,s in st):poss.append(tuple(Lt))
 return poss,seen
def residual_counts(t):
 y=t-3;a12=14-2*t
 if a12<0:return None
 a={11:t,12:a12,13:y,14:0};b={d:SEQ[d]-(d==11)-a[d] for d in SEQ}
 if min(b.values())<0:return None
 return tuple(b[11+e] for e in range(4))
def alpha(g,vs):
 for k in range(len(vs),-1,-1):
  for S in combinations(vs,k):
   if all(not(g[u]>>v&1) for u,v in combinations(S,2)):return k
def component_type(g):
 unseen=set(range(6));cs=[]
 while unseen:
  s=unseen.pop();stack=[s];C={s}
  while stack:
   v=stack.pop()
   for u in range(6):
    if u in unseen and g[v]>>u&1:unseen.remove(u);C.add(u);stack.append(u)
  e=sum(1 for u,v in combinations(C,2) if g[u]>>v&1);cs.append(('C' if len(C)>=4 and e==len(C) else 'P',len(C)))
 return tuple(sorted(cs))
def marked_complement_types():
 E=list(combinations(range(6),2));rows={}
 for mask in range(1<<15):
  g=[0]*6;d=[0]*6;ok=True
  for i,(u,v) in enumerate(E):
   if mask>>i&1:
    d[u]+=1;d[v]+=1
    if d[u]>2 or d[v]>2:ok=False;break
    g[u]|=1<<v;g[v]|=1<<u
  if not ok:continue
  if any(g[a]>>b&1 and g[a]>>c&1 and g[b]>>c&1 for a,b,c in combinations(range(6),3)):continue
  if alpha(g,range(6))>3:continue
  inds=[set(S) for S in combinations(range(6),3) if all(not(g[u]>>v&1) for u,v in combinations(S,2))]
  tau=7
  for k in range(7):
   if any(all(set(T)&I for I in inds) for T in combinations(range(6),k)):tau=k;break
  typ=component_type(g);e=edges(g);q=12-2*e;rows[typ]=(e,tau,q,4*tau)
 expected={(('P',2),('P',2),('P',2)),(('P',2),('P',4)),(('C',5),('P',1)),(('P',6),),(('C',4),('P',2)),(('C',6),)}
 assert set(rows)==expected,(set(rows),expected);assert all(q<need for e,tau,q,need in rows.values()),rows;return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--output');a=p.parse_args();vals=class_relaxation();A=[g6(x) for x in A26];B=[g6(x) for x in B116]
 assert all(edges(x)==26 for x in A);taus=[transversal_number(x) for x in A];assert taus==[2,2];assert all(edges(x)==116 for x in B)
 minr3=10-(max(vals)-30);assert minr3==6;checks=[]
 for t in range(3,8):
  bc=residual_counts(t);assert bc is not None
  for bi,bg in enumerate(B):
   poss,n=weak_B_feasible(bg,bc);checks.append({'t':t,'B_counts':bc,'b_ordinal':bi,'possible_low_sets':poss,'dp_states':n})
   if t<7:assert not poss,(t,bi,poss)
 t7=[r for r in checks if r['t']==7 and r['possible_low_sets']];assert len(t7)==1 and t7[0]['b_ordinal']==1 and t7[0]['possible_low_sets']==[(0,3)],t7;assert (B[1][0]>>3)&1;assert residual_counts(8) is None
 types=marked_complement_types();out={'campaign':'m219-n11-10-r3-lowgraph-obstruction','degree_sequence':{'11':10,'12':10,'13':16},'dependencies':{'no_lucky_d12':'certified closure implies S(v)<=146 for degree 12 in class relaxation','A26':'complete authenticated McKay stratum, 2 graphs; both I5 transversal number 2','B116':'complete authenticated McKay stratum, 9 graphs'},'class_relaxation_count':len(vals),'max_sum_r':max(vals),'minimum_forced_r3_vertices':minr3,'A26_transversal_numbers':taus,'r3_local_rule':'r=3 forces t=7; weak B DP uniquely leaves B116 ordinal1 with the two low non-neighbours {0,3}, which are adjacent','r3_local_checks':checks,'marked_complement_types':{' + '.join(f'{x}{y}' for x,y in typ):{'edges_in_R':v[0],'independent_triple_transversal':v[1],'available_RU_edges':v[2],'required_RU_edges_for_four_U':v[3]} for typ,v in types.items()},'counting_obstruction':'for six marked r3 vertices R, H[R] is triangle-free with Delta<=2 and alpha<=3. Each of four U vertices must hit every independent triple of H[R]. For every possible component type, 12-2e(H[R]) < 4*tau_3(H[R]).','conclusion':'degree sequence 11^10 12^10 13^16 is impossible for an m=219 (4,6)-Ramsey graph'}
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({k:v for k,v in out.items() if k not in ('r3_local_checks','marked_complement_types')},sort_keys=True));
 if a.output:open(a.output,'w').write(text)
if __name__=='__main__':main()
