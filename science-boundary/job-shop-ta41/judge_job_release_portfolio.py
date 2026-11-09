#!/usr/bin/env python3
"""Independently judge the 10-second fair-WALL-BUDGET algorithms.

Arms evaluated from identical verified source-N7 20sec elite starts:
- native N7 alone, 5sec (previous source-faithful reference);
- joint job-release CP ladder, 5sec solver aggregate;
- (N7 5sec + CP5sec) simple two-solver portfolio, total 10sec;
- sequential CP5sec -> source N7 5sec true cross-representation warmstart;
- authentic source N7 alone, 10sec, same start and secondary seed.

No archived oracle needed even for grading; the exact legal objective is
recomputed by original independent verifiers in each generator. Distinguish
five-second and ten-second budgets and 4-thread CP from 1-thread N7.
"""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def load():
    n7five=json.loads((ROOT/'results'/'positive-independent-true-n7'/'results.json').read_text())
    assert n7five['complete'] and len(n7five['trials'])==24
    idx={(x['case'],x['seed']):x for x in n7five['trials']}
    rows=[]
    for seed in (4107,4113):
        cp=json.loads((ROOT/'results'/f'job-radius-ladder-s{seed}'/'results.json').read_text())
        n7ten=json.loads((ROOT/'results'/f'positive-independent-true-n7-10s-s{seed}'/'results.json').read_text())
        hybrid=json.loads((ROOT/'results'/f'positive-cp-to-n7-hybrid-s{seed}'/'results.json').read_text())
        assert cp['complete'] and len(cp['sample'])==12
        assert n7ten['complete'] and len(n7ten['trials'])==12
        assert hybrid['complete'] and len(hybrid['trials'])==12
        byn={x['case']:x for x in n7ten['trials']}
        byh={x['case']:x for x in hybrid['trials']}
        for x in cp['sample']:
            key=(x['case'],seed)
            old=idx[key]
            n= byn[x['case']]
            h= byh[x['case']]
            initial=x['initial']
            assert initial==old['start_score']==n['start_score']==h['original_initial_score']
            assert x['best_score']==h['cp_after_five_seconds']
            assert h['n7_after_cp_best_score']<=x['best_score']
            assert old['best_score']<=initial and n['best_score']<=initial
            row=dict(case=x['case'],seed=seed,initial=initial,
                cp5=x['best_score'],n7_5=old['best_score'],
                n7_10=n['best_score'],cp_then_n7=h['n7_after_cp_best_score'],
                simple_portfolio=min(x['best_score'],old['best_score']),
                wall_cp5=x['full_wall_seconds'],
                native_n7_5_seconds=old['native_seconds'],
                native_n7_10_seconds=n['native_seconds'],
                native_n7_after_cp_seconds=h['native_n7_seconds'])
            rows.append(row)
    assert len(rows)==24 and len(set((x['case'],x['seed']) for x in rows))==24
    return rows

def describe(rows,fields):
    out={}
    for policy in fields:
        gains=[x['initial']-x[policy] for x in rows]
        out[policy]=dict(trials=len(rows),strict_improvements=sum(g>0 for g in gains),
            mean_makespan_gain=statistics.mean(gains),
            total_makespan_gain=sum(gains),best_gain=max(gains))
    return out

def paired(rows,a,b):
    dif=[x[b]-x[a] for x in rows]
    return dict(policy_a=a,policy_b=b,
       a_better=sum(d>0 for d in dif),
       tied=sum(d==0 for d in dif),
       a_worse=sum(d<0 for d in dif),
       mean_objective_advantage_a=statistics.mean(dif))

def main():
    rows=load()
    fields=['cp5','n7_5','n7_10','cp_then_n7','simple_portfolio']
    bygroup={}
    for label,subset in [('all',rows),
            ('prospective_untouched_ta44_ta45_ta47',
                [x for x in rows if x['case'][:4] in ('ta44','ta45','ta47')]),
            ('other_ta42_ta43_ta46',
                [x for x in rows if x['case'][:4] in ('ta42','ta43','ta46')])]:
        bygroup[label]=dict(summary=describe(subset,fields),
            paired=dict(
                sequential_vs_n7_10=paired(subset,'cp_then_n7','n7_10'),
                portfolio_vs_n7_10=paired(subset,'simple_portfolio','n7_10'),
                cp5_vs_n7_5=paired(subset,'cp5','n7_5')))
    report=dict(question='Does 5sec coupled job-release CP plus 5sec real original N7 beat 10sec original N7, with identical machine-order elite starts?',
        source_pins=dict(original_n7='Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8',
            CP='ortools==9.14.6206'),
        fairness='Approximately matched SOLVER WALL time (two five-second stages vs one ten-second). Not matched CPU: CP uses 4 worker threads, N7 is single-core; OS scheduling, build and process overhead differ. Oracle-derived tuning on ta43/ta46 makes those development cases, NOT untouched prospective holdouts.',
        hidden_optimal_orders_not_used=True,
        groups=bygroup,paired_trials=rows,complete=True)
    target=ROOT/'results'/'job-release-10sec-hybrid-judged.json'
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='paired_trials'},indent=2))

if __name__=='__main__':
    main()
