#!/usr/bin/env python3
"""Fixed-original-solution control for g103_tail_cadical.py.

Build the exact same start=28 / [0,0,2,0,22] CNF as the free tail search, then
add unit clauses selecting the parent pair, XOR/XNOR polarity, AND-operand source,
and final-output source used by the known NIST G103 tail.  This should solve SAT
quickly if the encoding really contains the baseline circuit.

This is an encoding calibration, not an optimization result.
"""
from __future__ import annotations

import json
import pathlib
import time

from pysat.solvers import Cadical153

import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_tail_cadical as tc


def force_match(cnf, rec, source_index):
    if rec['fixed']:
        return
    hits=[m for m,si in rec['choices'] if si==source_index]
    if len(hits)!=1:
        raise AssertionError(('missing match selector',rec['label'],source_index,rec['choices']))
    cnf.append([hits[0]])


def main():
    out=pathlib.Path('result'); out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    slots=[0,0,2,0,22]; start=28
    data=tc.build(c,start,slots)
    lo=tw.interval_boundaries(c)[start]
    local=c['gates'][lo:]
    if len(local)!=len(data['events']):
        raise AssertionError((len(local),len(data['events'])))

    src_names=[w for w,_v in data['live']]
    for g,ev in zip(local,data['events']):
        if g['op']=='AND':
            if ev['kind']!='and': raise AssertionError((g,ev))
            ia=src_names.index(g['a']); ib=src_names.index(g['b'])
            force_match(data['cnf'],data['matches'][ev['ma']],ia)
            force_match(data['cnf'],data['matches'][ev['mb']],ib)
            src_names.append(g['out'])
        else:
            if ev['kind']!='linear': raise AssertionError((g,ev))
            ia=src_names.index(g['a']); ib=src_names.index(g['b'])
            key=tuple(sorted((ia,ib)))
            hits=[r for r,pair in zip(ev['selectors'],ev['pairs']) if pair==key]
            if len(hits)!=1: raise AssertionError(('missing pair',g,key))
            data['cnf'].append([hits[0]])
            data['cnf'].append([ev['neg'] if g['op']=='XNOR' else -ev['neg']])
            src_names.append(g['out'])

    for o,lab in zip(c['outputs'],data['out_match']):
        force_match(data['cnf'],data['matches'][lab],src_names.index(o))

    t0=time.time()
    with Cadical153(bootstrap_with=data['cnf'].clauses) as solver:
        sat=solver.solve(); model=solver.get_model() if sat else None
    summary={'sat':bool(sat),'seconds':round(time.time()-t0,3),
             'vars':data['pool'].top,'clauses':len(data['cnf'].clauses),
             'start':start,'slots':slots,'source_count':data['source_count']}
    if not sat: raise AssertionError(('fixed known baseline is UNSAT',summary))
    full=tc.reconstruct(c,data,model)
    assert ras.independent_check(full)[0]
    summary['reconstructed_gates']=len(full['gates']); summary['verified_all_256']=True
    (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__': main()
