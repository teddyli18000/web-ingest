#!/usr/bin/env python3
"""Oracle-blind job-coupled implicit hitting set for JSSP target improvement.

Representation is the 30 complete JOB trajectories, rather than 580
individual machine-adjacent precedences. Releasing job j unpins every
incumbent machine adjacency incident to its 20 operations. The hard CP
model ALWAYS contains all job chains, all 600 operations, every machine
NoOverlap, and target <= incumbent-1.

At a failed fixed-partial-order completion obtain an exact CP-SAT sufficient
UNSAT core C of incumbent machine-arc assumptions. This implies a valid
job-level disjunction: at least one endpoint job of any edge in C must be
released. Accumulate these clauses and globally RESELECT the entire set
of released jobs by a minimum-cardinality hitting set. Thus chosen bundles
may be replaced across iterations, unlike monotone arc deletions.

The three policies differ only in cardinality-preserving tie-breaking:
dynamic by recently observed endpoint-jobs in replacement UNSAT cores,
static by initial critical-arc concentration, random by fixed pseudorandom
weights. Identical hard CP, time limits and starts.

Neither hidden optimum nor historical target schedule is read. This is a
controlled experimental construction, not a novelty claim for core-guided
LNS or job-level relaxations. UNKNOWN never implies infeasibility.
"""
import argparse,json,random,time
from collections import Counter
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from constructive_implicit_hitting_set import make_full
from structural_cut import disjunctive_dag
from search import evaluate

ROOT=Path(__file__).resolve().parent

def solve_master(clauses,weights,seconds,seed,min_jobs=0,forbidden=()):
    mdl=cp_model.CpModel()
    z=[mdl.new_bool_var(f'release_job_{j}') for j in range(30)]
    for clause in clauses:
        mdl.add(sum(z[j] for j in clause)>=1)
    if min_jobs>0:
        mdl.add(sum(z)>=min_jobs)
    # A CP UNKNOWN is NOT UNSAT. Optional exact-set no-goods diversify
    # the search without being interpreted as necessary repair clauses.
    for blocked in forbidden:
        chosen=set(blocked)
        mdl.add(sum(z[j] if j in chosen else 1-z[j]
                    for j in range(30))<=29)
    # All weights 0..25. Dominance is guaranteed: 30*25 < 1000.
    mdl.minimize(1000*sum(z)+sum(weights[j]*z[j] for j in range(30)))
    slv=cp_model.CpSolver()
    slv.parameters.num_search_workers=4
    slv.parameters.max_time_in_seconds=seconds
    slv.parameters.random_seed=seed
    stat=slv.solve(mdl)
    if stat not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return None,dict(status=slv.status_name(stat))
    chosen={j for j in range(30) if slv.value(z[j])}
    assert len(chosen)>=min_jobs,(len(chosen),min_jobs)
    assert all(chosen.intersection(c) for c in clauses)
    return chosen,dict(status=slv.status_name(stat),num_jobs=len(chosen),
             exact_master_optimal=(stat==cp_model.OPTIMAL),
             objective=slv.objective_value,bound=slv.best_objective_bound)

def static_priority(orders,pos,dur,C,endpoint):
    _,arcs,_,head,tail,lb=disjunctive_dag(orders,pos,dur,set())
    assert lb==C and len(arcs)==580
    priority=Counter()
    for idx,(m,k,u,v) in enumerate(arcs):
        slack=C-(head[u]+dur[u]+tail[v])
        if slack<=20:
            for j in endpoint[idx]:
                priority[j]+=max(1,21-slack)
    return priority

