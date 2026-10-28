#!/usr/bin/env python3
"""Propagation-strengthened exact m=219 r=3 fixed-A/B cover.

Same A26/B116 gluing as m219_r3_fixed_ab.py, but with two facts made explicit:
only the eight degree sequences proved to require an r=3 anchor are selected,
and e(A,B)=66 is encoded directly from 219=11+26+116+e(A,B).
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
from pysat.card import CardEnc,EncType
from pysat.formula import IDPool
from pysat.solvers import Solver
import m219_n11_6_degree3_fixed_ab as core
NA,NB=11,24
SEQS=({11:7,12:17,13:11,14:1},{11:7,12:18,13:9,14:2},{11:8,12:15,13:12,14:1},{11:9,12:12,13:15},{11:9,12:13,13:13,14:1},{11:10,12:10,13:16},{11:11,12:8,13:17},{11:12,12:6,13:18})
ORIGINAL_INDICES=(1,2,4,5,6,7,8,9);CLASSES=(11,12,13,14)
def add_exact(s,lits,bound,pool,guard=None):
 if not 0<=bound<=len(lits):s.add_clause([] if guard is None else [guard]);return 1
 cnf=CardEnc.equals(lits=lits,bound=bound,vpool=pool,encoding=EncType.seqcounter)
 for cl in cnf.clauses:s.add_clause(list(cl)+([] if guard is None else [guard]))
 return len(cnf.clauses)
def solve(cat,ao,bo,solver_name,summary,output):
 ag6,A,ae=core.base.select_record(cat/'A26.g6',ao,NA);bg6,B,be=core.base.select_record(cat/'B116.g6',bo,NB)
 core.validate_A(A);core.validate_B(B);assert (ae,be)==(26,116);da,db=core.base.degrees(A),core.base.degrees(B)
 x=[[a*NB+b+1 for b in range(NB)] for a in range(NA)];nxt=NA*NB+1
 qA={(a,d):nxt+a*len(CLASSES)+i for a in range(NA) for i,d in enumerate(CLASSES)};nxt+=NA*len(CLASSES)
 qB={(b,d):nxt+b*len(CLASSES)+i for b in range(NB) for i,d in enumerate(CLASSES)};nxt+=NB*len(CLASSES)
 z=list(range(nxt,nxt+len(SEQS)));nxt+=len(SEQS);pool=IDPool(start_from=nxt);counts={'cross_total':0,'labels':0,'degree':0,'k4':0,'i6':0}
 with Solver(name=solver_name) as s:
  counts['cross_total']+=add_exact(s,[x[a][b] for a in range(NA) for b in range(NB)],66,pool);counts['labels']+=add_exact(s,z,1,pool)
  for a in range(NA):counts['labels']+=add_exact(s,[qA[a,d] for d in CLASSES],1,pool)
  for b in range(NB):counts['labels']+=add_exact(s,[qB[b,d] for d in CLASSES],1,pool)
  for si,seq in enumerate(SEQS):
   for d in CLASSES:counts['labels']+=add_exact(s,[qA[a,d] for a in range(NA)]+[qB[b,d] for b in range(NB)],seq.get(d,0)-(1 if d==11 else 0),pool,guard=-z[si])
  for a in range(NA):
   for d in CLASSES:counts['degree']+=add_exact(s,x[a],d-1-da[a],pool,guard=-qA[a,d])
  for b in range(NB):
   col=[x[a][b] for a in range(NA)]
   for d in CLASSES:counts['degree']+=add_exact(s,col,d-db[b],pool,guard=-qB[b,d])
  sub=core.subsets
  for a in range(NA):
   for bs in sub(B,3,True):s.add_clause([-x[a][b] for b in bs]);counts['k4']+=1
  for aa in sub(A,2,True):
   for bb in sub(B,2,True):s.add_clause([-x[a][b] for a in aa for b in bb]);counts['k4']+=1
  for aa in sub(A,5,False):
   for b in range(NB):s.add_clause([x[a][b] for a in aa]);counts['i6']+=1
  for aa in sub(A,4,False):
   for bb in sub(B,2,False):s.add_clause([x[a][b] for a in aa for b in bb]);counts['i6']+=1
  for aa in sub(A,3,False):
   for bb in sub(B,3,False):s.add_clause([x[a][b] for a in aa for b in bb]);counts['i6']+=1
  for aa in sub(A,2,False):
   for bb in sub(B,4,False):s.add_clause([x[a][b] for a in aa for b in bb]);counts['i6']+=1
  sat=s.solve();model=set(v for v in (s.get_model() or []) if v>0)
 result={'campaign':'m219-r3-fixedAB-v2','a_ordinal':ao,'b_ordinal':bo,'a_graph6':ag6,'b_graph6':bg6,'status':'SAT' if sat else 'UNSAT','solver':solver_name,'clauses_by_kind':counts,'max_var':pool.top};summary.parent.mkdir(parents=True,exist_ok=True)
 if not sat:summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 20
 si=next(i for i,v in enumerate(z) if v in model);seq=SEQS[si];result.update(sequence_selector=si,original_sequence_index=ORIGINAL_INDICES[si],degree_sequence=seq)
 rows=[['0']*36 for _ in range(36)]
 for a in range(NA):rows[0][1+a]=rows[1+a][0]='1'
 for i in range(NA):
  for j in range(i+1,NA):
   if (A[i]>>j)&1:rows[1+i][1+j]=rows[1+j][1+i]='1'
 for i in range(NB):
  for j in range(i+1,NB):
   if (B[i]>>j)&1:rows[12+i][12+j]=rows[12+j][12+i]='1'
 for a in range(NA):
  for b in range(NB):
   if x[a][b] in model:rows[1+a][12+b]=rows[12+b][1+a]='1'
 rr=[''.join(r) for r in rows]
 for vs in itertools.combinations(range(36),4):assert not all(rr[u][v]=='1' for u,v in itertools.combinations(vs,2))
 for vs in itertools.combinations(range(36),6):assert not all(rr[u][v]=='0' for u,v in itertools.combinations(vs,2))
 want=[]
 for d,n in seq.items():want += [d]*n
 assert sorted(r.count('1') for r in rr)==sorted(want);assert sum(rr[u].count('1') for u in range(1,12))==129;assert sum(rr[1+a][12+b]=='1' for a in range(NA) for b in range(NB))==66
 output.write_text(json.dumps({'adjacency':rr},indent=2)+'\n');summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return 0
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--catalog-dir',type=Path);ap.add_argument('--a-ordinal',type=int);ap.add_argument('--b-ordinal',type=int);ap.add_argument('--summary',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--solver',default='cadical195');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 if a.self_test:assert ORIGINAL_INDICES==(1,2,4,5,6,7,8,9) and all(sum(s.values())==36 and sum(d*n for d,n in s.items())==438 for s in SEQS);print('m219 r3 fixed-AB v2 self-test ok');return 0
 return solve(a.catalog_dir,a.a_ordinal,a.b_ordinal,a.solver,a.summary,a.output)
if __name__=='__main__':raise SystemExit(main())
