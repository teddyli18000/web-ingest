#!/usr/bin/env python3
"""Exhaustive machine-group cardinality exclusions for <=2005 ta41.

All eight machines that carry *any* critical baseline machine arc are
free to reorder. Select k more machines from the remaining twelve,
and pin the incumbent order on all other machines. Every INFEASIBLE
result excludes that entire enormous subspace, not merely local swaps.

If ALL C(12,k) subspaces are INFEASIBLE for every k<=K, then any
<=2005 schedule must change the machine order on at least K+1 of
the 12 noncritical machines. That is a formal restricted-coupling
statement; UNKNOWN invalidates the exclusion for its level.
"""
import argparse
import itertools
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate


def make_model(orders,pos,dur,target):
    model=cp_model.CpModel()
    s=[model.new_int_var(0,target,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,target,'e%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(s[i],dur[i],e[i],'i%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    keep=[model.new_bool_var('keep_m%d'%m) for m in range(20)]
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        for j,h in zip(orders[m],orders[m][1:]):
            model.add(s[h*20+pos[h][m]]>=e[j*20+pos[j][m]]).only_enforce_if(keep[m])
    return model,keep,s


def run(out,levels,seconds,total_seconds):
    routes,ds,orders=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    critical={1,2,3,5,6,11,15,16}
    noncritical=sorted(set(range(20))-critical)
    assert len(noncritical)==12
    model,keep,s=make_model(orders,pos,dur,2005)
    out.mkdir(parents=True,exist_ok=True)
    reports=[]
    started=time.monotonic()
    candidate=None
    proven_through=-1
    for k in range(levels+1):
        stat={'additional_noncritical_machines':k,'total_subspaces':0,
              'infeasible':0,'feasible':0,'unknown':0,
              'complete':False,'examples_unknown':[]}
        for chosen in itertools.combinations(noncritical,k):
            if time.monotonic()-started>total_seconds:
                stat['reason']='total time limit reached'
                break
            free=critical.union(chosen)
            model.clear_assumptions()
            model.add_assumptions([keep[m] for m in range(20) if m not in free])
            solver=cp_model.CpSolver()
            solver.parameters.max_time_in_seconds=seconds
            solver.parameters.num_search_workers=1
            solver.parameters.random_seed=41
            status=solver.solve(model)
            name=solver.status_name(status)
            stat['total_subspaces']+=1
            if status==cp_model.INFEASIBLE:stat['infeasible']+=1
            elif status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
                stat['feasible']+=1
                candidate=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]])) for m in range(20)]
                makespan=evaluate(candidate,pos,dur)
                assert makespan is not None and makespan<=2005,makespan
                stat['validated_dag_score']=makespan
                break
            else:
                stat['unknown']+=1
                if len(stat['examples_unknown'])<5:
                    stat['examples_unknown'].append(list(chosen))
                # Cannot claim a global cardinality exclusion for this level.
                break
        from math import comb
        stat['complete']=stat['infeasible']==comb(12,k)
        if stat['complete']:proven_through=k
        reports.append(stat)
        result=dict(target=2005,baseline=2006,
                    always_free_critical_machines=sorted(critical),
                    formerly_noncritical_machines=noncritical,
                    proven_all_subspaces_through_additional_k=proven_through,
                    proved_minimum_noncritical_changed_machines=proven_through+1,
                    proof_scope='Only original 2006 baseline; complete INFEASIBLE coverage of all subsets up to K needed',
                    levels=reports,
                    elapsed=round(time.monotonic()-started,3))
        (out/'machine-cardinality.json').write_text(json.dumps(result,indent=2)+'\n')
        print('LEVEL',json.dumps(stat),flush=True)
        if candidate is not None:
            (out/'certificate.json').write_text(json.dumps({'machines':candidate},separators=(',',':'))+'\n')
            break
        if not stat['complete']:break
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='levels'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-cardinality')
    p.add_argument('--levels',type=int,default=3)
    p.add_argument('--seconds',type=float,default=3)
    p.add_argument('--total-seconds',type=int,default=480)
    a=p.parse_args();run(a.out,a.levels,a.seconds,a.total_seconds)
