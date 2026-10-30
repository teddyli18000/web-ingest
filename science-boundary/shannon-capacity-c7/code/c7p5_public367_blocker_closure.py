#!/usr/bin/env python3
"""Exact support-subset prize closure of every validated public 367 basin in C7^5.

Let C be the certified independent 315-core. Completing a public 367-set S
relative to C yields outside set Y and source blocker footprint B=N_C(Y).
For that source basin, permit every ambient outside vertex v with
N_C(v) subseteq B.  Crucially, an optimized outside set Y' need not activate all
of B; the correct objective is therefore the exact prize

    315 + |Y'| - |N_C(Y')|,

not `315-|B|+alpha(pool_B)`.  This script encodes one blocker variable per core
point and charges only actually activated blockers.  Thus each job exactly
closes the entire support-subset basin under the 315-core prize identity.

Distinct public seeds with identical source B are deduplicated. Searches run in
parallel worker processes. Any score >=368 is a global valid witness; a miss is
an exact exclusion only for the tested support-subset basins.
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

_G_OUTSIDE=None;_G_SUPPORT=None;_G_CORE=None
def solve_one(job):
 idx,blockers,sources=job;B=set(blockers);pool=tuple(v for v in _G_OUTSIDE if _G_SUPPORT[v].issubset(B));P=set(pool);var={v:i+1 for i,v in enumerate(pool)};bb=len(pool)+1;bvar={c:bb+i for i,c in enumerate(_G_CORE)};w=WCNF();edges=imp=0
 for v in pool:
  for u in neigh(v):
   if u in P and u>v:w.append([-var[v],-var[u]]);edges+=1
  for c in _G_SUPPORT[v]:w.append([-var[v],bvar[c]]);imp+=1
 for v in pool:w.append([var[v]],weight=1)
 for c in _G_CORE:w.append([-bvar[c]],weight=1)
 with RC2(w,solver='g4',adapt=True,exhaust=True,verbose=0) as rc2:
  model=rc2.compute();cost=int(rc2.cost)
 if model is None:raise RuntimeError(('no model',idx))
 pos={z for z in model if z>0};Y={v for v in pool if var[v] in pos};blocked=set()
 for v in Y:blocked.update(_G_SUPPORT[v])
 C=set(_G_CORE);completed=Y|(C-blocked);score=len(completed)
 if not independent(Y) or not independent(completed):raise RuntimeError(('independence replay',idx))
 if not blocked.issubset(B):raise RuntimeError(('escaped basin',idx,len(blocked),len(B)))
 soft_total=len(pool)+CORE
 if score!=soft_total-cost:raise RuntimeError(('objective replay',idx,score,soft_total-cost))
 return {'basin_index':idx,'source_blockers':list(blockers),'source_blocker_count':len(B),'source_sha256':sources,'pool_size':len(pool),'conflict_edges':edges,'support_implications':imp,'selected_outside':len(Y),'activated_core_blockers':len(blocked),'score':score,'prize':score-CORE,'points5':sorted(completed)}

def main():
 global _G_OUTSIDE,_G_SUPPORT,_G_CORE
 ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('corpus_json',type=Path);ap.add_argument('output',type=Path);ap.add_argument('certificate',type=Path);ap.add_argument('--workers',type=int,default=max(1,mp.cpu_count()));a=ap.parse_args()
 with gzip.open(a.c7five_root/'data'/'core-overlap.json.gz','rt') as f:bundle=json.load(f)
 core=tuple(sorted(map(int,bundle['core'])));C=set(core)
 if len(core)!=CORE or len(C)!=CORE or not independent(C):raise RuntimeError('bad core')
 outside=tuple(v for v in range(U) if v not in C);support={v:frozenset(u for u in neigh(v) if u in C) for v in outside}
 corpus=json.loads(a.corpus_json.read_text());groups={};seed_stats=[]
 for row in corpus['sets']:
  S=set(map(int,row['points']))
  if len(S)!=367 or not independent(S):raise RuntimeError(('seed',row.get('sha256')))
  Y=S-C;B=set()
  for v in Y:B.update(support[v])
  T=Y|(C-B)
  if len(T)!=367 or not independent(T):raise RuntimeError(('completion',row.get('sha256'),len(T)))
  key=tuple(sorted(B));groups.setdefault(key,[]).append(row.get('sha256'));seed_stats.append({'sha256':row.get('sha256'),'blocker_count':len(B),'outside_count':len(Y)})
 jobs=[(i,k,groups[k]) for i,k in enumerate(sorted(groups,key=lambda q:(len(q),q)))]
 _G_OUTSIDE=outside;_G_SUPPORT=support;_G_CORE=core
 workers=max(1,min(int(a.workers),len(jobs)))
 print('SETUP',json.dumps({'method':'exact-public367-support-subset-core-prize-closure','public_sets':len(corpus['sets']),'distinct_blocker_basins':len(jobs),'workers':workers,'blocker_histogram':{str(k):sum(len(q)==k for q in groups) for k in sorted({len(q) for q in groups})}},sort_keys=True),flush=True)
 if workers==1:results=[solve_one(j) for j in jobs]
 else:
  with mp.get_context('fork').Pool(workers) as p:
   results=[]
   for r in p.imap_unordered(solve_one,jobs,chunksize=1):results.append(r);print('BASIN',json.dumps({k:v for k,v in r.items() if k not in ('points5','source_blockers')},sort_keys=True),flush=True)
 results.sort(key=lambda r:r['basin_index']);best=max(results,key=lambda r:r['score'])
 out={'method':'exact-public367-support-subset-core-prize-closure','public_sets':len(corpus['sets']),'distinct_blocker_basins':len(jobs),'workers':workers,'seed_stats':seed_stats,'results':results,'best_score':best['score'],'candidate_368':best['score']>=TARGET}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 if best['score']>=TARGET:
  S=best['points5'][:TARGET]
  if len(S)!=TARGET or not independent(S):raise RuntimeError('target replay')
  a.certificate.parent.mkdir(parents=True,exist_ok=True);a.certificate.write_text(json.dumps({'points5':S},separators=(',',':'))+'\n')
 print('SUMMARY',json.dumps({k:v for k,v in out.items() if k not in ('seed_stats','results')},sort_keys=True),flush=True)
if __name__=='__main__':main()
