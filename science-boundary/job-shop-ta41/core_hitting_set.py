#!/usr/bin/env python3
"""Turn CP-SAT infeasibility cores into a certified distance obstruction.

Every UNSAT core is a set of incumbent adjacent machine precedences that
cannot *all* hold in any ta41 schedule of makespan <=2005. Thus a feasible
target schedule must violate at least one arc in each such core. The minimum
hitting-set cardinality is a rigorous lower bound on the number of baseline
adjacent precedences that any improved schedule must reverse (and hence on
adjacent-transposition distance from the baseline).

The core collection is not assumed complete. OPTIMAL solves the finite core
hitting-set exactly, NOT the ta41 job-shop problem.
"""
import argparse
import json
import random
import time
from pathlib import Path
from ortools.sat.python import cp_model


def disjoint_core_packing(cores,seed=41,restarts=400):
    # A disjoint family proves an independent cardinality lower bound
    # without trusting an optimizer: each core must be hit separately.
    rng=random.Random(seed)
    best=[]
    core_sets=[set(c) for c in cores]
    for trial in range(restarts):
        order=list(range(len(cores)))
        if trial==0:order.sort(key=lambda i:len(cores[i]))
        elif trial%2:order.sort(key=lambda i:(len(cores[i]),rng.random()))
        else:rng.shuffle(order)
        used=set();pack=[]
        for idx in order:
            if used.isdisjoint(core_sets[idx]):
                pack.append(idx);used.update(core_sets[idx])
        if len(pack)>len(best):best=pack
    return best


def main(inp,out,seconds):
    data=json.loads(inp.read_text())
    assert data['target']==2005 and data['baseline']==2006
    raw=data['core_sets']
    cores=[]
    seen=set()
    for c in raw:
        cc=tuple(sorted(set(c)))
        assert cc and all(0<=i<580 for i in cc)
        if cc not in seen:
            seen.add(cc);cores.append(cc)
    assert len(cores)>=100,(len(cores),"core dataset unexpectedly too small")
    packed=disjoint_core_packing(cores)
    model=cp_model.CpModel()
    x=[model.new_bool_var('break_%03d'%i) for i in range(580)]
    for c in cores:
        model.add(sum(x[i] for i in c)>=1)
    model.minimize(sum(x))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=41
    solver.parameters.relative_gap_limit=0
    tic=time.monotonic()
    status=solver.solve(model)
    status_name=solver.status_name(status)
    solution=None
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        solution=[i for i in range(580) if solver.value(x[i])]
        assert all(set(solution).intersection(c) for c in cores)
    bound=solver.best_objective_bound
    proven=(status==cp_model.OPTIMAL)
    report={
        'target_makespan':2005,'incumbent':2006,
        'core_count':len(cores),'core_min_size':min(map(len,cores)),
        'core_max_size':max(map(len,cores)),
        'mathematical_scope':'Necessary minimum number of incumbent machine-adjacency precedences violated by any <=2005 feasible schedule; not a global infeasibility result',
        'independent_disjoint_core_count':len(packed),
        'independent_disjoint_core_indices':packed,
        'independent_disjoint_core_sets':[list(cores[i]) for i in packed],
        'cp_sat_status':status_name,
        'cp_sat_objective':len(solution) if solution is not None else None,
        'cp_sat_objective_bound':bound,
        'cp_sat_exact_hitting_set_optimum':proven,
        'selected_baseline_arcs':solution,
        'elapsed_seconds':round(time.monotonic()-tic,3),
        'ortools_version':__import__('ortools').__version__,
        'interpretation':'A disjoint family of d cores independently proves >=d broken original adjacencies; a completed exact hitting-set solve can establish stronger K. No claims of a <=2005 schedule.'
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('independent_disjoint_core_sets','selected_baseline_arcs')},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path(__file__).parent/'results'/'core-seed4107'/'core-analysis.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'core-distance.json')
    p.add_argument('--seconds',type=int,default=120)
    a=p.parse_args();main(a.input,a.out,a.seconds)
