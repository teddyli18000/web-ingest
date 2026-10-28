#!/usr/bin/env python3
"""Eight-branch exact cover for the final m=219 r=4 anchor cases.

After excluding r=3 anchors, the exact degree-class relaxation forces an r=4
anchor in each of the only two not-r3-forced degree sequences:
  11^7 12^16 13^13 and 11^8 12^14 13^14.
For a degree-11 anchor r=4 gives S=128 and e(B)-e(A)=91, hence only
(A25,B116) or (A26,B117).

There are 6 A25 and 2 A26 graphs.  Instead of branching over the 9 B116 or 90
B117 isomorphism types, each fixed-A SAT instance contains a one-hot selector
for the whole B catalogue and 276 B-edge variables conditionally fixed by that
selector.  Thus the complete cover has only 6+2=8 solver branches.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
from pysat.card import CardEnc,EncType
from pysat.formula import IDPool
from pysat.solvers import Solver
import m219_n11_6_degree3_fixed_ab as core

NA,NB=11,24
SEQS=({11:7,12:16,13:13},{11:8,12:14,13:14})
CLASSES=(11,12,13)

def add_exact(s,lits,bound,pool,guard=None):
 if not 0<=bound<=len(lits):s.add_clause([] if guard is None else [guard]);return 1
 cnf=CardEnc.equals(lits=lits,bound=bound,vpool=pool,encoding=EncType.seqcounter)
 for cl in cnf.clauses:s.add_clause(list(cl)+([] if guard is None else [guard]))
 return len(cnf.clauses)

def load_all(path,n,e):
 out=[]
 for _,g,adj,ee in core.base.iter_g6(path):
  assert len(adj)==n and ee==e;(core.validate_B(adj) if n==24 else core.validate_A(adj));out.append((g,adj))
 return out

def solve(cat,case,ao,solver_name,summary,output):
 if case==0:ap,bp,ae,be,expected=cat/'A25.g6',cat/'B116.g6',25,116,9
 else:ap,bp,ae,be,expected=cat/'A26.g6',cat/'B117.g6',26,117,90
 ag6,A,aedges=core.base.select_record(ap,ao,NA);core.validate_A(A);assert aedges==ae
 Bs=load_all(bp,NB,be);assert len(Bs)==expected,len(Bs);da=core.base.degrees(A)
 # B-edge vars, then A-B cross vars.
 y={};nxt=1
 for i in range(NB):
  for j in range(i+1,NB):y[i,j]=nxt;nxt+=1
 x=[[0]*NB for _ in range(NA)]
 for a in range(NA):
  for b in range(NB):x[a][b]=nxt;nxt+=1
 zB=list(range(nxt,nxt+len(Bs)));nxt+=len(Bs)
 qA={(a,d):nxt+a*len(CLASSES)+i for a in range(NA) for i,d in enumerate(CLASSES)};nxt+=NA*len(CLASSES)
 qB={(b,d):nxt+b*len(CLASSES)+i for b in range(NB) for i,d in enumerate(CLASSES)};nxt+=NB*len(CLASSES)
 zS=list(range(nxt,nxt+2));nxt+=2;pool=IDPool(start_from=nxt)
 counts={'catalog_select':0,'labels':0,'degree':0,'k4':0,'i6':0}
 with Solver(name=solver_name) as s:
  counts['catalog_select']+=add_exact(s,zB,1,pool)
  for gi,(_,B) in enumerate(Bs):
   z=zB[gi]
   for i in range(NB):
    for j in range(i+1,NB):s.add_clause([-z,y[i,j] if ((B[i]>>j)&1) else -y[i,j]]);counts['catalog_select']+=1
  counts['labels']+=add_exact(s,zS,1,pool)
  for a in range(NA):counts['labels']+=add_exact(s,[qA[a,d] for d in CLASSES],1,pool)
  for b in range(NB):counts['labels']+=add_exact(s,[qB[b,d] for d in CLASSES],1,pool)
  for si,seq in enumerate(SEQS):
   for d in CLASSES:
    target=seq.get(d,0)-(1 if d==11 else 0)
    counts['labels']+=add_exact(s,[qA[a,d] for a in range(NA)]+[qB[b,d] for b in range(NB)],target,pool,guard=-zS[si])
  for a in range(NA):
   for d in CLASSES:counts['degree']+=add_exact(s,x[a],d-1-da[a],pool,guard=-qA[a,d])
  for b in range(NB):
   inc=[x[a][b] for a in range(NA)]+[y[min(b,c),max(b,c)] for c in range(NB) if c!=b]
   for d in CLASSES:counts['degree']+=add_exact(s,inc,d,pool,guard=-qB[b,d])
  # Mixed K4 constraints: A is triangle-free and selected B is already R(4,5).
  for a in range(NA):
   for bs in itertools.combinations(range(NB),3):
    b0,b1,b2=bs;s.add_clause([-y[min(b0,b1),max(b0,b1)],-y[min(b0,b2),max(b0,b2)],-y[min(b1,b2),max(b1,b2)]]+[-x[a][b] for b in bs]);counts['k4']+=1
  for aa in core.subsets(A,2,True):
   for b0,b1 in itertools.combinations(range(NB),2):s.add_clause([-y[b0,b1]]+[-x[a][b] for a in aa for b in (b0,b1)]);counts['k4']+=1
  # Mixed independent-6 constraints; selected B has no independent 5-set.
  for aa in core.subsets(A,5,False):
   for b in range(NB):s.add_clause([x[a][b] for a in aa]);counts['i6']+=1
  for aa in core.subsets(A,4,False):
   for b0,b1 in itertools.combinations(range(NB),2):s.add_clause([y[b0,b1]]+[x[a][b] for a in aa for b in (b0,b1)]);counts['i6']+=1
  for aa in core.subsets(A,3,False):
   for bs in itertools.combinations(range(NB),3):
    bed=[y[min(u,v),max(u,v)] for u,v in itertools.combinations(bs,2)];s.add_clause(bed+[x[a][b] for a in aa for b in bs]);counts['i6']+=1
  for aa in core.subsets(A,2,False):
   for bs in itertools.combinations(range(NB),4):
    bed=[y[min(u,v),max(u,v)] for u,v in itertools.combinations(bs,2)];s.add_clause(bed+[x[a][b] for a in aa for b in bs]);counts['i6']+=1
  sat=s.solve();model=set(v for v in (s.get_model() or []) if v>0)
 result={'campaign':'m219-r4-Bselector','case':case,'a_ordinal':ao,'a_graph6':ag6,'a_edges':ae,'b_edges':be,'b_catalog_count':len(Bs),
         'status':'SAT' if sat else 'UNSAT','solver':solver_name,'clauses_by_kind':counts,'max_var':pool.top}
 summary.parent.mkdir(parents=True,exist_ok=True)
 if not sat:summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 20
 bi=next(i for i,z in enumerate(zB) if z in model);si=next(i for i,z in enumerate(zS) if z in model);bg6,B=Bs[bi];seq=SEQS[si]
 result.update(b_ordinal=bi,b_graph6=bg6,sequence_index=si,degree_sequence=seq)
 rows=[['0']*36 for _ in range(36)]
 for a in range(NA):rows[0][1+a]=rows[1+a][0]='1'
 for i in range(NA):
  for j in range(i+1,NA):
   if (A[i]>>j)&1:rows[1+i][1+j]=rows[1+j][1+i]='1'
 for i in range(NB):
  for j in range(i+1,NB):
   if y[i,j] in model:rows[12+i][12+j]=rows[12+j][12+i]='1'
 for a in range(NA):
  for b in range(NB):
   if x[a][b] in model:rows[1+a][12+b]=rows[12+b][1+a]='1'
 rr=[''.join(r) for r in rows]
 for vs in itertools.combinations(range(36),4):assert not all(rr[u][v]=='1' for u,v in itertools.combinations(vs,2))
 for vs in itertools.combinations(range(36),6):assert not all(rr[u][v]=='0' for u,v in itertools.combinations(vs,2))
 want=[]
 for d,n in seq.items():want += [d]*n
 assert sorted(r.count('1') for r in rr)==sorted(want);assert sum(rr[u].count('1') for u in range(1,12))==128
 output.write_text(json.dumps({'adjacency':rr},indent=2)+'\n');summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return 0

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--catalog-dir',type=Path);ap.add_argument('--case',type=int,choices=(0,1));ap.add_argument('--a-ordinal',type=int);ap.add_argument('--summary',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--solver',default='cadical195');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 if a.self_test:assert all(sum(s.values())==36 and sum(d*n for d,n in s.items())==438 for s in SEQS);print('r4 B-selector self-test ok');return 0
 return solve(a.catalog_dir,a.case,a.a_ordinal,a.solver,a.summary,a.output)
if __name__=='__main__':raise SystemExit(main())
