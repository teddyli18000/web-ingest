#!/usr/bin/env python3
"""Paired 5-second source-N7 versus full-machine release-IHS comparison.

The positive source N7 seeds (1701,1711) are independent native 20-second
optimizations and are not oracle mutations. All four methods see the EXACT
same 12 valid starts and paired second-stage seeds 4107,4113.

Read only already persisted post-search machine-order/DAG certificates,
never permit oracle target answers to guide the algorithm. Judge any
improvement over the source incumbent, paired wins/ties/losses, time and
cost. The N7 wall-time is exactly 5 seconds; Python start-up and per-call
CP-SAT cap can cause small budget deviations in the new method.
"""
import json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DATA=ROOT/"results"
POLICIES=["dynamic","static","random"]
SEEDS=[4107,4113]
alltrials={}
for policy in POLICIES:
    trials=[]
    for shard in (0,1):
        for seed in SEEDS:
            path=DATA/f"whole-machine-transfer-{policy}-shard{shard}-seed{seed}"/"results.json"
            report=json.loads(path.read_text())
            assert report["complete"],path
            assert len(report["cases"])==6
            trials+=report["cases"]
    assert len(trials)==24 and len({(t["case"],t["seed"]) for t in trials})==24
    alltrials[policy]={(t["case"],t["seed"]):t for t in trials}
old=json.loads((DATA/"positive-independent-true-n7"/"results.json").read_text())
assert old["complete"] and len(old["trials"])==24
alltrials["true-n7"]={(t["case"],t["seed"]):t for t in old["trials"]}
keyset=set(alltrials["true-n7"])
assert len(keyset)==24 and all(set(alltrials[p])==keyset for p in alltrials)
rows=[]
for key in sorted(keyset):
    initial=alltrials["true-n7"][key]["start_score"]
    row={"case":key[0],"seed":key[1],"start":initial}
    for p in alltrials:
        t=alltrials[p][key]
        assert t.get("start_score")==initial,(key,p,t)
        score=t["best_score"]
        assert score<=initial,(key,p,score,initial)
        row[p+"_score"]=score
        row[p+"_gain"]=initial-score
        row[p+"_wall_seconds"]=t.get("actual_wall_seconds",t.get("native_seconds"))
    rows.append(row)
summary={}
for p in alltrials:
    summary[p]={
        "trials":len(rows),
        "improved":sum(t[p+"_gain"]>0 for t in rows),
        "mean_improvement":statistics.mean(t[p+"_gain"] for t in rows),
        "median_improvement":statistics.median(t[p+"_gain"] for t in rows),
        "mean_final_makespan":statistics.mean(t[p+"_score"] for t in rows),
        "mean_wall_seconds":statistics.mean(t[p+"_wall_seconds"] for t in rows),
        "max_wall_seconds":max(t[p+"_wall_seconds"] for t in rows)
    }
pairwise={}
for p in POLICIES:
    delta=[row["true-n7_score"]-row[p+"_score"] for row in rows]
    pairwise[p+"_vs_true_n7"]={
        "whole_machine_wins":sum(d>0 for d in delta),
        "ties":sum(d==0 for d in delta),
        "whole_machine_losses":sum(d<0 for d in delta),
        "mean_score_advantage":statistics.mean(delta)
    }
for p in ("static","random"):
    delta=[row[p+"_score"]-row["dynamic_score"] for row in rows]
    pairwise["dynamic_vs_"+p]={
        "dynamic_wins":sum(d>0 for d in delta),
        "ties":sum(d==0 for d in delta),
        "dynamic_losses":sum(d<0 for d in delta),
        "mean_score_advantage":statistics.mean(delta)
    }
report={
    "instance_shape":"30x20",
    "all_starts_independently_generated_by_published_N7":True,
    "oracle_machine_order_not_available_during_search":True,
    "policies":summary,
    "pairwise":pairwise,
    "notes":"Each candidate score independently rescored from 600-operation job+machine DAG. Original N7 true source 5s. New group-IHS is ~5s Python wall bound, possibly overshoots by one CP call; report measured times.",
    "trials":rows
}
outfile=DATA/"whole-machine-heldout-paired-judgment.json"
outfile.write_text(json.dumps(report,indent=2)+"\n")
print("RESULT",json.dumps({"summary":summary,"pairwise":pairwise}),flush=True)
