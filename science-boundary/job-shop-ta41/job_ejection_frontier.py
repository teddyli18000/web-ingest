#!/usr/bin/env python3
"""Exact full 3-job global ejection and exploratory 4-job portfolios.

Fix the relative machine order of all non-ejected jobs; allow ejected
jobs to be independently reinserted on every machine. All job arcs and
all machine NoOverlap constraints stay hard. A recorded INFEASIBLE
result therefore excludes that *entire* global insertion subspace.

For k=3 enumerate C(30,3)=4060 subsets, sharded exhaustively.
For k=4 take a deterministic, documented sample of 500 from C(30,4)=27405.
UNSAT is exact; UNKNOWN is never counted as proof. If a feasible candidate
emerges, recanonicalize to machine permutations and check via DAG and
independent Few Shots upstream verifier before publication.
"""
import argparse
import itertools
import json
import random
import time
from pathlib import Path

from search import obtain, setup, evaluate
from job_ejection_search import counterfactual
from job_ejection_dag import lower_bound


def sampled_combinations(k, n, selection_seed):
    combos = list(itertools.combinations(range(30), k))
    if k == 4:
        rng = random.Random(selection_seed)
        rng.shuffle(combos)
        combos = combos[:n]
    else:
        assert k == 3 and n == 4060
        assert len(combos) == n
    return combos


def main(a):
    routes, durs_by_job, baseline = obtain()
    pos, durations = setup(routes, durs_by_job)
    assert evaluate(baseline, pos, durations) == 2006
    combos = sampled_combinations(a.k, a.sample_size, a.selection_seed)
    allocated = [(i, c) for i, c in enumerate(combos) if i % a.shards == a.shard]
    report = {
        'instance': 'Taillard ta41',
        'baseline': 2006,
        'target': 2005,
        'ejection_cardinality': a.k,
        'enumeration_complete_at_cardinality': a.k == 3,
        'all_combinations_at_cardinality': 4060 if a.k == 3 else 27405,
        'selected_combinations': len(combos),
        'selection_seed': a.selection_seed,
        'shard': a.shard,
        'shards': a.shards,
        'assigned_count': len(allocated),
        'tested': 0,
        'dag_exclusions': 0,
        'cp_proven_infeasible': 0,
        'unknown': 0,
        'found_feasible': 0,
        'outcomes': [],
        'complete_shard': False,
        'methodology': 'All non-ejected jobs keep their relative machine order. Ejected jobs are reinserted globally with unconditional job arcs and NoOverlap. Job-only longest-path relaxations can rule out subspaces but cannot certify a schedule.'
    }
    a.out.mkdir(parents=True,exist_ok=True)
    begin=time.monotonic()
    for idx, combo in allocated:
        if time.monotonic()-begin > a.total_seconds-3:
            break
        jobs = set(combo)
        relaxed = lower_bound(baseline,pos,durations,jobs)
        if relaxed > 2005:
            record = dict(global_index=idx,jobs=list(combo),
                          status='INFEASIBLE_BY_PRECEDENCE',precedence_bound=relaxed)
            report['dag_exclusions']+=1
        else:
            record,candidate = counterfactual(
                baseline,pos,durations,jobs,2005,
                min(a.per_case_seconds,max(.5,a.total_seconds-(time.monotonic()-begin)-2)),
                a.seed+idx)
            record.update(global_index=idx,jobs=list(combo),precedence_bound=relaxed)
            if record['status'] == 'INFEASIBLE':
                report['cp_proven_infeasible']+=1
            elif record['status'] in ('FEASIBLE','OPTIMAL'):
                assert evaluate(candidate,pos,durations) <= 2005
                report['found_feasible']+=1
                (a.out/'certificate.json').write_text(
                    json.dumps({'machines':candidate},separators=(',',':'))+'\n')
                report['outcomes'].append(record)
                break
            else:
                report['unknown']+=1
        report['outcomes'].append(record)
        if len(report['outcomes']) % 100 == 0:
            print(f"PROGRESS k={a.k} shard={a.shard} "
                  f"done={len(report['outcomes'])}/{len(allocated)} "
                  f"unknown={report['unknown']} "
                  f"elapsed={time.monotonic()-begin:.1f}",flush=True)
    report['tested']=len(report['outcomes'])
    report['complete_shard']=report['tested']==len(allocated)
    report['elapsed_seconds']=round(time.monotonic()-begin,3)
    (a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='outcomes'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--k',type=int,choices=(3,4),required=True)
    p.add_argument('--sample-size',type=int,required=True)
    p.add_argument('--selection-seed',type=int,default=4141)
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,required=True)
    p.add_argument('--seed',type=int,default=9200)
    p.add_argument('--per-case-seconds',type=float,default=3.0)
    p.add_argument('--total-seconds',type=int,default=530)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
