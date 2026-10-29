#!/usr/bin/env python3
"""Controlled external solver sanity check: OptalCP free Preview on ta41.

This is NOT a submit-ready search: OptalCP Preview masks every solution's
operation time and machine sequence. The resulting objective is interesting
as external solver evidence but cannot be independently Few Shots checked.
Do not confuse a Preview objective with a validated certificate.
"""
import argparse,json,time
from pathlib import Path
from search import obtain,setup,evaluate

def main(a):
    import optalcp as cp
    routes,durs,baseline=obtain()
    pos,duration=setup(routes,durs)
    assert evaluate(baseline,pos,duration)==2006
    model=cp.Model()
    operations=[[model.interval_var(length=durs[j][k],name=f"J{j}_O{k}") for k in range(20)]
                for j in range(30)]
    for j in range(30):
        for k in range(19):
            model.end_before_start(operations[j][k],operations[j][k+1])
    for m in range(20):
        model.no_overlap([operations[j][pos[j][m]] for j in range(30)])
    model.minimize(model.max([operations[j][19].end() for j in range(30)]))
    begun=time.monotonic()
    result=model.solve({"timeLimit":a.seconds,"nbWorkers":4})
    reported=result.objective
    # Deliberately do NOT infer a schedule from Preview's masked solution.
    sample=None
    if result.solution is not None:
        sample=result.solution.get_start(operations[0][0])
    out={
      "instance":"ta41","previous_verifiable_makespan":2006,
      "external_engine":"OptalCP Preview edition","license":"free-preview",
      "status":"objective_only_not_certificate",
      "reported_objective":reported,
      "operation_start_available":sample is not None,
      "elapsed_seconds":round(time.monotonic()-begun,3),
      "model":"600 mandatory intervals, fixed job precedences, 20 hard no_overlap, minimize max of job endings",
      "note":"Preview licenses do not supply complete solution values. Never claim an independent Few Shots success from objective alone.",
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2)+'\n')
    print('RESULT',json.dumps(out),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--out',type=Path,default=Path(__file__).resolve().parent/'results'/'optalcp-preview.json')
    main(p.parse_args())
