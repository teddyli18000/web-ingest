#!/usr/bin/env python3
"""Exact prize recombination across all validated public 367 basins in C7^5.

The certified 315-core C gives the exact completion score

    score(Y) = 315 + |Y| - |N_C(Y)|

for any outside independent set Y. Each public 367-set is first completed
relative to C, yielding a set of selected outside vertices. Three nested exact
candidate pools are then optimized with RC2:

1. seed-union: every outside vertex selected by any completed public 367-set;
2. same-support: all ambient outside vertices whose exact core-neighbour support
   equals a support pattern observed in the seed-union;
3. support-subset: all ambient outside vertices whose support is a subset of at
   least one observed support pattern (never a larger core cost than that
   observed pattern).

The three exact RC2 jobs are independent and may be solved concurrently on one
runner via fork workers. This is a restricted exact recombination family, not a
global upper-bound method. Any 368 witness is globally valid and independently
replayed.
"""
from __future__ import annotations

import argparse,gzip,itertools,json,multiprocessing as mp
from pathlib import Path
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2

Q=7;D=5;U=Q**D;CORE=315;TARGET=368;POW=tuple(Q**i for i in range(D))
def dec(v):return tuple((v//POW[i])%Q for i in range(D))
def enc(w):return sum(int(w[i])*POW[i] for i in range(D))
def neigh(v):
 d=dec(v)
 for z in itertools.product((-1,0,1),repeat=D):
  if all(t==0 for t in z):continue
  yield enc(tuple((d[i]+z[i])%Q for i in range(D)))
def independent(S):
 S=set(S);return all(u not in S for v in S for u in neigh(v))

_G_SUPPORT=None;_G_CORE=None;_G_C=None
def solve_pool(name,pool,support,core,C):
 pool=tuple(sorted(pool));P=set(pool);cvar={v:i+1 for i,v in enumerate(pool)};bb=len(pool)+1;bvar={c:bb+i for i,c in enumerate(core)};w=WCNF();edges=imp=0
 for v in pool:
  for u in neigh(v):
   if u in P and u>v:w.append([-cvar[v],-cvar[u]]);edges+=1
  for c in support[v]:w.append([-cvar[v],bvar[c]]);imp+=1
 for v in pool:w.append([cvar[v]],weight=1)
 for c in core:w.append([-bvar[c]],weight=1)
 with RC2(w,solver='g4',adapt=True,exhaust=True,verbose=1) as rc2:
  model=rc2.compute();cost=int(rc2.cost)
 if model is None:raise RuntimeError(('no model',name))
 pos={z for z in model if z>0};Y={v for v in pool if cvar[v] in pos};blocked=set()
 for v in Y:blocked.update(support[v])
 completed=Y|(C-blocked);score=len(completed)
 if score!=len(pool)+CORE-cost or not independent(completed):raise RuntimeError(('replay',name,score,len(pool)+CORE-cost))
 return {'name':name,'pool_size':len(pool),'conflict_edges':edges,'support_implications':imp,'selected_outside':len(Y),'activated_core_blockers':len(blocked),'score':score,'prize':score-CORE,'points5':sorted(completed)}
def _solve_job(job):
 name,pool=job
 return solve_pool(name,pool,_G_SUPPORT,_G_CORE,_G_C)

def main():
 global _G_SUPPORT,_G_CORE,_G_C
 ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('corpus_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=3);a=ap.parse_args()
 with gzip.open(a.c7five_root/'data'/'core-overlap.json.gz','rt') as f:bundle=json.load(f)
 core=tuple(sorted(map(int,bundle['core'])));C=set(core)
 if len(core)!=CORE or len(C)!=CORE or not independent(C):raise RuntimeError('bad core')
 outside=tuple(v for v in range(U) if v not in C)
 support={v:frozenset(u for u in neigh(v) if u in C) for v in outside}
 corpus=json.loads(a.corpus_json.read_text());rows=corpus['sets'];seed_union=set();seed_rows=[]
 for row in rows:
  S=set(map(int,row['points']))
  if len(S)!=367 or not independent(S):raise RuntimeError(('seed',row.get('sha256')))
  Y=S-C;blocked=set()
  for v in Y:blocked.update(support[v])
  T=Y|(C-blocked)
  if len(T)!=367 or not independent(T):raise RuntimeError(('completion',row.get('sha256'),len(T)))
  Y2=T-C;seed_union.update(Y2);seed_rows.append({'sha256':row.get('sha256'),'outside':len(Y2),'blocked_core':len(C-T)})
 patterns={support[v] for v in seed_union};pats=tuple(patterns)
 same={v for v in outside if support[v] in patterns}
 subset={v for v in outside if any(support[v].issubset(p) for p in pats)}
 pools=[('seed-union',seed_union),('same-support',same),('support-subset',subset)]
 for name,pool in pools:print('POOL',name,'size',len(pool),flush=True)
 _G_SUPPORT=support;_G_CORE=core;_G_C=C
 workers=max(1,min(int(a.workers),len(pools)))
 if workers==1:
  results=[_solve_job(j) for j in pools]
 else:
  with mp.get_context('fork').Pool(workers) as p:results=list(p.imap_unordered(_solve_job,pools,chunksize=1))
 order={n:i for i,(n,_) in enumerate(pools)};results.sort(key=lambda r:order[r['name']])
 for r in results:print('RESULT',json.dumps({k:v for k,v in r.items() if k!='points5'},sort_keys=True),flush=True)
 best=max(results,key=lambda r:r['score'])
 out={'method':'exact-public367-cross-basin-core-prize-recombination','corpus_sets':len(rows),'seed_union_size':len(seed_union),'observed_support_patterns':len(patterns),'pool_sizes':{n:len(p) for n,p in pools},'workers':workers,'seed_completion_stats':seed_rows,'results':results,'best_score':best['score'],'candidate_368':best['score']>=TARGET}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 if best['score']>=TARGET:
  S=best['points5'][:TARGET]
  if len(S)!=TARGET or not independent(S):raise RuntimeError('target replay')
  a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points5':S},separators=(',',':'))+'\n')
 print('SUMMARY',json.dumps({k:v for k,v in out.items() if k not in ('seed_completion_stats','results')},sort_keys=True),flush=True)
if __name__=='__main__':main()
