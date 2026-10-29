#!/usr/bin/env python3
"""Exact SAT for arbitrary regrowth of selected vertices of a fixed Ramsey near-miss."""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path

def load(path):
 d=json.load(open(path)); r=d['adjacency']; n=len(r)
 assert all(len(x)==n for x in r) and all(r[i][i]=='0' for i in range(n))
 assert all(r[i][j]==r[j][i] for i in range(n) for j in range(n))
 return r

def verify(r):
 n=len(r)
 for vs in itertools.combinations(range(n),4):
  if all(r[a][b]=='1' for a,b in itertools.combinations(vs,2)): return False,('K4',vs)
 for vs in itertools.combinations(range(n),6):
  if all(r[a][b]=='0' for a,b in itertools.combinations(vs,2)): return False,('I6',vs)
 return True,None

def generate(src, removed, cnf, meta):
 r=load(src); n=len(r); R=set(removed); assert len(R)==len(removed)
 var={}; nxt=1
 for i in range(n):
  for j in range(i+1,n):
   if i in R or j in R: var[(i,j)]=nxt; nxt+=1
 cls=[]; kinds={'k4':0,'i6':0}
 for vs in itertools.combinations(range(n),4):
  lits=[]; sat=False
  for a,b in itertools.combinations(vs,2):
   e=(min(a,b),max(a,b))
   if e in var: lits.append(-var[e])
   elif r[a][b]=='0': sat=True; break
  if not sat:
   if not lits: raise ValueError(f'fixed core has K4 {vs}')
   cls.append(lits); kinds['k4']+=1
 for vs in itertools.combinations(range(n),6):
  lits=[]; sat=False
  for a,b in itertools.combinations(vs,2):
   e=(min(a,b),max(a,b))
   if e in var: lits.append(var[e])
   elif r[a][b]=='1': sat=True; break
  if not sat:
   if not lits: raise ValueError(f'fixed core has I6 {vs}')
   cls.append(lits); kinds['i6']+=1
 cnf.parent.mkdir(parents=True,exist_ok=True)
 with cnf.open('w') as f:
  f.write(f'p cnf {nxt-1} {len(cls)}\n')
  for c in cls:f.write(' '.join(map(str,c))+' 0\n')
 md={'source':str(src),'removed':removed,'n':n,'variables':nxt-1,'clauses':len(cls),'clauses_by_kind':kinds,
     'var_edges':{str(v):list(e) for e,v in var.items()}}
 meta.write_text(json.dumps(md,indent=2,sort_keys=True)+'\n'); print(json.dumps(md,sort_keys=True)); return md

def parse_model(path):
 true=set(); sat=False
 for line in path.read_text(errors='replace').splitlines():
  if line.startswith('s ') and 'SATISFIABLE' in line and 'UNSATISFIABLE' not in line:sat=True
  if line.startswith('v '):
   for t in line.split()[1:]:
    try:x=int(t)
    except:continue
    if x>0:true.add(x)
 return sat,true

def decode(src,meta,solver,out):
 r=[list(x) for x in load(src)]; md=json.load(open(meta)); sat,true=parse_model(solver)
 if not sat: raise SystemExit('solver log is not SAT')
 for sv,e in md['var_edges'].items():
  i,j=e; val='1' if int(sv) in true else '0'; r[i][j]=r[j][i]=val
 rr=[''.join(x) for x in r]; ok,bad=verify(rr); assert ok,bad
 out.write_text(json.dumps({'adjacency':rr},indent=2)+'\n'); print(json.dumps({'valid':True,'edges':sum(x.count('1') for x in rr)//2}))

def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
 g=sub.add_parser('generate');g.add_argument('source',type=Path);g.add_argument('cnf',type=Path);g.add_argument('meta',type=Path);g.add_argument('vertices',nargs='+',type=int)
 d=sub.add_parser('decode');d.add_argument('source',type=Path);d.add_argument('meta',type=Path);d.add_argument('solver',type=Path);d.add_argument('output',type=Path)
 v=sub.add_parser('verify');v.add_argument('candidate',type=Path)
 a=ap.parse_args()
 if a.cmd=='generate': generate(a.source,a.vertices,a.cnf,a.meta); return
 if a.cmd=='decode': decode(a.source,a.meta,a.solver,a.output); return
 r=load(a.candidate);ok,bad=verify(r);print(json.dumps({'valid':ok,'bad':bad}));raise SystemExit(0 if ok else 1)
if __name__=='__main__':main()
