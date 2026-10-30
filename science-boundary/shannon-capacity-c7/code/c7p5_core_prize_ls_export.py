#!/usr/bin/env python3
"""Export the certified 315-core and validated public 367 seeds for C++ prize LS.

The output is deliberately simple whitespace text:

  315
  <315 core vertex ids>
  <number of seeds>
  367 <seed ids...>
  ...

Every core/seed is replayed under the exact C7^5 conflict rule before export.
For each 367 seed, its completion relative to the 315-core must still have size
exactly 367; otherwise the seed would already imply a larger public witness.
"""
from __future__ import annotations
import argparse,gzip,json
from itertools import product
from pathlib import Path
Q=7;D=5;U=Q**D;POW=tuple(Q**i for i in range(D))
def dec(v):return tuple((v//POW[i])%Q for i in range(D))
def enc(w):return sum(int(w[i])*POW[i] for i in range(D))
def neigh(v):
 d=dec(v)
 for z in product((-1,0,1),repeat=D):
  if all(x==0 for x in z):continue
  yield enc(tuple((d[i]+z[i])%Q for i in range(D)))
def independent(S):
 S=set(S)
 return all(u not in S for v in S for u in neigh(v))
def completed(seed,C):
 Y=set(seed)-C;blocked=set()
 for v in Y:blocked.update(u for u in neigh(v) if u in C)
 return Y|(C-blocked)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('corpus_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);a=ap.parse_args()
 with gzip.open(a.c7five_root/'data'/'core-overlap.json.gz','rt') as f:bundle=json.load(f)
 core=sorted(map(int,bundle['core']));C=set(core)
 if len(core)!=315 or len(C)!=315 or not independent(C):raise RuntimeError('bad core')
 corpus=json.loads(a.corpus_json.read_text());rows=corpus['sets'];seeds=[];seen=set();comp=[]
 for r in rows:
  S=tuple(sorted(map(int,r['points'])))
  if len(S)!=367 or len(set(S))!=367 or not independent(S):raise RuntimeError(('bad seed',r.get('sha256')))
  T=completed(S,C)
  if len(T)!=367 or not independent(T):raise RuntimeError(('completion drift',r.get('sha256'),len(T)))
  q=tuple(sorted(T))
  if q not in seen:seen.add(q);seeds.append(q);comp.append({'sha256':r.get('sha256'),'sources':r.get('sources',[]),'outside':len(set(q)-C),'blocked_core':len(C-set(q))})
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('w') as f:
  f.write('315\n'+' '.join(map(str,core))+'\n')
  f.write(str(len(seeds))+'\n')
  for S in seeds:f.write('367 '+' '.join(map(str,S))+'\n')
 st={'method':'validated-c7p5-core-prize-ls-export','core_size':315,'input_exact_seeds':len(rows),'distinct_completed_seeds':len(seeds),'seed_completion_stats':comp,'core_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
 a.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in st.items() if k!='seed_completion_stats'},sort_keys=True))
if __name__=='__main__':main()
