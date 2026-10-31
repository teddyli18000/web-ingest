#!/usr/bin/env python3
"""Fixed-topology controls for the affine G103 suffix CaDiCaL encoding.

The unconstrained 19/20/22-gate SAT instances can be hard.  A slow 22-gate run
therefore does not validate the encoding.  This control builds the exact same
22-slot CNF, then fixes every operand pair and XOR/XNOR polarity to the known
NIST G103 suffix.  The positive control must be SAT.  A negative control flips
one fixed gate polarity while keeping all target constraints; it must be UNSAT.
"""
from __future__ import annotations
import json,time
from pysat.solvers import Cadical153
import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf
import g103_suffix_exact_z3 as ez
import g103_suffix_cadical as sat


def fixed_clauses(c,flip_gate=None):
    last,prefix,suffix,boundary=suf.split(c)
    assert len(suffix)==22,len(suffix)
    _last,_prefix,_old,_b,_e,_ei,m,_C,targets,_q=ez.problem(c,(1,2,4))
    pool,cls,ids=sat.build(None,targets,m,len(suffix));val,inactive,pair,xn,match=ids
    wire={w:i for i,w in enumerate(boundary)}
    for j,g in enumerate(suffix):
        a=wire[g['a']];b=wire[g['b']]
        if a>b:a,b=b,a
        cls.append([-inactive(j)])
        cls.append([pair(j,a,b)])
        isxn=(g['op']=='XNOR')
        if flip_gate==j:isxn=not isxn
        cls.append([xn(j) if isxn else -xn(j)])
        wire[g['out']]=m+j
    for r,o in enumerate(c['outputs']):
        cls.append([match(r,wire[o])])
    return pool,cls


def solve(cls):
    t=time.time()
    with Cadical153(bootstrap_with=cls) as s:ok=s.solve()
    return bool(ok),round(time.time()-t,4)


def main():
    c=ras.load_circuit('nist-g103');assert ras.independent_check(c)[0]
    p,pc=fixed_clauses(c,None);ok,ts=solve(pc)
    print(json.dumps({'control':'known22','sat':ok,'seconds':ts,'vars':p.top,'clauses':len(pc)},sort_keys=True))
    assert ok,'known 22-gate suffix must satisfy the CNF'
    # Flip the first XNOR if possible; otherwise gate zero.  A single polarity
    # error on a live fixed topology must not still satisfy all eight targets.
    _last,_prefix,suffix,_boundary=suf.split(c)
    flip=next((i for i,g in enumerate(suffix) if g['op']=='XNOR'),0)
    n,nc=fixed_clauses(c,flip);nok,nts=solve(nc)
    print(json.dumps({'control':'flipped-polarity','gate':flip,'sat':nok,'seconds':nts,'vars':n.top,'clauses':len(nc)},sort_keys=True))
    assert not nok,'flipped-polarity negative control unexpectedly SAT'

if __name__=='__main__':main()
