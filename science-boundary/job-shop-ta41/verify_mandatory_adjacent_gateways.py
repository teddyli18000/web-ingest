#!/usr/bin/env python3
"""Independent full-NoOverlap CP verification of necessary ta41 gateways."""
import json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate

ROOT=Path(__file__).resolve().parent
def main():
    routes,rows,orders=obtain()
    pos,duration=setup(routes,rows)
    assert evaluate(orders,pos,duration)==2006
    data=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert data['instance']=='ta41' and data['target']==2005
    assert data['status']=='INFEASIBLE' and data['all_parents_independently_verified_2006']
    arcs=data['proven_unsat_core']
    assert len(arcs)==21
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2005-duration[i],f's{i}') for i in range(600)]
    e=[model.new_int_var(duration[i],2005,f'e{i}') for i in range(600)]
    intervals=[model.new_interval_var(s[i],duration[i],e[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    ids=[]
    for x in arcs:
        m=x['machine'];a=x['from_job'];b=x['to_job']
        i=orders[m].index(a)
        assert orders[m].index(b)==i+1,(x,i)
        ids.append(m*29+i)
        model.add(s[b*20+pos[b][m]]>=e[a*20+pos[a][m]])
    ids=sorted(ids)
    assert len(set(ids))==21 and len(set(i//29 for i in ids))==5
    slv=cp_model.CpSolver()
    slv.parameters.max_time_in_seconds=20
    slv.parameters.num_search_workers=1
    slv.parameters.random_seed=20261108
    start=time.monotonic();status=slv.solve(model)
    report=dict(instance='ta41',target=2005,incumbent=2006,
        asserted_machine_resource_arcs=ids,number_of_gateways=21,
        source='results/consensus-five-parents/consensus-analysis.json',
        independently_rebuilt_full_NoOverlap_model=True,
        solver_status=slv.status_name(status),
        seconds=round(time.monotonic()-start,3),
        conflicts=slv.num_conflicts,branches=slv.num_branches,
        ortools_version=__import__('ortools').__version__,
        exact_claim=('Any makespan <=2005 schedule must reverse at least one listed original machine adjacency' if status==cp_model.INFEASIBLE else 'NOT ESTABLISHED'),
        caution='Necessary, not sufficient. This does not assert existence of a 2005 schedule.')
    p=ROOT/'results'/'ta41-mandatory-adjacent-gateways-independently-proved.json'
    p.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)
    assert status==cp_model.INFEASIBLE,report
if __name__=='__main__':main()
