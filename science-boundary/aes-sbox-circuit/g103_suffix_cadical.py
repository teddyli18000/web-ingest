#!/usr/bin/env python3
"""Bounded affine SLP synthesis for the G103 suffix using CaDiCaL via PySAT.

This is an independent affine extension of the classic SAT encoding for shortest
GF(2) straight-line programs (Fuhs--Schneider-Kamp, SAT 2010).  Every synthesized
signal carries its full coefficient vector on the 17 cut variables plus one
affine-constant bit.  An active slot chooses one unordered pair of earlier
signals; a Boolean polarity bit chooses XOR versus XNOR.  Inactive trailing slots
are allowed, so a K-slot model represents any circuit with at most K gates.

The purpose here is constructive: SAT yields a concrete suffix, which for the
identity cut basis is attached to the original 32-AND/49-linear G103 prefix and
verified on all 256 AES inputs.  An UNSAT result from this experimental encoding
is not promoted to a scientific lower bound unless separately proof-certified.
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import g103_suffix_exact_z3 as ez


def add_guarded_xor(cls,g,x,y,z):
    # g -> (z == x xor y)
    cls += [
        [-g,-x,-y,-z],[-g,-x,y,z],[-g,x,-y,z],[-g,x,y,-z]
    ]


def add_guarded_xnor_choice(cls,g,x,y,n,z):
    # g -> z == x xor y xor n.  Ban all eight parity-violating assignments.
    vs=(x,y,n,z)
    for xb,yb,nb,zb in itertools.product((0,1),repeat=4):
        if zb == (xb^yb^nb):
            continue
        clause=[-g]
        for v,b in zip(vs,(xb,yb,nb,zb)):
            clause.append(-v if b else v)
        cls.append(clause)


def build(z3_unused, targets, n_inputs, k):
    # z3_unused is kept out of the public API intentionally; this encoder is CNF.
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    pool=IDPool();cls=[];width=n_inputs+1;Cbit=n_inputs

    def val(s,b):return pool.id(('v',s,b))
    def inactive(j):return pool.id(('inactive',j))
    def pair(j,p,q):return pool.id(('pair',j,p,q))
    def xn(j):return pool.id(('xn',j))
    def match(r,s):return pool.id(('match',r,s))

    # Cut inputs are affine basis variables with zero constant coordinate.
    for i in range(n_inputs):
        for b in range(width):
            cls.append([val(i,b)] if i==b else [-val(i,b)])

    gate_base=n_inputs
    for j in range(k):
        sidx=gate_base+j;preds=list(range(sidx));ino=inactive(j)
        pairs=[(p,q) for p in preds for q in range(p+1,sidx)]
        opts=[ino]+[pair(j,p,q) for p,q in pairs]
        cls.extend(CardEnc.equals(lits=opts,bound=1,vpool=pool,encoding=EncType.seqcounter).clauses)
        if j+1<k:
            # Once a slot is inactive, all later slots are inactive padding.
            cls.append([-ino,inactive(j+1)])
        cls.append([-ino,-xn(j)])

        # Inactive padding aliases x0; target matches to inactive slots are banned.
        for b in range(width):
            cls.append([-ino, val(sidx,b) if b==0 else -val(sidx,b)])

        for p,q in pairs:
            g=pair(j,p,q)
            for b in range(n_inputs):
                add_guarded_xor(cls,g,val(p,b),val(q,b),val(sidx,b))
            add_guarded_xnor_choice(cls,g,val(p,Cbit),val(q,Cbit),xn(j),val(sidx,Cbit))

        # Active gates in a minimum representative never produce zero or duplicate
        # an earlier signal.  These constraints remove large value symmetries.
        cls.append([ino]+[val(sidx,b) for b in range(width)])
        for u in range(sidx):
            diffs=[]
            for b in range(width):
                d=pool.id(('diff',j,u,b));x=val(sidx,b);y=val(u,b)
                # d <-> x xor y
                cls += [[-d,x,y],[-d,-x,-y],[d,-x,y],[d,x,-y]]
                diffs.append(d)
            cls.append([ino]+diffs)

    total=n_inputs+k
    # Each target affine form must be an input or an active synthesized signal.
    for r,t in enumerate(targets):
        ms=[match(r,s) for s in range(total)];cls.append(ms)
        for s in range(total):
            if s>=n_inputs:
                cls.append([-match(r,s),-inactive(s-n_inputs)])
            for b in range(width):
                lit=val(s,b) if ((t>>b)&1) else -val(s,b)
                cls.append([-match(r,s),lit])
    return pool,cls,(val,inactive,pair,xn,match)


def solve(targets,n_inputs,k,conf_budget=0):
    from pysat.solvers import Cadical153
    pool,cls,ids=build(None,targets,n_inputs,k);val,inactive,pair,xn,match=ids
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

    names=[f'b{i}' for i in range(n_inputs)];exact=[1<<i for i in range(n_inputs)];gates=[]
    active=0
    for j in range(k):
        if inactive(j) in pos:break
        sidx=n_inputs+j;chosen=None
        for p in range(sidx):
            for q in range(p+1,sidx):
                if pair(j,p,q) in pos:
                    chosen=(p,q);break
            if chosen:break
        if chosen is None:raise AssertionError(('no pair',j))
        p,q=chosen;isxn=xn(j) in pos;out=f's{j}'
        gates.append({'op':'XNOR' if isxn else 'XOR','a':names[p],'b':names[q],'out':out})
        exact.append(exact[p]^exact[q]^((1<<n_inputs) if isxn else 0));names.append(out);active+=1
    outs=[]
    for r,t in enumerate(targets):
        choices=[s for s in range(n_inputs+active) if match(r,s) in pos]
        if not choices:
            # A target may have multiple match variables; if the SAT model leaves
            # a true match outside the active prefix, that would contradict its
            # inactive-match ban, so this is a hard consistency error.
            raise AssertionError(('no active target witness',r,t))
        s=choices[0];assert exact[s]==t,(r,s,exact[s],t);outs.append(names[s])
    net={'gates':gates,'outputs':outs}
    return {'status':'sat','elapsed_s':round(elapsed,3),'vars':pool.top,'clauses':len(cls),
            'active_gates':active,'gate_ops':{'XOR':sum(g['op']=='XOR' for g in gates),
                                             'XNOR':sum(g['op']=='XNOR' for g in gates)}},net


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--basis-rows',type=ez.parse_rows,default=(1,2,4))
    ap.add_argument('--gates',type=int,default=19)
    ap.add_argument('--conf-budget',type=int,default=0)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    last,prefix,old_suffix,boundary,extras,extra_idx,m,C,targets,qtargets=ez.problem(c,args.basis_rows)
    meta,net=solve(targets,m,args.gates,args.conf_budget)
    summary={'basis_rows':list(args.basis_rows),'bound':args.gates,'boundary_count':m,
             'extras':extras,'original_suffix_gates':len(old_suffix),'prefix_gates':len(prefix),
             'solver':meta}
    print(json.dumps(meta,sort_keys=True),flush=True)
    if net is not None:
        (out/'suffix.json').write_text(json.dumps(net,indent=2)+'\n')
        if tuple(args.basis_rows)==(1,2,4):
            full=ez.attach_identity(c,prefix,boundary,net)
            (out/'full.json').write_text(json.dumps(full,indent=2)+'\n')
            summary['full_gates']=len(full['gates']);summary['verified_all_256']=True
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='solver'},sort_keys=True),flush=True)

if __name__=='__main__':main()
