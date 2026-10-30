#!/usr/bin/env python3
"""Exact 50-orbit decision decomposition for a 368-set in C7^5.

First use vertex transitivity to require vertex 00000.  Its stabilizer contains
all coordinate permutations and independent coordinate sign reversals.  Hence a
second selected vertex is classified only by the sorted multiset of its five
cyclic distances from zero, each in {0,1,2,3}.  There are C(8,3)=56 such
multisets; six use only {0,1} and are confusable with zero, leaving exactly 50
nonconfusable orbits.

For every hypothetical independent set of size >=368, choose any second vertex
and apply an automorphism fixing zero that maps it to the canonical representative
of its orbit.  Therefore the 50 branches 'zero + representative_i selected'
cover every target solution without loss.

Each worker builds the exact 315-core prize decision model once and solves its
assigned representatives as assumptions, reusing learned clauses.  The model
also includes the certified target-specific 315-core overlap cut: at least four
core vertices are blocked/omitted in every 368-set.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
from pathlib import Path
from pysat.solvers import Minicard

Q=7;D=5;U=Q**D;CORE=315;TARGET=368;POW=tuple(Q**i for i in range(D))

def dec(v):return tuple((v//POW[i])%Q for i in range(D))
def enc(w):return sum(int(w[i])*POW[i] for i in range(D))
def neigh(v):
 d=dec(v)
 for z in itertools.product((-1,0,1),repeat=D):
  if all(t==0 for t in z):continue
  yield enc(tuple((d[i]+z[i])%Q for i in range(D)))
def independent(S):
 S=set(S)
 return all(u not in S for v in S for u in neigh(v))
def orbit_reps():
 out=[]
 for typ in itertools.combinations_with_replacement(range(4),D):
  if max(typ)<2:continue
  v=enc(typ)
  out.append((typ,v))
 if len(out)!=50:raise RuntimeError(('orbit count',len(out)))
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);a=ap.parse_args()
 if a.shards<1 or not 0<=a.shard<a.shards:raise SystemExit('bad shard')
 with gzip.open(a.c7five_root/'data'/'core-overlap.json.gz','rt') as f:bundle=json.load(f)
 core=tuple(sorted(map(int,bundle['core'])));C=set(core)
 if len(core)!=CORE or len(C)!=CORE or not independent(C):raise RuntimeError('bad core')
 outside=tuple(v for v in range(U) if v not in C);O=set(outside)
 x={v:i+1 for i,v in enumerate(outside)};bb=len(outside)+1;b={c:bb+i for i,c in enumerate(core)}
 s=Minicard();edges=0;impl=0;hist={}
 for v in outside:
  supp=[]
  for u in neigh(v):
   if u in C:supp.append(u)
   elif u in O and u>v:s.add_clause([-x[v],-x[u]]);edges+=1
  hist[len(supp)]=hist.get(len(supp),0)+1
  for c in supp:s.add_clause([-x[v],b[c]]);impl+=1
 # Exact target size in the completed representation.
 s.add_atleast([x[v] for v in outside]+[-b[c] for c in core],TARGET)
 # Portable molind core-overlap theorem for every 368-set.
 s.add_atleast([b[c] for c in core],4)
 # Lossless translation symmetry break: completed solution contains zero.
 zero_lit=(-b[0] if 0 in C else x[0]);s.add_clause([zero_lit])
 reps=orbit_reps();assigned=[(i,t,v) for i,(t,v) in enumerate(reps) if i%a.shards==a.shard]
 setup={'method':'exact-c7p5-368-core-prize-50-orbit-decomposition','ambient':U,'core_size':CORE,'outside':len(outside),'outside_conflict_edges':edges,'support_implications':impl,'support_histogram':{str(k):v for k,v in sorted(hist.items())},'orbit_count':len(reps),'shard':a.shard,'shards':a.shards,'assigned_orbits':len(assigned),'certified_min_core_blockers':4,'core_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
 print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
 rows=[];sat_model=None;sat_meta=None
 for j,(idx,typ,v) in enumerate(assigned):
  lit=(-b[v] if v in C else x[v])
  print('ORBIT',j+1,'/',len(assigned),'global',idx,'type',typ,'rep',v,flush=True)
  sat=s.solve(assumptions=[lit])
  row={'orbit_index':idx,'type':list(typ),'representative':v,'sat':bool(sat)};rows.append(row)
  print('ORBIT_RESULT',json.dumps(row,sort_keys=True),flush=True)
  if sat:
   sat_model=s.get_model();sat_meta=row;break
 s.delete();out={'setup':setup,'rows':rows,'candidate':False,'sat_orbit':sat_meta}
 if sat_model is not None:
  pos={z for z in sat_model if z>0};Y={v for v in outside if x[v] in pos};blocked=set()
  for v in Y:blocked.update(u for u in neigh(v) if u in C)
  completed=Y|(C-blocked)
  if len(completed)<TARGET or not independent(completed) or 0 not in completed or len(blocked)<4:raise RuntimeError(('SAT replay',len(completed),len(blocked)))
  rep=sat_meta['representative']
  if rep not in completed:raise RuntimeError('orbit representative replay')
  out.update(candidate=True,completed_size=len(completed),selected_outside=len(Y),activated_core_blockers=len(blocked),points5=sorted(completed)[:TARGET])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('RESULT',json.dumps({k:v for k,v in out.items() if k not in ('points5','rows')},sort_keys=True),flush=True)
if __name__=='__main__':main()
