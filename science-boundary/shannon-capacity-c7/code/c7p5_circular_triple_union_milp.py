#!/usr/bin/env python3
"""Exact three-basin union MIS: circular 367 + two translated public 367 codes.

Pairwise Hall saturation is irrelevant to a three-colorable union conflict
graph: a three-way combination might still have alpha >= 368.
This script solves complete 3-basin union graphs with binary MILP (SciPy
HiGHS). Every returned feasible code is independently replayed; only solver
status OPTIMAL can certify a restricted-union maximum of 367.
"""
import argparse
import itertools
import json
import random
import time
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

P=(1,7,49,343,2401)
OFFSETS=tuple(itertools.product((-1,0,1),repeat=5))
SCENARIOS={
    "I0_X":("I0","X"),
    "I0_F0":("I0","F0"),
    "X_F0":("X","F0"),
    "F0_F17":("F0","F17"),
}

def dec(v):return tuple((v//p)%7 for p in P)
def enc(d):return sum(x*p for x,p in zip(d,P))
def independent(S):
    a=sorted(S)
    if len(set(a))!=len(a):return False
    return all(not all((x-y)%7 in (0,1,6) for x,y in zip(dec(u),dec(v)))
               for i,u in enumerate(a) for v in a[i+1:])

def shift(S,t):
    dt=dec(t)
    return {enc(tuple((x+y)%7 for x,y in zip(dec(v),dt))) for v in S}

def graph(U):
    V=sorted(U);idx={v:i for i,v in enumerate(V)}
    er=[];ec=[]
    for i,v in enumerate(V):
        d=dec(v)
        for h in OFFSETS:
            j=idx.get(enc(tuple((x+y)%7 for x,y in zip(d,h))))
            if j is not None and j>i:
                er.append(i);ec.append(j)
    E=len(er);n=len(V)
    row=np.repeat(np.arange(E,dtype=np.int32),2)
    col=np.column_stack((er,ec)).ravel()
    A=coo_matrix((np.ones(2*E,dtype=np.float64),(row,col)),shape=(E,n)).tocsr()
    return V,A,E

def optimize(U,seconds):
    V,A,E=graph(U)
    n=len(V)
    z=milp(-np.ones(n),integrality=np.ones(n),
           bounds=Bounds(np.zeros(n),np.ones(n)),
           constraints=LinearConstraint(A,-np.inf,np.ones(E)),
           options={"time_limit":float(seconds),"mip_rel_gap":0.0})
    chosen=sorted(V[i] for i in range(n) if z.x is not None and z.x[i]>.5)
    if chosen and not independent(chosen):
        raise RuntimeError("MILP candidate replay failed")
    score=len(chosen)
    if z.status==0 and score!=round(-z.fun):
        raise RuntimeError(("objective mismatch",score,z.fun))
    return chosen,{"solver_status":int(z.status),"optimal":z.status==0,
                   "score":score,"union_vertices":n,"conflict_edges":E,
                   "mip_gap":float(z.mip_gap) if z.mip_gap is not None else None}

def profile(S):
    return tuple(sorted(tuple(sorted(sum((v//p)%7==d for v in S)
                                   for d in range(7))) for p in P))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input_directory",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("witness",type=Path)
    p.add_argument("novel",type=Path)
    p.add_argument("--scenario",choices=sorted(SCENARIOS),required=True)
    p.add_argument("--trials",type=int,default=24)
    p.add_argument("--seconds",type=float,default=12.0)
    a=p.parse_args()
    A={int(x) for x in (a.input_directory/"circle.ids").read_text().split()}
    nameB,nameC=SCENARIOS[a.scenario]
    B={int(x) for x in (a.input_directory/(nameB+".ids")).read_text().split()}
    C={int(x) for x in (a.input_directory/(nameC+".ids")).read_text().split()}
    assert all(len(x)==367 and independent(x) for x in (A,B,C))
    rng=random.Random(20261105+sum(ord(x) for x in a.scenario))
    initial=[(0,0),(1,0),(0,1),(137,883),(200,1493),(1441,8191),(6228,1517)]
    translations=initial+[(rng.randrange(7**5),rng.randrange(7**5))
                          for _ in range(max(0,a.trials-len(initial)))]
    rows=[];best_score=367;best_novel=None;novel_distance=-1;candidate=None
    for i,(t1,t2) in enumerate(translations[:a.trials]):
        Bt=shift(B,t1);Ct=shift(C,t2)
        U=A|Bt|Ct
        start=time.monotonic()
        S,info=optimize(U,a.seconds)
        info.update({"trial":i,"shift_B":t1,"shift_C":t2,
                     "elapsed_seconds":time.monotonic()-start})
        rows.append(info)
        if info["score"]>best_score:
            best_score=info["score"]
        if info["score"]>=368:
            candidate=S
            print("FOUND",json.dumps(info,sort_keys=True),flush=True)
            break
        if info["score"]==367:
            origins=[A,Bt,Ct]
            gaps=[len(S-set(x)) for x in origins]
            if min(gaps)>novel_distance and profile(S) not in set(map(profile,origins)):
                best_novel=S;novel_distance=min(gaps)
        print("TRIAL",json.dumps(info,sort_keys=True),flush=True)
    if candidate is not None:
        a.witness.parent.mkdir(parents=True,exist_ok=True)
        a.witness.write_text("".join(f"{v}\n" for v in candidate))
    if best_novel is not None:
        a.novel.parent.mkdir(parents=True,exist_ok=True)
        a.novel.write_text("".join(f"{v}\n" for v in best_novel))
    result={"method":"three-basin-union-exact-MILP","scenario":a.scenario,
            "source_sets":["circle",nameB,nameC],
            "trials_requested":a.trials,"trials_completed":len(rows),
            "optimal_trials":sum(row["optimal"] for row in rows),
            "timeout_trials":sum(row["solver_status"]==1 for row in rows),
            "best_size":best_score,"candidate_368":candidate is not None,
            "most_distant_neutral_novel_367":best_novel is not None,
            "neutral_min_distance_to_any_parent":novel_distance if best_novel is not None else None,
            "rows":rows}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FINAL",json.dumps({k:v for k,v in result.items() if k!="rows"},sort_keys=True),flush=True)

if __name__=="__main__":
    main()
