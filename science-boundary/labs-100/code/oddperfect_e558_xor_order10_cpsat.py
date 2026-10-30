#!/usr/bin/env python3
"""Exact E558 shard model with an order-10 profile partition audit.

The base model in oddperfect_e558_xor_cpsat.py encodes the complete length-100
E=558 candidate problem.  This wrapper computes the ten residue sums of each
parity half and either:

  --mode allowed:   requires the 20-tuple to be one of the supplied profiles;
  --mode forbidden: requires the 20-tuple NOT to be one of those profiles.

Thus allowed+forbidden partition every assignment of the exact base model,
independently of whether the supplied profile generator is complete.  If both
modes are INFEASIBLE for a ka shard, that shard is excluded by the base model.
UNKNOWN is never an exclusion.
"""
from __future__ import annotations
import argparse, json, sys
from ortools.sat.python import cp_model
import oddperfect_e558_xor_cpsat as base


def decode(code: int):
    out=[]
    for _ in range(10):
        out.append(-5 + 2*(code % 6)); code//=6
    return out


def load_profiles(path: str):
    rows=[]
    with open(path) as f:
        for line in f:
            line=line.strip()
            if not line: continue
            a,b=map(int,line.split())
            rows.append(decode(a)+decode(b))
    rows=sorted(set(tuple(r) for r in rows))
    if len(rows)!=4220:
        raise ValueError(f'expected 4220 profile rows in audit partition, got {len(rows)}')
    return [list(r) for r in rows]


def solve(ka: int, profiles: str, mode: str, seconds: float, workers: int, seed: int):
    model,x,corr=base.build(ka)
    sums=[]
    for half in (0,1):
        for r in range(10):
            neg=[x[2*i+half] for i in range(50) if i%10==r]
            s=model.NewIntVar(-5,5,f'ord10_s_{half}_{r}')
            model.Add(s == 5 - 2*sum(neg))
            sums.append(s)
    rows=load_profiles(profiles)
    if mode=='allowed':
        model.AddAllowedAssignments(sums,rows)
    elif mode=='forbidden':
        model.AddForbiddenAssignments(sums,rows)
    else:
        raise ValueError(mode)

    err=model.Validate()
    if err: raise SystemExit('MODEL_INVALID '+err)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=seed
    solver.parameters.randomize_search=True
    solver.parameters.cp_model_presolve=True
    solver.parameters.symmetry_level=2
    st=solver.Solve(model)
    out={'ka':ka,'mode':mode,'status':solver.StatusName(st),
         'wall_time':solver.WallTime(),'branches':solver.NumBranches(),
         'conflicts':solver.NumConflicts(),'partition_rows':len(rows),'workers':workers}
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        seq=''.join('-' if solver.Value(v) else '+' for v in x)
        e,odd,cs,asum,bsum=base.exact(seq)
        ok=(e==558 and odd==50 and asum==20 and bsum==0
            and all(abs(cs[k])==1 for k in range(1,100,2))
            and all(cs[k] in (2,4) for k in range(2,100,2)))
        out.update(sequence=seq,energy=e,odd_energy=odd,asum=asum,bsum=bsum,
                   independent_check=ok,
                   residue_sums=[solver.Value(s) for s in sums])
        print(json.dumps(out,sort_keys=True),flush=True)
        return 0 if ok else 3
    print(json.dumps(out,sort_keys=True),flush=True)
    return 0 if st==cp_model.INFEASIBLE else 2


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ka',type=int,required=True,choices=[12,14])
    ap.add_argument('--profiles',required=True)
    ap.add_argument('--mode',choices=['allowed','forbidden'],default='allowed')
    ap.add_argument('--seconds',type=float,default=720.0)
    ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--seed',type=int,default=1)
    args=ap.parse_args()
    return solve(args.ka,args.profiles,args.mode,args.seconds,args.workers,args.seed)

if __name__=='__main__': sys.exit(main())
