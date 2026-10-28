#!/usr/bin/env python3
"""Exhaustive, reproducible 580 adjacent swap check around 2006 incumbent.

This detects whether critical-path relaxations predict a feasible change,
or merely hide new machine adjacency arcs that arise when the permutation
itself is changed. It is a completeness result for the 1-swap neighborhood
of the particular published incumbent only.
"""
import json
import argparse
from pathlib import Path
from collections import Counter
from search import obtain,setup,evaluate

def run(out):
    routes,durations,orders=obtain()
    pos,dur=setup(routes,durations)
    assert evaluate(orders,pos,dur)==2006
    values=[]
    best=2006
    best_orders=None
    for m in range(20):
        for k in range(29):
            a,b=orders[m][k:k+2]
            orders[m][k:k+2]=[b,a]
            score=evaluate(orders,pos,dur)
            if score is not None and score<best:
                best=score
                best_orders=[o[:] for o in orders]
            values.append({"machine":m,"position":k,"from":a,"to":b,"makespan":score})
            orders[m][k:k+2]=[a,b]
    histogram=Counter("cyclic" if x["makespan"] is None else x["makespan"] for x in values)
    result={"baseline":2006,"best_feasible_single_adjacent_swap":best,
            "total_swaps":len(values),"cyclic_swaps":histogram.get("cyclic",0),
            "feasible_swaps_better_than_baseline":[x for x in values if x["makespan"] is not None and x["makespan"]<2006],
            "machine16_cut_471_swap":values[16*29+7],
            "machine16_cut_472_swap":values[16*29+8],
            "lowest_feasible_swaps":sorted([x for x in values if x["makespan"] is not None],key=lambda x:x["makespan"])[:25],
            "score_histogram":{str(k):v for k,v in sorted(histogram.items(),key=lambda x:str(x[0]))},
            "scope":"Only the 580 individual adjacent swaps of the verified 2006 incumbent"}
    out.mkdir(parents=True,exist_ok=True)
    (out/"single-swap.json").write_text(json.dumps(result,indent=2)+"\n")
    if best_orders is not None:
        (out/"certificate.json").write_text(json.dumps({"machines":best_orders},separators=(",",":"))+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("lowest_feasible_swaps","score_histogram")},indent=2),flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,default=Path(__file__).parent/"results"/"swap-probe")
    a=p.parse_args();run(a.out)
