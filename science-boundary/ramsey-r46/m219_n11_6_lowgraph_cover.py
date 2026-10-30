#!/usr/bin/env python3
from itertools import combinations, permutations
from collections import Counter
import json, argparse
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
RR={
3:["001110","001101","110011","110011","101101","011110"],
4:["011001","100101","100011","010011","001101","111110"],
5:["011010","100101","100011","010011","101101","011110"],
6:["011100","101100","110011","110011","001101","001110"],
7:["011100","101010","110001","100011","010101","001110"]}
AR={3:[0],4:[0],5:[0,2],6:[0],7:[0]}
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
def from_rows(rows):return [sum((ch=='1')<<j for j,ch in enumerate(r)) for r in rows]
def degs(g):return [x.bit_count() for x in g]
def edge(g,u,v):return (g[u]>>v)&1
def has_k4(g):return any(all(edge(g,u,v) for u,v in combinations(S,2)) for S in combinations(range(len(g)),4))
def perm_code(g,p):
 bits=[]
 for i in range(len(g)):
  for j in range(i+1,len(g)):bits.append(edge(g,p[i],p[j]))
 return tuple(bits)
def canon(g):return min(perm_code(g,p) for p in permutations(range(len(g))))
def autos(g):
 base=perm_code(g,tuple(range(len(g))))
 return [p for p in permutations(range(len(g))) if perm_code(g,p)==base]
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
def enumerate_types():
 E=list(combinations(range(6),2)); by={}
 for mask in range(1<<15):
  g=[0]*6
  for i,(u,v) in enumerate(E):
   if mask>>i&1:g[u]|=1<<v;g[v]|=1<<u
  if min(degs(g))<3 or has_k4(g):continue
  c=canon(g);by.setdefault(c,g)
 return list(by.values())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output');a=ap.parse_args();Bs=[g6(s) for s in B116];weak={}
 for name,bc in [('S0',(2,10,12,0)),('S1',(2,11,10,1))]:
  rows=[]
  for bi,B in enumerate(Bs):
   p=weak_B_feasible(B,bc)
   if p:rows.append({'b_ordinal':bi,'pairs':[list(x) for x in p]})
  assert rows==[{'b_ordinal':1,'pairs':[[0,3]]}],(name,rows);assert edge(Bs[1],0,3)==1;weak[name]=rows
 types=enumerate_types();assert len(types)==9,len(types);cRR={canon(from_rows(rows)):typ for typ,rows in RR.items()};surv=[];dead=[];k222=[]
 for g in types:
  ds=degs(g);c=canon(g);d3=[v for v,d in enumerate(ds) if d==3]
  if not d3:
   assert sorted(ds)==[4]*6;k222.append({'degree_sequence':ds,'canonical':''.join(map(str,c))});continue
  bad=[]
  for v in d3:
   U=[u for u in range(6) if u!=v and not edge(g,v,u)];assert len(U)==2
   if not edge(g,U[0],U[1]):bad.append(v)
  if bad:dead.append({'degree_sequence':sorted(ds),'bad_degree3_anchors':bad,'canonical':''.join(map(str,c))})
  else:
   assert c in cRR,(ds,c);typ=cRR[c];gg=from_rows(RR[typ]);A=autos(gg);anchors=[i for i,d in enumerate(degs(gg)) if d==3];orbs=[];rem=set(anchors)
   while rem:
    v=min(rem);o={p[v] for p in A}&set(anchors);rem-=o;orbs.append(sorted(o))
   assert [min(o) for o in orbs]==AR[typ],(typ,orbs,AR[typ]);surv.append({'type':typ,'degree_sequence':degs(gg),'degree3_anchor_orbits':orbs,'rows':RR[typ]})
 assert len(dead)==3 and len(k222)==1 and len(surv)==5,(len(dead),len(k222),len(surv))
 out={'campaign':'m219-n11-6-lowgraph-cover','weak_B_unique_pair':weak,'unlabeled_low_types':9,'eliminated_by_unique_B_edge_pair':dead,'k222_types':k222,'surviving_types':sorted(surv,key=lambda x:x['type']),'surviving_type_count':5,'anchor_orbit_count':sum(len(x['degree3_anchor_orbits']) for x in surv),'conclusion':'For the first two n11=6 degree sequences, every non-K222 candidate has a degree-3 low anchor. The exact B116 weak label condition forces its two low B vertices to be the adjacent pair {0,3} of B116 ordinal 1. Three low-graph types violate this at a degree-3 anchor; K222 is independently excluded; exactly the five hard-coded fixed-low CSP types remain.'};assert out['anchor_orbit_count']==6
 text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(json.dumps({k:v for k,v in out.items() if k not in ('surviving_types','eliminated_by_unique_B_edge_pair')},sort_keys=True))
 if a.output:open(a.output,'w').write(text)
if __name__=='__main__':main()
