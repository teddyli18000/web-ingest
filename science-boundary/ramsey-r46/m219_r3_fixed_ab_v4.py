#!/usr/bin/env python3
"""Exact m=219 r=3 fixed-A/B SAT with k=2 column-domain closure.

Extends v3 by exposing exact structure of minimum A-transversals.  For either
A26 graph, every B cross-neighborhood has size at least 2.  The size-2
transversals form K_{5,4} (A ordinal 0) or K_{4,4} (A ordinal 1).  Therefore:

* with e(A,B)=66 across 24 B columns, at least 6 columns have cross-degree 2;
* at most 12 columns can have cross-degree 2, because the four vertices on a
  4-side each support a clique in B and B is K4-free;
* if two B vertices are nonadjacent and both have cross-degree 2, their two
  A-transversal edges are vertex-disjoint.  We add this as direct endpoint
  clauses rather than relying on long mixed independent-set clauses.

All added constraints are consequences of the original exact Ramsey gluing.
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
ORIGINAL_INDICES=(1,2,4,5,6,7,8,9)
CLASSES=(11,12,13,14)

def add_card(s,lits,bound,pool,kind='eq',guard=None):
    if not 0 <= bound <= len(lits):
        s.add_clause([] if guard is None else [guard]);return 1
    if kind=='eq': cnf=CardEnc.equals(lits=lits,bound=bound,vpool=pool,encoding=EncType.seqcounter)
    elif kind=='atleast': cnf=CardEnc.atleast(lits=lits,bound=bound,vpool=pool,encoding=EncType.seqcounter)
    elif kind=='atmost': cnf=CardEnc.atmost(lits=lits,bound=bound,vpool=pool,encoding=EncType.seqcounter)
    else: raise ValueError(kind)
    for cl in cnf.clauses:s.add_clause(list(cl)+([] if guard is None else [guard]))
    return len(cnf.clauses)

def independent_sets(A,k): return core.subsets(A,k,False)

def k2_structure(A):
    I5=independent_sets(A,5)
    masks=[]
    for u,v in itertools.combinations(range(NA),2):
        m=(1<<u)|(1<<v)
        if all(m & J for J in I5):masks.append(m)
    assert len(masks) in (16,20),len(masks)
    # Find a 4-set D meeting every minimum transversal in exactly one endpoint.
    D=None
    for C in itertools.combinations(range(NA),4):
        cm=sum(1<<u for u in C)
        if all((m&cm).bit_count()==1 for m in masks):D=tuple(C);break
    assert D is not None
    # All masks are edges of a complete bipartite graph between used vertices.
    used=0
    for m in masks:used|=m
    left=[u for u in range(NA) if (used>>u)&1 and u not in D]
    assert len(masks)==len(D)*len(left),(D,left,len(masks))
    assert {(u,v) if u<v else (v,u) for u in left for v in D}=={
        tuple(i for i in range(NA) if (m>>i)&1) for m in masks}
    return masks,D,tuple(left)

def solve(cat,ao,bo,solver_name,summary,output):
    ag6,A,ae=core.base.select_record(cat/'A26.g6',ao,NA)
    bg6,B,be=core.base.select_record(cat/'B116.g6',bo,NB)
    core.validate_A(A);core.validate_B(B);assert (ae,be)==(26,116)
    da,db=core.base.degrees(A),core.base.degrees(B)
    k2masks,D,left=k2_structure(A)
    x=[[a*NB+b+1 for b in range(NB)] for a in range(NA)];nxt=NA*NB+1
    qA={(a,d):nxt+a*len(CLASSES)+i for a in range(NA) for i,d in enumerate(CLASSES)};nxt+=NA*len(CLASSES)
    qB={(b,d):nxt+b*len(CLASSES)+i for b in range(NB) for i,d in enumerate(CLASSES)};nxt+=NB*len(CLASSES)
    z=list(range(nxt,nxt+len(SEQS)));nxt+=len(SEQS);pool=IDPool(start_from=nxt)
    counts={'cross_total':0,'domain_closure':0,'k2_count':0,'k2_nonedge_endpoint':0,'labels':0,'degree':0,'k4':0,'i6':0}
    with Solver(name=solver_name) as s:
        counts['cross_total']+=add_card(s,[x[a][b] for a in range(NA) for b in range(NB)],66,pool)
        counts['labels']+=add_card(s,z,1,pool)
        is2=[]
        for b in range(NB):
            d2=db[b]+2
            is2.append(qB[b,d2] if d2 in CLASSES else None)
        k2lits=[v for v in is2 if v is not None]
        counts['k2_count']+=add_card(s,k2lits,6,pool,'atleast')
        counts['k2_count']+=add_card(s,k2lits,12,pool,'atmost')
        for a in range(NA):
            counts['labels']+=add_card(s,[qA[a,d] for d in CLASSES],1,pool)
            lo=max(0,11-1-da[a]);hi=min(NB,14-1-da[a])
            counts['domain_closure']+=add_card(s,x[a],lo,pool,'atleast')
            counts['domain_closure']+=add_card(s,x[a],hi,pool,'atmost')
        for b in range(NB):
            col=[x[a][b] for a in range(NA)]
            counts['labels']+=add_card(s,[qB[b,d] for d in CLASSES],1,pool)
            lo=max(2,11-db[b]);hi=min(NA,14-db[b])
            counts['domain_closure']+=add_card(s,col,lo,pool,'atleast')
            counts['domain_closure']+=add_card(s,col,hi,pool,'atmost')
            for d in CLASSES:
                if d-db[b] < 2:s.add_clause([-qB[b,d]]);counts['domain_closure']+=1
        # If nonadjacent B vertices are both k2, their masks must be disjoint.
        for b,c in itertools.combinations(range(NB),2):
            if (B[b]>>c)&1:continue
            if is2[b] is None or is2[c] is None:continue
            for a in range(NA):
                s.add_clause([-is2[b],-is2[c],-x[a][b],-x[a][c]])
                counts['k2_nonedge_endpoint']+=1
        for si,seq in enumerate(SEQS):
            for d in CLASSES:
                lits=[qA[a,d] for a in range(NA)]+[qB[b,d] for b in range(NB)]
                counts['labels']+=add_card(s,lits,seq.get(d,0)-(1 if d==11 else 0),pool,guard=-z[si])
        for a in range(NA):
            for d in CLASSES:counts['degree']+=add_card(s,x[a],d-1-da[a],pool,guard=-qA[a,d])
        for b in range(NB):
            col=[x[a][b] for a in range(NA)]
            for d in CLASSES:
                bound=d-db[b]
                if 0<=bound<=NA:counts['degree']+=add_card(s,col,bound,pool,guard=-qB[b,d])
                else:s.add_clause([-qB[b,d]]);counts['degree']+=1
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
    result={'campaign':'m219-r3-fixedAB-v4-k2-closure','a_ordinal':ao,'b_ordinal':bo,'a_graph6':ag6,'b_graph6':bg6,'k2_mask_count':len(k2masks),'k2_four_side':D,'k2_other_side':left,'status':'SAT' if sat else 'UNSAT','solver':solver_name,'clauses_by_kind':counts,'max_var':pool.top}
    summary.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 20
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
    assert sorted(r.count('1') for r in rr)==sorted(want)
    assert sum(rr[u].count('1') for u in range(1,12))==129
    assert sum(rr[1+a][12+b]=='1' for a in range(NA) for b in range(NB))==66
    output.write_text(json.dumps({'adjacency':rr},indent=2)+'\n');summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');return 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--catalog-dir',type=Path);ap.add_argument('--a-ordinal',type=int);ap.add_argument('--b-ordinal',type=int);ap.add_argument('--summary',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--solver',default='cadical195');ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:
        assert all(sum(s.values())==36 and sum(d*n for d,n in s.items())==438 for s in SEQS)
        print('m219 r3 fixed-AB v4 k2-closure self-test ok');return 0
    return solve(a.catalog_dir,a.a_ordinal,a.b_ordinal,a.solver,a.summary,a.output)
if __name__=='__main__':raise SystemExit(main())
