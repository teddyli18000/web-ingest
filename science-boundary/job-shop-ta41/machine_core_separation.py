#!/usr/bin/env python3
"""Machine-group UNSAT core learning for ta41 makespan <=2005.

Twenty binary KEEP assumptions, one per incumbent machine order. All 600
nonpreemptive intervals and all NoOverlap constraints are unconditional.

Each validated UNSAT core says a target schedule must change at least one
machine order in that group. A separate exact minimum-hitting-set problem
over only 20 machines proposes the next released machine set.

Only UNSAT or independently evaluated feasible schedules are conclusive.
UNKNOWN terminates this run without claiming that the cover size is a
distance bound beyond what the learned cores mathematically establish.
"""
import argparse
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain, setup, evaluate


def build_oracle(orders, pos, dur, target):
    model = cp_model.CpModel()
    starts = [model.new_int_var(0, target, "s%d" % i) for i in range(600)]
    ends = [model.new_int_var(0, target, "e%d" % i) for i in range(600)]
    intervals = [model.new_interval_var(starts[i],dur[i],ends[i],"iv%d" % i)
                 for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j*20+k+1] >= ends[j*20+k])
    keep = [model.new_bool_var("keep_m%d" % m) for m in range(20)]
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        for a,b in zip(orders[m],orders[m][1:]):
            u=a*20+pos[a][m]
            v=b*20+pos[b][m]
            model.add(starts[v] >= ends[u]).only_enforce_if(keep[m])
    index_to_machine={v.index:m for m,v in enumerate(keep)}
    return model, keep, starts, index_to_machine


def oracle(model,keep,solver_seed,fixed_machines,seconds=10):
    model.clear_assumptions()
    model.add_assumptions([keep[m] for m in sorted(fixed_machines)])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=solver_seed
    status=solver.solve(model)
    return status, solver


def cover(cores):
    m=cp_model.CpModel()
    released=[m.new_bool_var("released_%d"%i) for i in range(20)]
    for core in cores:
        m.add(sum(released[i] for i in core)>=1)
    m.minimize(sum(released))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=15
    solver.parameters.num_search_workers=1
    status=solver.solve(m)
    if status != cp_model.OPTIMAL:
        return None, solver.best_objective_bound, solver.status_name(status)
    free=frozenset(i for i in range(20) if solver.value(released[i]))
    assert all(free.intersection(c) for c in cores)
    return free, len(free), "OPTIMAL"


def solve(out,total_seconds,oracle_seconds,iterations,seed):
    routes, ds, orders = obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    model,keep,starts,index_map=build_oracle(orders,pos,dur,2005)
    begin=time.monotonic()
    cores=[]
    seen=set()
    attempts=[]
    found=False
    out.mkdir(parents=True,exist_ok=True)
    for it in range(iterations):
        if time.monotonic()-begin>total_seconds-3:
            break
        free,lower,optimal=cover(cores)
        if free is None:
            attempts.append(dict(iteration=it,phase="min_cover",status=optimal,bound=lower))
            break
        fixed=set(range(20))-set(free)
        status,solver=oracle(model,keep,seed+it,fixed,
            seconds=min(oracle_seconds, max(1,total_seconds-(time.monotonic()-begin)-2)))
        rec=dict(iteration=it,proposed_release=sorted(free),proposed_size=len(free),
                 hitting_set_lower_bound=lower,oracle_status=solver.status_name(status),
                 elapsed=round(time.monotonic()-begin,3))
        if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
            candidate=[]
            for m in range(20):
                candidate.append(sorted(range(30),
                    key=lambda j: solver.value(starts[j*20+pos[j][m]])))
            score=evaluate(candidate,pos,dur)
            assert score is not None and score<=2005,(score,candidate)
            (out/"certificate.json").write_text(json.dumps({"machines":candidate},separators=(",",":"))+"\n")
            rec["independent_dag_makespan"]=score
            rec["actually_changed_machine_count"]=sum(a!=b for a,b in zip(candidate,orders))
            found=True
            attempts.append(rec)
            break
        if status==cp_model.INFEASIBLE:
            raw_core=solver.sufficient_assumptions_for_infeasibility()
            core=set()
            for lit in raw_core:
                if lit not in index_map:
                    raise ValueError("unmapped assumption literal")
                core.add(index_map[lit])
            if not core or not core.issubset(fixed):
                raise AssertionError("bad core")
            rec["raw_core_size"]=len(core)
            # Greedy deletion: re-solve HARD restricted machine groups. Any
            # successful reduction is a valid smaller sufficiency witness.
            # A timeout during shrinking preserves the original valid core.
            for m in sorted(core):
                trial=core-{m}
                if not trial:continue
                if time.monotonic()-begin>total_seconds-3:break
                s,_=oracle(model,keep,seed+it+101,trial,
                    seconds=min(1.25,max(0.3,total_seconds-(time.monotonic()-begin)-2)))
                if s==cp_model.INFEASIBLE:core=trial
            c=tuple(sorted(core))
            assert c not in seen,("duplicate core; hitting set logic inconsistent",c)
            seen.add(c);cores.append(c)
            rec["minimized_core"]=list(c)
            rec["number_of_cores"]=len(cores)
        else:
            rec["note"]="UNKNOWN: no exclusion or new bound follows; stopping"
            attempts.append(rec)
            break
        attempts.append(rec)
        if it%5==0:print("PROGRESS",json.dumps(rec),flush=True)
    free,lower,st=cover(cores)
    report=dict(
        method="group-level unsat core generation and exact hitting set",
        instance="ta41",target=2005,baseline=2006,
        status="candidate_found" if found else "no_candidate_proven",
        cores=[list(c) for c in cores],
        learned_core_count=len(cores),
        group_cover_status=st,
        group_cover_lower_bound=lower,
        next_free_machines=sorted(free) if free is not None else None,
        complete_exact_cover=(st=="OPTIMAL"),
        elapsed_seconds=round(time.monotonic()-begin,3),
        experiment_runs=attempts,
        semantics="Each core is an infeasible fixed-machine subspace at 2005. Exact group cover is an incumbent machine-order distance lower bound; no global makespan bound follows."
    )
    (out/"machine-core-analysis.json").write_text(json.dumps(report,indent=2)+"\n")
    print("SUMMARY",json.dumps({k:v for k,v in report.items() if k not in ("experiment_runs","cores")}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path(__file__).parent/"results"/"machine-cores")
    parser.add_argument("--seconds",type=int,default=540)
    parser.add_argument("--oracle-seconds",type=float,default=8)
    parser.add_argument("--iterations",type=int,default=150)
    parser.add_argument("--seed",type=int,default=4107)
    args=parser.parse_args()
    solve(args.out,args.seconds,args.oracle_seconds,args.iterations,args.seed)
