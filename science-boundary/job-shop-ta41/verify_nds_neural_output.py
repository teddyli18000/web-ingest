#!/usr/bin/env python3
"""Re-score the original 2026 NDS-S pretrained evaluation on ta41.

The authors' eval.py writes one activityList to solutions.csv and a
makespan to results.csv. Rebuild the SAME original C++ Solution from this
activity list, verify that its score agrees with the reported score,
convert start times to machine orders, and separately score against the
Few Shots DAG evaluator. For a <=2005 candidate save a certificate.json
which will then be graded by upstream Few Shots verify/verify.py.
"""
import argparse
import ast
import csv
import json
import sys
from pathlib import Path

TOPIC=Path(__file__).resolve().parent
sys.path.insert(0,str(TOPIC))
from search import obtain,setup,evaluate
from reproduce_nds_cpp import build_jssp_module, data_validation, canonical_machine_orders


def main(a):
    routes,durs,baseline=obtain()
    pos,dur=setup(routes,durs)
    assert evaluate(baseline,pos,dur)==2006
    name=data_validation(a.nds_repo,routes,durs)
    with a.results.open() as f:
        rows=list(csv.reader(f))
    with a.solutions.open() as f:
        solrows=list(csv.reader(f))
    assert len(rows)==len(solrows)==1,(len(rows),len(solrows))
    score=int(round(float(rows[0][1])))
    activity,alternative=ast.literal_eval(solrows[0][1])
    assert len(activity)==600 and all(0<=x<30 for x in activity)
    assert len(alternative)==30 and all(len(x)==20 for x in alternative)
    JSSP=build_jssp_module(a.nds_repo)
    inst=JSSP.Instance(30,20,[[[durs[j][k]] for k in range(20)] for j in range(30)],
                        [[[routes[j][k]] for k in range(20)] for j in range(30)])
    s=JSSP.Solution(inst)
    s.activityList=activity
    s.alternative=alternative
    s.schedule(False)
    native=s.getMakespan()
    assert native==score,(native,score)
    machine_orders=canonical_machine_orders(s,routes,durs,pos)
    independent=evaluate(machine_orders,pos,dur)
    assert independent==score,(independent,score)
    out=a.out
    out.mkdir(parents=True,exist_ok=True)
    report={
      'instance':'ta41','original_author_code':'dawoz/NDS-S',
      'model':'jssp30x20/checkpoint-1000.pt',
      'upstream_commit':'c58783b0271f95d9a56252d8841fa2a78535a4d2',
      'source_instance':name,
      'ta41_data_cross_checked':True,
      'upstream_reported_score':score,
      'native_cpp_replayed_makespan':native,
      'independent_fewshots_dag_score':independent,
      'beats_fewshots_2006':score<=2005,
      'note':'Reconstructed from original C++ activity-list solution and independently DAG-scored. Full official Few Shots verifier runs in the workflow on all new <=2005 candidates.'
    }
    (out/'neural-eval.json').write_text(json.dumps(report,indent=2)+'\n')
    if score<=2005:
        (out/'certificate.json').write_text(json.dumps({'machines':machine_orders},separators=(',',':'))+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--nds-repo',type=Path,required=True)
    p.add_argument('--results',type=Path,required=True)
    p.add_argument('--solutions',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
