#!/usr/bin/env python3
"""Exact nonuniform zero-stabilizer orbit cover for a hypothetical 368-set in C7^5.

After translating one selected word to 00000, the remaining 367 selected words
lie in 50 nonconfusable orbits classified by sorted cyclic-distance multisets.
Three orbit capacities are elementary:

* (0,0,0,0,3): five disjoint K2, alpha=5;
* (0,3,3,3,3): five disjoint K16, alpha=5;
* (3,3,3,3,3): K32, alpha=1.

So those three never need a branch with occupancy >=8.  Among the remaining 47
orbits, assign threshold 9 to 26 (chosen deterministically as the largest orbit
sizes, purely as a solver heuristic) and threshold 8 to the other 21.  If all
47 branches fail, total selected nonzero vertices are at most

    5 + 5 + 1 + 26*8 + 21*7 = 366,

contradicting the required 367.  Thus the 47 branches cover every 368-set.
For a crowded orbit, the zero stabilizer maps one selected point to the canonical
representative, so each branch additionally fixes that representative selected.

The 315-core prize identity and the independently certified target cut of at
least four activated core blockers are encoded exactly.  Conditional orbit
occupancy constraints are native MiniCard lower bounds gated by NOT(selector).
"""
from __future__ import annotations
import argparse,gzip,itertools,json,math
from collections import Counter
from pathlib import Path
from pysat.solvers import Minicard
Q=7;D=5;U=Q**D;CORE=315;TARGET=368;POW=tuple(Q**i for i in range(D))
LOW_CAP={(0,0,0,0,3):5,(0,3,3,3,3):5,(3,3,3,3,3):1}
def dec(v):return tuple((v//POW[i])%Q for i in range(D))
def enc(w):return sum(int(w[i])*POW[i] for i in range(D))
def neigh(v):
 d=dec(v)
 for z in itertools.product((-1,0,1),repeat=D):
  if all(t==0 for t in z):continue
  yield enc(tuple((d[i]+z[i])%Q for i in range(D)))
def independent(S):
 S=set(S);return all(u not in S for v in S for u in neigh(v))
def dtype(v):return tuple(sorted(min(x,7-x) for x in dec(v)))
def orbit_types():
 a=[t for t in itertools.combinations_with_replacement(range(4),D) if max(t)>=2]
 if len(a)!=50:raise RuntimeError(len(a))
 return a
def orbit_size(t):
 n=math.factorial(D)
 for c in Counter(t).values():n//=math.factorial(c)
 return n*(2**sum(x!=0 for x in t))
def add_atleast(s,lits,k):
 if not 0<=k<=len(lits):raise ValueError((len(lits),k))
 s.add_atmost([-z for z in lits],len(lits)-k)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);a=ap.parse_args()
 if a.shards<1 or not 0<=a.shard<a.shards:raise SystemExit('bad shard')
 with gzip.open(a.c7five_root/'data'/'core-overlap.json.gz','rt') as f:bundle=json.load(f)
 core=tuple(sorted(map(int,bundle['core'])));C=set(core)
 if len(core)!=CORE or len(C)!=CORE or not independent(C):raise RuntimeError('core')
 outside=tuple(v for v in range(U) if v not in C);O=set(outside);x={v:i+1 for i,v in enumerate(outside)};bb=len(outside)+1;b={c:bb+i for i,c in enumerate(core)}
 s=Minicard();edges=impl=0
 for v in outside:
  for u in neigh(v):
   if u in C:s.add_clause([-x[v],b[u]]);impl+=1
   elif u in O and u>v:s.add_clause([-x[v],-x[u]]);edges+=1
 sel=lambda v:(-b[v] if v in C else x[v])
 add_atleast(s,[sel(v) for v in range(U)],TARGET);add_atleast(s,[b[c] for c in core],4);s.add_clause([sel(0)])
 types=orbit_types();by={t:[] for t in types}
 for v in range(1,U):
  t=dtype(v)
  if t in by:by[t].append(v)
 if sum(map(len,by.values()))!=U-243:raise RuntimeError(('partition',sum(map(len,by.values()))))
 regular=[t for t in types if t not in LOW_CAP]
 if len(regular)!=47:raise RuntimeError(len(regular))
 # Largest 26 get the stronger threshold 9. This choice does not affect the
 # coverage proof; it is a deterministic solver heuristic.
 strong=set(sorted(regular,key=lambda t:(-orbit_size(t),t))[:26])
 threshold={t:(9 if t in strong else 8) for t in regular}
 failure_cap=sum(LOW_CAP.values())+sum(threshold[t]-1 for t in regular)
 if failure_cap!=366:raise RuntimeError(('cover arithmetic',failure_cap))
 top=bb+len(core)-1;selectors=[];meta=[]
 for t in regular:
  thr=threshold[t];rep=enc(t);top+=1;sv=top;selectors.append(sv);gates=[]
  for _ in range(thr):
   top+=1;q=top;gates.append(q);s.add_clause([q,sv]);s.add_clause([-q,-sv])
  add_atleast(s,[sel(v) for v in by[t]]+gates,thr);s.add_clause([-sv,sel(rep)])
  meta.append((t,rep,thr,sv))
 for i in range(len(selectors)):
  for j in range(i+1,len(selectors)):s.add_clause([-selectors[i],-selectors[j]])
 assigned=[i for i in range(len(meta)) if i%a.shards==a.shard]
 setup={'method':'exact-c7p5-368-nonuniform-orbit-pigeonhole','orbit_count_total':50,'analytic_low_caps':{','.join(map(str,k)):v for k,v in LOW_CAP.items()},'active_branches':47,'threshold9_count':26,'threshold8_count':21,'all-fail_nonzero_cap':failure_cap,'shard':a.shard,'shards':a.shards,'assigned':len(assigned),'outside_edges':edges,'support_implications':impl,'core_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
 print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
 rows=[];model=hit=None
 for k,i in enumerate(assigned):
  t,rep,thr,sv=meta[i];print('ORBIT',k+1,'/',len(assigned),'global',i,'type',t,'size',len(by[t]),'threshold',thr,'rep',rep,flush=True)
  sat=s.solve(assumptions=[sv]);row={'branch_index':i,'type':list(t),'orbit_size':len(by[t]),'threshold':thr,'representative':rep,'sat':bool(sat)};rows.append(row);print('ORBIT_RESULT',json.dumps(row,sort_keys=True),flush=True)
  if sat:model=s.get_model();hit=row;break
 s.delete();out={'setup':setup,'rows':rows,'candidate':False,'sat_branch':hit}
 if model is not None:
  pos={z for z in model if z>0};Y={v for v in outside if x[v] in pos};blocked=set()
  for v in Y:blocked.update(u for u in neigh(v) if u in C)
  completed=Y|(C-blocked);t=tuple(hit['type']);occ=sum(dtype(v)==t for v in completed)
  if len(completed)<TARGET or not independent(completed) or 0 not in completed or len(blocked)<4 or hit['representative'] not in completed or occ<hit['threshold']:raise RuntimeError(('replay',len(completed),len(blocked),occ))
  out.update(candidate=True,completed_size=len(completed),activated_core_blockers=len(blocked),orbit_occupancy=occ,points5=sorted(completed)[:TARGET])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('RESULT',json.dumps({k:v for k,v in out.items() if k not in ('points5','rows')},sort_keys=True),flush=True)
if __name__=='__main__':main()
