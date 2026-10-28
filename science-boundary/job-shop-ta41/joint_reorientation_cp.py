#!/usr/bin/env python3
"""Search <=2005 using simultaneous, explicitly reoriented machine adjacencies.

Unlike relaxed fixed arcs, every violated baseline adjacency u->v becomes
an *explicit reversed disjunction* v->u, so replacement resource effects
cannot disappear in a partial-order relaxation. The 1,433 previously
verified infeasibility cores are valid learned cuts for the binary
reorientation variables. Optimize Hamming distance in baseline adjacent
orders, not the makespan; target horizon is fixed at 2005.

This is exploratory exact CP-SAT: OPTIMAL proves the minimum distance
subject to Cmax<=2005; a FEASIBLE candidate is independently rescored
against the original DAG and Few Shots verifier. UNKNOWN proves nothing.
"""
import argparse
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate


def run(out,seconds,workers,seed):
    path=Path(__file__).resolve().parent
    raw=json.loads((path/'results'/'core-seed4107'/'core-analysis.json').read_text())
    cores=raw['core_sets']
    assert raw['target']==2005 and len(cores)>=1000
    routes,durations_by_job,base=obtain()
    pos,dur=setup(routes,durations_by_job)
    assert evaluate(base,pos,dur)==2006
    model=cp_model.CpModel()
    T=2005
    starts=[model.new_int_var(0,T,'start_%d'%i) for i in range(600)]
    ends=[model.new_int_var(0,T,'end_%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(starts[i],dur[i],ends[i],'interval_%d'%i)
               for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j*20+k+1]>=ends[j*20+k])
    broken=[]
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        for k,(j,h) in enumerate(zip(base[m],base[m][1:])):
            u=j*20+pos[j][m];v=h*20+pos[h][m]
            x=model.new_bool_var('reverse_%d_%d'%(m,k))
            model.add(starts[v]>=ends[u]).only_enforce_if(x.Not())
            model.add(starts[u]>=ends[v]).only_enforce_if(x)
            broken.append(x)
    assert len(broken)==580
    for c in cores:
        model.add(sum(broken[i] for i in c)>=1)
    model.add(sum(broken)>=7) # prior CP-SAT-certified hitting-set bound
    model.minimize(sum(broken))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=seed
    now=time.monotonic()
    status=solver.solve(model)
    rec=dict(target=2005,initial_score=2006,
             status=solver.status_name(status),elapsed_seconds=round(time.monotonic()-now,3),
             solver_best_objective_bound=solver.best_objective_bound,
             learned_core_count=len(cores),num_search_workers=workers,
             conflicts=solver.num_conflicts,branches=solver.num_branches,
             claim='No schedule claimed without feasible certificate and independent official verifier')
    out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        candidate=[]
        for m in range(20):
            candidate.append(sorted(range(30),key=lambda j:solver.value(starts[j*20+pos[j][m]])))
        val=evaluate(candidate,pos,dur)
        assert val is not None and val<=2005,val
        original_inversions=sum(solver.value(x) for x in broken)
        assert all(sum(solver.value(broken[i]) for i in c)>=1 for c in cores)
        rec.update(verified_dag_makespan=val,broken_original_adjacencies=original_inversions,
                   solver_objective=solver.objective_value)
        (out/'certificate.json').write_text(json.dumps({'machines':candidate},separators=(',',':'))+'\n')
    (out/'joint-reorientation.json').write_text(json.dumps(rec,indent=2)+'\n')
    print('RESULT',json.dumps(rec),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seconds',type=int,default=540)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'joint-reorientation')
    a=p.parse_args();run(a.out,a.seconds,a.workers,a.seed)
