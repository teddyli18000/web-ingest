#!/usr/bin/env python3
"""Exact 50-branch 368 decision with stabilizer-orbit pigeonhole cuts.

After translating one selected word to 00000, the remaining 367 selected words
fall into 50 nonconfusable orbits under the zero stabilizer (coordinate
permutations and independent sign reversals).  Therefore at least one orbit
contains >= ceil(367/50) = 8 selected words.  For such an orbit, map one of its
selected words to the canonical representative using the same stabilizer.

Thus every 368-set has an automorphic image satisfying one of 50 branches:
  * 00000 selected;
  * the branch's canonical representative selected;
  * at least 8 selected words from that entire orbit.

All 50 conditional cardinality encodings live in one MiniCard instance behind
selector literals.  An at-most-one selector constraint means an assumption on
one selector disables every other orbit encoding, while learned clauses remain
reusable across branch solves.
"""
from __future__ import annotations
import argparse,gzip,itertools,json
from pathlib import Path
from pysat.card import CardEnc,EncType
from pysat.solvers import Minicard
Q=7;D=5;U=Q**D;CORE=315;TARGET=368;OCC=8;POW=tuple(Q**i for i in range(D))
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
def main():
 ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);a=ap.parse_args()
 if a.shards<1 or not 0<=a.shard<a.shards:raise SystemExit('bad shard')
 with gzip.open(a.c7five_root/'data'/'core-overlap.json.gz','rt') as f:bundle=json.load(f)
 core=tuple(sorted(map(int,bundle['core'])));C=set(core)
 if len(core)!=CORE or len(C)!=CORE or not independent(C):raise RuntimeError('core')
 outside=tuple(v for v in range(U) if v not in C);O=set(outside);x={v:i+1 for i,v in enumerate(outside)};bb=len(outside)+1;b={c:bb+i for i,c in enumerate(core)}
 s=Minicard();edges=impl=0;hist={}
 for v in outside:
  supp=[]
  for u in neigh(v):
   if u in C:supp.append(u)
   elif u in O and u>v:s.add_clause([-x[v],-x[u]]);edges+=1
  hist[len(supp)]=hist.get(len(supp),0)+1
  for c in supp:s.add_clause([-x[v],b[c]]);impl+=1
 sel_lit=lambda v:(-b[v] if v in C else x[v])
 s.add_atleast([sel_lit(v) for v in range(U)],TARGET)
 s.add_atleast([b[c] for c in core],4)
 s.add_clause([sel_lit(0)])
 types=orbit_types();by={t:[] for t in types}
 for v in range(1,U):
  t=dtype(v)
  if t in by:by[t].append(v)
 if sum(map(len,by.values()))!=U-243:raise RuntimeError(('orbit partition',sum(map(len,by.values()))))
 # Build all conditional orbit occupancy constraints.  Selectors are positive
 # fresh variables; only one is permitted true.
 top=bb+len(core)-1;selectors=[];reps=[];clause_count=0
 for t in types:
  rep=enc(t)
  if dtype(rep)!=t or rep not in by[t]:raise RuntimeError(('rep',t,rep))
  top+=1;sv=top;selectors.append(sv);reps.append(rep)
  cnf=CardEnc.atleast(lits=[sel_lit(v) for v in by[t]],bound=OCC,top_id=top,encoding=EncType.seqcounter);top=cnf.nv
  for cl in cnf.clauses:s.add_clause([-sv]+cl);clause_count+=1
  s.add_clause([-sv,sel_lit(rep)]);clause_count+=1
 for i in range(len(selectors)):
  for j in range(i+1,len(selectors)):s.add_clause([-selectors[i],-selectors[j]]);clause_count+=1
 assigned=[i for i in range(50) if i%a.shards==a.shard]
 setup={'method':'exact-c7p5-368-core-prize-orbit-pigeonhole','ambient':U,'core_size':CORE,'outside':len(outside),'outside_conflict_edges':edges,'support_implications':impl,'support_histogram':{str(k):v for k,v in sorted(hist.items())},'orbit_count':50,'occupancy_lower_bound':OCC,'conditional_orbit_clauses':clause_count,'shard':a.shard,'shards':a.shards,'assigned':len(assigned),'certified_min_core_blockers':4,'core_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
 print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
 rows=[];model=None;hit=None
 for k,i in enumerate(assigned):
  print('ORBIT',k+1,'/',len(assigned),'global',i,'type',types[i],'size',len(by[types[i]]),'rep',reps[i],flush=True)
  sat=s.solve(assumptions=[selectors[i]]);row={'orbit_index':i,'type':list(types[i]),'orbit_size':len(by[types[i]]),'representative':reps[i],'sat':bool(sat)};rows.append(row);print('ORBIT_RESULT',json.dumps(row,sort_keys=True),flush=True)
  if sat:model=s.get_model();hit=row;break
 s.delete();out={'setup':setup,'rows':rows,'candidate':False,'sat_orbit':hit}
 if model is not None:
  pos={z for z in model if z>0};Y={v for v in outside if x[v] in pos};blocked=set()
  for v in Y:blocked.update(u for u in neigh(v) if u in C)
  completed=Y|(C-blocked);t=tuple(hit['type']);occ=sum(dtype(v)==t for v in completed)
  if len(completed)<TARGET or not independent(completed) or 0 not in completed or len(blocked)<4 or hit['representative'] not in completed or occ<OCC:raise RuntimeError(('replay',len(completed),len(blocked),occ))
  out.update(candidate=True,completed_size=len(completed),activated_core_blockers=len(blocked),selected_outside=len(Y),orbit_occupancy=occ,points5=sorted(completed)[:TARGET])
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print('RESULT',json.dumps({k:v for k,v in out.items() if k not in ('points5','rows')},sort_keys=True),flush=True)
if __name__=='__main__':main()
