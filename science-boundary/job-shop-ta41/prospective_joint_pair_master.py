#!/usr/bin/env python3
"""Prospective joint-pair master for whole-machine partial-resource repair.

Unlike a sum of per-machine synergy degrees, this master scores the PRODUCT
x[m] * x[n]: genuine pair opening is rewarded only if BOTH machines are
freed together. Matched static uses the unchanged old master and the same
CP completion. No hidden improved schedule/oracle is used by either method.

Pilot only. Positive synergy of a relaxed precedence DAG is an optimistic
graph feature, not itself a hard joint-precedence necessity proof.
"""
import argparse
import json
import random
import time
from pathlib import Path

from ortools.sat.python import cp_model
import machine_group_order_repair as mgo
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import immutable_and_resource, dag_graph

ROOT=Path(__file__).resolve().parent
ORIGINAL_MASTER=mgo.machine_master

def pair_interactions_source_only(orders,pos,dur):
    edges=immutable_and_resource(orders,pos)
    C=dag_graph(dur,edges,set())["lb"]
    singleton=[]
    for m in range(20):
        r=set(range(29*m,29*(m+1)))
        singleton.append(C-dag_graph(dur,edges,r)["lb"])
    pairs=[]
    for m in range(20):
        for n in range(m+1,20):
            r=set(range(29*m,29*(m+1)))
            r.update(range(29*n,29*(n+1)))
            dual=C-dag_graph(dur,edges,r)["lb"]
            synergy=dual-singleton[m]-singleton[n]
            if synergy>0:
                pairs.append((m,n,synergy))
    return sorted(pairs)

def joint_master_factory(pairs):
    strongest=max([v for _,_,v in pairs],default=0)
    if strongest==0:
        return ORIGINAL_MASTER
    def joint_master(k,clauses,exploration_nogoods,prior_score,policy,seed,budget):
        model=cp_model.CpModel()
        x=[model.new_bool_var("open_%s"%m) for m in range(20)]
        model.add(sum(x)==k)
        for c in clauses:
            assert c
            model.add(sum(x[m] for m in c)>=1)
        for opened in exploration_nogoods:
            if len(opened)==k:
                model.add(sum(x[m] for m in opened)<=k-1)
        rng=random.Random(seed)
        # Original static priors are deliberately retained. This is an
        # intervention ONLY on the joint (x_m AND x_n) opening rewards.
        single=[int(prior_score[m]*200)+rng.randrange(0,100)
                for m in range(20)]
        terms=[]
        for m,n,weight in pairs:
            both=model.new_bool_var("both_%d_%d"%(m,n))
            model.add(both<=x[m])
            model.add(both<=x[n])
            model.add(both>=x[m]+x[n]-1)
            terms.append(int(400*weight/strongest)*both)
        model.maximize(sum(single[m]*x[m] for m in range(20))+sum(terms))
        solver=cp_model.CpSolver()
        solver.parameters.num_search_workers=4
        solver.parameters.random_seed=int(seed%2147483647)
        solver.parameters.max_time_in_seconds=budget
        result=solver.solve(model)
        if result not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            return None,{"status":solver.status_name(result),
                         "wall_seconds":solver.wall_time,"joint_pairs":len(pairs)}
        opened={m for m in range(20) if solver.value(x[m])}
        assert len(opened)==k and all(opened.intersection(c) for c in clauses)
        return opened,{
            "status":solver.status_name(result),
            "wall_seconds":solver.wall_time,
            "opened":sorted(opened),
            "master_heuristic_score":int(solver.objective_value),
            "joint_pairs":len(pairs),
            "rewarded_simultaneously_opened_pairs":sum(
                m in opened and n in opened for m,n,_ in pairs)
        }
    return joint_master

def experiment(start,seed,mode,total,out):
    begin=time.monotonic()
    orders,pos,dur,initial=parse_case(str(start))
    pairs=pair_interactions_source_only(orders,pos,dur) if mode=="joint" else []
    setup=time.monotonic()-begin
    remaining=max(0.05,total-setup)
    mgo.machine_master=joint_master_factory(pairs) if mode=="joint" else ORIGINAL_MASTER
    a=argparse.Namespace(
        start=str(start),policy="static",seed=seed,target_drop=1,
        auxiliary_start=None,auxiliary_mode="none",auxiliary_weight=3.0,
        only_groups=[],repair_objective="minimal-change",fixed_open_machines=[],
        cp_seconds=1.5,core_probe_seconds=0.2,core_probe_every=1,
        master_seconds=0.3,total_seconds=remaining,trials_per_stage=12,out=out
    )
    out.mkdir(parents=True,exist_ok=True)
    try:
        mgo.run(a)
    finally:
        mgo.machine_master=ORIGINAL_MASTER
    result=json.loads((out/"results.json").read_text())
    score=result.get("verified_makespan",initial)
    assert score<=initial
    report={"case":start.parent.name,"seed":seed,"mode":mode,
            "initial":initial,"final":score,"improvement":initial-score,
            "status":result["status"],"source_only_interactions":len(pairs),
            "preprocessing_seconds":round(setup,4),
            "total_wall_seconds":round(time.monotonic()-begin,3),
            "requested_total_budget_seconds":total,
            "uses_actual_joint_pair_selection":mode=="joint",
            "uses_full_original_CP_completion":True,
            "hidden_better_schedule_not_seen":True}
    print("JOINT",json.dumps(report,sort_keys=True),flush=True)
    return report

def main(a):
    cases=sorted((ROOT/"positive-n7-holdout-data").glob(
        a.family+"js-n7elite*/start.txt"))
    assert len(cases)==2,(a.family,len(cases))
    a.out.mkdir(parents=True,exist_ok=True)
    results=[]
    for case in cases:
        for seed in a.seeds:
            d=a.out/(case.parent.name+"-seed"+str(seed))
            results.append(experiment(case,seed,a.mode,a.seconds,d))
            (a.out/"summary.json").write_text(
                json.dumps({"complete":False,"trials":results},indent=2)+"\n")
    out={"complete":True,"family":a.family,"mode":a.mode,
         "count":len(results),"success":sum(r["improvement"]>0 for r in results),
         "aggregate_gain":sum(r["improvement"] for r in results),
         "mean_gain":sum(r["improvement"] for r in results)/len(results),
         "source_only":True,"trials":results}
    (a.out/"summary.json").write_text(json.dumps(out,indent=2)+"\n")
    print("JOINT_SUMMARY",json.dumps({k:v for k,v in out.items() if k!="trials"}),flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--family",choices=["ta48","ta49","ta50"],required=True)
    p.add_argument("--mode",choices=["joint","static"],required=True)
    p.add_argument("--seconds",type=float,default=5.0)
    p.add_argument("--seeds",nargs="+",type=int,default=[4107,4113])
    p.add_argument("--out",type=Path,required=True)
    main(p.parse_args())
