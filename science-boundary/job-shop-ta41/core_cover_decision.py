#!/usr/bin/env python3
"""Cross-check integer core-cover lower bounds as direct SAT feasibility queries.

Unlike the optimization run, solve the decision problems
  H(k): exists a set of <=k baseline machine-arc violations hitting
        every certified UNSAT core?
An INFEASIBLE result for H(k) proves every target schedule must reverse
at least k+1 baseline adjacent precedences. A FEASIBLE result is merely
a core-cover witness, not a valid job-shop schedule. UNKNOWN proves nothing.
"""
import argparse
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model


def check(cores,k,seconds,seed):
    model=cp_model.CpModel()
    x=[model.new_bool_var('x_%d'%i) for i in range(580)]
    model.add(sum(x)<=k)
    for core in cores:model.add(sum(x[i] for i in core)>=1)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    status=solver.solve(model)
    rec=dict(k=k,status=solver.status_name(status),
             conflicts=solver.num_conflicts,branches=solver.num_branches,
             elapsed=round(solver.wall_time,3))
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        cover=[i for i in range(580) if solver.value(x[i])]
        assert len(cover)<=k and all(set(cover).intersection(c) for c in cores)
        rec['hitting_set']=cover
    if status==cp_model.INFEASIBLE:
        rec['certified_necessary_violated_adjacent_arcs']=k+1
    return rec


def run(inp,out,seconds):
    raw=json.loads(inp.read_text())
    assert raw['target']==2005
    cores=raw['core_sets'];assert len(cores)>1000
    records=[]
    for k in (6,7,8):
        rec=check(cores,k,seconds,41+k)
        records.append(rec)
        print('RESULT',json.dumps(rec),flush=True)
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(dict(target=2005,baseline=2006,
             results=records,
             semantics='Only hitting-set cover of sampled proven UNSAT cores; core cover is not feasible job-shop schedule'),
             indent=2)+'\n')
        if rec['status']!='INFEASIBLE':break

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path(__file__).parent/'results'/'core-seed4107'/'core-analysis.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'core-cover-decision.json')
    p.add_argument('--seconds',type=int,default=120)
    a=p.parse_args();run(a.input,a.out,a.seconds)
