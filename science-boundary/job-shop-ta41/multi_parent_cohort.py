#!/usr/bin/env python3
"""Multi-parent, conflict-guided global job-cohort repair for ta41.

Research question: full 1/2/3-job reinsertion near the original 2006
incumbent is infeasible. Are *larger* globally coupled job moves near
different, independently verified 2006-neutral incumbents more productive?

Cross parents (baseline, critical8, mixed20) with two model semantics:
- deadline: exact Cmax<=2005 feasibility (hard resource NoOverlap).
- optimize: warm-start at a verified feasible 2006 incumbent and minimize
  Cmax<=2006, a controlled way to preserve a viable basin during repair.

The removed cohort can move freely on all machines; survivor relative
machine orders stay fixed. Every candidate is rescored by the independent
DAG evaluator; <=2005 candidates require the official Few Shots verifier.

This is an exploratory portfolio. A finite UNSAT result excludes only
that exact parent/cohort subspace. UNKNOWN proves nothing.
"""
import argparse
import collections
import json
import random
import time
from pathlib import Path

from ortools.sat.python import cp_model
from search import obtain, setup, evaluate
from core_guided_lns import graph_analysis
from job_ejection_search import counterfactual
from job_ejection_dag import lower_bound

ROOT=Path(__file__).resolve().parent


def verified_parent(name, baseline, pos, durations):
    if name=='baseline':
        return baseline
    root=ROOT/'results'/('neutral-'+name)
    verdict=json.loads((root/'neutral-verdict.json').read_text())
    assert verdict['valid'] and int(verdict['score'])==2006,verdict
    parent=json.loads((root/'neutral-certificate.json').read_text())['machines']
    assert evaluate(parent,pos,durations)==2006
    return parent


def priority_jobs(parent,baseline):
    evidence=json.loads((ROOT/'results'/'consensus-five-parents'/
                         'consensus-analysis.json').read_text())
    assert evidence['status']=='INFEASIBLE' and evidence['unsat_core_size']==21
    freq=collections.Counter()
    for c in evidence['proven_unsat_core']:
        freq[c['from_job']]+=1
        freq[c['to_job']]+=1
    displace=collections.Counter()
    for m in range(20):
        rb={j:i for i,j in enumerate(baseline[m])}
        rp={j:i for i,j in enumerate(parent[m])}
        for j in range(30):
            displace[j]+=abs(rb[j]-rp[j])
    return freq,displace


def cohorts(parent,baseline,seed):
    rng=random.Random(seed)
    freq,displace=priority_jobs(parent,baseline)
    options=[]
    seen=set()
    for n in (6,8,10,12,15):
        for variant in ('core','diff','uniform'):
            jobs=set()
            if variant=='core':
                jobs.update(sorted(range(30),key=lambda j:(-freq[j],j))[:min(3,n)])
            elif variant=='diff':
                jobs.update(sorted(range(30),key=lambda j:(-displace[j],j))[:min(3,n)])
            remaining=[j for j in range(30) if j not in jobs]
            rng.shuffle(remaining)
            jobs.update(remaining[:n-len(jobs)])
            pair=tuple(sorted(jobs))
            if pair not in seen:
                options.append(dict(jobs=pair,size=n,strategy=variant))
                seen.add(pair)
    assert len(options)==15,len(options)
    return options


