#!/usr/bin/env python3
"""Independent after-the-fact grading of blinded 30x20 positive controls.

Search kernels never receive this script or its archived-oracle makespans.
Every result was already re-evaluated by an independent DAG scorer.
Pair by (case,seed); compare N7-source, N7-inspired tabu, static3, dynamic3
at their ACTUAL budgets without falsely equating fixed scoring counts
and fixed wall-clock runs.
"""
import argparse,collections,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main(a):
    fixtures=json.loads((ROOT/'positive-control-data'/'manifest.json').read_text())['cases']
    oracle={x['case']:x for x in fixtures}
    assert len(oracle)==24
    policies={}
    for name,loc in {
        'tabu':'positive-cascade-tabu',
        'static3':'positive-cascade-static3',
        'dynamic3':'positive-cascade-dynamic3',
        'true-n7':'positive-original-n7',
    }.items():
        data=json.loads((ROOT/'results'/loc/'results.json').read_text())
        assert data['complete'] and len(data['trials'])==48,(name,len(data['trials']))
        outcomes={(x['case'],x['seed']):x for x in data['trials']}
        assert len(outcomes)==48
        assert set(outcomes)=={(name,seed) for name in oracle for seed in (4107,4113)}
        for (case,seed),x in outcomes.items():
            assert x['start_score']==oracle[case]['initial_makespan']
            assert x['best_score']<=x['start_score']
            if 'independently_reproduced_score' in x:
                assert x['best_score']==x['independently_reproduced_score']
            else:assert x['best_score']==x['independent_DAG_makespan']
        policies[name]=outcomes
    metrics={}
    for name,items in policies.items():
        stat={'trials':48,'improved':0,'recovered_hidden_oracle':0,
              'multi_trials':0,'multi_recovered':0,
              'total_remaining_gap':0,'total_gain':0,
              'outperforms_archived_oracle':0}
        cost=[]
        ratios=[]
        for (case,seed),x in items.items():
            ref=oracle[case];gap=ref['known_positive_gap']
            leftover=x['best_score']-ref['verified_hidden_oracle_makespan']
            stat['improved']+=x['improvement']>0
            stat['recovered_hidden_oracle']+=leftover<=0
            stat['total_remaining_gap']+=leftover
            stat['total_gain']+=x['improvement']
            stat['outperforms_archived_oracle']+=leftover<0
            if 'multi' in case:
                stat['multi_trials']+=1
                stat['multi_recovered']+=leftover<=0
            cost.append(x.get('harness_wall_seconds',x.get('wall_seconds')))
            ratios.append(min(1,(x['start_score']-x['best_score'])/gap))
        stat['mean_wall_seconds']=round(statistics.mean(cost),3)
        stat['mean_fraction_of_known_positive_gap_recovered']=round(statistics.mean(ratios),5)
        stat['mean_remaining_makespan_above_oracle']=round(stat['total_remaining_gap']/48,5)
        stat['mean_score_improvement']=round(stat['total_gain']/48,5)
        metrics[name]=stat
    paired={}
    for a_name,b_name in [('dynamic3','static3'),('dynamic3','tabu'),('dynamic3','true-n7'),('tabu','true-n7')]:
        better=worse=tie=0
        cases=[]
        for key in sorted(policies[a_name]):
            x=policies[a_name][key]['best_score']
            y=policies[b_name][key]['best_score']
            if x<y:better+=1
            elif x>y:worse+=1
            else:tie+=1
            if x!=y:cases.append({'case':key[0],'seed':key[1],
                'candidate_score':x,'control_score':y})
        paired[f'{a_name}_vs_{b_name}']=dict(wins=better,losses=worse,ties=tie,
                                             non_tie_cases=cases)
    summary=dict(experiment='24 blinded published high-quality 30x20 positive starts, 2 seeds',
         source='ScheduleOpt/benchmarks jobshop/solutions; target machine orders never read by search',
         compared_methods=list(policies),scoring_budget_note='Three in-house arms use identical 350,000 exact DAG scores/trial; author original N7 uses fixed five seconds/trial. Time, scores, and evaluation counts are not equivalent. Do not claim fair wall-clock superiority.',
         metrics=metrics,paired=paired,all_results_independently_score_checked=True,
         complete=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(summary,indent=2)+'\n')
    for method,row in metrics.items():
        print('SCORECARD',method,json.dumps(row),flush=True)
    print('RESULT graded',len(paired),'pairwise contrasts across 48 paired starts',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=ROOT/'results'/'positive-blind-compare.json')
    main(p.parse_args())