def run(a):
    orders,pos,dur,initial=parse_case(a.start)
    L=initial-1
    mdl,arcs,s=make_full(orders,pos,dur,L)
    assert len(arcs)==580
    endpoint=[(ja,jb) for row in orders for ja,jb in zip(row,row[1:])]
    assert len(endpoint)==580
    byidx={b.index:i for i,b in enumerate(arcs)}
    rng=random.Random(a.seed)
    static=static_priority(orders,pos,dur,initial,endpoint)
    job_counts=Counter()
    clauses=[]
    clause_set=set()
    skipped=[]
    report=dict(instance='ta41' if a.start=='ta41' else Path(a.start).parent.name,
        initial_score=initial,target=L,policy=a.policy,seed=a.seed,
        mechanism='30 atomic job-level release decisions, grouped over 580 original adjacent machine precedences, global implicit hitting set with exact full NoOverlap completion',
        historic_oracle_unavailable_to_search=True,
        cp_sat_version=__import__('ortools').__version__,
        time_budget_seconds=a.seconds,cp_per_query_seconds=a.cp_seconds,
        hitting_per_query_seconds=a.hit_seconds,
        iterations=[],status='ACTIVE',complete=False,
        minimum_job_growth_interval=a.growth_step,
        starting_min_job_floor=a.min_jobs)
    a.out.mkdir(parents=True,exist_ok=True)
    t0=time.monotonic()
    prior=set()
    for it in range(a.max_iterations):
        remain=a.seconds-(time.monotonic()-t0)
        if remain<=0.7:
            report['status']='TIME_LIMIT';break
        if a.policy=='dynamic':
            # Smaller weights for currently/frequently conflicting jobs.
            weights=[max(0,25-min(25,job_counts[j])) for j in range(30)]
        elif a.policy=='static':
            maxcrit=max(static.values(),default=1)
            weights=[int(25*(maxcrit-static[j])/maxcrit) for j in range(30)]
        else:
            weights=[rng.randrange(26) for j in range(30)]
        floor=min(a.max_jobs,a.min_jobs+(it//a.growth_step if a.growth_step else 0))
        selected,master=solve_master(clauses,weights,
            min(a.hit_seconds,max(0.05,remain*.15)),a.seed+it,
            min_jobs=floor,forbidden=skipped)
        if selected is None:
            report['status']='MASTER_UNKNOWN'
            report['iterations'].append(dict(i=it,master=master))
            break
        freed={i for i,(j,k) in enumerate(endpoint) if j in selected or k in selected}
        mdl.clear_assumptions()
        mdl.add_assumptions([v for i,v in enumerate(arcs) if i not in freed])
        solver=cp_model.CpSolver()
        solver.parameters.num_search_workers=1
        solver.parameters.max_time_in_seconds=min(a.cp_seconds,max(0.05,remain*.8))
        solver.parameters.random_seed=a.seed+it
        st=solver.solve(mdl)
        record=dict(i=it,cp_status=solver.status_name(st),
            selected_jobs=sorted(selected),released_jobs=len(selected),
            target_min_jobs_floor=floor,diversified_unknowns=len(skipped),
            released_machine_arcs=len(freed),master=master,
            changed_selected_jobs=len(selected.symmetric_difference(prior)),
            cp_seconds=round(solver.wall_time,4),
            cp_branches=solver.num_branches,cp_conflicts=solver.num_conflicts)
        report['iterations'].append(record)
        if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
            full=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
                  for m in range(20)]
            val=evaluate(full,pos,dur)
            assert val is not None and val<=L,(val,L)
            flips=[m*29+k for m,row in enumerate(orders)
                   for k,(ja,jb) in enumerate(zip(row,row[1:]))
                   if full[m].index(ja)>full[m].index(jb)]
            assert set(flips).issubset(freed),(flips,freed)
            (a.out/'certificate.json').write_text(
                json.dumps({'machines':full},separators=(',',':'))+'\n')
            record['independent_score']=val
            record['original_adjacent_reversals']=flips
            report.update(status='CONSTRUCTIVE_IMPROVEMENT',best_score=val,
                          improvement=initial-val,successful_iteration=it)
            break
        elif st==cp_model.INFEASIBLE:
            core_raw=solver.sufficient_assumptions_for_infeasibility()
            if not core_raw:
                # Would prove this target infeasible for entire instance
                # only when no assumptions actually required.
                report['status']='FULL_TARGET_INFEASIBLE_WITH_EMPTY_ASSUMPTION_CORE'
                record['core_size']=0;break
            core={byidx[x] for x in core_raw}
            assert core and core.isdisjoint(freed),(core,freed)
            clause=frozenset(j for idx in core for j in endpoint[idx])
            assert clause and clause.isdisjoint(selected)
            if clause in clause_set:
                # A repeated identical projected job clause has already
                # been hit; this is a correctness invariant violation.
                raise AssertionError('repeated unhit projected job clause')
            clause_set.add(clause)
            clauses.append(sorted(clause))
            for j in clause:job_counts[j]+=1
            record.update(core_size=len(core),core_jobs=len(clause),
                          new_job_clause=sorted(clause),
                          core_incumbent_arc_ids=sorted(core))
        else:
            # Continue searching other bundles or larger cardinalities;
            # this UNKNOWN is only a computational limit.
            skipped.append(frozenset(selected))
            record['unknown_no_good_added']=True
        prior=selected
        if it%20==0:
            print('STEP',report['instance'],a.policy,it,st,
                  'jobs',len(selected),'released arcs',len(freed),
                  'clauses',len(clauses),flush=True)
        if len(selected)>a.max_jobs:
            report['status']='MAX_RELEASED_JOBS';break
    else:
        report['status']='ITERATION_LIMIT'
    report['complete']=True
    report['elapsed_seconds']=round(time.monotonic()-t0,3)
    report['total_new_job_clauses']=len(clauses)
    report['queried_partial_schedules']=len(report['iterations'])
    (a.out/'job-group-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='iterations'}),
          flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',choices=['dynamic','static','random'],required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--seconds',type=float,default=90)
    p.add_argument('--max-iterations',type=int,default=500)
    p.add_argument('--cp-seconds',type=float,default=0.6)
    p.add_argument('--hit-seconds',type=float,default=0.3)
    p.add_argument('--max-jobs',type=int,default=30)
    p.add_argument('--min-jobs',type=int,default=1)
    p.add_argument('--growth-step',type=int,default=35,
                   help='after this many attempts increase the minimum released-job cardinality by 1; 0 disables growth')
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
