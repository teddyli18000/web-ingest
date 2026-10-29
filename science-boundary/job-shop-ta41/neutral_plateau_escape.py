#!/usr/bin/env python3
"""Search the equal-makespan manifold by maximizing machine-order diversity.

The 2006 incumbent is a *feasible witness*, not the center of the entire
search. Select a cohort of jobs; hold only non-cohort jobs' relative
machine sequences fixed, while every machine keeps its NoOverlap
constraint. Maximize the number of machine permutations changed, then
the number of reversed incumbent adjacency relations, at Cmax<=2006.

This deliberately seeks distant, equal-quality seeds rather than
minimizing makespan from the old incumbent. From each verified neutral
seed, an exact 2005 CP feasibility portfolio re-inserts 1-3 jobs globally.

A neutral schedule is not a new record. An improving certificate must
pass the full original DAG evaluation and the external Few Shots verifier.
"""
import argparse,itertools,json,random,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis
from job_ejection_dag import lower_bound
from job_ejection_search import counterfactual

COHORTS={
  "critical8":[0,4,5,9,14,15,24,26],
  "mixed12":[0,1,4,5,8,9,13,14,15,19,24,26],
  "mixed16":[0,1,3,4,5,6,7,8,9,11,13,14,15,19,24,26],
  "mixed20":[0,1,2,3,4,5,6,7,8,9,11,12,13,14,15,18,19,23,24,26],
}

def diversify(orders,pos,dur,jobs,seconds,seed):
    _,hint,_,H=graph_analysis(orders,pos,dur)
    assert H==2006
    model=cp_model.CpModel()
    s=[model.new_int_var(0,H,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,H,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19): model.add(s[j*20+k+1]>=e[j*20+k])
    flips=[]
    machine_changes=[]
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        survivors=[j for j in orders[m] if j not in jobs]
        for j,h in zip(survivors,survivors[1:]):
            model.add(s[h*20+pos[h][m]]>=e[j*20+pos[j][m]])
        local=[]
        for idx,(j,h) in enumerate(zip(orders[m],orders[m][1:])):
            if j not in jobs and h not in jobs: continue
            u=j*20+pos[j][m];v=h*20+pos[h][m]
            b=model.new_bool_var('invert_%d_%d'%(m,idx))
            model.add(s[u]>=e[v]).only_enforce_if(b)
            model.add(s[v]>=e[u]).only_enforce_if(b.Not())
            model.add_hint(b,0)
            local.append(b);flips.append(b)
        group=model.new_bool_var('changed_m%d'%m)
        if local:model.add_max_equality(group,local)
        else:model.add(group==0)
        model.add_hint(group,0)
        machine_changes.append(group)
    model.maximize(100*sum(machine_changes)+sum(flips))
    for i in range(600):
        model.add_hint(s[i],hint[i])
        model.add_hint(e[i],hint[i]+dur[i])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    st=time.monotonic()
    status=solver.solve(model)
    outcome=dict(status=solver.status_name(status),
                 seconds=round(time.monotonic()-st,3),
                 cohort=sorted(jobs),
                 objective_bound=solver.best_objective_bound,
                 conflicts=solver.num_conflicts,branches=solver.num_branches)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        candidate=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
                   for m in range(20)]
        makespan=evaluate(candidate,pos,dur)
        assert makespan is not None and makespan<=2006,makespan
        true_diff=sum(candidate[m]!=orders[m] for m in range(20))
        flipped=sum(solver.value(b) for b in flips)
        assert sum(solver.value(b) for b in machine_changes)==true_diff
        outcome.update(score=makespan,changed_machine_orders=true_diff,
                       reversed_baseline_adjacent_relations=flipped,
                       chosen_objective=solver.objective_value)
        return outcome,candidate
    return outcome,None

def escape(neutral,pos,dur,seconds,seed,output):
    rows=[];begin=time.monotonic()
    singles=[(lower_bound(neutral,pos,dur,{j}),(j,)) for j in range(30)]
    pairs=[(lower_bound(neutral,pos,dur,set(t)),t)
           for t in itertools.combinations(range(30),2)]
    triples=[(lower_bound(neutral,pos,dur,set(t)),t)
             for t in itertools.combinations(range(30),3)]
    ranked=sorted(singles)+sorted(pairs)+sorted(triples)
    screened=set();scheduled=[]
    for v,cohort in ranked:
        if v>2005: continue
        if len(cohort)==1 and len([x for x in scheduled if len(x)==1])>=8:continue
        if len(cohort)==2 and len([x for x in scheduled if len(x)==2])>=24:continue
        if len(cohort)==3 and len([x for x in scheduled if len(x)==3])>=60:continue
        scheduled.append(cohort)
    for n,cohort in enumerate(scheduled):
        if time.monotonic()-begin>seconds-2:break
        val,cert=counterfactual(neutral,pos,dur,set(cohort),2005,
            min(1.8,max(.4,seconds-(time.monotonic()-begin)-1)),seed+n)
        val['cohort_size']=len(cohort)
        rows.append(val)
        if val['status'] in ('FEASIBLE','OPTIMAL'):
            score=evaluate(cert,pos,dur)
            assert score is not None and score<=2005
            (output/'certificate.json').write_text(
                json.dumps({'machines':cert},separators=(',',':'))+'\n')
            break
    return dict(total_candidate_cohorts=len(scheduled),tested=len(rows),
                proved_infeasible=sum(x['status']=='INFEASIBLE' for x in rows),
                unknown=sum(x['status']=='UNKNOWN' for x in rows),
                improved=sum(x['status'] in ('FEASIBLE','OPTIMAL') for x in rows),
                elapsed=round(time.monotonic()-begin,3),
                outcomes=rows)

def main(a):
    routes,ds,base=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(base,pos,dur)==2006
    a.out.mkdir(parents=True,exist_ok=True)
    div,neutral=diversify(base,pos,dur,set(COHORTS[a.variant]),a.seconds,a.seed)
    result=dict(instance='ta41',baseline=2006,variant=a.variant,
                exact_resource_model=True,diversification=div,escape=None)
    if neutral is not None and div['changed_machine_orders']>0:
        (a.out/'neutral-certificate.json').write_text(
            json.dumps({'machines':neutral},separators=(',',':'))+'\n')
        if div['score']<=2005:
            (a.out/'certificate.json').write_text(
                json.dumps({'machines':neutral},separators=(',',':'))+'\n')
        else:
            result['escape']=escape(neutral,pos,dur,a.escape_seconds,a.seed+100,a.out)
    (a.out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({**result,'escape':None if not result['escape']
          else {k:v for k,v in result['escape'].items() if k!='outcomes'}}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--variant',choices=tuple(COHORTS),required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--seconds',type=int,default=125)
    p.add_argument('--escape-seconds',type=int,default=150)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
