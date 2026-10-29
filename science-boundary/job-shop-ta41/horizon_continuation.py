#!/usr/bin/env python3
"""Horizon continuation through a previously unvisited ta41 backbone orientation.

The 21-arc independently extracted shared-precedence UNSAT core shows that
an improved schedule must reverse at least one of its directed job pairs.
Direct CP-SAT Cmax<=2005 with each reversal was UNKNOWN.

Instead of demanding 2005 immediately, first find any feasible 2600-time
schedule with the reversal and minimize Cmax. Persist the exact completed
machine order as the next feasibility hint, and progressively tighten
the allowed horizon. This homotopy/continuation crosses resource-order
phase changes at looser horizons before tackling the narrow 2005 target.

Different from earlier unconditional 2005 SAT tests:
  - Full NoOverlap on all machines ALWAYS
  - Mandatory reverse of a proven 5-parent backbone core relation
  - Warm-start with a genuinely distinct, feasible reversed-arc schedule
  - Progressive lower horizons and repeated objective minimization
  - Hard DAG reevaluation of every generated candidate
UNKNOWN is not a proof. A schedule with <=2005 is held for official
Few Shots independent verification in the Action.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis

HORIZONS=[2600,2350,2200,2125,2075,2050,2025,2010,2006,2005]

def stage(base,pos,dur,arc,horizon,seed,secs,hint_starts):
    model=cp_model.CpModel()
    start=[model.new_int_var(0,horizon,'s%d'%i) for i in range(600)]
    end=[model.new_int_var(0,horizon,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(start[i],dur[i],end[i],'iv%d'%i)
        for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(start[j*20+k+1]>=end[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    m,j,h=arc['machine'],arc['from_job'],arc['to_job']
    model.add(start[j*20+pos[j][m]]>=end[h*20+pos[h][m]])
    C=model.new_int_var(0,horizon,'Cmax')
    model.add_max_equality(C,end)
    model.minimize(C)
    if hint_starts is not None:
        for i in range(600):
            ss=min(horizon,max(0,hint_starts[i]))
            model.add_hint(start[i],ss)
            model.add_hint(end[i],min(horizon,ss+dur[i]))
        model.add_hint(C,min(horizon,max(hint_starts[i]+dur[i] for i in range(600))))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=secs
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    wall=time.monotonic()
    outcome=solver.solve(model)
    record={'horizon':horizon,'status':solver.status_name(outcome),
            'wall_seconds':round(time.monotonic()-wall,3),
            'best_objective_bound':solver.best_objective_bound,
            'branches':solver.num_branches,'conflicts':solver.num_conflicts}
    if outcome not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return record,None,None
    order=[sorted(range(30),key=lambda j:solver.value(start[j*20+pos[j][m]]))
           for m in range(20)]
    score=evaluate(order,pos,dur)
    assert score is not None and score<=horizon,score
    assert order[m].index(h)<order[m].index(j)
    record['score']=score
    record['change_machines']=sum(order[i]!=base[i] for i in range(20))
    hint=[solver.value(start[i]) for i in range(600)]
    return record,order,hint


def run(args):
    routes,durations_by_job,base=obtain()
    pos,dur=setup(routes,durations_by_job)
    assert evaluate(base,pos,dur)==2006
    data=json.loads((Path(__file__).parent/'results/consensus-five-parents/consensus-analysis.json').read_text())
    assert data['unsat_core_size']==21
    arc=data['proven_unsat_core'][args.arc]
    _,baseline_starts,_,C=graph_analysis(base,pos,dur)
    assert C==2006
    out=args.out;out.mkdir(parents=True,exist_ok=True)
    hint_starts=baseline_starts
    current_best=1000000
    trajectory=[]
    found_order=None
    began=time.monotonic()
    for index,horizon in enumerate(HORIZONS):
        if time.monotonic()-began>args.total_seconds-3:break
        # If a genuine feasible reversed-arc seed at Cmax<=best is known,
        # do not abandon it while searching a stricter horizon.
        secs=min(args.phase_seconds,
                 max(1,args.total_seconds-(time.monotonic()-began)-2))
        rec,order,hints=stage(base,pos,dur,arc,horizon,
                              args.seed+index*710,secs,hint_starts)
        trajectory.append(rec)
        if order is not None:
            assert evaluate(order,pos,dur)==rec['score']
            if rec['score']<current_best:
                current_best=rec['score'];found_order=order
                (out/'best-reversed-order.json').write_text(
                    json.dumps({'machines':order},separators=(',',':'))+'\n')
            hint_starts=hints
            if rec['score']<=2006:
                (out/'neutral-certificate.json').write_text(
                    json.dumps({'machines':order},separators=(',',':'))+'\n')
            if rec['score']<=2005:
                (out/'certificate.json').write_text(
                    json.dumps({'machines':order},separators=(',',':'))+'\n')
                print('IMPROVEMENT SCORE',rec['score'],'horizon',horizon,flush=True)
                break
        print('STAGE',args.arc,index,'horizon',horizon,rec['status'],
              'best',current_best,'elapsed',round(time.monotonic()-began,1),flush=True)
    result={
        'instance':'ta41','baseline':2006,'target':2005,
        'core_arc_index':args.arc,'mandatory_reversal':arc,
        'continuation_horizons':HORIZONS,
        'complete_target_coverage':False,
        'best_reversed_feasible_makespan':None if found_order is None else current_best,
        'found_improved_certificate':current_best<=2005,
        'found_neutral_reversed_certificate':current_best<=2006,
        'stages':trajectory,
        'elapsed_seconds':round(time.monotonic()-began,3),
        'semantics':'All stages retain hard original machine NoOverlap, job precedence, and mandatory reversed shared-core arc; UNKNOWN is inconclusive. An improving certificate requires external official verification.'
    }
    (out/'continuation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='stages'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--arc',type=int,required=True)
    p.add_argument('--seed',type=int,default=2026)
    p.add_argument('--total-seconds',type=int,default=320)
    p.add_argument('--phase-seconds',type=float,default=40)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
