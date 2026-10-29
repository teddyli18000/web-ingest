#!/usr/bin/env python3
"""A genuinely different ta41 neighborhood: globally eject and reinsert jobs.

For each chosen subset S of <=2 jobs (30 singles + 435 pairs), retain
the original relative order among all jobs NOT in S on every machine,
and allow the jobs in S to be reinserted anywhere on each of their
20 machines, subject to unconditional job-order and NoOverlap constraints.

One ejected job may change up to 20 full machine permutations at once,
so this representation bypasses the >=15 changed machine-order
obstruction without requiring a massive neighborhood in JOB space.

This is an exact (not local-swap) subspace. INFEASIBLE certifies absence
of a <=2005 schedule in that job-ejection subspace. A feasible CP
candidate is recanonicalized to machine orders and DAG checked.
"""
import argparse
import itertools
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain, setup, evaluate


def counterfactual(orders,pos,duration,ejected,target,seconds,seed):
    model=cp_model.CpModel()
    starts=[model.new_int_var(0,target,"s%d"%i) for i in range(600)]
    ends=[model.new_int_var(0,target,"e%d"%i) for i in range(600)]
    intervals=[model.new_interval_var(starts[i],duration[i],ends[i],"op%d"%i)
               for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j*20+k+1]>=ends[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        survivors=[j for j in orders[m] if j not in ejected]
        for j,h in zip(survivors,survivors[1:]):
            model.add(starts[h*20+pos[h][m]]>=ends[j*20+pos[j][m]])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=seed
    t=time.monotonic()
    status=solver.solve(model)
    rec={'ejected_jobs':sorted(ejected),'status':solver.status_name(status),
         'elapsed_seconds':round(time.monotonic()-t,3),
         'conflicts':solver.num_conflicts,'branches':solver.num_branches}
    candidate=None
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        candidate=[]
        for m in range(20):
            candidate.append(sorted(range(30),key=lambda j:solver.value(starts[j*20+pos[j][m]])))
        val=evaluate(candidate,pos,duration)
        assert val is not None and val<=target,(val,ejected)
        rec['verified_dag_makespan']=val
        rec['changed_machine_orders']=sum(a!=b for a,b in zip(orders,candidate))
    return rec,candidate


def solve(a):
    routes,ds,orders=obtain()
    pos,duration=setup(routes,ds)
    assert evaluate(orders,pos,duration)==2006
    subsets=list(itertools.combinations(range(30),1))+list(itertools.combinations(range(30),2))
    assert len(subsets)==465
    chosen=[(idx,set(jobs)) for idx,jobs in enumerate(subsets) if idx%a.shards==a.shard]
    result={
        'instance':'ta41','baseline':2006,'target':2005,
        'neighborhood':'job-centered all-machine reinsertion preserving all non-ejected jobs relative orders',
        'total_job_ejection_subspaces':465,
        'shard':a.shard,'shards':a.shards,'expected_subspaces':len(chosen),
        'processed_subspaces':0,'proven_infeasible':0,'unknown':0,'feasible':0,
        'outcomes':[],'complete':False,
        'methodological_note':'NoOverlap is never relaxed. Selected jobs can move across all 20 machines; the result is not bounded by adjacency or changed-machine distance.'
    }
    a.out.mkdir(parents=True,exist_ok=True)
    began=time.monotonic()
    for idx,jobs in chosen:
        if time.monotonic()-began>a.total_seconds-2:break
        rec,candidate=counterfactual(orders,pos,duration,jobs,2005,
            min(a.per_subspace_seconds,max(0.5,a.total_seconds-(time.monotonic()-began)-1)),
            a.seed+idx)
        rec['global_index']=idx
        result['outcomes'].append(rec)
        if rec['status']=='INFEASIBLE':result['proven_infeasible']+=1
        elif rec['status'] in ('FEASIBLE','OPTIMAL'):
            result['feasible']+=1
            (a.out/'certificate.json').write_text(json.dumps({'machines':candidate},separators=(',',':'))+'\n')
            break
        else:result['unknown']+=1
        result['processed_subspaces']+=1
        if result['processed_subspaces']%15==0:
            print('PROGRESS',a.shard,result['processed_subspaces'],len(chosen),
                  'unknown',result['unknown'],'seconds',round(time.monotonic()-began,1),flush=True)
    result['processed_subspaces']=len(result['outcomes'])
    result['complete']=result['processed_subspaces']==len(chosen)
    result['elapsed_seconds']=round(time.monotonic()-began,3)
    (a.out/'job-ejection.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='outcomes'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,default=5)
    p.add_argument('--seed',type=int,default=9200)
    p.add_argument('--per-subspace-seconds',type=float,default=3)
    p.add_argument('--total-seconds',type=int,default=570)
    p.add_argument('--out',type=Path,required=True)
    solve(p.parse_args())
