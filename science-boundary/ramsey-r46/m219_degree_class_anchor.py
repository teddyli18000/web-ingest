#!/usr/bin/env python3
"""Exact degree-class relaxation for m=219 low-degree anchor strength.

For a degree-11 vertex v define
    r(v) = 132 - S(v) = t(v) - w(v),
where t(v) is its number of degree-11 neighbours and w(v) is the sum of
(deg(u)-12) over neighbours of degree at least 13.  The exact endpoint bounds
give S(v)<=129, hence r(v)>=3.

This script exhausts integer edge counts between degree classes for the ten
surviving m=219 degree sequences with n11>=7.  It uses exact class degree sums,
edge capacities, the K4-free Turan bound inside each degree class, exact local
S-intervals aggregated over each class, and the already-proved no-lucky-d12
bound S<=146 for degree 12.  Maximising sum_v r(v) over this relaxation gives a
rigorous upper bound.  If max sum r < 4*n11, some degree-11 vertex has r=3.
"""
from __future__ import annotations
import argparse,json
from math import comb
from pathlib import Path

SEQS=(
 {11:7,12:16,13:13}, {11:7,12:17,13:11,14:1}, {11:7,12:18,13:9,14:2},
 {11:8,12:14,13:14}, {11:8,12:15,13:12,14:1},
 {11:9,12:12,13:15}, {11:9,12:13,13:13,14:1},
 {11:10,12:10,13:16}, {11:11,12:8,13:17}, {11:12,12:6,13:18},
)
A_MIN={11:8,12:11,13:15,14:20,15:25,16:32,17:40}
A_MAX={11:26,12:29,13:32,14:35,15:37,16:40,17:42}
B_MIN={11:116,12:101,13:88,14:77,15:68,16:57,17:50}
B_MAX={11:132,12:122,13:114,14:107,15:100,16:92,17:85}

def s_interval(d,m=219):return max(11*d,m+A_MIN[d]-B_MAX[d]),min(17*d,m+A_MAX[d]-B_MIN[d])
def ex_k4(n):
 q,r=divmod(n,3);parts=[q+(i<r) for i in range(3)]
 return sum(parts[i]*parts[j] for i in range(3) for j in range(i+1,3))

def distributions(total,limits,prefix=()):
 if len(limits)==1:
  if 0<=total<=limits[0]:yield prefix+(total,)
  return
 lo=max(0,total-sum(limits[1:]));hi=min(limits[0],total)
 for x in range(lo,hi+1):yield from distributions(total-x,limits[1:],prefix+(x,))

def solve_seq(seq):
 ds=sorted(seq);k=len(ds);mat=[[0]*k for _ in range(k)]
 cap=[[0]*k for _ in range(k)]
 for i,d in enumerate(ds):
  for j in range(i,k):
   e=ds[j];cap[i][j]=min(comb(seq[d],2),ex_k4(seq[d])) if i==j else seq[d]*seq[e]
 rem0=[d*seq[d] for d in ds];feasible=0;maxR=-1;arg=None
 def check_class(i):
  d=ds[i];ss=2*d*mat[i][i]
  for j,e in enumerate(ds):
   if j!=i:ss += e*mat[min(i,j)][max(i,j)]
  lo,hi=s_interval(d)
  if d==12:hi=146
  return lo*seq[d]<=ss<=hi*seq[d]
 def rec(i,rem):
  nonlocal feasible,maxR,arg
  if i==k-1:
   if rem[i]<0 or rem[i]%2:return
   z=rem[i]//2
   if z>cap[i][i]:return
   mat[i][i]=z
   if not check_class(i):return
   feasible+=1;i11=ds.index(11);R=2*mat[i11][i11]
   for j,d in enumerate(ds):
    if d>=13:R-=(d-12)*mat[min(i11,j)][max(i11,j)]
   if R>maxR:maxR=R;arg=[row[:] for row in mat]
   return
  for eii in range(min(cap[i][i],rem[i]//2)+1):
   need=rem[i]-2*eii;future=list(range(i+1,k));limits=[min(cap[i][j],rem[j]) for j in future]
   if need<0 or need>sum(limits):continue
   mat[i][i]=eii
   for vals in distributions(need,limits):
    nr=rem[:]
    for j,x in zip(future,vals):mat[i][j]=x;nr[j]-=x
    if min(nr)<0 or not check_class(i):continue
    rec(i+1,nr)
 rec(0,rem0)
 n=seq[11]
 return {'degree_sequence':{str(k):v for k,v in seq.items()},'class_edge_relaxation_count':feasible,
         'max_sum_r':maxR,'four_n11':4*n,'forces_r3_anchor':maxR<4*n,
         'maximizer_edge_matrix':{'degrees':ds,'upper_triangle':[[matv if j>=i else None for j,matv in enumerate(row)] for i,row in enumerate(arg)]} if arg else None}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);a=ap.parse_args()
 rows=[solve_seq(s) for s in SEQS];forced=[i for i,r in enumerate(rows) if r['forces_r3_anchor']]
 assert [r['max_sum_r'] for r in rows]==[31,25,21,32,26,33,27,34,35,36]
 assert forced==[1,2,4,5,6,7,8,9],forced
 d={'campaign':'m219-degree-class-r-anchor','rows':rows,'r3_forced_indices':forced,
    'r3_not_forced_indices':[0,3],
    'interpretation':'exact integer relaxation; forced r=3 conclusions are rigorous, surviving relaxations are not claimed realizable'}
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'max_sum_r':[r['max_sum_r'] for r in rows],'r3_forced_indices':forced},sort_keys=True))
if __name__=='__main__':main()
