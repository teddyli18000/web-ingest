#!/usr/bin/env python3
"""Post-search grading of independent 20-second author N7 elite starts.

No hidden oracle is ever supplied to any search subprocess; this is the
separate judge. The four policies share identical 12 starting machine-order
schedules, two second-stage seeds, and independent full DAG grading.
Three original arms use matched 350k candidate evaluation budgets, genuine
N7 is matched start with 5-second runtime; compare fairness explicitly.
"""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
cases=json.loads((ROOT/'positive-n7-elite-data'/'manifest.json').read_text())['cases']
assert len(cases)==12
known={x['case']:x for x in cases}
runs={}
for policy in ('tabu','static3','dynamic3','true-n7'):
    source=ROOT/'results'/f'positive-independent-{policy}'/'results.json'
    d=json.loads(source.read_text())
    assert d['complete'] and len(d['trials'])==24,(policy,d.get('complete'),len(d.get('trials',[])))
    runs[policy]={(x['case'],x['seed']):x for x in d['trials']}
    assert len(runs[policy])==24
summary={}
for policy in runs:
    trials=list(runs[policy].values())
    successes=0
    for x in trials:
        y=known[x['case']]
        assert x['start_score']==y['independently_constructed_start'],(policy,x)
        assert x['best_score']<=x['start_score'],(policy,x)
        successes+=x['best_score']<=y['hidden_oracle_makespan']
    summary[policy]=dict(trials=24,improved=sum(x['improvement']>0 for x in trials),
        recovered_hidden_known_best=successes,
        average_improvement=statistics.mean(x['improvement'] for x in trials),
        max_improvement=max(x['improvement'] for x in trials),
        average_final_makespan=statistics.mean(x['best_score'] for x in trials),
        average_search_seconds=statistics.mean(x.get('native_wall_seconds',x.get('native_seconds')) for x in trials))
reference=[]
for key in sorted(runs['tabu']):
    row=known[key[0]]
    z=dict(case=key[0],seed=key[1],initial=row['independently_constructed_start'],
           hidden_oracle=row['hidden_oracle_makespan'])
    for p in runs:z[p]=runs[p][key]['best_score']
    reference.append(z)
pair={}
for p in ('tabu','static3','true-n7'):
    differences=[x[p]-x['dynamic3'] for x in reference]
    pair[p]=dict(dynamic_wins=sum(v>0 for v in differences),
      tied=sum(v==0 for v in differences),
      dynamic_losses=sum(v<0 for v in differences),
      mean_score_gain_dynamic_over_baseline=statistics.mean(differences))
report=dict(instance_shape='30x20',
    truly_independent_source='12 actual 20-second published N7 search incumbents, NOT oracle perturbations',
    no_reference_machine_orders_seen_by_search=True,
    n=24,distinct_source_instances=6,
    policy_budgets=dict(tabu='350k full exact DAG candidate evals',
         static3='350k full exact DAG candidate evals',
         dynamic3='350k full exact DAG candidate evals',
         true_n7='5 seconds genuine published N7 kernel; iterations differ from exact DAG count'),
    scope='One source N7 elite initialization family, six instances, two first-stage and two second-stage seeds. Not sufficient for a universal transfer claim.',
    summary=summary,pairwise=pair,trials=reference)
dest=ROOT/'results'/'positive-independent-elite-judged.json'
dest.write_text(json.dumps(report,indent=2)+'\n')
print('RESULT',json.dumps({'summary':summary,'pairwise':pair}),flush=True)
