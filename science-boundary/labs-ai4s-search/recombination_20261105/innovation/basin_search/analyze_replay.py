#!/usr/bin/env python3
"""Source-pair clustered, genuinely unseen seed 4..19 replay of repair-aware B geometry.

Primary endpoint is novel <=5/10% source-orbit success after full repair.
Mean best E is explicitly secondary and compared with elite-copy/ILS baseline.
"""
import csv,json,pathlib,collections
import numpy as np
from argparse import ArgumentParser

ARMS={0:'true_B_random',1:'true_B_raw_energy_swaps',
      2:'true_B_basin_guided',3:'virtual_B_basin_guided',
      4:'true_B_basin_novelty',5:'single_parent_ILS'}
def read(p):
    with open(p,newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def main():
    p=ArgumentParser();p.add_argument('sessions');p.add_argument('novel')
    p.add_argument('--output',required=True);a=p.parse_args()
    rows=read(a.sessions);certs=read(a.novel)
    bypair=collections.defaultdict(lambda:collections.defaultdict(list))
    bykey=collections.defaultdict(dict)
    assert all(4<=int(r['rep'])<=19 for r in rows)
    for r in rows:
        arm=int(r['arm']);bykey[(r['pair'],int(r['rep']))][arm]=r
        bypair[r['pair']][arm].append(r)
    assert len(bypair)==9 and len(bykey)==144 and all(set(v)==set(range(6)) for v in bykey.values())
    rnd=np.random.default_rng(20261108)
    group={}
    for name,pairs in [('all',list(bypair)),('N_ge59',[z for z in bypair if int(bypair[z][0][0]['N'])>=59])]:
        diffs=[];pnov={str(k):0 for k in ARMS};pnov5={str(k):0 for k in ARMS}
        pstats={}
        for pair in pairs:
            armStats={}
            for arm in ARMS:
                subset=bypair[pair][arm]
                assert len(subset)==16
                armStats[str(arm)]={'mean_best_E':float(np.mean([int(r['bestE']) for r in subset])),
                   'nov5':sum(int(r['novel5']) for r in subset),
                   'nov10':sum(int(r['novel10']) for r in subset),
                   'successful_sessions5':sum(int(r['novel5'])>0 for r in subset),
                   'successful_sessions10':sum(int(r['novel10'])>0 for r in subset),
                   'mean_evaluated':float(np.mean([int(r['evaluated']) for r in subset]))}
                pnov[str(arm)]+=armStats[str(arm)]['nov10']
                pnov5[str(arm)]+=armStats[str(arm)]['nov5']
            pstats[pair]=armStats
            diffs.append({str(arm):armStats[str(arm)]['mean_best_E']-armStats['2']['mean_best_E']
                          for arm in [0,1,3,4,5]})
        summary={}
        for arm in [0,1,3,4,5]:
            x=np.array([v[str(arm)] for v in diffs]);boot=x[rnd.integers(len(x),size=(10000,len(x)))].mean(axis=1)
            summary[ARMS[arm]+'_minus_true_B_guided']={'mean_E_difference':float(x.mean()),
               'CI95_pair_cluster_bootstrap':[float(z) for z in np.quantile(boot,[.025,.975])],
               'source_pairs':len(x),
               'individual_pair_differences':[float(z) for z in x]}
        group[name]={'pairs':len(pairs),'nov5':pnov5,'nov10':pnov,
                      'mean_E_comparisons':summary,'by_pair':pstats}
    registered={k:set() for k in ARMS}
    paircanon=collections.defaultdict(set)
    for r in certs:
        arm=int(r['arm']);paircanon[(r['pair'],arm)].add(r['canonical'])
        registered[arm].add((int(r['N']),r['canonical']))
    result={'protocol':'heldout seed offset 4..19, 250ms inclusive, nine source pairs, 6 methods',
            'full_session_rows':len(rows),'source_pair_seed_contexts':len(bykey),
            'full_repair_unique_novel_orbits_by_arm':{ARMS[a]:len(s) for a,s in registered.items()},
            'groups':group,
            'interpretation':[
              'Source pairs share some underlying lineages; pair-cluster bootstrap descriptive not formal independent source-population inference.',
              'Pilot used 150ms, replay 250ms; no direct pooled same-budget meta-analysis.',
              'True B value must be measured against virtual-B and original-vs-postrepair controls, not just lower E than random.',
              'No neural architecture or frontier solver claim without repeated new superior postrepair orbits.'
            ]}
    path=pathlib.Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'sessions':len(rows),'nov5':group['all']['nov5'],'nov10':group['all']['nov10'],
      'trueB_vs_fakeB':group['all']['mean_E_comparisons']['virtual_B_basin_guided_minus_true_B_guided']},indent=2))
if __name__=='__main__':main()
