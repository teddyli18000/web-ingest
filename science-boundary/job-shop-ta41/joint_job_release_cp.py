#!/usr/bin/env python3
"""Directly couple job-bundle keep/release variables to complete scheduling.

No outer greedy joint-hit-set. The SAME CP-SAT optimization decides both:
which of the 30 jobs' whole-machine constraints to release (free_job[j])
and exactly how to reorder all 600 operations under the hard deadline.

For each original adjacent machine pair (job a immediately before job b)
the old order is hard only IF NEITHER job is released:
    start[b] >= end[a] ONLY IF ~free_job[a] and ~free_job[b].

Full route precedences and 20 NoOverlap constraints are always HARD.
sum(free_job) <= K is the only structural search restriction. There are
no forced hidden-root reversals, no oracle, and all full candidates are
independently checked. This represents an exact, joint, non-monotone
multi-resource subspace at each K, not a greedy list of released arcs.

If search concludes INFEASIBLE, the conclusion pertains ONLY to the
K-job-release neighborhood under target L. UNKNOWN is not exclusion.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from structural_cut import disjunctive_dag
from search import evaluate

ROOT=Path(__file__).resolve().parent

def run(a):
    orders,pos,dur,initial=parse_case(a.start)
    L=initial-1
    start=time.monotonic()
    model=cp_model.CpModel()
    st=[model.new_int_var(0,L-dur[i],f's{i}') for i in range(600)]
    en=[model.new_int_var(dur[i],L,f'e{i}') for i in range(600)]
    interval=[model.new_interval_var(st[i],dur[i],en[i],f'iv{i}') for i in range(600)]
    released=[model.new_bool_var(f'free_job_{j}') for j in range(30)]
    model.add(sum(released)<=a.max_jobs)
    for j in range(30):
        for k in range(19):
            model.add(st[j*20+k+1]>=en[j*20+k])
    original_edges=[]
    for m,row in enumerate(orders):
        model.add_no_overlap([interval[j*20+pos[j][m]] for j in range(30)])
        for ja,jb in zip(row,row[1:]):
            u=ja*20+pos[ja][m];v=jb*20+pos[jb][m]
            model.add(st[v]>=en[u]).only_enforce_if(
                [released[ja].Not(),released[jb].Not()])
            original_edges.append((m,ja,jb))
    assert len(original_edges)==580
    # Hints strictly from incumbent, not from any improved historical oracle.
    _,_,_,head,tail,full=disjunctive_dag(orders,pos,dur,set())
    assert full==initial
    for op in range(600):
        hint=min(head[op],L-dur[op])
        model.add_hint(st[op],hint)
        model.add_hint(en[op],hint+dur[op])
    for j in range(30):model.add_hint(released[j],0)
    if a.optimize_job_count:
        # Costs all identical: exact minimum released-job cardinality
        # among target-feasible schedules, if OPTIMAL is obtained.
        model.minimize(sum(released))
    cp=cp_model.CpSolver()
    cp.parameters.max_time_in_seconds=a.seconds
    cp.parameters.num_search_workers=a.workers
    cp.parameters.random_seed=a.seed
    status=cp.solve(model)
    report=dict(case=('ta41' if a.start=='ta41' else Path(a.start).parent.name),
        incumbent_makespan=initial,target_makespan=L,
        release_unit='whole job across 20 machines',
        released_jobs_upper_bound=a.max_jobs,
        allowed_job_sets='ANY <=K of the 30 source jobs, chosen jointly with full machine order',
        solver='OR-Tools CP-SAT 9.14.6206',
        case_source_only=True,
        solver_status=cp.status_name(status),
        full_solver_seconds=round(cp.wall_time,3),
        total_wall_seconds=round(time.monotonic()-start,3),
        num_branches=cp.num_branches,num_conflicts=cp.num_conflicts,
        optimize_release_cardinality=bool(a.optimize_job_count),
        interpretation='INFEASIBLE excludes only this K-job source-neighborhood, not the global JSSP. UNKNOWN has no exclusion force.')
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        orders2=[sorted(range(30),key=lambda j:cp.value(st[j*20+pos[j][m]]))
                 for m in range(20)]
        score=evaluate(orders2,pos,dur)
        assert score is not None and score<=L
        changed_jobs={j for j in range(30) if cp.value(released[j])}
        actual=[]
        for m,row in enumerate(orders):
            pos2={job:k for k,job in enumerate(orders2[m])}
            for k,(ja,jb) in enumerate(zip(row,row[1:])):
                if pos2[ja]>pos2[jb]:
                    actual.append(m*29+k)
                    assert ja in changed_jobs or jb in changed_jobs
        (a.out/'certificate.json').write_text(
            json.dumps({'machines':orders2},separators=(',',':'))+'\n')
        report.update(independently_verified_makespan=score,
            declared_released_jobs=sorted(changed_jobs),
            released_job_count=len(changed_jobs),
            actual_original_adjacent_reversals=actual,
            actual_reversals=len(actual),
            affected_machines=sorted({i//29 for i in actual}))
    (a.out/'joint-job-cp.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--max-jobs',type=int,required=True)
    p.add_argument('--optimize-job-count',action='store_true')
    p.add_argument('--seconds',type=float,default=60)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=333)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    assert 0<=args.max_jobs<=30
    run(args)
