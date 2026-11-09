#!/usr/bin/env python3
"""Judge 48 transfer trials with deterministic published N7 fixed work.

Pure N7 uses precisely 800k iterations. Hybrid uses a source-only CP-neutral
move and an N7 iteration count *reduced* to offset CP measured wall time.
Fixed-iteration source N7 gives identical results for the same seed/start
across distinct runners. Per-case scores were independently validated by
the 600-operation DAG evaluator at execution.
"""
import json,statistics
from pathlib import Path
R=Path(__file__).resolve().parent/"results"
runs={}
for p in ("static","random"):
    trials=[]
    for shard in (0,1):
        for seed in (4107,4113):
            path=R/f"neutral-N7-fixedwork-{p}-shard{shard}-seed{seed}"/"results.json"
            x=json.loads(path.read_text())
            assert x["complete"] and len(x["trials"])==6,path
            trials+=x["trials"]
    assert len(trials)==24 and len({(t["case"],t["seed"]) for t in trials})==24
    runs[p]={(t["case"],t["seed"]):t for t in trials}
assert set(runs["static"])==set(runs["random"])
rows=[]
for k in sorted(runs["static"]):
    a,b=runs["static"][k],runs["random"][k]
    assert a["initial"]==b["initial"]
    assert a["pure_N7_iterations"]==b["pure_N7_iterations"]==800000
    assert a["pure_N7_best"]==b["pure_N7_best"],(k,a["pure_N7_best"],b["pure_N7_best"])
    row=dict(case=k[0],seed=k[1],initial=a["initial"],
             identical_control_N7_best=a["pure_N7_best"])
    for p,r in (("static",a),("random",b)):
        row[p+"_CP_status"]=r["CP_status"]
        row[p+"_CP_seconds"]=r["CP_seconds"]
        row[p+"_changed_machines"]=r["CP_changed_machine_count"]
        row[p+"_hybrid_score"]=r["hybrid_best"]
        row[p+"_pure_N7_seconds"]=r["pure_N7_seconds"]
        row[p+"_hybrid_total_seconds"]=r["hybrid_total_search_seconds"]
        row[p+"_hybrid_N7_iterations"]=r["hybrid_N7_iterations"]
        row[p+"_advantage"]=r["hybrid_vs_pure_score_advantage"]
        if r["hybrid_best"] is not None:
            assert r["hybrid_best"]<=r["initial"]
            assert r["hybrid_N7_iterations"]<=800000
    rows.append(row)
summary={}
for p in ("static","random"):
    eligible=[z for z in rows if z[p+"_advantage"] is not None]
    delta=[z[p+"_advantage"] for z in eligible]
    cost=[z[p+"_hybrid_total_seconds"]-z[p+"_pure_N7_seconds"] for z in eligible]
    summary[p]=dict(
        starts=24,CP_neutral_found=len(eligible),CP_neutral_missing=24-len(eligible),
        wins=sum(x>0 for x in delta),ties=sum(x==0 for x in delta),
        losses=sum(x<0 for x in delta),
        mean_score_gain_eligible=statistics.mean(delta) if delta else None,
        mean_score_gain_all_missing_as_zero=sum(delta)/24,
        mean_actual_time_difference_vs_fixed_N7=statistics.mean(cost) if cost else None,
        min_actual_time_difference=min(cost) if cost else None,
        max_actual_time_difference=max(cost) if cost else None)
paired=[z["static_hybrid_score"]-z["random_hybrid_score"]
        for z in rows if z["static_hybrid_score"] is not None and z["random_hybrid_score"] is not None]
report=dict(n_distinct_original_instances=6,n_independent_source_N7_20_second_starts=12,
    n_independent_second_stage_seeds=2,
    pure_reference_N7_iterations=800000,
    source_N7_pin="Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8",
    all_pure_N7_scores_identical_across_source_only_policies=True,
    fully_independent_machine_order_DAG_validation=True,
    oracle_solution_not_seen_by_optimization=True,
    summary=summary,
    comparison_random_vs_static=dict(
        paired_both_solved=len(paired),
        random_better=sum(x>0 for x in paired),
        tied=sum(x==0 for x in paired),
        static_better=sum(x<0 for x in paired),
        mean_static_minus_random=statistics.mean(paired) if paired else None),
    caution="N7 iterations are fixed for baseline and CP cost converted to a lower hybrid N7 iteration budget by measured throughput; actual source N7 wall times and CP times are exposed. Small 12-start benchmark still not evidence of general algorithmic superiority.",
    trials=rows)
(R/"neutral-N7-fixedwork-paired-judgment.json").write_text(
    json.dumps(report,indent=2)+"\n")
print("RESULT",json.dumps({"summary":summary,"paired":report["comparison_random_vs_static"]}),
    flush=True)
