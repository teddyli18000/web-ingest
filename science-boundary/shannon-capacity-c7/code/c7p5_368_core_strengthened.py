#!/usr/bin/env python3
"""Global exact C7^5 target-368 SAT strengthened by a verified 315-core inequality.

The base model is the exact 7^5 binary-cube clique cover plus cardinality >=368
and the lossless translation symmetry break 00000 selected.

molind/c7-five proves by portable exact replay that every independent set of
size 368 omits at least four vertices from one explicit 315-word core C; hence
sum_{v in C} x_v <= 311.  Graph automorphisms preserve the statement, so we add
the same inequality for all 7^5 translations of C.  These cuts do not exclude
any valid 368-set; they only remove regions already exactly certified impossible.

A SAT model is replayed pairwise and squared to a 135424-point C7^10 Few Shots
certificate.
"""
import argparse,gzip,json
from itertools import combinations,product
from pathlib import Path
from pysat.solvers import Minicard

Q=7;D=5;U=Q**D;TARGET5=368;TARGET10=TARGET5*TARGET5
POW=tuple(Q**i for i in range(D))

def dec(v):return tuple((v//POW[i])%Q for i in range(D))
def enc(w):return sum(w[i]*POW[i] for i in range(D))
def cube(a):
    for b in product((0,1),repeat=D):yield enc(tuple((a[j]+b[j])%Q for j in range(D)))
def translate(v,t,digits):
    a=digits[v];b=digits[t];return enc(tuple((a[j]+b[j])%Q for j in range(D)))
def conflict(a,b,digits):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(digits[a],digits[b]))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('c7five_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();digits=tuple(dec(v) for v in range(U));var=[v+1 for v in range(U)]
    with gzip.open(args.c7five_root/'data'/'core-overlap.json.gz','rt') as f:bundle=json.load(f)
    core=list(map(int,bundle['core']))
    if len(core)!=315 or len(set(core))!=315 or any(not 0<=v<U for v in core):raise RuntimeError('core data drift')
    # The molind integer convention reverses coordinate order relative to this
    # script.  Coordinate reversal is a graph automorphism, so the same integer
    # list denotes another valid image of the certified core here.
    s=Minicard();cube_literals=0
    for a in range(U):
        lits=[var[v] for v in cube(digits[a])];s.add_atmost(lits,1);cube_literals+=len(lits)
    s.add_clause([var[0]])
    s.add_atmost([-x for x in var],U-TARGET5)
    translated=[]
    for t in range(U):
        C=tuple(sorted(translate(v,t,digits) for v in core))
        if len(C)!=315 or len(set(C))!=315:raise RuntimeError('translated core collision')
        s.add_atmost([var[v] for v in C],311)
        translated.append(C)
    setup={'ambient_vertices':U,'target_5d':TARGET5,'target_10d':TARGET10,'cube_constraints':U,'cube_literal_total':cube_literals,'symmetry_fixed_vertex':0,'certified_core_size':315,'core_max_selected_for_368':311,'translated_core_cuts':len(translated),'core_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5'};print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=s.solve();model=s.get_model() if sat else None;s.delete();args.status.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        st={'candidate':False,'sat':False,'method':'C7^5-global-368-cube-SAT-plus-all-translated-315-core-cuts','setup':setup};args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('UNSAT',json.dumps(st,sort_keys=True),flush=True);return
    pos={z for z in model if z>0};S=[v for v in range(U) if var[v] in pos][:TARGET5]
    if len(S)!=TARGET5 or 0 not in S:raise RuntimeError('SAT cardinality/symmetry replay')
    for a,b in combinations(S,2):
        if conflict(a,b,digits):raise RuntimeError(f'conflicting SAT pair {a} {b}')
    for C in translated:
        if len(set(S)&set(C))>311:raise RuntimeError('core-cut replay failed')
    points=[''.join(map(str,digits[a]+digits[b])) for a in S for b in S]
    if len(points)!=TARGET10 or len(set(points))!=TARGET10:raise RuntimeError('10D square replay')
    st={'candidate':True,'sat':True,'method':'C7^5-global-368-cube-SAT-plus-all-translated-315-core-cuts','score5':len(S),'score10':len(points),'points5':S,'setup':setup};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n');args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps({k:v for k,v in st.items() if k!='points5'},sort_keys=True),flush=True)
if __name__=='__main__':main()
