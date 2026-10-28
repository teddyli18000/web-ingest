#!/usr/bin/env python3
"""Independent ta41 budget-k machine reorder feasibility; NO learned cuts."""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate

def main(a):
    r,d,baseline=obtain();pos,dur=setup(r,d)
    assert evaluate(baseline,pos,dur)==2006
    model=cp_model.CpModel(); T=2005
    s=[model.new_int_var(0,T,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,T,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19): model.add(s[j*20+k+1]>=e[j*20+k])
    changed=[model.new_bool_var('changed%d'%m) for m in range(20)]
    model.add(sum(changed)<=a.k)
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        for x,y in zip(baseline[m],baseline[m][1:]):
            model.add(s[y*20+pos[y][m]]>=e[x*20+pos[x][m]]).only_enforce_if(changed[m].Not())
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=a.workers
    solver.parameters.random_seed=a.seed
    t=time.monotonic();status=solver.solve(model)
    info=dict(instance='ta41',baseline=2006,target=2005,maximum_changed_machine_orders=a.k,
              model='independent NoOverlap machine-cardinality decision without core constraints',
              status=solver.status_name(status),elapsed_seconds=round(time.monotonic()-t,3),
              conflicts=solver.num_conflicts,branches=solver.num_branches,
              theorem_if_infeasible='Any <=2005 schedule differs from baseline on at least %d machine orders'%(a.k+1),
              ortools_version=__import__('ortools').__version__)
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        orders=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]])) for m in range(20)]
        score=evaluate(orders,pos,dur)
        assert score is not None and score<=2005,score
        count=sum(x!=y for x,y in zip(orders,baseline))
        assert count<=a.k,count
        info.update(score=score,changed_machine_orders=count)
        (a.out/'certificate.json').write_text(json.dumps({'machines':orders},separators=(',',':'))+'\n')
    (a.out/'decision.json').write_text(json.dumps(info,indent=2)+'\n')
    print('RESULT',json.dumps(info),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--k',type=int,default=14)
    p.add_argument('--seconds',type=int,default=540)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=11414)
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-budget14')
    main(p.parse_args())
