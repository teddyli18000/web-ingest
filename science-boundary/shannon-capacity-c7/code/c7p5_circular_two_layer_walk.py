#!/usr/bin/env python3
"""Walk exact 4D adjacent-layer MIS neighborhoods from the circular 367 basin.

The earlier I0/X two-layer campaign fixed very different public basins.
Here a source-independent 367 circular-quantization witness seeds repeated
full adjacent-slice reoptimizations. A single move may change many points,
even though every chosen move is replayed in C7^5. Each independent walk
uses a different deterministic tie-breaking order.
"""
from __future__ import annotations
import argparse
import json
import random
import time
from pathlib import Path

from c7p5_circular_hall_io import independent,read_circular
from c7p5_two_layer_repair import solve_pair,dump_certificate

def main():
    p=argparse.ArgumentParser()
    p.add_argument("seed",type=Path)
    p.add_argument("status",type=Path)
    p.add_argument("certificate",type=Path)
    p.add_argument("farthest367",type=Path)
    p.add_argument("--random-seed",type=int,default=2026110501)
    p.add_argument("--sweeps",type=int,default=4)
    p.add_argument("--seconds",type=float,default=5.0)
    a=p.parse_args()
    initial=set(read_circular(a.seed))
    assert len(initial)==367 and independent(sorted(initial))
    S=initial.copy();best=S.copy();rng=random.Random(a.random_seed)
    seen={frozenset(S)};farthest=S.copy();max_distance=0;rows=[]
    t0=time.monotonic()
    for sweep in range(a.sweeps):
        pairs=[(k,s) for k in range(5) for s in range(7)]
        rng.shuffle(pairs)
        for axis,s in pairs:
            S,res=solve_pair(S,axis,s,rng,a.seconds)
            assert len(S)>=367 and independent(sorted(S))
            dist=len(S.symmetric_difference(initial))
            if dist>max_distance and len(S)==367:
                farthest=S.copy();max_distance=dist
            seen.add(frozenset(S))
            if len(S)>len(best):
                best=S.copy()
            rows.append({"sweep":sweep,**res,"current_size":len(S),"distance_from_start":dist})
            print("MOVE",json.dumps({"sweep":sweep,"axis":axis,"pair":s,
                                  "score":len(S),"distance":dist,
                                  "solver_status":res["solver_status"]},sort_keys=True),flush=True)
            if len(best)>=368:break
        if len(best)>=368:break
    candidate=dump_certificate(best,a.certificate) if len(best)>=368 else False
    if len(farthest)==367:
        a.farthest367.parent.mkdir(parents=True,exist_ok=True)
        a.farthest367.write_text("".join(f"{v}\n" for v in sorted(farthest)))
    result={"method":"circular-367-full-adjacent-4D-MIS-walk",
            "random_seed":a.random_seed,"sweeps_requested":a.sweeps,
            "sweeps_completed":len(rows)//35,
            "exact_milp_solves":sum(r["solver_status"]==0 for r in rows),
            "limited_milp_solves":sum(r["solver_status"]==1 for r in rows),
            "total_milp_solves":len(rows),"distinct_367_states":len(seen),
            "max_symmetric_difference_from_seed":max_distance,
            "best_5d_size":len(best),"candidate_368":candidate,
            "seconds":time.monotonic()-t0,"rows":rows}
    a.status.parent.mkdir(parents=True,exist_ok=True)
    a.status.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps({k:v for k,v in result.items() if k!="rows"},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
