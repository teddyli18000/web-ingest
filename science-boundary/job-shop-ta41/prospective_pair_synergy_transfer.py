#!/usr/bin/env python3
"""Prospective held-out test of genuine pairwise machine-release synergy.

Scientific question: Do nonlinear, target-relevant *partial precedence DAG*
effects identify jointly useful machine groups before any better complete
schedule exists? No improved witness, ScheduleOpt oracle or label is read.

The ONLY intervention versus static whole-machine CP repair is replacing
initial machine priority by positive two-machine release synergy. Same
search kernel, group stages, solver budgets and starts. Priority formula
is fixed *before* evaluating ta48-50 (the previously unseen-to-this-feature
cases). A pilot, not a state-of-the-art or ta41 record claim.
"""
import argparse
import json
import time
from pathlib import Path

import machine_group_order_repair as mgo
from counterfactual_joint_cut import immutable_and_resource, dag_graph
from partial_resource_pair_repair import parse_case

ROOT = Path(__file__).resolve().parent
BASE_WEIGHT = mgo.group_static_slack

def source_only_pair_priority(orders, dur, pos):
    standard = BASE_WEIGHT(orders, dur, pos)
    original = mgo.MACHINES
    assert original == 20
    arcs = immutable_and_resource(orders, pos)
    C = dag_graph(dur, arcs, set())["lb"]
    single = []
    for m in range(20):
        removed = set(range(m*29, (m+1)*29))
        single.append(C - dag_graph(dur, arcs, removed)["lb"])
    degree = [0] * 20
    positive_pairs = 0
    for m in range(20):
        for n in range(m+1,20):
            removed = set(range(m*29,(m+1)*29))
            removed.update(range(n*29,(n+1)*29))
            gain = C - dag_graph(dur, arcs, removed)["lb"]
            synergy = gain - single[m] - single[n]
            if synergy > 0:
                degree[m] += synergy
                degree[n] += synergy
                positive_pairs += 1
    if max(degree) == 0:
        return standard  # explicit no-information fallback
    mx = max(degree)
    ms = max(standard)
    # Frozen 2:0.1 scale from exploratory diagnosis; no case-specific tune.
    return [2.0*degree[m]/mx + 0.1*standard[m]/max(1e-9,ms)
            for m in range(20)]

def run_one(source, seed, mode, out, total):
    wall0 = time.monotonic()
    # Parse only source schedules. Reference solutions never loaded.
    orders, pos, dur, inc = parse_case(str(source))
    mgo.group_static_slack = BASE_WEIGHT
    if mode == "pair":
        proposed = source_only_pair_priority(orders, dur, pos)
        def frozen_source_priority(*ignored):
            return proposed
        mgo.group_static_slack = frozen_source_priority
    used_preprocessing = time.monotonic() - wall0
    remaining = max(0.05, total - used_preprocessing)
    a = argparse.Namespace(
        start=str(source), policy="static", seed=seed, target_drop=1,
        auxiliary_start=None, auxiliary_mode="none", auxiliary_weight=3.0,
        only_groups=[], repair_objective="minimal-change",
        fixed_open_machines=[], cp_seconds=1.5, core_probe_seconds=0.2,
        core_probe_every=1, master_seconds=0.3,
        total_seconds=remaining, trials_per_stage=12, out=out)
    try:
        mgo.run(a)
    finally:
        mgo.group_static_slack = BASE_WEIGHT
    result=json.loads((out/"results.json").read_text())
    improved = result.get("verified_makespan")
    score = improved if improved is not None else inc
    assert score <= inc
    full_seconds=time.monotonic()-wall0
    record={"case":source.parent.name, "seed":seed, "mode":mode,
            "initial":inc, "final":score, "gain":inc-score,
            "status":result["status"],
            "preprocessing_seconds":round(used_preprocessing,4),
            "full_wall_seconds":round(full_seconds,3),
            "search_clock_seconds":result.get("wall_seconds"),
            "source_only_precompletion_priority":True,
            "hidden_reference_absent":True,
            "requested_total_wall_budget_seconds":total,
            "matched_complete_cp_kernel":True}
    print("PROSPECTIVE",json.dumps(record,sort_keys=True),flush=True)
    return record

def main(a):
    cases=sorted((ROOT/"positive-n7-holdout-data").glob(a.family+"js-n7elite*/start.txt"))
    assert len(cases)==2,(a.family,cases)
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for source in cases:
        for seed in a.seeds:
            out=a.out/(source.parent.name+"-seed"+str(seed))
            out.mkdir(parents=True,exist_ok=True)
            rows.append(run_one(source,seed,a.mode,out,a.seconds))
            (a.out/"summary.json").write_text(json.dumps({
                "complete":False, "family":a.family,
                "mode":a.mode,"trials":rows},indent=2)+"\n")
    payload={"complete":True,"family":a.family,"mode":a.mode,
             "source_family":"genuine independent 20s native N7 Taillard ta48-50 elites",
             "paired_seeds":list(a.seeds),
             "strict_trial_wall_budget":a.seconds,
             "improved":sum(x["gain"]>0 for x in rows),
             "aggregate_gain":sum(x["gain"] for x in rows),
             "mean_gain":sum(x["gain"] for x in rows)/len(rows),
             "no_oracle_data_read":True,
             "trials":rows}
    (a.out/"summary.json").write_text(json.dumps(payload,indent=2)+"\n")
    print("SUMMARY",json.dumps({k:v for k,v in payload.items() if k!="trials"}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--family",choices=["ta48","ta49","ta50"],required=True)
    p.add_argument("--mode",choices=["pair","static"],required=True)
    p.add_argument("--seeds",type=int,nargs="+",default=[4107,4113])
    p.add_argument("--seconds",type=float,default=5.0)
    p.add_argument("--out",type=Path,required=True)
    main(p.parse_args())
