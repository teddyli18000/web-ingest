#!/usr/bin/env python3
"""Independently validate and shrink the five-parent ta41 shared-order UNSAT core.

Source: 21 assumption-selected same-machine precedences in
consensus-five-parents/consensus-analysis.json.

Rebuild a *separate hard-constraint* interval scheduling model, with
all 600 job operations and NoOverlap on every machine, and ONLY the
selected core precedences. Do not import any original assumption bits.
For each candidate deletion, if the new hard model remains INFEASIBLE
at target makespan 2005, deletion is rigorous. UNKNOWN never authorizes
deletion. Multiple distinct deletion orders may yield smaller cores.

Result, once independently verified INFEASIBLE, is a sufficient set of
fixed machine pair orientations that NO <=2005 schedule can retain.
Its reverse alternatives form a complete disjunctive cover of the full
2005 feasibility problem.
"""
import argparse,json,random,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate


def test_hard_core(core,pos,dur,target,seconds,seed):
    model=cp_model.CpModel()
    starts=[model.new_int_var(0,target,'s%d'%i) for i in range(600)]
    ends=[model.new_int_var(0,target,'e%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(starts[i],dur[i],ends[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j*20+k+1]>=ends[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    for arc in core:
        m,j,h=arc['machine'],arc['from_job'],arc['to_job']
        model.add(starts[h*20+pos[h][m]]>=ends[j*20+pos[j][m]])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=seed
    start=time.monotonic();status=solver.solve(model)
    return solver.status_name(status),round(time.monotonic()-start,3),solver.num_conflicts

def main(a):
    root=Path(__file__).parent
    src=json.loads((root/'results/consensus-five-parents/consensus-analysis.json').read_text())
    assert src['status']=='INFEASIBLE' and src['unsat_core_size']==21
    original=src['proven_unsat_core']
    routes,ds,baseline=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(baseline,pos,dur)==2006
    status,elapsed,_=test_hard_core(original,pos,dur,2005,20,a.seed)
    if status!='INFEASIBLE':
        raise RuntimeError('Independent hard NoOverlap checker did not certify initial 21-arc core: '+status)
    before=time.monotonic()
    logs=[];best=original[:]
    for restart in range(a.restarts):
        if time.monotonic()-before>a.total_seconds-12:break
        rng=random.Random(a.seed+restart*11)
        trial=best[:] if restart%2 else original[:]
        permutation=list(range(len(trial)))
        rng.shuffle(permutation)
        processed=0
        for item in [trial[i] for i in permutation]:
            if time.monotonic()-before>a.total_seconds-10:break
            if len(trial)<=1:break
            reduced=[x for x in trial if x is not item]
            status,sec,conflicts=test_hard_core(reduced,pos,dur,2005,
                  a.per_deletion_seconds,a.seed+restart*100+processed)
            logs.append(dict(restart=restart,deleted_arc=item,
                             remaining_if_deleted=len(reduced),
                             verdict=status,seconds=sec,conflicts=conflicts))
            if status=='INFEASIBLE':trial=reduced
            processed+=1
        if len(trial)<len(best):
            best=trial[:]
            print('BETTER certified core',len(best),'restart',restart,flush=True)
        elif restart%5==0:
            print('PASS',restart,'core',len(trial),'best',len(best),flush=True)
    status,elapsed2,_=test_hard_core(best,pos,dur,2005,30,a.seed+99999)
    assert status=='INFEASIBLE'
    report={
        'instance':'Taillard ta41','deadline':2005,'baseline':2006,
        'original_assumption_core_size':len(original),
        'original_independently_verified_hard_infeasible':True,
        'final_hard_core_size':len(best),
        'final_core_hard_verdict':status,
        'final_hard_core_machine_ids':sorted(set(x['machine'] for x in best)),
        'final_necessary_reverse_disjunction':best,
        'remaining_deletion_trials':len(logs),
        'deletion_trial_INFEASIBLE':sum(x['verdict']=='INFEASIBLE' for x in logs),
        'deletion_trial_UNKNOWN':sum(x['verdict']=='UNKNOWN' for x in logs),
        'all_deletion_attempts':logs,
        'initial_hard_verification_seconds':elapsed,
        'final_hard_verification_seconds':elapsed2,
        'elapsed_total_seconds':round(time.monotonic()-before,3),
        'logical_claim':'Any valid ta41 schedule of makespan <=2005 must reverse at least one original machine precedence in final_necessary_reverse_disjunction. This is a necessary condition, not a feasible certificate.',
        'core_minimality_claim':'No globally minimum or inclusion-minimal core is claimed; only each accepted deletion was independently proved to retain hard infeasibility.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items()
                               if k not in ('all_deletion_attempts','final_necessary_reverse_disjunction')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=41)
    p.add_argument('--restarts',type=int,default=6)
    p.add_argument('--per-deletion-seconds',type=float,default=3.0)
    p.add_argument('--total-seconds',type=float,default=260)
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'shared-hard-core-shrink.json')
    main(p.parse_args())
