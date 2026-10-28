#!/usr/bin/env python3
"""High-budget independent recheck of the four hard ta41 machine cores.

The original 114 machine-group UNSAT assumptions included four triples
for which a *second* hard-NoOverlap model timed out at four seconds.
Test each with more time and multiple workers, then recompute the
independent finite 2^20 mask proof from ONLY hard-verified cores.
"""
import argparse,json,time
from pathlib import Path
from search import obtain,setup,evaluate
from machine_interface_cp import probe

def run(a):
    source=json.loads(a.cores.read_text())
    prior=json.loads(a.audit.read_text())
    assert prior['source_core_count']==len(source['cores'])==114
    routes,ds,orders=obtain();pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    all_cores=[list(x) for x in source['cores']]
    checked={x['index'] for x in prior['independent_hard_statuses']
             if x['status']=='INFEASIBLE'}
    unresolved=[x for x in prior['independent_hard_statuses']
                if x['status']!='INFEASIBLE']
    outcomes=[]
    a.out.mkdir(parents=True,exist_ok=True)
    for item in unresolved:
        idx=item['index']
        core=set(all_cores[idx])
        info,certificate=probe(orders,pos,dur,set(range(20))-core,
                               2005,a.seconds,a.seed+idx)
        outcomes.append(dict(source_core_index=idx,
                             pinned_machine_core=sorted(core),
                             status=info['status'],wall_seconds=info['elapsed']))
        if info['status']=='INFEASIBLE':checked.add(idx)
        if certificate is not None:
            (a.out/'certificate.json').write_text(
                json.dumps({'machines':certificate},separators=(',',':'))+'\n')
        print('CORE-RETEST',idx,info['status'],info['elapsed'],flush=True)
    assert len(unresolved)==len(outcomes)
    masks=[sum(1<<x for x in all_cores[i]) for i in sorted(checked)]
    counts=[0]*21;witnesses=[None]*21
    for released in range(1<<20):
        if all(released&group for group in masks):
            k=released.bit_count();counts[k]+=1
            if witnesses[k] is None:witnesses[k]=released
    bound=next(i for i,c in enumerate(counts) if c)
    report=dict(
        instance='ta41',baseline=2006,target=2005,
        original_core_count=len(all_cores),
        independently_verified_machine_core_count=len(checked),
        still_unknown_core_indices=[x['source_core_index'] for x in outcomes if x['status']=='UNKNOWN'],
        independently_reverified_changed_machine_lower_bound=bound,
        exact_machine_change_masks_checked=1<<20,
        cover_counts_by_size=counts,
        smallest_witness_release_machines=[m for m in range(20) if witnesses[bound]&(1<<m)],
        retest_outcomes=outcomes,
        proof_scope='Every <=2005 schedule must change at least bound machine orders relative to the given 2006 baseline, based only on independently rebuilt hard-NoOverlap unsat cores and complete machine-mask enumeration.'
    )
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k not in ('retest_outcomes','cover_counts_by_size')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cores',type=Path,default=Path(__file__).parent/'results'/'machine-cores'/'machine-core-analysis.json')
    p.add_argument('--audit',type=Path,default=Path(__file__).parent/'results'/'machine-core-independent-all.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-core-hard-retest')
    p.add_argument('--seconds',type=int,default=105)
    p.add_argument('--seed',type=int,default=7777)
    run(p.parse_args())
