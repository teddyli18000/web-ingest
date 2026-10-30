#!/usr/bin/env python3
"""Independent decision encoding for the exact 315-core C7^5 prize identity.

For the certified independent core C of size 315,

  alpha(C7^5) = max_{Y independent in V\C} |Y| + 315 - |N_C(Y)|.

This script asks only whether the right-hand side is at least 368.  It uses
MiniCard native cardinality rather than RC2/MaxSAT, providing an independent
solver route for any future exact optimum claim from c7p5_core_prize_maxsat.py.

Variables:
- x_v for each outside vertex v, selected into Y;
- b_c for each core vertex c, meaning some selected outside vertex conflicts
  with c.
Hard constraints:
- x_u + x_v <= 1 for outside conflict edges;
- x_v -> b_c for every core neighbour c of v;
- sum(x_v) + sum(1-b_c) >= 368;
- lossless symmetry: completed solution contains vertex 0;
- optional residue branch over a second nonzero completed vertex.

A SAT model is independently replayed as Y union (C\N_C(Y)); UNSAT across every
branch proves no 368-set exists relative to an identity that is itself exact.
"""
from __future__ import annotations

import argparse
import gzip
import itertools
import json
from pathlib import Path

from pysat.solvers import Minicard

Q=7
D=5
U=Q**D
TARGET=368
CORE_EXPECT=315
POW=tuple(Q**i for i in range(D))


def dec(v):
    return tuple((v//POW[i])%Q for i in range(D))


def enc(w):
    return sum(int(w[i])*POW[i] for i in range(D))


def neighbors(v):
    d=dec(v)
    for delta in itertools.product((-1,0,1),repeat=D):
        if all(z==0 for z in delta):
            continue
        yield enc(tuple((d[i]+delta[i])%Q for i in range(D)))


def independent(S):
    S=set(S)
    for v in S:
        for u in neighbors(v):
            if u in S:
                return False
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('c7five_root',type=Path)
    ap.add_argument('output',type=Path)
    ap.add_argument('--branch-mod',type=int,default=1)
    ap.add_argument('--branch-residue',type=int,default=0)
    a=ap.parse_args()
    if a.branch_mod<1 or not 0<=a.branch_residue<a.branch_mod:
        raise SystemExit('invalid branch')

    with gzip.open(a.c7five_root/'data'/'core-overlap.json.gz','rt') as f:
        bundle=json.load(f)
    core=tuple(sorted(map(int,bundle['core'])))
    if len(core)!=CORE_EXPECT or len(set(core))!=CORE_EXPECT or not independent(core):
        raise RuntimeError(('core',len(core),len(set(core))))
    C=set(core)
    outside=tuple(v for v in range(U) if v not in C)
    O=set(outside)
    x={v:i+1 for i,v in enumerate(outside)}
    b0=len(outside)+1
    b={c:b0+i for i,c in enumerate(core)}

    s=Minicard()
    edge_count=0
    implications=0
    support_hist={}
    for v in outside:
        support=[]
        for u in neighbors(v):
            if u in C:
                support.append(u)
            elif u in O and u>v:
                s.add_clause([-x[v],-x[u]])
                edge_count+=1
        support_hist[len(support)]=support_hist.get(len(support),0)+1
        for c in support:
            s.add_clause([-x[v],b[c]])
            implications+=1

    # Completed solution size = selected outside + unblocked core.
    value_lits=[x[v] for v in outside]+[-b[c] for c in core]
    s.add_atleast(value_lits,TARGET)

    # Lossless graph-transitivity symmetry break.
    if 0 in C:
        s.add_clause([-b[0]])
        sym='core-zero-unblocked'
    else:
        s.add_clause([x[0]])
        sym='outside-zero-selected'

    branch=[]
    if a.branch_mod>1:
        for v in range(1,U):
            if v%a.branch_mod!=a.branch_residue:
                continue
            branch.append(-b[v] if v in C else x[v])
        if not branch:
            raise RuntimeError('empty branch')
        s.add_clause(branch)

    setup={
        'method':'exact-c7p5-315core-prize-decision-minicard',
        'ambient_vertices':U,
        'core_size':len(core),
        'outside_vertices':len(outside),
        'outside_conflict_edges':edge_count,
        'support_implications':implications,
        'support_size_histogram':{str(k):v for k,v in sorted(support_hist.items())},
        'target':TARGET,
        'symmetry_break':sym,
        'branch_mod':a.branch_mod,
        'branch_residue':a.branch_residue,
        'branch_literals':len(branch),
        'core_source_commit':'ae81e0d24b356aef3d388238f6fb4d02c4aa32a5',
    }
    print('SETUP',json.dumps(setup,sort_keys=True),flush=True)
    sat=s.solve()
    model=s.get_model() if sat else None
    s.delete()
    out={'sat':bool(sat),'candidate':False,'setup':setup}
    if sat:
        pos={z for z in model if z>0}
        Y={v for v in outside if x[v] in pos}
        blocked=set()
        for v in Y:
            blocked.update(u for u in neighbors(v) if u in C)
        completed=Y|(C-blocked)
        if len(completed)<TARGET or not independent(completed) or 0 not in completed:
            raise RuntimeError(('SAT replay',len(completed)))
        if a.branch_mod>1 and not any(v and v%a.branch_mod==a.branch_residue for v in completed):
            raise RuntimeError('branch replay')
        S=sorted(completed)[:TARGET]
        out.update(candidate=True,completed_size=len(completed),points5=S,
                   selected_outside=len(Y),activated_core_blockers=len(blocked))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('RESULT',json.dumps({k:v for k,v in out.items() if k!='points5'},sort_keys=True),flush=True)

if __name__=='__main__':
    main()
