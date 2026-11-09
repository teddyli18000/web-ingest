#!/usr/bin/env python3
"""Paired validation of 48 independent-start CP-neutral + source-authentic N7 trials.

12 source-N7-generated elite starts x 2 independent second-stage seeds x 2
source-only neutral-machine selection policies. Pure original N7 receives
14 seconds. Hybrid receives at most 5 seconds CP and the remaining seconds
as unchanged original N7. Compare within identical starting incumbent and
N7 random seed, not only independent per-arm averages.

No archived target order or oracle is provided to any search.
"""
import json,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent
res=ROOT/"results"
policies=["static","random"]
combined={}
for policy in policies:
    records=[]
    for shard in (0,1):
        for seed in (4107,4113):
            f=res/f"neutral-N7-transfer-{policy}-shard{shard}-seed{seed}"/"results.json"
            obj=json.loads(f.read_text())
            assert obj["complete"] and len(obj["cases"])==6,(f,obj.get("complete"))
            records+=obj["cases"]
    assert len(records)==24 and len({(r["case"],r["seed"]) for r in records})==24
    combined[policy]={(r["case"],r["seed"]):r for r in records}
keys=set(combined["static"])
assert set(combined["random"])==keys and len(keys)==24
outrows=[]
for key in sorted(keys):
    s=combined["static"][key];r=combined["random"][key]
    assert s["original"]==r["original"]
    # A wall-clock-stopped N7 can execute different iteration counts on
    # different hosted runners even with identical random seed. Preserve
    # separate controls and never silently require equal makespans.
    assert s["direct_N7_seconds"]>=13.99 and r["direct_N7_seconds"]>=13.99
    row={"case":key[0],"seed":key[1],
        "start":s["original"],
        "direct_N7_difference_across_runners":s["direct_N7_score"]-r["direct_N7_score"]}
    for policy,t in (("static",s),("random",r)):
        row[policy+"_direct_N7_score"]=t["direct_N7_score"]
        row[policy+"_direct_N7_seconds"]=t["direct_N7_seconds"]
        row[policy+"_CP_status"]=t["neutral_CP_status"]
        row[policy+"_CP_sec"]=t["neutral_CP_seconds"]
        row[policy+"_neutral"]=t["neutral_makespan"]
        row[policy+"_changed_machines"]=t["changed_machines"]
        row[policy+"_hybrid_N7_sec"]=t["hybrid_N7_seconds"]
        row[policy+"_hybrid_score"]=t["hybrid_score"]
        row[policy+"_advantage"]=(
           t["direct_N7_score"]-t["hybrid_score"]
           if t["hybrid_score"] is not None else None)
        if t["hybrid_score"] is not None:
            assert t["hybrid_score"]<=t["original"]
    outrows.append(row)
summary={}
for policy in policies:
    xs=[r for r in outrows if r[policy+"_hybrid_score"] is not None]
    advantages=[r[policy+"_advantage"] for r in xs]
    summary[policy]=dict(
        trial_count=24,
        neutral_constructible=len(xs),
        neutral_unavailable=24-len(xs),
        hybrid_better=sum(x>0 for x in advantages),
        hybrid_tie=sum(x==0 for x in advantages),
        hybrid_worse=sum(x<0 for x in advantages),
        hybrid_advantage_mean_eligible=statistics.mean(advantages) if advantages else None,
        hybrid_advantage_mean_all_unavailable_as_zero=sum(advantages)/24,
        mean_CP_seconds=statistics.mean(r[policy+"_CP_sec"] for r in outrows),
        mean_hybrid_N7_seconds=statistics.mean(r[policy+"_hybrid_N7_sec"] for r in xs) if xs else None,
    )
relative=[]
for r in outrows:
    a=r["static_hybrid_score"];b=r["random_hybrid_score"]
    if a is not None and b is not None:relative.append(a-b)
report=dict(experiment="CP-neutral machine reorientation followed by unchanged native N7 vs equal-search-time native N7",
     instance_shape="30x20",num_independent_20_second_original_N7_starts=12,
     num_independent_second_stage_seeds=2,
     previous_oracle_machine_order_never_seen=True,
     source_N7_pin="Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8",
     direct_N7_seconds=14,
     hybrid_budget="CP <=5 seconds + genuine original N7 with 14-ceil(CP wall seconds) seconds, may leave unused budget",
     summary=summary,
     cross_runner_direct_N7_repeatability=dict(
         n_same_start_seed=24,
         different_direct_N7_objective_count=sum(
             x["direct_N7_difference_across_runners"]!=0 for x in outrows),
         direct_N7_abs_score_difference_total=sum(
             abs(x["direct_N7_difference_across_runners"]) for x in outrows),
         conclusion="Wall-clock N7 search is not iteration-matched across runners; only within-run source control comparisons are interpretable, and fixed-work audit is required."),
     paired_policy_comparison=dict(n_both_eligible=len(relative),
         random_better=sum(x>0 for x in relative),
         tied=sum(x==0 for x in relative),
         static_better=sum(x<0 for x in relative),
         mean_static_minus_random=statistics.mean(relative) if relative else None),
     rows=outrows,
     interpretive_limit="This is machine-CP neutral repair + published tabu, a known hybrid family; small budget and 12 individual starts. Results must not be called new optimal bounds unless officially verified.")
dest=res/"neutral-N7-12case-transfer-judged.json"
dest.write_text(json.dumps(report,indent=2)+"\n")
print("RESULT",json.dumps({"summary":summary,"comparison":report["paired_policy_comparison"]}),flush=True)
