#!/usr/bin/env python3
"""Exact 3-consecutive-layer 368 feasibility relative to a pinned C7^5 seed.

Only the three consecutive cyclic-symbol layers (s,s+1,s+2) of one
coordinate may change.  The other four layers are fixed. The endpoint
projection pools exclude the fixed neighbor at s-1 or s+3, while the
middle projection pool is unrestricted. All within-layer and
adjacent-layer 4D confusability edges are enforced exactly. CP-SAT
INFEASIBLE excludes a +1 improvement in this complete block; UNKNOWN
only means the solve was interrupted by a limit.
"""
import argparse,itertools,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from c7p5_two_layer_repair import code5,digits5,proj,lift,NEIGH4,independent,dump_certificate,N4

def solve(raw,seed,axis,start,seconds,workers,witness,certificate):
    S=set(map(int,raw[seed]))
    assert len(S)==367 and independent(S)
    layers=[(start+i)%7 for i in range(3)]
    fixed=S-{v for v in S if digits5(v)[axis] in layers}
    prev={(proj(v,axis)) for v in fixed if digits5(v)[axis]==(start-1)%7}
    nxt ={(proj(v,axis)) for v in fixed if digits5(v)[axis]==(start+3)%7}
    forbidL=set().union(*(NEIGH4[q] for q in prev))
    forbidR=set().union(*(NEIGH4[q] for q in nxt))
    pools=[sorted(set(range(N4))-forbidL),list(range(N4)),sorted(set(range(N4))-forbidR)]
    maps=[{q:i for i,q in enumerate(P)} for P in pools]
    model=cp_model.CpModel()
    V=[[model.new_bool_var(f'x_{k}_{q}') for q in P] for k,P in enumerate(pools)]
    old=[{proj(v,axis) for v in S if digits5(v)[axis]==lay} for lay in layers]
    oldsize=sum(map(len,old))
    assert oldsize+len(fixed)==367
    for k,P in enumerate(pools):
        for q,v in zip(P,V[k]):
            if q in old[k]:model.add_hint(v,1)
    intra=cross=0
    for k,P in enumerate(pools):
        idx=maps[k]
        for i,q in enumerate(P):
            for w in NEIGH4[q]:
                j=idx.get(w)
                if j is not None and j>i:
                    model.add_at_most_one(V[k][i],V[k][j]);intra+=1
    for k in range(2):
        idx=maps[k+1]
        for i,q in enumerate(pools[k]):
            for w in NEIGH4[q]:
                j=idx.get(w)
                if j is not None:
                    model.add_at_most_one(V[k][i],V[k+1][j]);cross+=1
    model.add(sum(v for L in V for v in L)>=oldsize+1)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=20261104+axis*7+start
    solver.parameters.cp_model_presolve=True
    solver.parameters.linearization_level=2
    t=time.monotonic()
    status=solver.solve(model)
    name=solver.status_name(status)
    chosen=[]
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        chosen=[lift(q,axis,layers[k]) for k,P in enumerate(pools) for q,v in zip(P,V[k]) if solver.boolean_value(v)]
        cand=fixed|set(chosen)
        assert len(cand)>=368 and independent(cand)
        witness.parent.mkdir(parents=True,exist_ok=True)
        witness.write_text(json.dumps({'points5':sorted(cand)})+'\n')
        dump_certificate(cand,certificate)
    out={'method':'exact-full-three-layer-cpsat','seed':seed,'axis':axis,'start':start,
         'layers':layers,'old_triple_size':oldsize,'fixed_points':len(fixed),
         'candidate_pool_sizes':list(map(len,pools)),
         'variables':sum(map(len,pools)),'intra_edges':intra,'cross_edges':cross,
         'target_triple_size':oldsize+1,'solver_status':name,
         'proven_no_plus_one_in_block':name=='INFEASIBLE',
         'candidate_368':bool(chosen),'elapsed_seconds':time.monotonic()-t,
         'branches':solver.num_branches,'conflicts':solver.num_conflicts}
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path);p.add_argument('status',type=Path)
    p.add_argument('witness',type=Path);p.add_argument('certificate',type=Path)
    p.add_argument('--seed',choices=['I0','X'],required=True)
    p.add_argument('--axis',type=int,required=True);p.add_argument('--start',type=int,required=True)
    p.add_argument('--seconds',type=float,default=90.);p.add_argument('--workers',type=int,default=4)
    a=p.parse_args()
    out=solve(json.loads(a.source.read_text()),a.seed,a.axis,a.start,a.seconds,a.workers,a.witness,a.certificate)
    a.status.parent.mkdir(parents=True,exist_ok=True)
    a.status.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True),flush=True)

if __name__=='__main__':main()
