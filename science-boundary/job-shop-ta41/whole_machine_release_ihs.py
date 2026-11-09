#!/usr/bin/env python3
"""Machine-Complete Release IHS for the 30x20 job shop.

Research question: Does global release of *whole machine sequences*, rather
than scattered adjacent precedence arcs, allow core-guided repair to produce
legal improvements in independent high-quality basins, and ultimately ta41?

Machine m is either completely fixed to the incumbent order, or ALL of its
29 machine adjacency precedences are omitted. All jobs/600 intervals and
20 hard NoOverlap constraints always remain. For each fixed machine, the
entire sequence is guarded by one assumption literal. A sufficient UNSAT
core proves at least one fixed MACHINE in that core must be released under
the fixed horizon; an implicit hitting set reselects all free machines
jointly and nonmonotonically. CP UNKNOWN teaches no logical constraint;
its exact mask is blocked only as a search-diversification measure.

Critically this differs from earlier '20 free arcs on 15 machines' code,
which still froze nearly every position within each machine.

This is source-only constructive search; published better machine orders are
NEVER loaded or used to rank decisions. Full results are scored independently.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import immutable_and_resource, dag_graph
from search import evaluate

ROOT = Path(__file__).resolve().parent


def root_invariants(orders, is_ta41):
    if not is_ta41:
        return [], None
    proof = json.loads((ROOT / "results" / "machine-budget14" / "decision.json").read_text())
    assert proof["status"] == "INFEASIBLE" and proof["maximum_changed_machine_orders"] == 14
    gate = json.loads((ROOT / "results" /
        "ta41-mandatory-adjacent-gateways-independently-proved.json").read_text())
    assert gate["solver_status"] == "INFEASIBLE" and len(gate["asserted_machine_resource_arcs"]) == 21
    # Each arc in this core is an incumbent adjacent pair. A shorter
    # improved schedule must reverse >=1, so it MUST alter at least one
    # of these machines.
    gateway_groups = sorted(set(i // 29 for i in gate["asserted_machine_resource_arcs"]))
    assert len(gateway_groups) == 5
    return [gateway_groups, [1, 10, 13, 15, 17, 19]], 15


def do_completion(orders, pos, duration, keep_machines, deadline, seed, seconds):
    model = cp_model.CpModel()
    starts = [model.new_int_var(0, deadline - duration[u], f"s{u}") for u in range(600)]
    ends = [model.new_int_var(duration[u], deadline, f"e{u}") for u in range(600)]
    intervals = [model.new_interval_var(starts[u], duration[u], ends[u], f"iv{u}")
                 for u in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j * 20 + k + 1] >= ends[j * 20 + k])
    assumed = {}
    for m in range(20):
        operations = [j * 20 + pos[j][m] for j in range(30)]
        model.add_no_overlap([intervals[u] for u in operations])
        if m in keep_machines:
            assumption = model.new_bool_var(f"keep_machine_{m}")
            for a, b in zip(orders[m], orders[m][1:]):
                u = a * 20 + pos[a][m]
                v = b * 20 + pos[b][m]
                model.add(starts[v] >= ends[u]).only_enforce_if(assumption)
            model.add_assumption(assumption)
            assumed[assumption.index] = m

    cp = cp_model.CpSolver()
    cp.parameters.max_time_in_seconds = seconds
    cp.parameters.num_search_workers = 1  # needed for reliable assumption cores
    cp.parameters.random_seed = seed % 2147483647
    start = time.monotonic()
    status = cp.solve(model)
    report = dict(status=cp.status_name(status),
                  seconds=round(time.monotonic() - start, 3),
                  conflicts=cp.num_conflicts, branches=cp.num_branches,
                  fixed_machines=sorted(keep_machines))
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        orders_new = [
            sorted(range(30), key=lambda j: cp.value(starts[j*20+pos[j][m]]))
            for m in range(20)]
        score = evaluate(orders_new, pos, duration)
        assert score is not None and score <= deadline, (score, deadline)
        for m in keep_machines:
            assert orders_new[m] == orders[m], (m, orders_new[m], orders[m])
        report["independently_reproduced_makespan"] = score
        return report, orders_new, None
    if status == cp_model.INFEASIBLE:
        raw = cp.sufficient_assumptions_for_infeasibility()
        assert all(i in assumed for i in raw), (raw, assumed)
        machines = frozenset(assumed[i] for i in raw)
        report["necessary_release_machine_core"] = sorted(machines)
        return report, None, machines
    return report, None, None


def choose_open_set(size, cores, excluded, weights, seed, master_seconds):
    model = cp_model.CpModel()
    xs = [model.new_bool_var(f"open_{m}") for m in range(20)]
    model.add(sum(xs) == size)
    for c in cores:
        assert c
        model.add(sum(xs[m] for m in c) >= 1)
    for chosen in excluded:
        assert len(chosen) == size
        model.add(sum(xs[m] for m in chosen) <= size-1)
    rng = random.Random(seed)
    objective = [int(weights[m] * 1000) + rng.randrange(100) for m in range(20)]
    model.maximize(sum(objective[m] * xs[m] for m in range(20)))
    cp = cp_model.CpSolver()
    cp.parameters.max_time_in_seconds = master_seconds
    cp.parameters.num_search_workers = 4
    cp.parameters.random_seed = seed % 2147483647
    status = cp.solve(model)
    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        return None, dict(status=cp.status_name(status), wall=cp.wall_time)
    chosen = frozenset(m for m in range(20) if cp.value(xs[m]))
    assert len(chosen) == size and all(chosen & c for c in cores)
    return chosen, dict(status=cp.status_name(status), wall=cp.wall_time)


def original_machine_scores(orders, pos, duration):
    edges = immutable_and_resource(orders, pos)
    graph = dag_graph(duration, edges, set())
    assert graph is not None
    score = [0.0 for _ in range(20)]
    for u,v,m in edges:
        slack = graph["lb"] - (graph["head"][u] + duration[u] + graph["tail"][v])
        score[m] += 1.0 / (1.0 + max(0,slack))
    mx = max(score)
    return [x/mx for x in score]


def main(args):
    order,pos,duration,initial = parse_case(args.start)
    ta41 = args.start == "ta41"
    baseline, hard_min = root_invariants(order,ta41)
    deadline = initial - 1
    static_weight = original_machine_scores(order,pos,duration)
    start = time.monotonic()
    if ta41:
        sizes = [15,17,19,20]
    else:
        sizes = [2,3,4,5,7,10,15,20]

    groups = [frozenset(c) for c in baseline]
    extra_cores = set(groups)
    trials = []
    output = dict(instance="ta41" if ta41 else Path(args.start).parent.name,
        baseline=initial,target=deadline,policy=args.policy,
        search_representation="whole-machine ordering completely free if selected; all 20 NoOverlap unconditional; job arcs hard",
        independent_15_machine_distance_proof_used=ta41,
        ta41_known_gateway_machine_sets=[sorted(c) for c in groups],
        stages=sizes,
        success=False,complete=False,trials=trials)
    args.out.mkdir(parents=True,exist_ok=True)

    def persist(complete):
        output["complete"] = complete
        output["wall_seconds"] = round(time.monotonic()-start,3)
        (args.out/"results.json").write_text(json.dumps(output,indent=2)+"\n")

    for size in sizes:
        if size < (hard_min or 0):
            continue
        unknown_masks=[]
        stage_counts=Counter()
        for attempt in range(args.per_stage):
            if time.monotonic()-start > args.seconds:
                output["status"]="TIME_LIMIT_NOT_INFEASIBLE"
                persist(True)
                return
            frequency=Counter()
            for c in extra_cores:
                for m in c:
                    frequency[m] += 1.0 / (len(c)**0.5)
            if args.policy=="dynamic":
                weights=[static_weight[m]*0.4 + 2.0*frequency[m] for m in range(20)]
            elif args.policy=="static":
                weights=static_weight
            else:
                weights=[0.0]*20
            opened,ms=choose_open_set(size,extra_cores,unknown_masks,
                weights,args.seed+size*173+attempt*13,args.master_seconds)
            record=dict(size=size,attempt=attempt,open=sorted(opened) if opened else [],
                master=ms,cores_known=len(extra_cores))
            trials.append(record)
            if opened is None:
                record["outcome"]="MASTER_NO_MORE_CHOICES_OR_TIMEOUT"
                break
            keep=set(range(20))-set(opened)
            cp, certificate, newcore=do_completion(order,pos,duration,keep,deadline,
                args.seed+attempt*101+size*4709,args.cp_seconds)
            record["completion"]=cp
            stage_counts[cp["status"]]+=1
            if certificate is not None:
                score=evaluate(certificate,pos,duration)
                assert score < initial
                (args.out/"certificate.json").write_text(
                    json.dumps({"machines":certificate},separators=(",",":"))+"\n")
                output.update(success=True,status="CONSTRUCTIVE_IMPROVEMENT",
                    verified_makespan=score,groups_opened=sorted(opened))
                persist(True)
                print("CONSTRUCTIVE",output["instance"],args.policy,
                      initial,score,sorted(opened),flush=True)
                return
            if newcore is not None:
                if not newcore:
                    record["outcome"]="UNCONDITIONAL_UNSAT_REQUIRE_INDEPENDENT_CONFIRMATION"
                    output["status"]="UNCONDITIONAL_UNSAT_FROM_SINGLE_WORKER_CP"
                    persist(True)
                    return
                assert not (newcore & opened)
                extra_cores.add(newcore)
                record["outcome"]="NEW_MACHINE_CORE"
            else:
                unknown_masks.append(opened)
                record["outcome"]="CP_UNKNOWN_DOES_NOT_EXCLUDE_ANY_SCHEDULE"
            if attempt % 4 == 0:
                persist(False)
                print("TRIAL",output["instance"],args.policy,"size",size,
                      "i",attempt,"cores",len(extra_cores),
                      "verdict",cp["status"],flush=True)
        print("STAGE",output["instance"],args.policy,"size",size,
              "counts",dict(stage_counts),"cores",len(extra_cores),flush=True)
    output["status"]="NO_IMPROVEMENT_WITHIN_FINITE_SEARCH_BUDGET"
    persist(True)
    print("RESULT",json.dumps({k:v for k,v in output.items() if k!="trials"}),
          flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--start",required=True)
    p.add_argument("--policy",choices=["dynamic","static","random"],required=True)
    p.add_argument("--seed",type=int,default=20261108)
    p.add_argument("--per-stage",type=int,default=16)
    p.add_argument("--master-seconds",type=float,default=0.3)
    p.add_argument("--cp-seconds",type=float,default=1.0)
    p.add_argument("--seconds",type=float,default=130.0)
    p.add_argument("--out",type=Path,required=True)
    main(p.parse_args())
