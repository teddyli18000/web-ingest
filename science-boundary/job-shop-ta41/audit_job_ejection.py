#!/usr/bin/env python3
"""Independent audit of complete ta41 job reinsertion neighborhoods k=1,2,3.

Checks every result record against C(30,1)+C(30,2)+C(30,3)=4525
distinct job cohorts, recomputes all asserted DAG longest-path exclusions
with a newly implemented precedence-only topological evaluator, and
rebuilds a deterministic sample of 60 CP-SAT hard-NoOverlap instances
independently of the experiment generator.

This establishes exhaustive *coverage* and independently audits sample
solver statuses. It is NOT a proof of the global ta41 optimum.
"""
import argparse
import itertools
import json
import random
import time
from collections import Counter,deque
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate

ROOT=Path(__file__).resolve().parent
SAMPLES=60

def graph_lb(orders,pos,dur,ejected):
    successors=[[] for _ in range(600)]
    degree=[0]*600
    for j in range(30):
        for k in range(19):
            u=j*20+k
            successors[u].append(u+1)
            degree[u+1]+=1
    for m in range(20):
        survivors=[j for j in orders[m] if j not in ejected]
        for a,b in zip(survivors,survivors[1:]):
            u=a*20+pos[a][m]
            v=b*20+pos[b][m]
            successors[u].append(v)
            degree[v]+=1
    earliest=[0]*600
    ready=deque(i for i in range(600) if degree[i]==0)
    count=0;score=0
    while ready:
        u=ready.popleft()
        count+=1
        finish=earliest[u]+dur[u]
        score=max(score,finish)
        for v in successors[u]:
            earliest[v]=max(earliest[v],finish)
            degree[v]-=1
            if degree[v]==0:ready.append(v)
    assert count==600
    return score

def hard_cp(orders,pos,dur,removed,seconds):
    model=cp_model.CpModel()
    horizon=2005
    start=[model.new_int_var(0,horizon,'s%d'%i) for i in range(600)]
    end=[model.new_int_var(0,horizon,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(start[i],dur[i],end[i],'op%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(start[j*20+k+1]>=end[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        rest=[j for j in orders[m] if j not in removed]
        for a,b in zip(rest,rest[1:]):
            model.add(start[b*20+pos[b][m]]>=end[a*20+pos[a][m]])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=527
    verdict=solver.solve(model)
    return solver.status_name(verdict)

def main(out,limit):
    routes,durs,baseline=obtain()
    pos,dur=setup(routes,durs)
    assert evaluate(baseline,pos,dur)==2006
    grouped={1:{},2:{},3:{}}
    srcfiles=[]
    for shard in range(5):
        p=ROOT/'results'/('job-eject-%d'%shard)/'job-ejection.json'
        d=json.loads(p.read_text())
        assert d['complete'] and d['expected_subspaces']==93 and d['processed_subspaces']==93
        for rec in d['outcomes']:
            key=tuple(sorted(rec['ejected_jobs']))
            assert len(key) in (1,2) and key not in grouped[len(key)],key
            grouped[len(key)][key]=rec
        srcfiles.append(str(p.relative_to(ROOT)))
    for shard in range(8):
        p=ROOT/'results'/('job-frontier-k3-s%d'%shard)/'analysis.json'
        d=json.loads(p.read_text())
        assert d['complete_shard'] and d['selected_combinations']==4060
        for rec in d['outcomes']:
            key=tuple(sorted(rec['jobs']))
            assert len(key)==3 and key not in grouped[3],key
            grouped[3][key]=rec
        srcfiles.append(str(p.relative_to(ROOT)))
    for k in (1,2,3):
        expected=set(itertools.combinations(range(30),k))
        assert set(grouped[k])==expected, (k,len(grouped[k]),len(expected))
    verdicts=Counter()
    dag_independent=0
    cp_rows=[]
    for group in grouped.values():
        for key,rec in group.items():
            status=rec['status']
            verdicts[status]+=1
            if status in ('INFEASIBLE_BY_DAG_LB','INFEASIBLE_BY_PRECEDENCE'):
                value=graph_lb(baseline,pos,dur,set(key))
                assert value>2005,(key,value,status)
                dag_independent+=1
            elif status=='INFEASIBLE':
                cp_rows.append(key)
            else:
                raise AssertionError(('unresolved or feasible recorded',key,status))
    rng=random.Random(4107)
    sampled=rng.sample(cp_rows,min(limit,len(cp_rows)))
    audits=[]
    for i,group in enumerate(sampled):
        outcome=hard_cp(baseline,pos,dur,set(group),12)
        audits.append({'jobs':list(group),'status':outcome})
        if outcome!='INFEASIBLE':
            break
        if (i+1)%20==0:print('PROGRESS independently rechecked',i+1,flush=True)
    complete=len(audits)==len(sampled) and all(x['status']=='INFEASIBLE' for x in audits)
    report={
      'instance':'ta41','deadline':2005,'baseline':2006,
      'audit_date':'2026-10-28',
      'covered_cardinalities':{'1':30,'2':435,'3':4060},
      'all_unique_subsets_verified':True,
      'total_exact_subspaces':4525,
      'solver_verdict_histogram':dict(verdicts),
      'all_precedence_only_exclusions_recomputed_independently':dag_independent,
      'sampled_independent_hard_CP_models':len(audits),
      'independent_hard_CP_all_INFEASIBLE':complete,
      'rechecked_core_samples':audits,
      'source_files':srcfiles,
      'scope':'Any <=2005 schedule cannot arise from ejection/reinsertion of <=3 jobs in this specific 2006 baseline while preserving all other pairwise machine orders.',
      'limitation':'The exact 4525-subspace coverage is exhaustive. Only a stratified sample of the original CP infeasibility statuses was independently rerun; CP solver correctness remains the computational trusted base.'
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items()
      if k not in ('source_files','rechecked_core_samples')}),flush=True)
    if not complete: raise RuntimeError('Independent hard-CP audit incomplete')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=ROOT/'results'/'job-ejection-independent-audit.json')
    p.add_argument('--samples',type=int,default=SAMPLES)
    a=p.parse_args()
    main(a.out,a.samples)
