#!/usr/bin/env python3
"""Audit preprocessing compute FAIRLY: LP is NOT free for synthetic TSPLIB.

Run same HiGHS degree+some-SEC LP constructor on public-only instances
three times, no solution data and no hidden tour. Report measured wall
seconds, exact input LP trace and edge support agreement. Future comparisons
must add amortized LP preprocessing cost to LP-driven methods, or treat
the LP as explicitly pre-given external information as for Mona Lisa.
"""
import argparse,json,statistics,time,hashlib
from pathlib import Path
import numpy as np
from tsplib_counterfactual_bench import degree_lp
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--dir',required=True)
 p.add_argument('--out',required=True)
 p.add_argument('--repeats',type=int,default=3)
 a=p.parse_args()
 logs={}
 for path in sorted(Path(a.dir).rglob('public.json')):
    d=json.loads(path.read_text())
    D=np.asarray(d['distance'],dtype=np.int32)
    times=[];traces=[];hashes=[]
    for repeat in range(a.repeats):
        start=time.perf_counter()
        lp,rounds=degree_lp(D)
        elapsed=time.perf_counter()-start
        times.append(elapsed)
        traces.append(rounds)
        hashes.append(hashlib.sha256(json.dumps(lp,sort_keys=True).encode()).hexdigest())
    assert all(x==hashes[0] for x in hashes)
    assert all(x==traces[0] for x in traces)
    assert all(abs(x['objective']-y['objective'])<1e-5 for x,y in zip(traces[0],d['lp_rounds']))
    logs[d['instance']]={'n':d['n'],'wall_seconds':times,
         'median_precompute_seconds':round(statistics.median(times),6),
         'min_precompute_seconds':round(min(times),6),
         'max_precompute_seconds':round(max(times),6),
         'LP_rounds':len(traces[0]),
         'LP_support':len(lp),'identical_result_sha256':hashes[0],
         'reference_score':d['reference_score']}
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(logs,indent=2)+'\n')
 print(json.dumps({'stage':'LP_cost_audit','cases':logs},separators=(',',':')),flush=True)
if __name__=='__main__':main()
