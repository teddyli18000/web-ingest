#!/usr/bin/env python3
"""Paired 5-second blind whole-machine LNS transfer benchmark.

12 independently generated source-faithful N7 elite starts, with two fresh
second-stage seeds: 24 matched trials per policy. Search never reads archived
optimal machine orders or target makespan; requires only current score-1.
The separate judge compares full DAG scores to 5-second genuine author N7.

The policy of each trial is identical to machine_group_order_repair.py.
Every complete result is re-scored by an independent Python DAG evaluator.
"""
import argparse,json,statistics,time
from pathlib import Path
from machine_group_order_repair import run
from partial_resource_pair_repair import parse_case
from search import evaluate
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parent

def main(a):
    cases=sorted((ROOT/'positive-n7-elite-data').glob(f'ta*js-n7elite{a.initial_seed}/start.txt'))
    assert len(cases)==6,len(cases)
    a.out.mkdir(parents=True,exist_ok=True)
    trials=[]
    for case in cases:
        for seed in (4107,4113):
            folder=a.out/f'{case.parent.name}-seed{seed}'
            params=SimpleNamespace(
                start=str(case),policy=a.policy,seed=seed,
                trials_per_stage=a.trials_per_stage,
                only_groups=[],fixed_open_machines=[],
                cp_seconds=a.cp_seconds,
                master_seconds=a.master_seconds,
                total_seconds=a.total_seconds,
                out=folder)
            original,pos,duration,initial=parse_case(str(case))
            run(params)
            result=json.loads((folder/'results.json').read_text())
            assert result['complete'] and result['incumbent']==initial
            assert result['status'] in ('CONSTRUCTIVE_IMPROVEMENT','UNRESOLVED')
            if result['status']=='CONSTRUCTIVE_IMPROVEMENT':
                cert=json.loads((folder/'certificate.json').read_text())['machines']
                assert len(cert)==20 and all(sorted(seq)==list(range(30)) for seq in cert)
                best=evaluate(cert,pos,duration)
                assert best==result['verified_makespan'] and best<initial
            else:best=initial
            trial=dict(case=case.parent.name,seed=seed,policy=a.policy,
                start_score=initial,best_score=best,gain=initial-best,
                wall_seconds=result['wall_seconds'],
                tested_machine_sets=len(result['traces']),
                full_resource_unsat_group_clauses=sum(
                    x.get('outcome')=='VALID_MACHINE_CORE' for x in result['traces']),
                complete=True,hidden_archived_oracle_never_accessed=True)
            trials.append(trial)
            (a.out/'partial-results.json').write_text(json.dumps(
                dict(complete=False,trials=trials),indent=2)+'\n')
            print('TRIAL',a.policy,trial['case'],seed,initial,'=>',best,
                'seconds',trial['wall_seconds'],flush=True)
    assert len(trials)==12
    result=dict(policy=a.policy,initial_N7_seed=a.initial_seed,
        second_stage_seeds=[4107,4113],cases_per_seed=6,
        trial_count=len(trials),wall_seconds_per_trial=a.total_seconds,
        improved=sum(x['gain']>0 for x in trials),
        mean_improvement=statistics.mean(x['gain'] for x in trials),
        complete=True,trials=trials,
        caveat='5-second timing is internal Python model and solver time, exclusive of dependency installation / GitHub runner startup. Genuine N7 is C++ 5-second native duration. All policies same machine-group CP model and budget.')
    (a.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='trials'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--policy',choices=['dynamic','static','random'],required=True)
    p.add_argument('--initial-seed',type=int,choices=[1701,1711],required=True)
    p.add_argument('--total-seconds',type=float,default=5.0)
    p.add_argument('--cp-seconds',type=float,default=0.7)
    p.add_argument('--master-seconds',type=float,default=0.15)
    p.add_argument('--trials-per-stage',type=int,default=8)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
