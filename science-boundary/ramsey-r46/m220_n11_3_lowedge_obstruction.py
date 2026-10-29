#!/usr/bin/env python3
"""Pure combinatorial exclusion of two low-edge orbits in m=220,n11=3.

Authenticated extreme catalogue rows are embedded as graph6 strings.  The
argument uses only: A is the degree-11 anchor neighborhood, B its 24-vertex
antineighborhood; the other two degree-11 vertices form an A-edge; all their
other neighbors have global degree 12; a B-column must hit every independent
5-set of A; and common B-neighbors of an A-edge are independent in B.
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

def clique_or_ind(a,vs,want_edge):
 return all(bool((a[i]>>j)&1)==want_edge for i,j in combinations(vs,2))
def sets(a,k,want_edge):return [c for c in combinations(range(len(a)),k) if clique_or_ind(a,c,want_edge)]
def min_hit_containing(a,u):
 I5=[set(x) for x in sets(a,5,False)]
 for k in range(1,len(a)+1):
  for c in combinations(range(len(a)),k):
   if u in c and all(set(c)&q for q in I5):return k
 raise AssertionError

def main():
 As=[decode(s) for s in A26]; Bs=[decode(s) for s in B116]
 assert all(sum(x.bit_count() for x in a)//2==26 and sets(a,5,False) and not sets(a,6,False) and not sets(a,3,True) for a in As)
 assert all(sum(x.bit_count() for x in b)//2==116 and sets(b,4,False) and not sets(b,5,False) and not sets(b,4,True) for b in Bs)
 bstats=[]
 for b in Bs:
  ds=[x.bit_count() for x in b];bstats.append({'degree_hist':{str(d):ds.count(d) for d in sorted(set(ds))},'degree_le9':sum(d<=9 for d in ds),'alpha':4})
 assert all(x['degree_le9']==8 and x['alpha']==4 for x in bstats)
 rows=[]
 # The exact A26 edge-orbit census has 5+3=8 orbits.  The two reps below
 # are the only ones killed by this lemma.  A0:(0,1) is a singleton orbit.
 # In A1, (0,1) and (0,2) are one orbit; the explicit permutation below
 # maps the representative to the other edge and is verified as an automorphism.
 killed_specs=[(0,(0,1),1,None),(1,(0,1),2,(0,2,1,7,8,9,10,3,4,5,6))]
 for ai,e,orbit_size,perm in killed_specs:
  a=As[ai];u,v=e
  assert (a[u]>>v)&1
  if perm is not None:
   assert sorted(perm)==list(range(11))
   for x in range(11):
    for y in range(x+1,11):
     assert bool((a[x]>>y)&1)==bool((a[perm[x]]>>perm[y])&1)
   assert tuple(sorted((perm[u],perm[v])))==(0,2)
  mu,mv=min_hit_containing(a,u),min_hit_containing(a,v)
  ru,rv=10-a[u].bit_count(),10-a[v].bit_count()
  assert mu==mv==3
  common_lb=ru+rv-8
  assert common_lb>=5
  rows.append({'A':ai,'representative':list(e),'orbit_size':orbit_size,
               'A_degrees':[a[u].bit_count(),a[v].bit_count()],'cross_needs':[ru,rv],
               'min_hitting_column_sizes':[mu,mv],'eligible_B_vertices_each':8,
               'common_neighbor_lower_bound':common_lb,'killed_by_alpha4':True})
 killed=[r for r in rows if r['killed_by_alpha4']]
 assert len(killed)==2
 out={'campaign':'m220-n11-3-lowedge-obstruction','A26_count':2,'B116_count':9,'B_stats':bstats,
      'killed_edge_orbits':rows,'killed_orbit_count':2,'killed_branch_count':2*9*16,
      'conclusion':'Two of the eight A26 low-edge orbits are impossible for every B116 type and every one of the 16 m220,n11=3 degree sequences.'}
 print(json.dumps(out,indent=2,sort_keys=True))
if __name__=='__main__':main()
