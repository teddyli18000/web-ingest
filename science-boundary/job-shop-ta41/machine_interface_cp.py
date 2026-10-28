#!/usr/bin/env python3
"""Interface-based feasibility decomposition for ta41 at target Cmax=2005.

Unfix *entire machines* rather than isolated arcs. For every tested machine
subset F, retain all the incumbent orders on machines outside F while
allowing an exact CP-SAT solve to reorder all operations on machines F.
INFEASIBLE certifies that no target schedule lies in this full subspace;
UNKNOWN is explicitly not treated as evidence of nonexistence.
"""
import argparse
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate


def probe(orders,pos,dur,free,target,seconds,seed):
    model=cp_model.CpModel()
    start=[model.new_int_var(0,target,'s_%d'%i) for i in range(600)]
    end=[model.new_int_var(0,target,'e_%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(start[i],dur[i],end[i],'op_%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(start[j*20+k+1]>=end[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        if m not in free:
            for a,b in zip(orders[m],orders[m][1:]):
                model.add(start[b*20+pos[b][m]]>=end[a*20+pos[a][m]])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    started=time.monotonic()
    status=solver.solve(model)
    rec=dict(free_machines=sorted(free),fixed_machines=20-len(free),
             status=solver.status_name(status),elapsed=round(time.monotonic()-started,3),
             conflicts=solver.num_conflicts,branches=solver.num_branches)
    candidate=None
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        new=[]
        for m in range(20):
            new.append(sorted(range(30),key=lambda j:solver.value(start[j*20+pos[j][m]])))
        score=evaluate(new,pos,dur)
        assert score is not None and score<=target,(score,target)
        rec['independent_dag_score']=score
        candidate=new
    elif status==cp_model.INFEASIBLE:
        rec['proof_scope']='All schedules with these machines free and all other machine orders fixed are excluded at target'
    else:rec['proof_scope']='No proof; solver returned UNKNOWN'
    return rec,candidate


def main(out,seconds,seed):
    routes,durations,orders=obtain()
    pos,dur=setup(routes,durations)
    assert evaluate(orders,pos,dur)==2006
    subsets=[
        [16],
        [16,1],
        [16,1,3,11],
        [16,1,3,11,2,5,6,15],
        [16,1,3,11,2,5,6,15,0,4,7,9],
    ]
    out.mkdir(parents=True,exist_ok=True)
    results=[]
    for ix,free in enumerate(subsets):
        rec,cert=probe(orders,pos,dur,set(free),2005,seconds,seed+ix)
        results.append(rec)
        (out/'machine-subsets.json').write_text(
            json.dumps(dict(target=2005,baseline=2006,probes=results),indent=2)+'\n')
        print(json.dumps(rec,separators=(',',':')),flush=True)
        if cert is not None:
            (out/'certificate.json').write_text(json.dumps({'machines':cert},separators=(',',':'))+'\n')
            break

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-interfaces')
    p.add_argument('--seconds',type=int,default=60)
    p.add_argument('--seed',type=int,default=41)
    a=p.parse_args();main(a.out,a.seconds,a.seed)
