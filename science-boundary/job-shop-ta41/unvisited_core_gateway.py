#!/usr/bin/env python3
"""Are 16 apparently invariant ta41 core precedences *truly* fixed at Cmax<=2006?

The 16 originally necessary consensus-core machine pairs were never
reversed among 16 independently verified 2006 schedules, including two
new max-min Hamming diverse schedules. Test a representative arc on
each implicated machine with a globally complete NoOverlap decision at
Cmax<=2006. One forced reversed pair is the ONLY hard extra constraint.

A valid FEASIBLE schedule discovers a previously unseen neutral
orientation class. True INFEASIBLE proves this exact orientation cannot
occur even at <=2006 and hence cannot occur at <=2005.
UNKNOWN proves nothing; machine adjacency is NOT frozen.

Choose the 2006 parent hint whose schedule has the smallest temporal
violation of the target reverse precedence. All stored hints must be
officially score=2006 verified, no guessed starts.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis
from cross_basin_poset import load

ROOT=Path(__file__).resolve().parent
ARC_INDEX=[115,172,380,526,541]

def score_parent_hints(pos,dur,base,arc):
    parents=load(pos,dur,base)
    for mode in ('false','true'):
        folder=ROOT/'results'/('orientation-maxmin-'+mode)/'witness'
        verdict=json.loads((folder/'upstream-verdict.json').read_text())
        assert verdict['valid'] and int(verdict['score'])==2006
        orders=json.loads((folder/'certificate.json').read_text())['machines']
        assert evaluate(orders,pos,dur)==2006
        parents['far'+mode]=orders
    for k in (1,2):
        folder=ROOT/'results'/'iterative-poset-refinement'/('neutral-%02d'%k)
        verdict=json.loads((folder/'upstream-verdict.json').read_text())
        assert verdict['valid'] and int(verdict['score'])==2006
        orders=json.loads((folder/'certificate.json').read_text())['machines']
        assert evaluate(orders,pos,dur)==2006
        parents['near%d'%k]=orders
    m=arc['machine'];a=arc['from_job'];b=arc['to_job']
    u=a*20+pos[a][m];v=b*20+pos[b][m]
    choices=[]
    for name,order in parents.items():
        assert order[m].index(a)<order[m].index(b),(name,arc)
        _,starts,_,C=graph_analysis(order,pos,dur)
        assert C==2006
        gap=starts[v]+dur[v]-starts[u]
        assert gap>0
        choices.append((gap,name,starts))
    return sorted(choices,key=lambda z:(z[0],z[1]))

def run(a):
    routes,rows,base=obtain();pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    record=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    core=record['proven_unsat_core']
    arc=next(x for x in core if x['index']==a.arc)
    assert a.arc in ARC_INDEX
    choices=score_parent_hints(pos,dur,base,arc)
    gap,name,hints=choices[0]
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2006,f's{i}') for i in range(600)]
    e=[model.new_int_var(0,2006,f'e{i}') for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    m=arc['machine'];ja=arc['from_job'];jb=arc['to_job']
    u=ja*20+pos[ja][m];v=jb*20+pos[jb][m]
    model.add(s[u]>=e[v])
    for i in range(600):
        model.add_hint(s[i],hints[i])
        model.add_hint(e[i],hints[i]+dur[i])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.random_seed=a.seed
    solver.parameters.num_search_workers=4
    t=time.monotonic();st=solver.solve(model)
    report=dict(instance='ta41',baseline=2006,target=2005,
      decision='exists Cmax<=2006 schedule with a never-observed consensus core machine pair reversed?',
      arc_id=a.arc,arc=arc,number_of_verified_source_parents=len(choices),
      nearest_temporal_hint_parent=name,nearest_reverse_gap=gap,
      status=solver.status_name(st),elapsed_seconds=round(time.monotonic()-t,3),
      conflicts=solver.num_conflicts,branches=solver.num_branches,
      all_job_precedences_and_machine_no_overlap_hard=True,
      no_other_machine_order_is_frozen=True,
      theorem_if_unsat='This exact precedence cannot reverse at Cmax<=2006, hence also cannot reverse at <=2005.',
      unknown_means_nothing=True)
    a.out.mkdir(parents=True,exist_ok=True)
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        solution=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]])) for m in range(20)]
        score=evaluate(solution,pos,dur)
        assert score is not None and score<=2006
        assert solution[m].index(jb)<solution[m].index(ja)
        report['verified_makespan']=score
        report['changed_machine_orders_from_baseline']=sum(solution[m]!=base[m] for m in range(20))
        (a.out/'certificate.json').write_text(json.dumps({'machines':solution},separators=(',',':'))+'\n')
    (a.out/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--arc',type=int,choices=ARC_INDEX,required=True)
    p.add_argument('--seconds',type=float,default=160)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
