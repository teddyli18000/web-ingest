#!/usr/bin/env python3
"""48-run held-out equal-budget CP-neutral/N7 versus original N7 benchmark.

Two policies x 12 independently source-N7-created elite starts x two second
stage seeds. Each trial runs published pinned native N7 alone for exactly
14 seconds and then CP-neutral whole-machine rearrangement followed by
the SAME author N7 with <=14 seconds total CPU budget. The user's hidden
benchmark oracle is never fetched by a solver; all native CSV operations
and Python DAG scores are independently audited during each run.

This intentionally differentiates coordination structure (CP intermediate)
from local search engine (identical native N7), with a matched total-search
budget, rather than crediting a different optimizer's strengths to a policy.
"""
import argparse,subprocess,sys,json,statistics,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def main(a):
    sources=sorted((ROOT/"positive-n7-elite-data").glob("ta*js-n7elite*/start.txt"))
    assert len(sources)==12
    sources=sources[a.shard*6:(a.shard+1)*6]
    assert len(sources)==6
    a.out.mkdir(parents=True,exist_ok=True)
    records=[]
    for path in sources:
        name=path.parent.name
        out=a.out/name
        begun=time.monotonic()
        command=[sys.executable,str(ROOT/"neutral_machine_cp_then_original_n7.py"),
            "--start",str(path),"--policy",a.policy,"--seed",str(a.seed),
            "--driver",str(a.driver),"--open-machines","8",
            "--min-changed-machines","2","--min-reversed-pairs","3",
            "--cp-seconds","5","--total-seconds","14","--out",str(out)]
        result=subprocess.run(command,text=True,capture_output=True,
            check=False,timeout=65)
        if result.returncode:
            raise RuntimeError((name,command,result.stderr[-1500:],result.stdout[-1500:]))
        report=json.loads((out/"results.json").read_text())
        assert report["complete"] and report["instance"]==name
        rec=dict(case=name,policy=a.policy,seed=a.seed,
                 original=report["original_makespan"],
                 direct_N7_score=report["control_only_N7"]["score"],
                 direct_N7_seconds=report["control_only_N7"]["native_seconds"],
                 neutral_CP_status=report["neutral_cp"]["status"],
                 neutral_CP_seconds=report["neutral_cp"]["cp_wall_seconds"],
                 neutral_makespan=report["neutral_cp"].get("neutral_makespan"),
                 changed_machines=report["neutral_cp"].get("changed_machines"),
                 hybrid_N7_seconds=(report["hybrid_CP_then_N7"] or {}).get("native_seconds"),
                 hybrid_score=(report["hybrid_CP_then_N7"] or {}).get("score"),
                 hybrid_better=report["hybrid_better_than_direct_N7"],
                 actual_trial_wall_seconds=round(time.monotonic()-begun,3))
        records.append(rec)
        (a.out/"partial-results.json").write_text(
            json.dumps(dict(complete=False,trials=records),indent=2)+"\n")
        print("TRIAL",name,a.policy,a.seed,"direct",rec["direct_N7_score"],
              "hybrid",rec["hybrid_score"],"CP",rec["neutral_CP_status"],
              flush=True)
    summary=dict(policy=a.policy,shard=a.shard,seed=a.seed,complete=True,
        original_N7_source='Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8',
        no_hidden_reference_available_to_search=True,
        equal_total_search_time_budget_seconds=14,
        cases=records,positive_hybrid_beat_N7=sum(x["hybrid_better"] for x in records),
        neutral_state_feasible=sum(x["neutral_makespan"] is not None for x in records))
    (a.out/"results.json").write_text(json.dumps(summary,indent=2)+"\n")
    print("RESULT",a.policy,a.seed,a.shard,"hybrid_wins",
          summary["positive_hybrid_beat_N7"],flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--policy",choices=["static","random"],required=True)
    p.add_argument("--shard",choices=[0,1],type=int,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--driver",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    main(p.parse_args())
