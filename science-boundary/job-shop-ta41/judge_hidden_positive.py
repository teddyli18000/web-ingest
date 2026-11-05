#!/usr/bin/env python3
"""Post-search blind benchmark judge; never import into search harnesses.

Combine ScheduleOpt independent best known 30x20 targets with:
* 350k exact DAG candidate eval tabu, static3 and dynamic3 runs
* 5s original author's N7 source with matched initial machine orders
The budget disparity is made EXPLICIT: the three cascade methods are
matched evaluation count, native N7 is fixed wall clock.
"""
import argparse,csv,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main(a):
    manifest=json.loads((ROOT/'positive-control-data'/'manifest.json').read_text())
    oracle={x['case']:x for x in manifest['cases']}
    assert len(oracle)==24
    results={}
    for policy in ('tabu','static3','dynamic3'):
        dat=json.loads((ROOT/'results'/f'positive-cascade-{policy}'/'results.json').read_text())
        assert dat['complete'] and len(dat['trials'])==48
        assert dat['evaluations_per_trial']==350000
        results[policy]={(x['case'],x['seed']):x for x in dat['trials']}
    native=json.loads((ROOT/'results'/'positive-original-n7'/'results.json').read_text())
    assert native['complete'] and len(native['trials'])==48
    results['true-n7']={(x['case'],x['seed']):x for x in native['trials']}
    keys={(case,seed) for case in oracle for seed in (4107,4113)}
    assert all(set(results[p])==keys for p in results)
    detail=[]
    for case,seed in sorted(keys):
        evidence=oracle[case]
        row={'case':case,'seed':seed,'instance':evidence['instance'],
             'difficulty':('multi' if 'multi' in case else 'single'),
             'initial':evidence['initial_makespan'],
             'hidden_target':evidence['verified_hidden_oracle_makespan'],
             'known_positive_gap':evidence['known_positive_gap']}
        for p in results:
            r=results[p][case,seed]
            assert r['start_score']==row['initial'] and r['best_score']<=row['initial']
            row[p+'_score']=r['best_score']
            row[p+'_recovered_oracle']=r['best_score']<=row['hidden_target']
            row[p+'_improvement']=row['initial']-r['best_score']
        detail.append(row)
    arms={}
    for policy in results:
        allrows=[x for x in detail]
        hard=[x for x in detail if x['difficulty']=='multi']
        arms[policy]={'trials':len(allrows),
          'any_improvement':sum(x[policy+'_improvement']>0 for x in allrows),
          'recovered_known_target':sum(x[policy+'_recovered_oracle'] for x in allrows),
          'multi_trails':len(hard),
          'multi_target_recoveries':sum(x[policy+'_recovered_oracle'] for x in hard),
          'average_makespan_gain':statistics.mean(x[policy+'_improvement'] for x in allrows),
          'average_multi_gain':statistics.mean(x[policy+'_improvement'] for x in hard)}
    comparisons={}
    for policy in ('tabu','static3','true-n7'):
        d=[x[policy+'_score']-x['dynamic3_score'] for x in detail]
        comparisons['dynamic3_vs_'+policy]={
          'dynamic_better':sum(v>0 for v in d),
          'dynamic_tied':sum(v==0 for v in d),
          'dynamic_worse':sum(v<0 for v in d),
          'mean_native_makespan_advantage':statistics.mean(d)}
    result={'experiment':'30x20 hidden-answer 24-case benchmark',
       'known_better_scores_verified_at_preparation':True,
       'all_starts_independent_valid_schedule_replays':True,
       'search_never_reads_hidden_oracle':True,
       'search_arm_budgets':{
          'tabu':'350000 fully evaluated candidate DAGs/trial',
          'static3':'350000 fully evaluated candidate DAGs/trial',
          'dynamic3':'350000 fully evaluated candidate DAGs/trial',
          'true-n7':'5 wall-clock seconds/trial; genuine source N7 neighborhood, not matched DAG count'},
       'fairness':'Only first three arms have matched evaluation counts. Comparing true N7 by score alone is exploratory unless CPU time is matched; original N7 search was warm-started with exactly the same start.',
       'summary':arms,'pairwise_dynamic_comparisons':comparisons,'cases':detail}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({'summary':arms,'comparisons':comparisons}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=ROOT/'results'/'positive-joint-benchmark-judged.json')
    main(p.parse_args())
