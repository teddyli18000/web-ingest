#!/usr/bin/env python3
"""Exact smallest one-machine job-insertion cost to break a 2006 backbone arc.

For each of the 21 shared-order UNSAT core constraints a->b on machine m:
enumerate ALL 30*29 legal single-operation removals and reinsertion
positions on machine m; keep other 19 machine orders fixed.

This is NOT a record attack by one machine (the machine-distance theorem
already rules out <=2005). It constructs the closest *feasible inversion
seed* for a continuation solver by measuring how costly each one-machine
backbone break is before coupled repairs can reduce makespan.

All candidates independently scored by the original 600-operation DAG;
cyclic candidates rejected. The best parent-based seed is saved for every
arc, and after ranking the cheapest reversal arcs one can optimize the
whole full-resource schedule from those warm starts.
"""
import argparse,json,time
from collections import Counter
from pathlib import Path
from search import obtain,setup,evaluate

def main(out):
    roots=Path(__file__).parent
    c=json.loads((roots/'results/consensus-five-parents/consensus-analysis.json').read_text())
    assert c['status']=='INFEASIBLE' and len(c['proven_unsat_core'])==21
    routes,ds,base=obtain();pos,dur=setup(routes,ds)
    assert evaluate(base,pos,dur)==2006
    per_machine={}
    records=[]
    t=time.monotonic();out.mkdir(parents=True,exist_ok=True)
    for idx,arc in enumerate(c['proven_unsat_core']):
        m=arc['machine'];left=arc['from_job'];right=arc['to_job']
        assert base[m].index(left)<base[m].index(right)
        best=10**9;bestorder=None;seen=0;cyclic=0
        orig=base[m]
        visited=set()
        for k in range(30):
            job=orig[k]
            without=orig[:k]+orig[k+1:]
            for newindex in range(30):
                if newindex==k:continue
                order=without[:newindex]+[job]+without[newindex:]
                if order==orig:continue
                key=tuple(order)
                if key in visited:continue
                visited.add(key)
                if order.index(right)>=order.index(left):continue
                base[m]=order
                C=evaluate(base,pos,dur)
                if C is None:cyclic+=1;continue
                seen+=1
                if C<best:
                    best=C;bestorder=[x[:] for x in base]
        base[m]=orig
        assert evaluate(base,pos,dur)==2006
        rec=dict(core_arc_index=idx,machine=m,from_job=left,to_job=right,
                 legal_acyclic_one_machine_insertions=seen,cyclic_insertions=cyclic,
                 minimum_feasible_makespan=None if bestorder is None else best,
                 delta_over_incumbent=None if bestorder is None else best-2006)
        records.append(rec)
        if bestorder is not None:
            (out/('reversal-warm-%02d.json'%idx)).write_text(
                json.dumps({'machines':bestorder},separators=(',',':'))+'\n')
        print('ARC',idx,'machine',m,'best',best,'delta',best-2006,'seen',seen,'cycles',cyclic,flush=True)
    result=dict(instance='ta41',baseline=2006,target=2005,
                method='exact single-machine job insertion seeding of complete 21-core reversal',
                inspected_core_arcs=len(records),
                viable_one_machine_reverse_arcs=sum(r['minimum_feasible_makespan'] is not None for r in records),
                best_single_machine_backbone_reverse=min((x['minimum_feasible_makespan'] for x in records if x['minimum_feasible_makespan'] is not None),default=None),
                records=records,
                elapsed=round(time.monotonic()-t,3),
                proof_scope='Per core arc exact among single-job ejection/reinsertion on that arc machine only, with 19 other machine sequences untouched. Score>2006 is merely a warm-start seed, not a proven global barrier.'
                )
    (out/'reversal-seeding.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'reversal-warm-seeds')
    main(p.parse_args())
