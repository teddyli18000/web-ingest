#!/usr/bin/env python3
"""Exact 50-branch 368 decision with stabilizer-orbit pigeonhole cuts."""
from __future__ import annotations
import argparse,gzip,itertools,json
from pathlib import Path
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
 s=Minicard();edges=impl=0;hist={}
 for v in outside:
  supp=[]
  for u in neigh(v):
   if u in C:supp.append(u)
   elif u in O and u>v:s.add_clause([-x[v],-x[u]]);edges+=1
  hist[len(supp)]=hist.get(len(supp),0)+1
  for c in supp:s.add_clause([-x[v],b[c]]);impl+=1
 sel_lit=lambda v:(-b[v] if v in C else x[v])
 add_atleast(s,[sel_lit(v) for v in range(U)],TARGET)
 add_atleast(s,[b[c] for c in core],4)
 s.add_clause([sel_lit(0)])
 types=orbit_types();by={t:[] for t in types}
 for v in range(1,U):
  t=dtype(v)
  if t in by:by[t].append(v)
 if sum(map(len,by.values()))!=U-243:raise RuntimeError(('orbit partition',sum(map(len,by.values()))))
 # Native conditional occupancy: q_j == not selector. With selector off the
 # eight q_j make the >=8 constraint tautological; with selector on they are
 # all false and the orbit itself must supply eight selected literals.
 top=bb+len(core)-1;selectors=[];reps=[];gate_clauses=0
 for t in types:
  rep=enc(t)
  if dtype(rep)!=t or rep not in by[t]:raise RuntimeError(('rep',t,rep))
  top+=1;sv=top;selectors.append(sv);reps.append(rep);gates=[]
  for _ in range(OCC):
   top+=1;q=top;gates.append(q);s.add_clause([q,sv]);s.add_clause([-q,-sv]);gate_clauses+=2
  add_atleast(s,[sel_lit(v) for v in by[t]]+gates,OCC)
  s.add_clause([-sv,sel_lit(rep)]);gate_clauses+=1
 for i in range(len(selectors)):
  for j in range(i+1,len(selectors)):s.add_clause([-selectors[i],-selectors[j]]);gate_clauses+=1
 assigned=[i for i in range(50) if i%a.shards==a.shard]
 setup={'method':'exact-c7p5-368-core-prize-orbit-pigeonhole-native','ambient':U,'core_size':CORE,'outside':len(outside),'outside_conflict_edges':edges,'support_implications':impl,'support_histogram':{str(k):v for k,v in sorted(hist.items())},'orbit_count':50,'occupancy_lower_bound':OCC,'gate_and_selector_clauses':gate_clauses,'shard':a.shard,'shards':a.shards,'assigned':len(assigned),'certified_min_core_blockers':4,'core_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'}
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
