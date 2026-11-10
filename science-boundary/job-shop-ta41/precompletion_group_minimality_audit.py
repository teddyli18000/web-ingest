#!/usr/bin/env python3
"""Audit conditional joint machine-order repair without claiming a blind predictor.

This is a *post-hoc* scientific control. A source-only partial-DAG
counterfactual ranking is computed before the known better witness is opened.
The witness then identifies an observed changed-machine set S. For each
m in S, a complete 600-operation CP feasibility model asks whether
all other original machine sequences can remain fixed when m is also
fixed. Proven INFEASIBLE deletion tests certify conditional necessity
within S (not global necessity); UNKNOWN proves nothing.

No solver receives the known target schedule, only source instance,
source machine orders, target makespan, and a mask S derived post-hoc.
Results are for mechanism audit, not algorithmic competition or ta41 record.
"""
import argparse
import json
import time
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import immutable_and_resource, dag_graph
from machine_group_order_repair import group_static_slack
from search import evaluate

ROOT = Path(__file__).resolve().parent
CASES = (
    ("ta43-independent", "positive-n7-elite-data/ta43js-n7elite1711/start.txt",
     "results/joint-global-ta43js-n7elite1711-static/certificate.json"),
    ("ta46-independent", "positive-n7-elite-data/ta46js-n7elite1701/start.txt",
     "results/joint-global-ta46js-n7elite1701-static/certificate.json"),
    ("dmu17-independent", "positive-n7-dmu16-20/dmu17-n7elite1901/start.txt",
     "results/novelty-only-dmu16-20-1901/dmu17-n7elite1901-seed4107/certificate.json"),
)

def source_only_partial_rank(orders, pos, dur, score):
    """Remove *one whole machine's arcs* to expose replacement paths.

    These are optimistic precedence DAGs, NOT complete schedules.
    Source-only ranking never touches a better machine-order witness.
    """
    arcs = immutable_and_resource(orders, pos)
    base = dag_graph(dur, arcs, set())
    assert base and base["lb"] == score
    static = group_static_slack(orders, dur, pos)
    old_critical = {
        i for i, (u, v, _) in enumerate(arcs)
        if base["head"][u] + dur[u] + base["tail"][v] == score
    }
    data = []
    for m in range(20):
        removed = set(range(m * 29, (m + 1) * 29))
        g = dag_graph(dur, arcs, removed)
        assert g and g["lb"] <= score
        new_replacement = [
            i for i, (u, v, mm) in enumerate(arcs)
            if i not in removed and i not in old_critical
            and g["head"][u] + dur[u] + g["tail"][v] == g["lb"]
        ]
        data.append({
            "machine": m,
            "optimistic_relaxed_longest_path": g["lb"],
            "optimistic_longest_path_drop": score - g["lb"],
            "newly_critical_old_resource_arcs": len(new_replacement),
            "static_slack_weight": round(static[m], 8),
        })
    # Predefine rankings; no reading or tuning on observed corrective sets.
    rank_static = sorted(range(20), key=lambda m: (-static[m], m))
    rank_relaxed = sorted(range(20), key=lambda m: (
        -data[m]["optimistic_longest_path_drop"],
        -data[m]["newly_critical_old_resource_arcs"],
        -static[m], m
    ))
    return {"features": data,
            "rank_static": rank_static, "rank_partial_counterfactual": rank_relaxed,
            "feature_scope": "optimistic precedence-only machine removal; not resource-feasible"}

