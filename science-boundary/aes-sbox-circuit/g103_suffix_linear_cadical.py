#!/usr/bin/env python3
"""Constructive 17-bit linear-SLP SAT for the G103 suffix.

For this suffix, affine constants need not be part of the combinatorial search.
Every synthesized non-input gate may independently be XOR or XNOR, so once a
linear XOR DAG is known we can assign each gate's constant bit (and hence its
XOR/XNOR polarity) recursively.  All eight G103 suffix targets have linear
weight > 1, so none requires the impossible operation of complementing a primary
cut input for free.

We therefore solve the standard shortest-GF(2)-SLP problem on only the 17 linear
coordinates, using a direct CNF encoding in the spirit of Fuhs--Schneider-Kamp
(SAT 2010): each gate chooses one unordered pair of earlier signals, signal bits
encode its GF(2) vector, and each target must match some signal.  Nonzero and
no-duplicate constraints remove value symmetries.  A SAT model is converted back
to XOR/XNOR gates, attached to the requested explicit G103 cut basis, and checked
on all 256 AES inputs.

The solver is used to find upper bounds.  We do not claim an UNSAT result as a
scientific lower bound without an independently checkable proof certificate.
"""
from __future__ import annotations
import argparse,itertools,json,pathlib,time
import released_and_skeleton as ras
import g103_suffix_exact_z3 as ez
import g103_explicit_cut_basis as xp


def add_guarded_xor(cls,g,x,y,z):
    cls += [[-g,-x,-y,-z],[-g,-x,y,z],[-g,x,-y,z],[-g,x,y,-z]]


def build(targets,n,k):
    from pysat.card import CardEnc,EncType
    from pysat.formula import IDPool
    pool=IDPool();cls=[]
    def val(s,b):return pool.id(('v',s,b))
    def pair(j,p,q):return pool.id(('p',j,p,q))
    def match(r,s):return pool.id(('m',r,s))

    for i in range(n):
        for b in range(n):cls.append([val(i,b)] if i==b else [-val(i,b)])
    for j in range(k):
        sidx=n+j;pairs=[(p,q) for p in range(sidx) for q in range(p+1,sidx)]
        choices=[pair(j,p,q) for p,q in pairs]
        cls.extend(CardEnc.equals(lits=choices,bound=1,vpool=pool,encoding=EncType.seqcounter).clauses)
        for p,q in pairs:
            g=pair(j,p,q)
            for b in range(n):add_guarded_xor(cls,g,val(p,b),val(q,b),val(sidx,b))
        # Minimal representatives never create zero or recompute an old value.
        cls.append([val(sidx,b) for b in range(n)])
        for u in range(sidx):
            diffs=[]
            for b in range(n):
                d=pool.id(('d',j,u,b));x=val(sidx,b);y=val(u,b)
                cls += [[-d,x,y],[-d,-x,-y],[d,-x,y],[d,x,-y]]
                diffs.append(d)
            cls.append(diffs)

    total=n+k
    for r,t in enumerate(targets):
        ms=[match(r,s) for s in range(total)];cls.append(ms)
        for s in range(total):
            for b in range(n):
                lit=val(s,b) if ((t>>b)&1) else -val(s,b)
                cls.append([-match(r,s),lit])
    return pool,cls,(val,pair,match)


def solve(linear_targets,affine_targets,n,k,conf_budget=0):
    from pysat.solvers import Cadical153
    pool,cls,ids=build(linear_targets,n,k);val,pair,match=ids
    t0=time.time()
    with Cadical153(bootstrap_with=cls) as s:
        if conf_budget:
            s.conf_budget(conf_budget);ok=s.solve_limited()
        else:ok=s.solve()
        elapsed=time.time()-t0
        if ok is None:return {'status':'unknown','elapsed_s':round(elapsed,3),'vars':pool.top,'clauses':len(cls)},None
        if not ok:return {'status':'unsat','elapsed_s':round(elapsed,3),'vars':pool.top,'clauses':len(cls)},None
        pos={x for x in s.get_model() if x>0}

    vals=[1<<i for i in range(n)];parents=[]
    for j in range(k):
        sidx=n+j;chosen=None
        for p in range(sidx):
            for q in range(p+1,sidx):
                if pair(j,p,q) in pos:chosen=(p,q);break
            if chosen:break
        if chosen is None:raise AssertionError(('no operand pair',j))
        p,q=chosen;vals.append(vals[p]^vals[q]);parents.append((p,q))
    outs=[]
    for r,t in enumerate(linear_targets):
        choices=[s for s in range(n+k) if match(r,s) in pos]
        if not choices:raise AssertionError(('no target witness',r))
        s=choices[0];assert vals[s]==t,(r,s,vals[s],t);outs.append(s)

    # Assign a desired affine constant to every signal.  Inputs are fixed zero;
    # target-producing gates take their required target constant; all other gates
    # use zero.  Because each gate has its own XNOR choice, these assignments are
    # always realizable recursively.
    constants=[0]*(n+k)
    req={}
    for r,s in enumerate(outs):
        c=(affine_targets[r]>>n)&1
        if s<n:
            if c:raise AssertionError(('complemented input target',r,s))
        else:
            if s in req and req[s]!=c:raise AssertionError(('conflicting target constants',s))
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
    _last,_prefix,old_suffix,_boundary,_extras,_extra_idx,n,C,affine_targets,qtargets=ez.problem(c,args.basis_rows)
    linear_targets=[t&((1<<n)-1) for t in affine_targets]
    meta,net=solve(linear_targets,affine_targets,n,args.gates,args.conf_budget)
    summary={'basis_rows':list(args.basis_rows),'bound':args.gates,'prefix':pmeta,
             'original_suffix_gates':len(old_suffix),'solver':meta}
    print(json.dumps(meta,sort_keys=True),flush=True)
    if net is not None:
        (out/'suffix.json').write_text(json.dumps(net,indent=2)+'\n')
        if prec is not None:
            full=xp.attach_suffix(c,prec,net);(out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
            summary['full_gates']=len(full['gates']);summary['verified_all_256']=True
            summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('prefix','solver')},sort_keys=True),flush=True)

if __name__=='__main__':main()
