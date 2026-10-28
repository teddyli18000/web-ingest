#!/usr/bin/env python3
"""Independently recheck the portable rational lower-bound certificate.

The dual packing is verified with Python exact integers. Every core whose
weight is nonzero is then independently certified as infeasible at Cmax=2005:
first by a pure DAG longest-path test using only pinned core arcs, then
(if needed) by a separately constructed interval/NoOverlap CP-SAT model
with hard precedence clauses rather than original assumption literals.

This reduces the trusted-core set from 1433 to just the positive-weight
cores needed by the dual certificate (67 in the first generated witness).
"""
import argparse
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from structural_cut import disjunctive_dag


def cp_core_infeasible(orders,pos,durations,selected,horizon,seconds):
    model=cp_model.CpModel()
    s=[model.new_int_var(0,horizon,'s_%d'%i) for i in range(600)]
    e=[model.new_int_var(0,horizon,'e_%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(s[i],durations[i],e[i],'i_%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    for index in selected:
        m,k=divmod(index,29)
        j,h=orders[m][k:k+2]
        u=j*20+pos[j][m];v=h*20+pos[h][m]
        model.add(s[v]>=e[u])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=41
    status=solver.solve(model)
    return solver.status_name(status),solver.wall_time


def main(source,weights_file,out,seconds):
    raw=json.loads(source.read_text())
    weights=json.loads(weights_file.read_text())
    assert raw['target']==weights['target']==2005
    assert raw['baseline']==weights['incumbent']==2006
    cores=raw['core_sets']
    scale=weights['rational_denominator']
    terms={int(k):v for k,v in weights['nonzero_core_weights'].items()}
    assert terms and all(isinstance(v,int) and 0<v<=scale for v in terms.values())
    loads=[0]*580
    for ix,num in terms.items():
        assert 0<=ix<len(cores)
        for j in set(cores[ix]):
            assert 0<=j<580
            loads[j]+=num
    assert max(loads)<=scale
    total=sum(terms.values())
    assert total==weights['rational_total_numerator']
    bound=(total+scale-1)//scale
    assert bound==weights['portable_lower_bound']
    routes,dur_by_job,orders=obtain()
    pos,dur=setup(routes,dur_by_job)
    assert evaluate(orders,pos,dur)==2006
    checked=[]
    start=time.monotonic()
    for ix in sorted(terms):
        core=set(cores[ix])
        _,_,_,_,_,C=disjunctive_dag(orders,pos,dur,set(range(580))-core)
        if C>2005:
            status='INFEASIBLE_BY_DAG_LONGEST_PATH'
            elapsed=0
        else:
            status,elapsed=cp_core_infeasible(orders,pos,dur,core,2005,seconds)
        checked.append(dict(core_index=ix,core_size=len(core),
                            precedence_only_longest_path=C,
                            independent_status=status,
                            verification_wall_seconds=round(elapsed,3)))
        print('CORE',ix,len(checked),'of',len(terms),status,'prec_lb',C,flush=True)
        if status not in ('INFEASIBLE','INFEASIBLE_BY_DAG_LONGEST_PATH'):
            break
    complete=len(checked)==len(terms) and all(r['independent_status'] in ('INFEASIBLE','INFEASIBLE_BY_DAG_LONGEST_PATH') for r in checked)
    report={
        'target':2005,'incumbent':2006,'verified_exact_dual_inequalities':True,
        'dual_sum_numerator':total,'dual_denominator':scale,
        'verified_dual_ceiling_lower_bound':bound if complete else None,
        'positive_weight_core_count':len(terms),
        'checked_core_count':len(checked),
        'complete_independent_infeasibility_checks':complete,
        'dag_only_core_proofs':sum(r['independent_status']=='INFEASIBLE_BY_DAG_LONGEST_PATH' for r in checked),
        'cp_sat_core_proofs':sum(r['independent_status']=='INFEASIBLE' for r in checked),
        'elapsed_wall_seconds':round(time.monotonic()-start,3),
        'per_core':checked,
        'semantics':'If verified, any ta41 schedule with Cmax<=2005 must reverse at least this many original adjacent machine precedences; the result is NOT a global makespan lower bound.'
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='per_core'}),flush=True)
    if not complete:raise RuntimeError('Some positive-weight cores were not independently verified; no formal claim')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cores',type=Path,default=Path(__file__).parent/'results'/'core-seed4107'/'core-analysis.json')
    p.add_argument('--weights',type=Path,default=Path(__file__).parent/'results'/'core-dual.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'core-dual-independent-verification.json')
    p.add_argument('--seconds',type=float,default=9)
    a=p.parse_args();main(a.cores,a.weights,a.out,a.seconds)
