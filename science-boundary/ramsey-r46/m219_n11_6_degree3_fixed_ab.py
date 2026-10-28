#!/usr/bin/env python3
"""Exact m=219, n11=6 cover for the branch where the 11-class has a degree-3 vertex.

Every degree-11 vertex has at least three neighbours in the degree-11 class L.
If L has no vertex of L-degree 3, then delta(L)>=4.  The complement of L has
maximum degree at most one; K4-freeness of L forces the complement to have
independence number at most three, hence it is a perfect matching and
L=K_{2,2,2}.  Thus every other L type has a degree-3 vertex v.

For such v, S(v)<=129 and its three degree-11 neighbours already lower the
12-baseline sum 132 to 129, so all eight remaining neighbours have degree 12.
Hence S(v)=129 and the exact local pair is forced to

    e(A)=26, e(B)=116,

where A=N(v) has 11 vertices and B has 24.  The complete catalogues contain
2 A26 graphs and 9 B116 graphs.

Rather than enumerate degree-class placements, labels are quantified inside
SAT.  A contains exactly three further degree-11 vertices and eight degree-12
vertices.  B receives the remaining class counts for one of the three n11=6
m=219 degree sequences.  Exact global degrees plus all mixed Ramsey clauses
leave only the 11*24=264 cross edges and label auxiliaries unknown.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import d12_fixed_ab_sat as base

NA, NB = 11, 24
SEQS = (
    {11: 6, 12: 18, 13: 12},
    {11: 6, 12: 19, 13: 10, 14: 1},
    {11: 6, 12: 20, 13: 8, 14: 2},
)


def subsets(adj: list[int], k: int, edge_value: bool):
    pred = base.is_clique if edge_value else base.is_independent
    return [vs for vs in itertools.combinations(range(len(adj)), k) if pred(adj, vs)]


def validate_A(A: list[int]) -> None:
    assert len(A) == NA
    if subsets(A, 3, True) or subsets(A, 6, False):
        raise ValueError("invalid R(3,6,11) A")


def validate_B(B: list[int]) -> None:
    assert len(B) == NB
    if subsets(B, 4, True) or subsets(B, 5, False):
        raise ValueError("invalid R(4,5,24) B")


def add_formula(s: Solver, cnf, guard: int | None = None) -> int:
    for cl in cnf.clauses:
        s.add_clause(list(cl) + ([] if guard is None else [guard]))
    return len(cnf.clauses)


def add_exact(s: Solver, lits: list[int], value: int, pool: IDPool, guard: int | None = None) -> int:
    if not 0 <= value <= len(lits):
        s.add_clause([] if guard is None else [guard])
        return 1
    return add_formula(s, CardEnc.equals(lits=lits, bound=value, vpool=pool, encoding=EncType.seqcounter), guard)


def prepare(r36_11: Path, r45_24: Path, outdir: Path, manifest: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    A = outdir / "A26.g6"; B = outdir / "B116.g6"
    ca = base.extract_g6_stratum(r36_11, 11, 26, A)
    cb = base.extract_g6_stratum(r45_24, 24, 116, B)
    assert (ca, cb) == (2, 9), (ca, cb)
    branches=[{'sequence':seq,'a_ordinal':a,'b_ordinal':b} for seq in range(3) for a in range(ca) for b in range(cb)]
    assert len(branches)==54
    d={'campaign':'m219-n11-6-degree3-fixedAB','logical_scope':'n11=6 except L=K_{2,2,2}',
       'counts':{'A26':ca,'B116':cb,'sequences':3,'branches':len(branches)},'branches':branches}
    manifest.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    return d


def b_counts(seq: int) -> dict[int,int]:
    g=SEQS[seq]
    # anchor v is one d11; A contains 3 d11 + 8 d12.
    out=dict(g); out[11]-=4; out[12]-=8
    return {d:n for d,n in out.items() if n}


def solve(catalog_dir: Path, seq: int, ao: int, bo: int, solver_name: str, summary: Path, output: Path) -> int:
    ag6,A,ae=base.select_record(catalog_dir/'A26.g6',ao,NA)
    bg6,B,be=base.select_record(catalog_dir/'B116.g6',bo,NB)
    validate_A(A);validate_B(B);assert (ae,be)==(26,116)
    da,db=base.degrees(A),base.degrees(B)
    x=[[a*NB+b+1 for b in range(NB)] for a in range(NA)]
    nxt=NA*NB+1
    lA=list(range(nxt,nxt+NA));nxt+=NA
    classes=sorted(b_counts(seq)); qB={}
    for b in range(NB):
        for d in classes:
            qB[b,d]=nxt;nxt+=1
    pool=IDPool(start_from=nxt)
    counts={'labels':0,'conditional_degree':0,'k4_1a3b':0,'k4_2a2b':0,'i6_5a1b':0,'i6_4a2b':0,'i6_3a3b':0,'i6_2a4b':0}
    with Solver(name=solver_name) as s:
        counts['labels']+=add_exact(s,lA,3,pool)
        for b in range(NB):
            counts['labels']+=add_exact(s,[qB[b,d] for d in classes],1,pool)
        for d,n in b_counts(seq).items():
            counts['labels']+=add_exact(s,[qB[b,d] for b in range(NB)],n,pool)
        # A: lA=true means global degree 11, false means degree 12.
        for a in range(NA):
            row=x[a]; k12=11-da[a]; k11=10-da[a]
            counts['conditional_degree']+=add_exact(s,row,k11,pool,guard=-lA[a])
            counts['conditional_degree']+=add_exact(s,row,k12,pool,guard=lA[a])
        for b in range(NB):
            col=[x[a][b] for a in range(NA)]
            for d in classes:
                counts['conditional_degree']+=add_exact(s,col,d-db[b],pool,guard=-qB[b,d])

        btri=subsets(B,3,True); aedges=subsets(A,2,True); bedges=subsets(B,2,True)
        ai5=subsets(A,5,False); ai4=subsets(A,4,False); bnon=subsets(B,2,False)
        ai3=subsets(A,3,False); bi3=subsets(B,3,False); anon=subsets(A,2,False); bi4=subsets(B,4,False)
        for a in range(NA):
            for bs in btri:s.add_clause([-x[a][b] for b in bs]);counts['k4_1a3b']+=1
        for aa in aedges:
            for bb in bedges:s.add_clause([-x[a][b] for a in aa for b in bb]);counts['k4_2a2b']+=1
        for aa in ai5:
            for b in range(NB):s.add_clause([x[a][b] for a in aa]);counts['i6_5a1b']+=1
        for aa in ai4:
            for bb in bnon:s.add_clause([x[a][b] for a in aa for b in bb]);counts['i6_4a2b']+=1
        for aa in ai3:
            for bb in bi3:s.add_clause([x[a][b] for a in aa for b in bb]);counts['i6_3a3b']+=1
        for aa in anon:
            for bb in bi4:s.add_clause([x[a][b] for a in aa for b in bb]);counts['i6_2a4b']+=1
        sat=s.solve();model=set(v for v in (s.get_model() or []) if v>0)
    result={'campaign':'m219-n11-6-degree3-fixedAB','sequence':seq,'degree_sequence':{str(k):v for k,v in SEQS[seq].items()},
            'a_ordinal':ao,'b_ordinal':bo,'a_graph6':ag6,'b_graph6':bg6,'a_edges':ae,'b_edges':be,
            'b_class_counts':b_counts(seq),'clauses_by_kind':counts,'max_var':pool.top,'solver':solver_name,'status':'SAT' if sat else 'UNSAT'}
    summary.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 20

    rows=[['0']*36 for _ in range(36)]
    # 0=anchor; A -> 1..11; B -> 12..35.
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
    srows=[''.join(r) for r in rows]
    # Direct Ramsey verification and exact degree multiset.
    for vs in itertools.combinations(range(36),4):
        assert not all(srows[u][v]=='1' for u,v in itertools.combinations(vs,2))
    for vs in itertools.combinations(range(36),6):
        assert not all(srows[u][v]=='0' for u,v in itertools.combinations(vs,2))
    want=[]
    for d,n in SEQS[seq].items():want += [d]*n
    ds=sorted(r.count('1') for r in srows); assert ds==sorted(want),(ds,want)
    output.write_text(json.dumps({'adjacency':srows},indent=2)+'\n')
    summary.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 0


def self_test() -> None:
    assert [b_counts(i) for i in range(3)] == [
        {11:2,12:10,13:12}, {11:2,12:11,13:10,14:1}, {11:2,12:12,13:8,14:2}]
    print('n11=6 degree3 fixed-AB self-test ok')


def main()->int:
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('prepare');p.add_argument('--r36-11',type=Path,required=True);p.add_argument('--r45-24',type=Path,required=True);p.add_argument('--outdir',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    q=sub.add_parser('solve');q.add_argument('--catalog-dir',type=Path,required=True);q.add_argument('--sequence',type=int,choices=(0,1,2),required=True);q.add_argument('--a-ordinal',type=int,required=True);q.add_argument('--b-ordinal',type=int,required=True);q.add_argument('--solver',default='cadical195');q.add_argument('--summary',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
    sub.add_parser('self-test');a=ap.parse_args()
    if a.cmd=='prepare':d=prepare(a.r36_11,a.r45_24,a.outdir,a.manifest);print(json.dumps(d['counts'],sort_keys=True));return 0
    if a.cmd=='solve':return solve(a.catalog_dir,a.sequence,a.a_ordinal,a.b_ordinal,a.solver,a.summary,a.output)
    self_test();return 0
if __name__=='__main__':raise SystemExit(main())
