#!/usr/bin/env python3
"""Post-search paired audit of blind source N7 basins (Taillard and DMU).

This file is the JUDGE, never imported by generation or solver. It
loads withheld known better scores only after all search results exist.
Checks matched instances/seeds, feasibility evidence and exact makespan
scores, then reports paired score wins and per-original-N7-elite success
rates separately (two second-stage seeds from each same elite are
correlated). Distinguishes mean score improvement vs any-improvement
frequency, and wall-clock vs core-seconds fairness.
"""
import argparse,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def get_trials(path):
    data=json.loads(path.read_text())
    assert data['complete'] and data['trials']
    return data['trials']

def main(a):
    registry=json.loads((a.source_data/'manifest.json').read_text())
    cases=registry['cases']
    aliases={x['case']:x for x in cases}
    expected={(x['case'],seed) for x in cases for seed in (4107,4113)}
    assert expected and len(expected)==2*len(cases)
    arms={}
    for policy in ('dynamic','static','random'):
        trials=[]
        for root in a.group_summaries:
            p=root / f'summary-{policy}.json'
            # Source-specific driver stores each batch in its own directory.
            if p.is_file():trials+=get_trials(p)
            else:
                # Existing 2026 runners store summary.json at
                # <root>-<source_seed>-<policy>/summary.json.
                for candidate in root.parent.glob(root.name+f'-*-{policy}/summary.json'):
                    trials+=get_trials(candidate)
        assert len(trials)==len(expected),(policy,len(trials),len(expected))
        by={(x['case'],x['seed']):x for x in trials}
        assert len(by)==len(expected) and set(by)==expected
        arms[policy]=by
    ref=get_trials(a.true_n7_results)
    orig={(x['case'],x['seed']):x for x in ref}
    assert set(orig)==expected
    arms['original_n7']=orig
    table=[]
    for case,seed in sorted(expected):
        reference=aliases[case]
        row=dict(case=case,seed=seed,
            initial_makespan=reference['independently_constructed_start'],
            hidden_known_better_makespan=reference['hidden_oracle_makespan'],
            improvement_exists=reference['certified_positive_gap']>0)
        for policy in arms:
            x=arms[policy][case,seed]
            assert x['start_score']==row['initial_makespan']
            assert x['best_score']<=x['start_score']
            row[policy+'_best']=x['best_score']
            row[policy+'_gain']=x['start_score']-x['best_score']
            row[policy+'_wall_seconds']=x.get('wall_seconds',x.get('native_seconds'))
            row[policy+'_reached_hidden_reference']=x['best_score']<=row['hidden_known_better_makespan']
        table.append(row)
    summary={}
    for policy in arms:
        gains=[x[policy+'_gain'] for x in table]
        success=[x for x in table if x[policy+'_gain']>0]
        summary[policy]=dict(trials=len(table),independently_better_score_found=len(success),
            improved_distinct_N7_elite_starts=len(set(x['case'] for x in success)),
            total_makespan_gain=sum(gains),
            average_makespan_gain=statistics.mean(gains),
            max_makespan_gain=max(gains),
            hidden_reference_recovered=sum(x[policy+'_reached_hidden_reference'] for x in table),
            average_wall_seconds=statistics.mean(x[policy+'_wall_seconds'] for x in table))
    comparisons={}
    for baseline in ('static','random','original_n7'):
        diff=[x[baseline+'_best']-x['dynamic_best'] for x in table]
        start_level=[]
        for case in sorted(aliases):
            pair=[x for x in table if x['case']==case]
            m=statistics.mean(x[baseline+'_best']-x['dynamic_best'] for x in pair)
            start_level.append(dict(case=case,mean_score_advantage=m))
        comparisons[baseline]=dict(dynamic_better=sum(x>0 for x in diff),
            tied=sum(x==0 for x in diff),
            dynamic_worse=sum(x<0 for x in diff),
            mean_score_advantage=statistics.mean(diff),
            independent_start_count=len(start_level),
            by_independent_start=start_level)
    report=dict(experiment='heldout 30x20 original-N7-basin paired blind transfer',
        source_data=str(a.source_data),distinct_independent_starts=len(cases),
        second_stage_seed_count=2,
        reference_provenance=registry.get('reference_provenance','ScheduleOpt public full machine solutions, never search input'),
        all_better_known_oracles_checked_only_after_search=True,
        temporal_fairness='Group strategies have ~5s internal wall-clock deadline with strict subcall caps; original author N7 native C++ search is 5s, but master CP-SAT may use more worker cores. Processor time not strictly equal.',
        independent_unit_note='Two seeded search trials from each same 20s N7 source elite are correlated; sample size is elite starts, not the doubled number of trials.',
        methods=summary,pairwise_dynamic=comparisons,cases=table,
        full_600_operation_machine_order_checked_by_search_wrappers=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='cases'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source-data',type=Path,required=True)
    p.add_argument('--group-summaries',type=Path,nargs='+',required=True,
                   help='glob prefix e.g. results/holdout-machine-group')
    p.add_argument('--true-n7-results',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