def feasibility(orders, pos, dur, horizon, opened, seconds, seed):
    model = cp_model.CpModel()
    start = [model.new_int_var(0, horizon - dur[u], "s%d" % u)
             for u in range(600)]
    end = [model.new_int_var(dur[u], horizon, "e%d" % u)
           for u in range(600)]
    iv = [model.new_interval_var(start[u], dur[u], end[u], "iv%d" % u)
          for u in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(start[j * 20 + k + 1] >= end[j * 20 + k])
    for m in range(20):
        model.add_no_overlap([iv[j * 20 + pos[j][m]] for j in range(30)])
        if m not in opened:
            for a, b in zip(orders[m], orders[m][1:]):
                model.add(start[b * 20 + pos[b][m]] >= end[a * 20 + pos[a][m]])
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = seed
    solver.parameters.max_time_in_seconds = seconds
    tic = time.monotonic()
    status = solver.solve(model)
    output = dict(status=solver.status_name(status),
                  wall_seconds=round(time.monotonic()-tic, 4),
                  conflicts=solver.num_conflicts,
                  branches=solver.num_branches)
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        new = [
            sorted(range(30), key=lambda j: solver.value(start[j * 20 + pos[j][m]]))
            for m in range(20)
        ]
        score = evaluate(new, pos, dur)
        assert score is not None and score <= horizon
        output["independently_scored_completed_makespan"] = score
    return output

def main(args):
    output = {"question": "Can a precompletion source-only signal locate joint corrections more effectively than static criticality?",
              "status": "post-hoc conditional minimality and pilot ranking, NOT a prospective success",
              "scope": "The actual changed machine sets come from independently verified completed schedules and are used ONLY in the offline deletion audit.",
              "cases": []}
    for caseidx, (label, src, witness) in enumerate(CASES):
        orders, pos, dur, initial = parse_case(str(ROOT / src))
        # All source-only analysis is executed before loading the witness.
        proposed = source_only_partial_rank(orders, pos, dur, initial)
        higher = json.loads((ROOT / witness).read_text())["machines"]
        assert len(higher) == 20 and all(sorted(row) == list(range(30)) for row in higher)
        target = evaluate(higher, pos, dur)
        assert target is not None and target < initial
        changed = [m for m in range(20) if orders[m] != higher[m]]
        assert changed
        k = len(changed)
        checks = []
        for m in changed:
            allow = set(changed) - {m}
            proof = feasibility(orders, pos, dur, target, allow,
                                args.seconds, args.seed + caseidx * 100 + m)
            checks.append({"machine_closed_again": m, "released_others": sorted(allow), **proof})
            print("DELETE", label, "m", m, proof["status"], flush=True)
        conditional = all(x["status"] == "INFEASIBLE" for x in checks)
        # Construct an inclusion-minimal *conditional* release set.
        # Sequential removals are valid because allowing more open machines
        # can never reduce the set of feasible complete schedules. Each
        # rejected single deletion remains infeasible after later removals.
        retained = set(changed)
        shrink_log = []
        for m in changed:
            if m not in retained:
                continue
            trial_group = retained - {m}
            proof = feasibility(orders, pos, dur, target, trial_group,
                                args.seconds, args.seed + 5000 + caseidx * 100 + m)
            if proof["status"] in ("FEASIBLE", "OPTIMAL"):
                retained.remove(m)
                verdict = "DROPPED_WITH_VERIFIED_REPLACEMENT_COMPLETION"
            elif proof["status"] == "INFEASIBLE":
                verdict = "CONDITIONALLY_NECESSARY_WITHIN_FINAL_SUBSPACE"
            else:
                verdict = "NOT_RESOLVED"
            shrink_log.append({"tested_machine": m,
                               "remaining_after_test": sorted(retained),
                               "deletion_verdict": verdict, **proof})
            print("SHRINK", label, m, verdict, flush=True)
        proven_inclusion_minimal = all(
            x["deletion_verdict"] != "NOT_RESOLVED" for x in shrink_log)
        row = {
            "case": label, "source_makespan": initial,
            "verified_completed_makespan": target,
            "posthoc_observed_changed_machine_set": changed,
            "observed_changed_machine_count": k,
            "source_only_rankings": proposed,
            "top_k_static_hits_observed": len(set(proposed["rank_static"][:k]) & set(changed)),
            "top_k_partial_hits_observed": len(set(proposed["rank_partial_counterfactual"][:k]) & set(changed)),
            "individual_machine_deletion_tests": checks,
            "all_single_deletions_infeasible": conditional,
            "conditional_inclusion_minimality_certified": conditional,
            "greedy_shrunken_machine_set": sorted(retained),
            "greedy_shrunk_group_count": len(retained),
            "greedy_shrink_log": shrink_log,
            "greedy_inclusion_minimality_certified": proven_inclusion_minimal,
            "logical_scope": "only schedules changing machine orders within the observed set S, with all other source machine sequences fixed; NOT a globally unique required set",
        }
        output["cases"].append(row)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({**output, "complete": False}, indent=2) + "\n")
        print("CASE", label, "C", initial, "->", target, "k", k,
              "static_hit", row["top_k_static_hits_observed"],
              "partial_hit", row["top_k_partial_hits_observed"],
              "strict_minimal", conditional, flush=True)
    output["complete"] = True
    args.out.write_text(json.dumps(output, indent=2) + "\n")
    print("RESULT", json.dumps({"count": len(output["cases"]), "rows": [
          {"case": x["case"], "group": x["posthoc_observed_changed_machine_set"],
           "static_hits": x["top_k_static_hits_observed"],
           "partial_hits": x["top_k_partial_hits_observed"],
           "minimal": x["conditional_inclusion_minimality_certified"],
           "shrunk": x["greedy_shrunken_machine_set"],
           "shrunk_proved": x["greedy_inclusion_minimality_certified"],
           "statuses": [s["status"] for s in x["individual_machine_deletion_tests"]]}
          for x in output["cases"]]}), flush=True)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seconds", type=float, default=1.5)
    p.add_argument("--seed", type=int, default=20261110)
    p.add_argument("--out", type=Path, required=True)
    main(p.parse_args())
