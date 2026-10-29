#!/usr/bin/env python3
"""Optimize the residual CP-core-feedback ta41 subspaces, not just decide them.

Input: six core-feedback release histories. At the last release step,
freeze ONLY survivor operations' relative machine order, retain full
NoOverlap and job precedences, and minimize makespan <=2006. The
published 2006 starting machine permutation is a verified feasible hint.

OPTIMAL and score=2006 proves *only this exact partial-order subspace*
cannot reach 2005. A <=2005 schedule is verified by an independent
DAG evaluator and then by upstream Few Shots in the Action.
FEASIBLE 2006 / UNKNOWN does not exclude 2005.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from temporal_band_repair import fixed_precedence
from core_guided_lns import graph_analysis

ROOT=Path(__file__).resolve().parent
def run(a):
    routes,rows,base=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    parent=base
    if a.parent!='baseline':
        root=ROOT/'results'/f'gateway-{a.parent}'
        vr=json.loads((root/'upstream-verdict.json').read_text())
        assert vr['valid'] and int(vr['score'])==2006
        parent=json.loads((root/'certificate.json').read_text())['machines']
    assert evaluate(parent,pos,dur)==2006
    source=ROOT/'results'/f'core-feedback-{a.parent}-{a.method}'/'core-release.json'
    source_json=json.loads(source.read_text())
    # The core-feedback history records ONLY additional releases beyond
    # the 240 operations from the original dynamic-path experiment.
    seed_src=ROOT/'results'/f'dcprcp-{a.parent}-dynamic-4107'/'dynamic-repair.json'
    seed_report=json.loads(seed_src.read_text())
    assert seed_report['complete'] and seed_report['rounds_completed']==8
    release={u for rec in seed_report['release_sets'] for u in rec['released_this_round']}
    assert len(release)==240
    for rec in source_json['records']:
        release.update(rec.get('released_this_round',[]))
    assert len(release)==source_json['records'][-1]['free_operations'],(
        len(release),source_json['records'][-1]['free_operations'])
    constraints=fixed_precedence(parent,pos,release)
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2006,f's{i}') for i in range(600)]
    e=[model.new_int_var(0,2006,f'e{i}') for i in range(600)]
    intervals=[model.new_interval_var(s[i],dur[i],e[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    for u,v in constraints:model.add(s[v]>=e[u])
    cmax=model.new_int_var(0,2006,'makespan')
    model.add_max_equality(cmax,e)
    model.minimize(cmax)
    _,head,_,score=graph_analysis(parent,pos,dur)
    assert score==2006 and len(head)==600
    for i in range(600):
        model.add_hint(s[i],head[i])
        model.add_hint(e[i],head[i]+dur[i])
    model.add_hint(cmax,2006)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=a.workers
    solver.parameters.random_seed=a.seed
    begin=time.monotonic();status=solver.solve(model)
    report=dict(instance='ta41',target=2005,parent=a.parent,method=a.method,
      source=str(source.relative_to(ROOT)),
      released_operation_count=len(release),fixed_survivor_precedence_arcs=len(constraints),
      status=solver.status_name(status),
      lower_bound=solver.best_objective_bound,
      wall_seconds=round(time.monotonic()-begin,3),
      branches=solver.num_branches,conflicts=solver.num_conflicts,
      workers=a.workers,ortools_version=__import__('ortools').__version__,
      correct_interpretation='Only OPTIMAL 2006 excludes the exact pinned-survivor subspace; UNKNOWN or FEASIBLE 2006 does not exclude target 2005.')
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        cert=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
              for m in range(20)]
        actual=evaluate(cert,pos,dur)
        assert actual is not None and actual<=2006,actual
        report['independent_DAG_score']=actual
        report['objective']=solver.objective_value
        assert int(round(solver.objective_value))==actual
        if actual<=2005:
            (a.out/'certificate.json').write_text(json.dumps({'machines':cert},separators=(',',':'))+'\n')
    (a.out/'objective-repair.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=['baseline','124'],required=True)
    p.add_argument('--method',choices=['degree','core_random','random'],required=True)
    p.add_argument('--seconds',type=float,default=105)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=4117)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
