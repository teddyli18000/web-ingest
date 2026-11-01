#!/usr/bin/env python3
"""Exact fixed-AND released-tail CaDiCaL synthesis for the FS101 record.

This reuses the validated released-tail CNF machinery from g103_tail_cadical.py
but applies it to the 101-gate Few Shots record.  A fixed prefix and the ordered
exact AND atom functions are retained; every local linear slot may choose a
completely new XOR/XNOR of any values available at that stage.  SAT witnesses
are reconstructed into the full AES circuit and checked on all 256 inputs.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time

from pysat.solvers import Cadical153

import released_and_skeleton as ras
import temporal_window_resynth as tw
import g103_tail_cadical as tc


def parse_ints(s): return [int(x) for x in s.split(',') if x!='']


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--start',type=int,required=True)
    ap.add_argument('--slots',type=parse_ints,required=True)
    ap.add_argument('--conf-budget',type=int,default=1000000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101'); assert len(c['gates'])==101 and ras.independent_check(c)[0]
    sched=tw.original_schedule(c); original=sched[args.start:]
    data=tc.build(c,args.start,args.slots)
    t0=time.time()
    with Cadical153(bootstrap_with=data['cnf'].clauses) as solver:
        if args.conf_budget>0:
            solver.conf_budget(args.conf_budget); sat=solver.solve_limited()
        else: sat=solver.solve()
        model=solver.get_model() if sat is True else None
    summary={'start':args.start,'slots':args.slots,'linear':data['linear'],'original_tail_schedule':original,
             'original_tail_linear':sum(original),'source_count':data['source_count'],
             'vars':data['pool'].top,'clauses':len(data['cnf'].clauses),'conf_budget':args.conf_budget,
             'sat':sat is True,'timed_out':sat is None,'unsat':sat is False,'seconds':round(time.time()-t0,3),
             'family_scope':'FS101 fixed prefix + exact ordered released AND atoms + arbitrary XOR/XNOR topology under fixed slot schedule'}
    if model is not None:
        full=tc.reconstruct(c,data,model)
        summary['candidate_gates']=len(full['gates']); summary['verified_all_256']=True
        summary['gate_counts']={op:sum(g['op']==op for g in full['gates']) for op in ('AND','XOR','XNOR')}
        (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__': main()
