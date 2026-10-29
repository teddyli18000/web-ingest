#!/usr/bin/env python3
"""Diversified 3-job globally coupled reinsertion subspaces around ta41=2006.

A third job can change all 20 machine orders yet retain the baseline
relative sequence of 27 unaffected jobs. Choose a bounded deterministic
portfolio by exact precedence-relaxation LB and diversity coverage:
45 smallest DAG-LB cohorts, then greedily add cohorts bringing new
pairwise job coverage, then seeded samples from other passing triples.

This is an exploratory portfolio, *not* an exhaustive triple exclusion.
Every individual INFEASIBLE is exact under its conditioned subspace;
UNKNOWN is not used as evidence.
"""
import argparse,itertools,json,random,time
from pathlib import Path
from search import obtain,setup,evaluate
from job_ejection_dag import lower_bound
from job_ejection_search import counterfactual


def candidate_portfolio(orders,pos,dur,count,seed):
    ranked=[]
    for jobs in itertools.combinations(range(30),3):
        lb=lower_bound(orders,pos,dur,set(jobs))
        if lb<=2005:ranked.append((lb,jobs))
    ranked.sort()
    selected=ranked[:min(45,count)]
    used={jobs for _,jobs in selected}
    coverage={tuple(sorted(p)) for _,js in selected for p in itertools.combinations(js,2)}
    remaining=ranked[len(selected):]
    while len(selected)<min(count,110) and remaining:
        best=max(range(len(remaining)),key=lambda z:(
            sum(p not in coverage for p in itertools.combinations(remaining[z][1],2)),
            -(remaining[z][0]-1968),-z))
        lb,jobs=remaining.pop(best)
        if jobs in used:continue
        selected.append((lb,jobs));used.add(jobs)
        coverage.update(itertools.combinations(jobs,2))
    rng=random.Random(seed)
    rng.shuffle(remaining)
    for item in remaining:
        if len(selected)>=count:break
        if item[1] not in used:
            selected.append(item);used.add(item[1])
    assert len(selected)==count,(len(selected),count)
    return selected


def run(a):
    routes,ds,orders=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    cohort_list=candidate_portfolio(orders,pos,dur,a.count,4107)
    chosen=[(i,j) for i,j in enumerate(cohort_list) if i%a.shards==a.shard]
    result={
      'instance':'ta41','baseline':2006,'target':2005,
      'method':'diversified exact three-job global reinsertion with 27 survivor jobs pinned in relative order',
      'portfolio_size':len(cohort_list),'all_triple_sets':4060,
      'selection':'top 45 DAG-relaxation LB, pair coverage diversification to 110, seeded random passing triples for remainder',
      'shard':a.shard,'shards':a.shards,'expected':len(chosen),
      'examined':0,'infeasible':0,'unknown':0,'feasible':0,
      'results':[],'complete':False}
    a.out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    for idx,(lb,jobs) in chosen:
        if time.monotonic()-started>=a.total_seconds-2:break
        record,candidate=counterfactual(orders,pos,dur,set(jobs),2005,
            min(a.per_case_seconds,max(0.5,a.total_seconds-(time.monotonic()-started)-1)),a.seed+idx)
        record.update(portfolio_index=idx,precedence_only_lower_bound=lb)
        result['results'].append(record)
        if len(result['results']) % 5 == 0:
            # Checkpoint within the shard: a stopped runner should not erase
            # exact subspace exclusions already established.
            result['examined']=len(result['results'])
            result['elapsed_seconds']=round(time.monotonic()-started,3)
            (a.out/'triple-portfolio.json').write_text(json.dumps(result,indent=2))
        if record['status']=='INFEASIBLE':result['infeasible']+=1
        elif record['status'] in ('FEASIBLE','OPTIMAL'):
            result['feasible']+=1
            (a.out/'certificate.json').write_text(json.dumps({'machines':candidate},separators=(',',':'))+'\n')
            break
        else:result['unknown']+=1
        if len(result['results'])%10==0:
            print('PROGRESS',a.shard,len(result['results']),len(chosen),
                  'infeasible',result['infeasible'],'unknown',result['unknown'],flush=True)
    result['examined']=len(result['results'])
    result['complete']=result['examined']==len(chosen)
    result['elapsed_seconds']=round(time.monotonic()-started,3)
    (a.out/'triple-portfolio.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--count',type=int,default=200)
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,default=5)
    p.add_argument('--seed',type=int,default=1057)
    p.add_argument('--per-case-seconds',type=float,default=4)
    p.add_argument('--total-seconds',type=int,default=540)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
