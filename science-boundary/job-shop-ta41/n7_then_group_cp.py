#!/usr/bin/env python3
"""Construction-focused N7->CP machine repair, total matched 5-second budget.

Published source N7 from exact same 20-second independent 30x20 elite A
gets four seconds of genuine unchanged N7 neighborhood/tabu search. Its
independently reconstructed full 600-operation candidate B is then the
ONLY input to a small target-constrained (Cmax(B)-1) CP machine-group
joint-repair engine. If CP finds better, return its independently verified
full machine orders; otherwise retain B.

Compare with native N7 alone at 5 seconds, same original A and seed.
This is not a reproduction of 2015 Failure Directed Search; it tests
the "strong plan A then constructive plan B" order suggested by FDS,
rather than the older neutral-CP->N7 sequence already tested here.

All N7 code pinned at 7e120ebada21cb604c871e0657814bf6e32611f8.
No hidden target machine schedule, published best reference score, or
artifact is passed to either optimizer.
"""
import argparse,json,time,statistics,tempfile,sys
from pathlib import Path
from types import SimpleNamespace
from partial_resource_pair_repair import parse_case
from search import evaluate
from neutral_machine_cp_then_original_n7 import native_n7
from machine_group_order_repair import run as group_run

ROOT=Path(__file__).resolve().parent
def write_legal_input(path,orders,target):
    lines=path.read_text().splitlines()
    assert len(lines)==51 and lines[0].strip()=='30 20'
    assert len(orders)==20 and all(sorted(row)==list(range(30)) for row in orders)
    target.write_text('\n'.join(lines[:31]+[' '.join(map(str,row)) for row in orders])+'\n')

def test_one(path,driver,out,seed,n7seconds,cpseconds,policy,target_drop):
    orders,pos,dur,C=parse_case(str(path))
    t=time.monotonic()
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as scratch:
        tmp=Path(scratch)
        instance=tmp/'instance.txt'
        data=path.read_text().splitlines()
        instance.write_text('\n'.join(data[:31])+'\n')
        n7,n7order=native_n7(driver,instance,orders,pos,dur,seed,n7seconds,tmp)
        assert n7['score']<=C
        after=n7['score']
        candidate=n7order
        cp_result=None
        # CP competes for the remaining headroom; Python orchestration
        # and N7 input parsing must also fit within requested total time.
        remaining=n7seconds+cpseconds-(time.monotonic()-t)
        if remaining>=0.10:
            inpath=tmp/'n7-improved.txt'
            write_legal_input(path,n7order,inpath)
            opt=SimpleNamespace(start=str(inpath),policy=policy,
                seed=seed+1109,trials_per_stage=10,only_groups=[],
                fixed_open_machines=[],target_drop=target_drop,
                auxiliary_start=None,auxiliary_mode='none',auxiliary_weight=3.,
                repair_objective='minimal-change',
                cp_seconds=min(0.48,max(0.01,remaining-0.035)),
                master_seconds=min(0.10,max(0.01,remaining-0.035)),
                total_seconds=max(0.02,remaining-0.035),
                out=tmp/'cp-joint')
            group_run(opt)
            record=json.loads((opt.out/'results.json').read_text())
            assert record['complete'] and record['incumbent']==after
            cp_result=dict(status=record['status'],score=record.get('verified_makespan'),
                 groups_attempted=len(record['traces']),elapsed=record['wall_seconds'],
                 valid_cp_unsat_cores=sum(
                    item.get('outcome')=='VALID_MACHINE_CORE'
                    for item in record['traces']))
            if record['status']=='CONSTRUCTIVE_IMPROVEMENT':
                candidate=json.loads((opt.out/'certificate.json').read_text())['machines']
                newscore=evaluate(candidate,pos,dur)
                assert newscore==record['verified_makespan'] and newscore<after
                after=newscore
        verify=evaluate(candidate,pos,dur)
        assert verify==after and after<=n7['score']<=C
        if after<C:
            (out/'certificate.json').write_text(json.dumps({'machines':candidate},separators=(',',':'))+'\n')
    report=dict(case=path.parent.name,seed=seed,initial_score=C,
        source_N7_seconds=n7seconds,source_N7_score=n7['score'],
        full_Cmax_after_CP=after,CP_extra_gain=n7['score']-after,
        total_gain=C-after,CP=cp_result,
        total_elapsed_seconds=round(time.monotonic()-t,3),
        verified_all_600_operation_final_DAG=True,
        original_N7_kernel_untouched=True,
        hidden_reference_never_loaded=True,
        cp_machine_selection_policy=policy,cp_target_drop=target_drop)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def main(a):
    cases=sorted(a.cases_dir.glob(f'*-n7elite{a.initial_seed}/start.txt'))
    assert len(cases)==a.expected_instances,len(cases)
    a.out.mkdir(parents=True,exist_ok=True)
    trials=[]
    for path in cases:
        for seed in [4107,4113]:
            result=test_one(path,a.driver,a.out/f'{path.parent.name}-seed{seed}',
                            seed,a.n7_seconds,a.cp_seconds,a.policy,a.target_drop)
            trials.append(result)
            (a.out/'partial-summary.json').write_text(json.dumps(
                 {'complete':False,'trials':trials},indent=2)+'\n')
            print('CASE',path.parent.name,seed,'start',result['initial_score'],
                  'N7',result['source_N7_score'],'hybrid',result['full_Cmax_after_CP'],
                  'time',result['total_elapsed_seconds'],flush=True)
    summary=dict(complete=True,n=len(trials),policy=a.policy,
        native_N7_seconds=a.n7_seconds,group_CP_budget_seconds=a.cp_seconds,
        target_drop=a.target_drop,
        improved_from_initial=sum(x['total_gain']>0 for x in trials),
        CP_helped_after_N7=sum(x['CP_extra_gain']>0 for x in trials),
        average_total_gain=statistics.mean(x['total_gain'] for x in trials),
        mean_CP_extra_gain=statistics.mean(x['CP_extra_gain'] for x in trials),
        average_wall_seconds=statistics.mean(x['total_elapsed_seconds'] for x in trials),
        trials=trials)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in summary.items() if k!='trials'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cases-dir',type=Path,required=True)
    p.add_argument('--initial-seed',type=int,required=True)
    p.add_argument('--expected-instances',type=int,default=5)
    p.add_argument('--driver',type=Path,required=True)
    p.add_argument('--policy',choices=('dynamic','static','random'),default='dynamic')
    p.add_argument('--target-drop',type=int,default=1)
    p.add_argument('--n7-seconds',type=int,default=4)
    p.add_argument('--cp-seconds',type=float,default=1.)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