def objective_repair(parent,pos,duration,ejected,seconds,seed):
    horizon=2006
    model=cp_model.CpModel()
    start=[model.new_int_var(0,horizon,'s%d'%i) for i in range(600)]
    end=[model.new_int_var(0,horizon,'e%d'%i) for i in range(600)]
    interval=[model.new_interval_var(start[i],duration[i],end[i],'iv%d'%i)
              for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(start[j*20+k+1]>=end[j*20+k])
    for m in range(20):
        model.add_no_overlap([interval[j*20+pos[j][m]] for j in range(30)])
        survive=[j for j in parent[m] if j not in ejected]
        for a,b in zip(survive,survive[1:]):
            model.add(start[b*20+pos[b][m]]>=end[a*20+pos[a][m]])
    cmax=model.new_int_var(0,horizon,'Cmax')
    model.add_max_equality(cmax,end)
    model.minimize(cmax)
    _,earliest,_,original=graph_analysis(parent,pos,duration)
    assert original==2006
    for i in range(600):
        model.add_hint(start[i],earliest[i])
        model.add_hint(end[i],earliest[i]+duration[i])
    model.add_hint(cmax,original)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    t=time.monotonic()
    status=solver.solve(model)
    rec={'status':solver.status_name(status),
         'elapsed_seconds':round(time.monotonic()-t,3),
         'objective_bound':solver.best_objective_bound,
         'branches':solver.num_branches,'conflicts':solver.num_conflicts}
    orders=None
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        orders=[sorted(range(30),
                 key=lambda j:solver.value(start[j*20+pos[j][m]]))
                for m in range(20)]
        rec['solver_reported_objective']=solver.objective_value
    return rec,orders


def run(args):
    routes,durations_by_job,baseline=obtain()
    pos,duration=setup(routes,durations_by_job)
    assert evaluate(baseline,pos,duration)==2006
    parent=verified_parent(args.parent,baseline,pos,duration)
    plan=cohorts(parent,baseline,args.seed)
    report={
        'instance':'ta41','baseline':2006,'target':2005,
        'parent':args.parent,'mode':args.mode,'seed':args.seed,
        'all_parent_permutations_verified_2006':True,
        'full_machine_NoOverlap_retained':True,
        'cohort_plan':plan,'results':[],
        'expected_cases':len(plan),'examined':0,
        'dag_excluded':0,'cp_infeasible':0,'unknown':0,
        'nonimproved_feasible':0,'improved_feasible':0,
        'complete':False,
        'note':'Each exact fixed-survivor-order subspace can change up to all 20 machine permutations; UNKNOWN is not proof.'
    }
    args.out.mkdir(parents=True,exist_ok=True)
    began=time.monotonic()
    def persist():
        report['examined']=len(report['results'])
        report['complete']=report['examined']==len(plan)
        report['elapsed_seconds']=round(time.monotonic()-began,3)
        (args.out/'cohort-experiment.json').write_text(json.dumps(report,indent=2)+'\n')

    for idx,entry in enumerate(plan):
        if time.monotonic()-began>args.seconds-5:
            break
        chosen=set(entry['jobs'])
        relaxation=lower_bound(parent,pos,duration,chosen)
        rec=dict(entry,precedence_only_lower_bound=relaxation,
                 case_index=idx)
        if relaxation>2005:
            rec['status']='INFEASIBLE_BY_DAG_LB'
            rec['elapsed_seconds']=0.0
            report['dag_excluded']+=1
        else:
            budget=min(args.case_seconds,max(1,args.seconds-(time.monotonic()-began)-4))
            if args.mode=='deadline':
                finding,orders=counterfactual(parent,pos,duration,chosen,2005,
                                               budget,args.seed+idx*101)
            else:
                finding,orders=objective_repair(parent,pos,duration,chosen,
                                                budget,args.seed+idx*101)
            rec.update(finding)
            if rec['status']=='INFEASIBLE':
                report['cp_infeasible']+=1
            elif rec['status'] in ('FEASIBLE','OPTIMAL'):
                assert orders is not None
                score=evaluate(orders,pos,duration)
                assert score is not None and score<=2006,(score,idx)
                rec['independently_evaluated_makespan']=score
                rec['changed_machine_orders']=sum(a!=b for a,b in zip(parent,orders))
                if score<=2005:
                    report['improved_feasible']+=1
                    (args.out/'certificate.json').write_text(
                        json.dumps({'machines':orders},separators=(',',':'))+'\n')
                else:
                    report['nonimproved_feasible']+=1
            else:
                report['unknown']+=1
        report['results'].append(rec)
        persist()
        print('CASE',args.parent,args.mode,idx,rec['status'],
              rec.get('independently_evaluated_makespan'),
              'seconds',report['elapsed_seconds'],flush=True)
        if report['improved_feasible']:
            break
    persist()
    print('RESULT',json.dumps({k:v for k,v in report.items()
                              if k not in ('cohort_plan','results')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=['baseline','critical8','mixed20'],required=True)
    p.add_argument('--mode',choices=['deadline','optimize'],required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--seconds',type=int,default=280)
    p.add_argument('--case-seconds',type=float,default=14)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
