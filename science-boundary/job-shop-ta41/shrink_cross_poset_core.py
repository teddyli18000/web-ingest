#!/usr/bin/env python3
"""Subsumption-grade greedy shrinking of independently verified ta41 poset cores.

Input: sufficient UNSAT machine precedence cover arcs from cross-parent
consensus, rebuilt and independently hard-NoOverlap verified. Remove
one arc at a time and rebuild a NEW hard 600-interval model. If still
INFEASIBLE, delete that arc permanently. FEASIBLE/UNKNOWN retain the
arc; UNKNOWN is not a proof of irreducibility.

Output: smaller independently verified core disjunction that EVERY
Cmax<=2005 schedule must violate. A truly singleton/small core would be
a strong, representation-independent structural insight.
"""
import argparse,json,random,time
from pathlib import Path
from cross_basin_poset import model_from_covers
from search import obtain,setup,evaluate

ROOT=Path(__file__).resolve().parent

def run(a):
    routes,ds,base=obtain();pos,dur=setup(routes,ds)
    assert evaluate(base,pos,dur)==2006
    source=ROOT/'results'/('cross-poset-'+a.cohort)/'intersection-analysis.json'
    report=json.loads(source.read_text())
    assert report['certified_new_disjunction'] and report['independent_hard_core_revalidation']['status']=='INFEASIBLE'
    edges=[(x['machine'],x['from_job'],x['to_job']) for x in report['new_sufficient_unsat_core']]
    assert edges
    rng=random.Random(a.seed)
    a.out.mkdir(parents=True,exist_ok=True)
    began=time.monotonic()
    checks=[];unknown=0
    for roundno in range(a.passes):
        order=edges[:]
        rng.shuffle(order)
        if roundno%2:order.reverse()
        changed=0
        for edge in order:
            candidate=[x for x in edges if x!=edge]
            if not candidate:continue
            check=model_from_covers(candidate,pos,dur,2005,False,a.per_test_seconds,
                                    a.seed+len(checks))
            item=dict(round=roundno,edge_removed=list(edge),result=check['status'],
                      size_before=len(edges),seconds=check['elapsed_seconds'])
            checks.append(item)
            if check['status']=='INFEASIBLE':
                edges=candidate;changed+=1
                item['removed_permanently']=True
            elif check['status']=='UNKNOWN':unknown+=1
            if len(checks)%10==0:
                print('PROGRESS',a.cohort,len(checks),'size',len(edges),'unknown',unknown,
                    'wall',round(time.monotonic()-began,1),flush=True)
        if changed==0:break
    final=model_from_covers(edges,pos,dur,2005,False,a.final_seconds,a.seed+999)
    complete=final['status']=='INFEASIBLE'
    output=dict(instance='ta41',target=2005,source_cohort=a.cohort,
        original_hard_certified_unsat_core_size=report['new_core_size'],
        retained_core_size=len(edges),deleted_core_edges=report['new_core_size']-len(edges),
        independent_final_hard_validation=final,
        retained_precedences=[dict(machine=m,from_job=j,to_job=k) for m,j,k in edges],
        tests=checks,unknown_checks=unknown,was_final_infeasibility_certified=complete,
        elapsed_seconds=round(time.monotonic()-began,3),
        scope='Any <=2005 ta41 schedule must reverse >=1 of these retained machine precedence pairs. Minimality NOT claimed unless all single deletion probes were fully solved and ruled out unsat.'
    )
    (a.out/'shrunk-core.json').write_text(json.dumps(output,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in output.items()
                  if k not in ('tests','retained_precedences')}),flush=True)
    if not complete:raise RuntimeError('Final sufficient core not re-certified')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cohort',choices=['oldplusnine','gateways','oldnew','all12'],required=True)
    p.add_argument('--passes',type=int,default=2)
    p.add_argument('--per-test-seconds',type=float,default=3.0)
    p.add_argument('--final-seconds',type=float,default=30)
    p.add_argument('--seed',type=int,default=41)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
