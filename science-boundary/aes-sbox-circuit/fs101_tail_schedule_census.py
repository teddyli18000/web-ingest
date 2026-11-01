#!/usr/bin/env python3
"""Exhaust fixed-prefix FS101 released-tail schedules one linear gate below baseline.

For a chosen AND atom `start`, derive the exact original linear-slot schedule from
the 101-gate record.  Calibrate the arbitrary-topology released-AND CNF on that
baseline schedule, then enumerate every weak composition of `baseline_linear-1`
across the same temporal stages.  Each slot is an unconstrained XOR/XNOR of any
signals available at that point.  Hence, modulo the fixed prefix and exact
ordered AND functions, this exhausts all temporal placements of a one-gate
linear saving.  SAT witnesses are reconstructed and checked on all 256 inputs;
UNSAT is family-local, timeout is inconclusive.
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


def compositions(total, parts):
    if parts == 1:
        yield (total,); return
    for x in range(total + 1):
        for rest in compositions(total - x, parts - 1):
            yield (x,) + rest


def solve_one(c,start,slots,budget):
    data=tc.build(c,start,list(slots)); t0=time.time()
    with Cadical153(bootstrap_with=data['cnf'].clauses) as solver:
        if budget>0:
            solver.conf_budget(budget); sat=solver.solve_limited()
        else:
            sat=solver.solve()
        model=solver.get_model() if sat is True else None
    row={'slots':list(slots),'linear':sum(slots),'sat':sat is True,'unsat':sat is False,
         'timed_out':sat is None,'seconds':round(time.time()-t0,4),
         'vars':data['pool'].top,'clauses':len(data['cnf'].clauses)}
    full=None
    if model is not None:
        full=tc.reconstruct(c,data,model)
        row['candidate_gates']=len(full['gates']); row['verified_all_256']=True
    return row,full


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--start',type=int,required=True)
    ap.add_argument('--shard',type=int,default=0)
    ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--conf-budget',type=int,default=300000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101'); assert len(c['gates'])==101 and ras.independent_check(c)[0]
    sk=ras.extract_skeleton(c); sched=tw.original_schedule(c)
    orig=tuple(sched[args.start:]); expected=sk['n_and']-args.start+1
    if len(orig)!=expected: raise AssertionError((args.start,orig,expected))
    target=sum(orig)-1
    if target<0: raise ValueError((args.start,orig))

    baseline=None
    if args.shard==0:
        baseline,_=solve_one(c,args.start,orig,args.conf_budget)
        if not baseline['sat'] or baseline.get('candidate_gates')!=101:
            raise AssertionError(('baseline calibration failed',args.start,orig,baseline))

    all_slots=list(compositions(target,len(orig)))
    rows=[]; best=None; tested=0; t0=time.time()
    for serial,slots in enumerate(all_slots):
        if serial % args.shards != args.shard: continue
        tested+=1
        row,full=solve_one(c,args.start,slots,args.conf_budget); rows.append(row)
        print(json.dumps(row,sort_keys=True),flush=True)
        if full is not None:
            n=len(full['gates'])
            if best is None or n<best[0]: best=(n,list(slots))
            if n<=100:
                (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
                summary={'status':'found','start':args.start,'original_schedule':list(orig),
                         'target_linear':target,'all_schedules':len(all_slots),'shard':args.shard,
                         'shards':args.shards,'tested':tested,'baseline':baseline,'winning_row':row,
                         'elapsed_s':round(time.time()-t0,3),'verified_all_256':True}
                (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
                print(json.dumps(summary,sort_keys=True),flush=True); return

    summary={'status':'exhausted','start':args.start,'original_schedule':list(orig),
             'original_linear':sum(orig),'target_linear':target,'all_schedules':len(all_slots),
             'shard':args.shard,'shards':args.shards,'tested':tested,'baseline':baseline,'best':best,
             'sat_count':sum(r['sat'] for r in rows),'unsat_count':sum(r['unsat'] for r in rows),
             'timeout_count':sum(r['timed_out'] for r in rows),'rows':rows,
             'elapsed_s':round(time.time()-t0,3),
             'family_scope':'fixed FS101 prefix + exact ordered released AND atoms; all total-(baseline-1) linear-slot schedules; arbitrary XOR/XNOR topology'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__': main()
