#!/usr/bin/env python3
"""Warm-started incumbent-conditioned CP optimization for ta41.

Different from prior deadline-feasibility runs: the full 2006 incumbent
with all 600 exact earliest start times is explicitly supplied as a feasible
hint to an optimization model with Cmax <=2006. The solver minimizes Cmax,
while 0, 4 or 5 entire machine orders remain pinned as large-neighborhood
reconstruction anchors. Every machine remains NoOverlap-constrained.

The research hypothesis is that preserving a valid 2006 witness and
optimizing from it is more useful than a pure 2005 feasibility query.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis

def main(a):
    routes,durs,orders=obtain()
    pos,dur=setup(routes,durs)
    assert evaluate(orders,pos,dur)==2006
    _,head,_,H=graph_analysis(orders,pos,dur)
    assert H==2006
    fixed={
      'allfree':[],
      'fixed4':[0,4,7,8],
      'fixed5a':[0,4,7,8,9],
      'fixed5b':[10,12,13,14,17],
      'fixed4b':[4,9,10,18],
    }[a.variant]
    model=cp_model.CpModel()
    s=[model.new_int_var(0,H,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,H,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        if m in fixed:
            for x,y in zip(orders[m],orders[m][1:]):
                model.add(s[y*20+pos[y][m]]>=e[x*20+pos[x][m]])
    makespan=model.new_int_var(0,H,'makespan')
    model.add_max_equality(makespan,e)
    model.minimize(makespan)
    for i in range(600):
        model.add_hint(s[i],head[i])
        model.add_hint(e[i],head[i]+dur[i])
    model.add_hint(makespan,H)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=a.workers
    solver.parameters.random_seed=a.seed
    start=time.monotonic()
    status=solver.solve(model)
    out=a.out;out.mkdir(parents=True,exist_ok=True)
    report=dict(instance='ta41',baseline=2006,target=2005,
      strategy='feasible incumbent-time hints, minimize Cmax, release whole machines, retain NoOverlap',
      variant=a.variant,seed=a.seed,fixed_machine_groups=fixed,
      solver_status=solver.status_name(status),wall_seconds=round(time.monotonic()-start,3),
      lower_bound=solver.best_objective_bound,conflicts=solver.num_conflicts,
      branches=solver.num_branches,ortools_version=__import__('ortools').__version__)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        machine_orders=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
                        for m in range(20)]
        score=evaluate(machine_orders,pos,dur)
        assert score is not None and score<=2006
        assert score<=solver.value(makespan)
        report['independent_dag_score']=score
        report['changed_machines']=sum(x!=y for x,y in zip(machine_orders,orders))
        if score<=2005:
            (out/'certificate.json').write_text(json.dumps({'machines':machine_orders},separators=(',',':'))+'\n')
    (out/'optimization.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--variant',choices=['allfree','fixed4','fixed5a','fixed5b','fixed4b'],required=True)
    p.add_argument('--seed',type=int,default=41)
    p.add_argument('--seconds',type=int,default=360)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
