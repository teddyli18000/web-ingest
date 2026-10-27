#!/usr/bin/env python3
"""Global exact SAT search for 368 independent vertices in C7^5.

The model uses one Boolean variable for each of the 7^5 vertices.  For every
anchor a, the 32 vertices a+{0,1}^5 form a clique; these 7^5 cliques cover every
conflict edge exactly enough to characterize independence.  Native MiniCard
at-most-one constraints enforce the clique conditions and one global cardinality
constraint requires at least 368 selected vertices.

Translation symmetry is broken losslessly by forcing vertex 00000 selected:
any nonempty independent set can be translated so that one of its members is 0.
A SAT model is replayed pairwise, then any 368 selected vertices are squared to
an explicit 135424-point independent set in C7^10 and sent to Few Shots p004.
"""
import argparse,json
from itertools import combinations,product
from pathlib import Path
from pysat.solvers import Minicard
Q=7;D=5;U=Q**D;TARGET5=368;TARGET10=TARGET5*TARGET5

def dec(v):
    out=[]
    for _ in range(D):out.append(v%Q);v//=Q
    return tuple(out)
def enc(w):
    v=0;m=1
    for x in w:v+=x*m;m*=Q
    return v
def cube(a):
    for b in product((0,1),repeat=D):yield enc(tuple((a[j]+b[j])%Q for j in range(D)))
def conflict(a,b,digits):return all((x-y)%Q in (0,1,Q-1) for x,y in zip(digits[a],digits[b]))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('status',type=Path);args=ap.parse_args();digits=tuple(dec(v) for v in range(U));var=[v+1 for v in range(U)];s=Minicard();lt=0
    for a in range(U):
        lits=[var[v] for v in cube(digits[a])];s.add_atmost(lits,1);lt+=len(lits)
    s.add_clause([var[0]])
    s.add_atmost([-x for x in var],U-TARGET5)
    setup={'ambient_vertices':U,'cube_constraints':U,'cube_literal_total':lt,'symmetry_fixed_vertex':0,'target_5d':TARGET5,'target_10d':TARGET10};print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=s.solve();model=s.get_model() if sat else None;s.delete();args.status.parent.mkdir(parents=True,exist_ok=True)
    if not sat:
        st={'candidate':False,'sat':False,'method':'C7^5-global-368-exact-cube-SAT','setup':setup};args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('UNSAT',json.dumps(st,sort_keys=True),flush=True);return
    pos={z for z in model if z>0};S=[v for v in range(U) if var[v] in pos][:TARGET5]
    if len(S)!=TARGET5 or 0 not in S:raise RuntimeError(f'model replay size={len(S)} zero={0 in S}')
    for a,b in combinations(S,2):
        if conflict(a,b,digits):raise RuntimeError(f'conflicting SAT pair {a} {b}')
    def p10(a,b):return ''.join(map(str,digits[a]+digits[b]))
    points=[p10(a,b) for a in S for b in S]
    if len(points)!=TARGET10 or len(set(points))!=TARGET10:raise RuntimeError('10D square size/uniqueness drift')
    st={'candidate':True,'sat':True,'method':'C7^5-global-368-exact-cube-SAT','score5':len(S),'score10':len(points),'points5':S,'setup':setup};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'points':points},separators=(',',':'))+'\n');args.status.write_text(json.dumps(st,indent=2,sort_keys=True)+'\n');print('FOUND',json.dumps({k:v for k,v in st.items() if k!='points5'},sort_keys=True),flush=True)
if __name__=='__main__':main()
