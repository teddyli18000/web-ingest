#!/usr/bin/env python3
"""Compact selector-CNF synthesis for the 17-bit G103 suffix linear SLP.

This is a constructive implementation of the standard exact GF(2) SLP SAT
formulation: each gate has separate one-hot selectors for its first and second
operand, ordered p<q, rather than a one-hot variable for every operand pair.
The value equations are guarded by the conjunction of the two selectors.
Compared with `g103_suffix_linear_cadical.py`, this keeps only O(t) selector
variables per gate while representing the same straight-line programs.

Affine XNOR polarities are recovered after the linear DAG is found, exactly as
in `g103_suffix_linear_cadical.py`.  Any candidate is attached to the explicit
G103 cut prefix and checked on all 256 AES inputs before being written.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

import released_and_skeleton as ras
import g103_suffix_exact_z3 as ez
import g103_explicit_cut_basis as xp


def build(targets,n,k):
    from pysat.card import CardEnc,EncType
    from pysat.formula import IDPool
    pool=IDPool();cls=[]
    def sa(t,p):return pool.id(('a',t,p))
    def sb(t,q):return pool.id(('b',t,q))
    def val(s,j):return pool.id(('v',s,j))
    def match(r,s):return pool.id(('m',r,s))

    for i in range(n):
        for j in range(n):cls.append([val(i,j)] if i==j else [-val(i,j)])

    for t in range(n,n+k):
        preds=list(range(t))
        cls.extend(CardEnc.equals(lits=[sa(t,p) for p in preds],bound=1,
                                  vpool=pool,encoding=EncType.pairwise).clauses)
        cls.extend(CardEnc.equals(lits=[sb(t,q) for q in preds],bound=1,
                                  vpool=pool,encoding=EncType.pairwise).clauses)
        for p in preds:
            for q in preds:
                if q<=p:
                    cls.append([-sa(t,p),-sb(t,q)])
                    continue
                a,b=sa(t,p),sb(t,q)
                for j in range(n):
                    x,y,z=val(p,j),val(q,j),val(t,j)
                    cls += [[-a,-b,-x,-y,-z],[-a,-b,-x,y,z],
                            [-a,-b,x,-y,z],[-a,-b,x,y,-z]]
        cls.append([val(t,j) for j in range(n)])
        for u in range(t):
            diffs=[]
            for j in range(n):
                d=pool.id(('d',t,u,j));x,y=val(t,j),val(u,j)
                cls += [[-d,x,y],[-d,-x,-y],[d,-x,y],[d,x,-y]]
                diffs.append(d)
            cls.append(diffs)

    total=n+k
    for r,tgt in enumerate(targets):
        cls.append([match(r,s) for s in range(total)])
        for s in range(total):
            for j in range(n):
                lit=val(s,j) if ((tgt>>j)&1) else -val(s,j)
                cls.append([-match(r,s),lit])
    return pool,cls,(sa,sb,val,match)


def solve(linear_targets,affine_targets,n,k,conf_budget=0):
    from pysat.solvers import Cadical153
    pool,cls,ids=build(linear_targets,n,k);sa,sb,val,match=ids
    t0=time.time()
    with Cadical153(bootstrap_with=cls) as s:
        if conf_budget:
            s.conf_budget(conf_budget);ok=s.solve_limited()
        else:ok=s.solve()
        elapsed=time.time()-t0
        if ok is None:
            return {'status':'unknown','elapsed_s':round(elapsed,3),'vars':pool.top,'clauses':len(cls)},None
        if not ok:
            return {'status':'unsat','elapsed_s':round(elapsed,3),'vars':pool.top,'clauses':len(cls)},None
        pos={x for x in s.get_model() if x>0}

    vals=[1<<i for i in range(n)];parents=[]
    for t in range(n,n+k):
        p=next(x for x in range(t) if sa(t,x) in pos)
        q=next(x for x in range(t) if sb(t,x) in pos)
        assert p<q,(t,p,q)
        parents.append((p,q));vals.append(vals[p]^vals[q])
    outs=[]
    for r,tgt in enumerate(linear_targets):
        choices=[s for s in range(n+k) if match(r,s) in pos]
        if not choices:raise AssertionError(('missing target match',r))
        s=choices[0];assert vals[s]==tgt,(r,s,vals[s],tgt);outs.append(s)

    constants=[0]*(n+k);req={}
    for r,s in enumerate(outs):
        c=(affine_targets[r]>>n)&1
        if s<n:
            if c:raise AssertionError(('complemented input target',r,s))
        else:
            if s in req and req[s]!=c:raise AssertionError(('conflicting constants',s))
            req[s]=c
    for s,c in req.items():constants[s]=c
    names=[f'b{i}' for i in range(n)];gates=[]
    for j,(p,q) in enumerate(parents):
        sidx=n+j;xn=constants[sidx]^constants[p]^constants[q]
        out=f's{j}';gates.append({'op':'XNOR' if xn else 'XOR','a':names[p],'b':names[q],'out':out});names.append(out)
    net={'gates':gates,'outputs':[names[s] for s in outs]}
    return {'status':'sat','elapsed_s':round(elapsed,3),'vars':pool.top,'clauses':len(cls),
            'gate_ops':{'XOR':sum(g['op']=='XOR' for g in gates),'XNOR':sum(g['op']=='XNOR' for g in gates)}},net


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis-rows',type=ez.parse_rows,default=(1,2,4))
    ap.add_argument('--gates',type=int,required=True)
    ap.add_argument('--conf-budget',type=int,default=10000000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    prec,pmeta=xp.synthesize_at_cut(c,args.basis_rows)
    _last,_prefix,old_suffix,_boundary,_extras,_extra_idx,n,_C,affine_targets,_q=ez.problem(c,args.basis_rows)
    linear_targets=[t&((1<<n)-1) for t in affine_targets]
    meta,net=solve(linear_targets,affine_targets,n,args.gates,args.conf_budget)
    summary={'basis_rows':list(args.basis_rows),'bound':args.gates,'prefix':pmeta,
             'original_suffix_gates':len(old_suffix),'solver':meta}
    print(json.dumps(meta,sort_keys=True),flush=True)
    if net is not None:
        (out/'suffix.json').write_text(json.dumps(net,indent=2)+'\n')
        if prec is not None:
            full=xp.attach_suffix(c,prec,net)
            (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
            summary['full_gates']=len(full['gates']);summary['verified_all_256']=True
            summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('prefix','solver')},sort_keys=True),flush=True)

if __name__=='__main__':main()
