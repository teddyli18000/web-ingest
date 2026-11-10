#!/usr/bin/env python3
"""Receding-incumbent whole-machine repair, strictly 5-second wall budget.

The previous source-only machine-group CP stops after its FIRST strict
improvement, often gain=1 while unchanged author N7 sometimes gains 3-9.
This study treats each independently verified improved complete 600-op
schedule as the NEXT incumbent, recomputes all source-only machine slack
and machine-conflict evidence for the new target Cmax-1, and repeats.
No hidden target machine orders or published oracle score are loaded.

The test measures whether constructive improvement RATE translates into
objective QUALITY by chaining coordinated group repairs. Dynamic/static/
random retain identical group selection and small-inversion CP objective.

This is standard iterated large-neighborhood search in general; novelty
cannot be claimed solely for iterative warm starting.
"""
import argparse,json,time,statistics
from pathlib import Path
from types import SimpleNamespace
from machine_group_order_repair import run
from partial_resource_pair_repair import parse_case
from search import evaluate

ROOT=Path(__file__).resolve().parent

def write_start(template,orders,path):
    lines=template.read_text().splitlines()
    assert len(lines)==51 and lines[0].strip()=="30 20"
    assert len(orders)==20 and all(sorted(x)==list(range(30)) for x in orders)
    path.write_text("\n".join(lines[:31]+[" ".join(map(str,x)) for x in orders])+"\n")

def one_instance(path,out,policy,seed,seconds,window,cp_seconds,master_seconds):
    initial_orders,pos,dur,initial=parse_case(str(path))
    out.mkdir(parents=True,exist_ok=True)
    incumbent=initial
    last_orders=initial_orders
    start=time.monotonic()
    history=[]
    attempts=0
    while attempts<30:
        remaining=seconds-(time.monotonic()-start)
        if remaining<=0.07:break
        attempts+=1
        round_dir=out/f'round{attempts:02d}'
        input_file=out/f'incumbent{attempts:02d}.txt'
        write_start(path,last_orders,input_file)
        params=SimpleNamespace(
            start=str(input_file),policy=policy,
            seed=seed+109*attempts,
            trials_per_stage=12,only_groups=[],
            fixed_open_machines=[],
            repair_objective='minimal-change',
            cp_seconds=min(cp_seconds,max(.01,remaining-.03)),
            master_seconds=min(master_seconds,max(.01,remaining-.03)),
            total_seconds=min(window,max(.01,remaining-.03)),
            out=round_dir)
        began=time.monotonic()
        run(params)
        measured=time.monotonic()-began
        result=json.loads((round_dir/'results.json').read_text())
        assert result['complete'] and result['incumbent']==incumbent
        assert result['status'] in ('CONSTRUCTIVE_IMPROVEMENT','UNRESOLVED')
        trace=dict(iteration=attempts,input_score=incumbent,search_wall_seconds=round(measured,3),
                   cp_calls=len(result['traces']),completed=result['status']=='CONSTRUCTIVE_IMPROVEMENT')
        if result['status']=='CONSTRUCTIVE_IMPROVEMENT':
            child=json.loads((round_dir/'certificate.json').read_text())['machines']
            score=evaluate(child,pos,dur)
            assert score==result['verified_makespan'] and score<incumbent
            # All 30x20 job+machine DAG constraints independently scored;
            # only strictly improving complete schedules are carried on.
            trace['improvement']=incumbent-score
            incumbent=score
            last_orders=child
        else:trace['improvement']=0
        history.append(trace)
        (out/'partial.json').write_text(json.dumps(dict(initial=initial,current=incumbent,
            complete=False,history=history),indent=2)+'\n')
        print('CHAIN',path.parent.name,policy,seed,attempts,
              trace['input_score'],'->',incumbent,
              'wall',trace['search_wall_seconds'],flush=True)
        # After a no-improvement short window, the revised seed
        # rescans source-only group sets; no proof claimed.
    write_start(path,last_orders,out/'best-start.txt')
    report=dict(instance=path.parent.name,seed=seed,policy=policy,
        original_N7_start=initial,best_score=incumbent,
        gain=initial-incumbent,steps=history,
        complete=True,elapsed_wall_seconds=round(time.monotonic()-start,3),
        strict_total_budget_seconds=seconds,
        window_seconds=window,
        improved_times=sum(x['improvement']>0 for x in history),
        all_intermediate_complete_schedules_DAG_reverified=True,
        hidden_archived_oracle_never_accessed=True)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def main(a):
    cases=sorted(a.cases_dir.glob(f'*-n7elite{a.initial_seed}/start.txt'))
    assert len(cases)==a.expected_instances,(len(cases),a.expected_instances)
    a.out.mkdir(parents=True,exist_ok=True)
    trials=[]
    for case in cases:
        for seed in (4107,4113):
            trial=one_instance(case,a.out/f'{case.parent.name}-seed{seed}',a.policy,seed,
                a.seconds,a.window,a.cp_seconds,a.master_seconds)
            trials.append(dict(case=case.parent.name,seed=seed,
                initial=trial['original_N7_start'],best=trial['best_score'],
                gain=trial['gain'],wall_seconds=trial['elapsed_wall_seconds'],
                phase_count=len(trial['steps']),improvement_steps=trial['improved_times']))
            (a.out/'partial-summary.json').write_text(json.dumps(
                dict(trials=trials,complete=False),indent=2)+'\n')
    summary=dict(policy=a.policy,initial_seed=a.initial_seed,
        cases=len(cases),trial_count=len(trials),
        improved=sum(x['gain']>0 for x in trials),
        average_gain=statistics.mean(x['gain'] for x in trials),
        total_gain=sum(x['gain'] for x in trials),
        chained_improvements=sum(x['improvement_steps']>1 for x in trials),
        complete=True,trials=trials)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('SUMMARY',json.dumps({k:v for k,v in summary.items() if k!='trials'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cases-dir',type=Path,required=True)
    p.add_argument('--initial-seed',type=int,required=True)
    p.add_argument('--expected-instances',type=int,required=True)
    p.add_argument('--policy',choices=['dynamic','static','random'],required=True)
    p.add_argument('--seconds',type=float,default=5.0)
    p.add_argument('--window',type=float,default=1.5)
    p.add_argument('--cp-seconds',type=float,default=.55)
    p.add_argument('--master-seconds',type=float,default=.12)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
