#!/usr/bin/env python3
"""Held-out constructive benchmark for whole-machine joint IHS.

Twelve 30x20 independent N7 elite schedules are published under
positive-n7-elite-data. Each trial sees only its initial machine
orders and instance route/duration; no archived hidden better order
is loaded. Judge the result post-run with full independent DAG
makespan evaluation. Compare paired trials with the independently
run original author's N7 source, which received 5s per trial.

CP stages are aborted at a 5s global budget (one bounded CP call can
overshoot), so report ACTUAL wall-time and don't assert exact equal
compute to real N7 without checking.
"""
import argparse,json,subprocess,statistics,time,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from search import evaluate
from benchmark_hidden_positive import load_start

def run(a):
    cases=sorted((ROOT/"positive-n7-elite-data").glob("ta*js-n7elite*/start.txt"))
    assert len(cases)==12,len(cases)
    cases=cases[a.shard*6:(a.shard+1)*6]
    assert len(cases)==6
    output={"policy":a.policy,"shard":a.shard,"seed":a.seed,
            "seconds_limit_per_case":a.seconds,
            "initial_solution_source":"published genuine N7 C++ run 20s from random initialization",
            "source_oracle_machine_orders_never_read":True,
            "cases":[],"complete":False}
    a.out.mkdir(parents=True,exist_ok=True)
    def save(done=False):
        output["complete"]=done
        (a.out/"results.json").write_text(json.dumps(output,indent=2)+"\n")
    for case in cases:
        pos,durs,initial=load_start(case)
        name=case.parent.name
        case_out=a.out/name
        cmd=[sys.executable,str(ROOT/"whole_machine_release_ihs.py"),
            "--start",str(case),"--policy",a.policy,
            "--seed",str(a.seed),"--seconds",str(a.seconds),
            "--cp-seconds",str(a.cp_seconds),"--master-seconds","0.2",
            "--per-stage","16",
            "--out",str(case_out)]
        start=time.monotonic()
        process=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                               text=True,check=False,timeout=a.seconds+15)
        elapsed=round(time.monotonic()-start,3)
        if process.returncode:
            raise RuntimeError({"case":name,"policy":a.policy,
                "stderr":process.stderr[-2200:],"out":process.stdout[-1000:]})
        result=json.loads((case_out/"results.json").read_text())
        assert result["complete"] and result["baseline"]==initial
        best=initial
        if result["success"]:
            machines=json.loads((case_out/"certificate.json").read_text())["machines"]
            best=evaluate(machines,pos,durs)
            assert best==result["verified_makespan"] and best<initial
        record={"case":name,"seed":a.seed,"policy":a.policy,
                "start_score":initial,"best_score":best,
                "improvement":initial-best,"constructive":result["success"],
                "actual_wall_seconds":elapsed,"CP_status_counts":{},
                "CP_tries":len(result["trials"])}
        for trial in result["trials"]:
            status=trial.get("completion",{}).get("status")
            if status:
                record["CP_status_counts"][status]=record["CP_status_counts"].get(status,0)+1
        output["cases"].append(record)
        save()
        print("CASE",name,"seed",a.seed,"policy",a.policy,
            "initial",initial,"best",best,"CP",record["CP_status_counts"],
            "wall",elapsed,flush=True)
    output["total_improved"]=sum(x["improvement"]>0 for x in output["cases"])
    output["mean_gain"]=statistics.mean(x["improvement"] for x in output["cases"])
    output["mean_wall_seconds"]=statistics.mean(x["actual_wall_seconds"] for x in output["cases"])
    save(True)
    print("RESULT",a.policy,a.seed,a.shard,
        "improved",output["total_improved"],
        "mean",output["mean_gain"],flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--policy",required=True,choices=("dynamic","static","random"))
    p.add_argument("--shard",type=int,required=True,choices=(0,1))
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--seconds",type=float,default=5.)
    p.add_argument("--cp-seconds",type=float,default=0.8)
    p.add_argument("--out",type=Path,required=True)
    run(p.parse_args())
