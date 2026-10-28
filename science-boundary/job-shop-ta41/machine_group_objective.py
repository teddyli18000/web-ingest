#!/usr/bin/env python3
"""Minimize number of wholly changed machine sequences at a 2005 horizon.

Unlike baseline-arc edits, the binary variable changed[m] controls an entire
machine's 29 incumbent adjacencies. If unchanged, all old machine orders
are pinned; if changed, NoOverlap chooses any sequence. Objective minimizes
# changed machines, not makespan, with target makespan <=2005 enforced.

This representation directly searches coordinated machine interfaces, which
the exhaustive 299-subset experiment proved necessary. Learned core cuts
are projected onto machine groups as valid redundant constraints.
"""
import argparse
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate


def main(out,seconds,workers):
    root=Path(__file__).parent
    cores=json.loads((root/'results'/'core-seed4107'/'core-analysis.json').read_text())['core_sets']
    routes,ds,orders=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    model=cp_model.CpModel()
    target=2005
    st=[model.new_int_var(0,target,'s%d'%i) for i in range(600)]
    en=[model.new_int_var(0,target,'e%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(st[i],dur[i],en[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(st[j*20+k+1]>=en[j*20+k])
    changed=[model.new_bool_var('changed_machine_%d'%m) for m in range(20)]
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        for j,h in zip(orders[m],orders[m][1:]):
            model.add(st[h*20+pos[h][m]]>=en[j*20+pos[j][m]]).only_enforce_if(changed[m].Not())
    group_cores={tuple(sorted(set(i//29 for i in c))) for c in cores}
    for machines in group_cores:model.add(sum(changed[m] for m in machines)>=1)
    model.add(sum(changed)>=5)
    model.minimize(sum(changed))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=4107
    t=time.monotonic()
    status=solver.solve(model)
    result=dict(target=2005,baseline=2006,status=solver.status_name(status),
                elapsed=round(time.monotonic()-t,3),num_group_core_cuts=len(group_cores),
                bound_on_changed_machines=solver.best_objective_bound,
                conflicts=solver.num_conflicts,branches=solver.num_branches,
                model='whole-machine change binary with exact 600 interval NoOverlap')
    out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        chosen=[]
        for m in range(20):
            chosen.append(sorted(range(30),key=lambda j:solver.value(st[j*20+pos[j][m]])))
        score=evaluate(chosen,pos,dur)
        assert score is not None and score<=2005,score
        real_changes=sum(chosen[m]!=orders[m] for m in range(20))
        assert real_changes<=sum(solver.value(x) for x in changed)
        result.update(verified_dag_makespan=score,real_changed_machines=real_changes,
                      declared_changed_machines=sum(solver.value(x) for x in changed),
                      solver_objective=solver.objective_value)
        (out/'certificate.json').write_text(json.dumps({'machines':chosen},separators=(',',':'))+'\n')
    (out/'group-objective.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-group-objective')
    p.add_argument('--seconds',type=int,default=540)
    p.add_argument('--workers',type=int,default=4)
    a=p.parse_args();main(a.out,a.seconds,a.workers)
