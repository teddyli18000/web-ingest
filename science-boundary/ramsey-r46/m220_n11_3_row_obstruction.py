#!/usr/bin/env python3
"""Exact row-support exclusion of the full m=220,n11=3 layer for R(4,6,36).

For a degree-11 anchor v, m220_structure.py forces A=N(v) to be one of two
A26 graphs and B to be one of nine B116 graphs. If n11=3, the other two
11-degree vertices form an edge in A and all other A vertices have degree 12.
This fixes each A vertex's cross-row size into B.

Every cross row R_a must be triangle-free in B. For two A vertices a,c:
* if ac is an A-edge, R_a intersect R_c must be independent in B (else K4);
* if ac is an A-nonedge, R_a union R_c must hit every independent 4-set in B
  (else those four vertices plus a,c form an independent 6-set).
For an independent A-triple, the three row union must hit every independent
3-set in B. The checks below show these necessary conditions already
contradict every possible low edge, independent of SAT or B degree labels.
"""
from itertools import combinations
import json

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

def decode(s):
 v=[ord(c)-63 for c in s];n=v[0];bits=[]
 for x in v[1:]:bits += [(x>>i)&1 for i in range(5,-1,-1)]
 a=[0]*n;k=0
 for j in range(1,n):
  for i in range(j):
   if bits[k]:a[i]|=1<<j;a[j]|=1<<i
   k+=1
 return a

def is_independent(g,m):
 q=m
 while q:
  u=(q&-q).bit_length()-1;q&=q-1
  if g[u]&q:return False
 return True

def triangle_free(g,m):
 q=m
 while q:
  u=(q&-q).bit_length()-1;q&=q-1;z=g[u]&q
  while z:
   w=(z&-z).bit_length()-1;z&=z-1
   if g[w]&q:return False
 return True

def masks(n,k):
 for c in combinations(range(n),k):yield sum(1<<i for i in c)
def independent_sets(g,k):return [m for m in masks(len(g),k) if is_independent(g,m)]
def row_domain(g,k):return [m for m in masks(len(g),k) if triangle_free(g,m)]
def edge(g,u,v):return bool((g[u]>>v)&1)
def hit_all(u,sets):return all(u&s for s in sets)

def min_hit_containing(A,u):
 I5=independent_sets(A,5)
 for k in range(1,12):
  for m in masks(11,k):
   if (m>>u)&1 and hit_all(m,I5):return k
 raise AssertionError

def main():
 As=[decode(s) for s in A26];Bs=[decode(s) for s in B116]
 assert all(sum(x.bit_count() for x in A)//2==26 and not independent_sets(A,6) for A in As)
 assert all(sum(x.bit_count() for x in B)//2==116 and not independent_sets(B,5) for B in Bs)
 binfo=[];cache=[]
 for bi,B in enumerate(Bs):
  D={k:row_domain(B,k) for k in range(5,10)};I3=independent_sets(B,3);I4=independent_sets(B,4)
  ds=[x.bit_count() for x in B]
  binfo.append({'B':bi,'degree_le9':sum(d<=9 for d in ds),'triangle_free_8':len(D[8]),'triangle_free_9':len(D[9])})
  cache.append((D,I3,I4))
 assert [x['triangle_free_8'] for x in binfo]==[0,0,0,0,9,1,1,1,1]
 assert all(x['triangle_free_9']==0 and x['degree_le9']==8 for x in binfo)

 A1=As[1];assert A1[0].bit_count()==2 and {i for i in range(11) if edge(A1,0,i)}=={1,2}
 a1_nonincident=[(u,v) for u in range(11) for v in range(u+1,11) if edge(A1,u,v) and 0 not in (u,v)]
 assert len(a1_nonincident)==24
 assert min_hit_containing(A1,0)==3 and min_hit_containing(A1,1)==3 and min_hit_containing(A1,2)==3
 for v in (1,2):assert 10-A1[0].bit_count()+10-A1[v].bit_count()-8==5

 A0=As[0];assert A0[0].bit_count()==3 and {i for i in range(11) if edge(A0,0,i)}=={1,5,6}
 assert min_hit_containing(A0,0)==min_hit_containing(A0,1)==3
 assert (10-A0[0].bit_count())+(10-A0[1].bit_count())-8==5

 def pair_support(A,B,D,I4,a,r,c,k):
  if edge(A,a,c):return any(is_independent(B,r&q) for q in D[k])
  return any(hit_all(r|q,I4) for q in D[k])

 incident_details=[]
 for lowv in (5,6):
  low={0,lowv};need=[(10 if a in low else 11)-A0[a].bit_count() for a in range(11)]
  assert need[0]==need[1]==7 and need[2]==need[3]==6
  for bi,B in enumerate(Bs):
   D,I3,I4=cache[bi];good=[]
   for r0 in D[7]:
    if all(pair_support(A0,B,D,I4,0,r0,c,need[c]) for c in range(1,11)):good.append(r0)
   if not good:
    incident_details.append({'low_edge':[0,lowv],'B':bi,'pair_supported_first_rows':0,'triple_supported_first_rows':0});continue
   triple_good=0
   for r0 in good:
    ok=False
    for r2 in D[6]:
     if not hit_all(r0|r2,I4):continue
     if any(hit_all(r0|r3,I4) and hit_all(r2|r3,I4) and hit_all(r0|r2|r3,I3) for r3 in D[6]):
      ok=True;break
    triple_good+=ok
   incident_details.append({'low_edge':[0,lowv],'B':bi,'pair_supported_first_rows':len(good),'triple_supported_first_rows':triple_good})
   assert triple_good==0

 remaining_details=[]
 other_edges=[(u,v) for u in range(11) for v in range(u+1,11) if edge(A0,u,v) and 0 not in (u,v)]
 assert len(other_edges)==23
 for lowe in other_edges:
  low=set(lowe);need=[(10 if a in low else 11)-A0[a].bit_count() for a in range(11)];assert need[0]==8
  for bi,B in enumerate(Bs):
   D,I3,I4=cache[bi]
   if not D[8]:
    remaining_details.append({'low_edge':list(lowe),'B':bi,'first_row_domain':0,'pair_supported_first_rows':0});continue
   good=0
   for r0 in D[8]:
    if all(pair_support(A0,B,D,I4,0,r0,c,need[c]) for c in range(1,11)):good+=1
   remaining_details.append({'low_edge':list(lowe),'B':bi,'first_row_domain':len(D[8]),'pair_supported_first_rows':good})
   assert good==0

 assert all(x['triple_supported_first_rows']==0 for x in incident_details)
 assert all(x['pair_supported_first_rows']==0 for x in remaining_details)
 out={'campaign':'m220-n11-3-row-obstruction','A26_count':2,'B116_count':9,'B_summary':binfo,
      'A1_nonincident_low_edges_killed_by_no_triangle_free9':len(a1_nonincident)*9,
      'A1_incident_low_edges_killed_by_common_neighbors':2*9,
      'A0_edge_01_killed_by_common_neighbors':9,
      'A0_edges_05_06_details':incident_details,'A0_other_edges_details':remaining_details,
      'actual_low_edge_B_pairs_checked':2*26*9,
      'conclusion':'No m=220 R(4,6,36) graph can have exactly three degree-11 vertices.'}
 print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
