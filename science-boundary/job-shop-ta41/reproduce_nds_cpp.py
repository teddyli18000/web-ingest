#!/usr/bin/env python3
"""Reproduce the 2026 NDS-S author's actual C++ random/heuristic repair operator.

Not a reimplementation: a pinned upstream checkout is compiled with cppimport.
The known valid ta41 2006 machine-order schedule is converted to a topologically
sorted activity list. The upstream C++ Solution::schedule MUST give exactly 2006.
The upstream job/machine/duration dataset MUST match Few Shots cell-for-cell.
Any <=2005 machine-order certificate is independently DAG-checked and subsequently
verified using Few Shots' official verify/verify.py on GitHub Actions.

Caveat: upstream C++ uses std::random_device; this search is not deterministically
replayable from a seed. Retain upstream SHA and exact verified certificate.
"""
import argparse
import importlib
import json
import os
import random
import sys
import time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from search import obtain,setup,evaluate
from structural_cut import disjunctive_dag

def data_validation(nds_repo,routes,durations):
    files=list((nds_repo/'data'/'jssp').glob('*__ta41__*.csv'))
    assert len(files)==1,files
    words=[int(v) for v in files[0].read_text().split()]
    assert words[:2]==[30,20]
    assert len(words)==2+2*600,(len(words),files[0])
    cursor=2
    for j in range(30):
        for op in range(20):
            m,d=words[cursor],words[cursor+1]
            cursor+=2
            assert (m,d)==(routes[j][op],durations[j][op]),(j,op,m,d,routes[j][op],durations[j][op])
    return files[0].name


def build_jssp_module(nds_repo):
    import cppimport
    target=nds_repo/'ndss'/'src'/'cpp'/'jssp'/'JSSP.cpp'
    assert target.is_file(),target
    return cppimport.imp_from_filepath(str(target),fullname='JSSP')


def canonical_machine_orders(solution,routes,durations,pos):
    # Native list is startTime[j][op]; each machine has a single operation per job.
    by_machine=[]
    for m in range(20):
        ordered=sorted(range(30),key=lambda j:solution.startTime[j][pos[j][m]])
        by_machine.append(ordered)
    return by_machine


def run(args):
    random.seed(args.seed)
    np.random.seed(args.seed)
    routes,duration_rows,baseline=obtain()
    pos,dur=setup(routes,duration_rows)
    assert evaluate(baseline,pos,dur)==2006
    dataset=data_validation(args.nds_repo,routes,duration_rows)
    JSSP=build_jssp_module(args.nds_repo)
    native_duration=[[[duration_rows[j][op]] for op in range(20)] for j in range(30)]
    native_machine=[[[routes[j][op]] for op in range(20)] for j in range(30)]
    instance=JSSP.Instance(30,20,native_duration,native_machine)
    _,_,topo,_,_,critical=disjunctive_dag(baseline,pos,dur,set())
    assert critical==2006
    start_list=[u//20 for u in topo]
    assert len(start_list)==600
    initial=JSSP.Solution(instance)
    initial.activityList=start_list
    initial.schedule(False)
    assert initial.getMakespan()==2006,initial.getMakespan()
    assert canonical_machine_orders(initial,routes,duration_rows,pos)==baseline
    # If neutral parents are used, the same topological canonical conversion
    # can bootstrap them; benchmark currently uses the official 2006 baseline.
    args.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    src=os.popen(f"git -C {args.nds_repo} rev-parse HEAD").read().strip()
    report={
        "instance":"ta41","target":2005,"starting_score":2006,
        "verified_native_bootstrap_score":initial.getMakespan(),
        "upstream_project":"dawoz/NDS-S",
        "upstream_commit":src,
        "paper":"doi:10.1007/s10994-026-07116-9",
        "upstream_instance_file":dataset,
        "exact_upstream_machine_durations_match":True,
        "native_method":"JSSP.remove_recreate (from upstream C++), no rewrite",
        "destroy_method":args.method,"removed_operations_per_step":args.q,
        "recreate_trials":args.recreate,"rollout_size":args.rollouts,
        "seed_python_only":args.seed,
        "cpp_rng":"std::random_device, non-seeded in upstream",
        "iterations":0,"best_machine_score":2006,
        "final_current_score":2006,"improved":False,
        "note":"Native C++ random_device prevents deterministic replay; machine-order certificate and official Few Shots verification are authoritative.",
        "progress":[]}
    cur=initial
    best=2006
    times=[0]*5
    limit=args.seconds
    i=0
    while (time.monotonic()-start)<limit and i<args.max_iters:
        T=max(0.15,2.0*(1.0-(time.monotonic()-start)/limit))
        if args.method=="random":
            selection=JSSP.random_node_selection(cur,args.q,args.rollouts)
            use_earliest_end=False
        else:
            selection=JSSP.heuristic_node_selection(cur,args.q,args.rollouts)
            use_earliest_end=True
        nxt,_=JSSP.remove_recreate(cur,selection,args.recreate,T,"allImp",use_earliest_end,False,False)
        cost=nxt.getMakespan()
        assert cost>=1
        cur=nxt
        i+=1
        if cost<best:
            orders=canonical_machine_orders(nxt,routes,duration_rows,pos)
            score=evaluate(orders,pos,dur)
            assert score==cost,(score,cost)
            best=cost
            report["best_machine_score"]=best
            report["progress"].append({"iter":i,"score":best,"elapsed_seconds":round(time.monotonic()-start,3)})
            print("NEW-BEST",args.method,"score",best,"iteration",i,flush=True)
            if cost<=2005:
                (args.out/'certificate.json').write_text(
                    json.dumps({"machines":orders},separators=(',',':'))+'\n')
                report["improved"]=True
                break
        if i%200==0:
            print("HEARTBEAT",args.method,i,best,cost,round(time.monotonic()-start,1),flush=True)
    report["iterations"]=i
    report["final_current_score"]=cur.getMakespan()
    report["elapsed_seconds"]=round(time.monotonic()-start,3)
    (args.out/'nds-reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
    print("RESULT",json.dumps(report),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--nds-repo',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--method',choices=('random','heuristic'),required=True)
    parser.add_argument('--q',type=int,default=10)
    parser.add_argument('--rollouts',type=int,default=12)
    parser.add_argument('--recreate',type=int,default=5)
    parser.add_argument('--seed',type=int,default=41)
    parser.add_argument('--seconds',type=int,default=300)
    parser.add_argument('--max-iters',type=int,default=100000)
    args=parser.parse_args()
    assert 1<=args.q<=600
    assert args.rollouts>0 and args.recreate>0
    run(args)
