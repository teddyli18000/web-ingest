#!/usr/bin/env python3
"""CP-SAT optimization from independently valid, backbone-breaking ta41 seeds.

Previous exact attempts with Cmax<=2005 were UNKNOWN because they lacked a
feasible incumbent that already reverses one of the 21 proven shared-core
precedences. The single-machine insertion proof now supplies such seeds
with makespans from 2024 onward.

For each selected arc, use its machine-order seed to compute exact
earliest starts. Optimize the full 600-interval resource problem with
  (1) Cmax upper-bounded by the VALID seed's makespan (not an infeasible
      2005 demand),
  (2) the selected shared-core orientation reversed,
  (3) hints equal to a VALID non-overlapping schedule,
  (4) first a small set of machine orders fixed to stabilize the search,
      then all machine orders released.
Any improvement relative to current seed is kept and rehinted. No UNKNOWN
is treated as evidence. A score<=2005 is independently rescored and
then independently officially verified in the Action.
"""
import argparse,json,random,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis

def optimize(base,seed_orders,pos,dur,arc,time_budget,random_seed,fixed):
    _,hint,_,H=graph_analysis(seed_orders,pos,dur)
    assert H==evaluate(seed_orders,pos,dur)
    model=cp_model.CpModel()
    starts=[model.new_int_var(0,H,'s%d'%i) for i in range(600)]
    ends=[model.new_int_var(0,H,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(starts[i],dur[i],ends[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j*20+k+1]>=ends[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        if m in fixed:
            for j,h in zip(seed_orders[m],seed_orders[m][1:]):
                model.add(starts[h*20+pos[h][m]]>=ends[j*20+pos[j][m]])
    m,j,h=arc['machine'],arc['from_job'],arc['to_job']
    model.add(starts[j*20+pos[j][m]]>=ends[h*20+pos[h][m]])
    makespan=model.new_int_var(0,H,'Cmax')
    model.add_max_equality(makespan,ends)
    model.minimize(makespan)
    for i in range(600):
        model.add_hint(starts[i],hint[i])
        model.add_hint(ends[i],hint[i]+dur[i])
    model.add_hint(makespan,H)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=time_budget
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=random_seed
    tic=time.monotonic();status=solver.solve(model)
    report=dict(status=solver.status_name(status),seconds=round(time.monotonic()-tic,3),
                initial_valid_makespan=H,
                fixed_machine_orders=sorted(fixed),
                solver_objective_bound=solver.best_objective_bound,
                branches=solver.num_branches,
                conflicts=solver.num_conflicts)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):return report,None
    result=[sorted(range(30),key=lambda j:solver.value(starts[j*20+pos[j][m]]))
            for m in range(20)]
    score=evaluate(result,pos,dur)
    assert score is not None and score<=H,(score,H)
    assert result[m].index(h)<result[m].index(j)
    report['independent_dag_makespan']=score
    report['changed_machines_from_baseline']=sum(a!=b for a,b in zip(base,result))
    return report,result

def main(a):
    routes,ds,base=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(base,pos,dur)==2006
    root=Path(__file__).parent/'results'
    arcs=json.loads((root/'consensus-five-parents'/'consensus-analysis.json').read_text())['proven_unsat_core']
    seed=json.loads((root/'reversal-warm-seeds'/('reversal-warm-%02d.json'%a.arc)).read_text())['machines']
    initial=evaluate(seed,pos,dur)
    assert initial is not None and initial>2006
    arc=arcs[a.arc];m=arc['machine']
    assert seed[m].index(arc['to_job'])<seed[m].index(arc['from_job'])
    a.out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(a.seed)
    stages=[];current=seed;best_score=initial
    for i in range(a.stages):
        if i%3==0: fixed=set()
        elif i%3==1:
            fixed=set(rng.sample([x for x in range(20) if x!=m],2))
        else:
            fixed=set(rng.sample([x for x in range(20) if x!=m],4))
        rec,improved=optimize(base,current,pos,dur,arc,a.phase_seconds,
                             a.seed+i*1100,fixed)
        rec['stage']=i
        if improved is not None:
            score=evaluate(improved,pos,dur)
            if score<best_score:
                best_score=score;current=improved
                (a.out/'best-reversed-order.json').write_text(
                    json.dumps({'machines':current},separators=(',',':'))+'\n')
            if score<=2006:
                (a.out/'neutral-certificate.json').write_text(
                    json.dumps({'machines':current},separators=(',',':'))+'\n')
            if score<=2005:
                (a.out/'certificate.json').write_text(
                    json.dumps({'machines':current},separators=(',',':'))+'\n')
                stages.append(rec)
                break
        stages.append(rec)
        print('STAGE',a.arc,i,'score',best_score,'status',rec['status'],
              'fixed',len(fixed),flush=True)
    summary=dict(instance='ta41',baseline=2006,target=2005,
        method='valid inverted-21-core schedule as CP-SAT optimization hint with alternating 0/2/4 machine-order anchors',
        selected_shared_core_arc=a.arc,original_start_score=initial,
        best_reversed_schedule_score=best_score,improved=best_score<=2005,
        neutral_with_core_reversed=best_score==2006,
        stages=stages,seed=a.seed,
        all_hard_NoOverlap=True,
        note='Every produced schedule rechecked against original disjunctive DAG. Official Few Shots verifier is independent required next step.')
    (a.out/'warm-descent.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in summary.items() if k!='stages'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--arc',type=int,required=True)
    p.add_argument('--stages',type=int,default=4)
    p.add_argument('--phase-seconds',type=float,default=75)
    p.add_argument('--seed',type=int,default=41)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
