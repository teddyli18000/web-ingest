#!/usr/bin/env python3
"""Exact low11 W129/W131 full-sequence shards after order-25 support transfer.

For W129-A, W131-A2 and W131-B1, the order-25 periodic weight multiset is
exactly 1^11 2^13, identical to W127.  Existing exact W127 order-25 searches
exclude kp=10,18,20,22,24; kp=16 has exactly four compressed survivors, each
of which is separately checked by the fibre MITM oracle for the relevant
one/two-defect targets.  Therefore only kp=12 or14 remain.

This wrapper adds that exact kp shard to the strengthened order-10 table model.
UNKNOWN is never an exclusion.
"""
from __future__ import annotations
import argparse,json,sys
from ortools.sat.python import cp_model
import oddperfect_h20_w129_w131_xor_cpsat as base
import oddperfect_h20_w129_w131_order10_cpsat as strong

CASES=('W129-A','W131-A2','W131-B1')

def build(case:str,profiles:str,ka:int):
    model,x,corr,targetE,nrows,sums,R=strong.build(case,profiles)
    # ka = #{i: A_i=A_(i+25)}. A_i is original s_(2i), so compare x[2i]
    # with x[2i+50]. base.xor_var is 1 exactly when the signs differ.
    diffs=[base.xor_var(model,x[2*i],x[2*i+50],f'ka_diff_{i}') for i in range(25)]
    model.Add(sum(diffs)==25-ka)
    return model,x,corr,targetE,nrows,sums,R

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True,choices=CASES);ap.add_argument('--ka',type=int,required=True,choices=[12,14]);ap.add_argument('--profiles',required=True)
    ap.add_argument('--seconds',type=float,default=240);ap.add_argument('--workers',type=int,default=1);ap.add_argument('--seed',type=int,default=1);args=ap.parse_args()
    model,x,corr,targetE,nrows,sums,R=build(args.case,args.profiles,args.ka);err=model.Validate()
    if err:raise SystemExit('MODEL_INVALID '+err)
    s=cp_model.CpSolver();s.parameters.max_time_in_seconds=args.seconds;s.parameters.num_search_workers=args.workers;s.parameters.random_seed=args.seed;s.parameters.randomize_search=True;s.parameters.cp_model_presolve=True;s.parameters.symmetry_level=2
    st=s.Solve(model);out={'case':args.case,'ka':args.ka,'profile_rows':nrows,'target_energy':targetE,'status':s.StatusName(st),'wall_time':s.WallTime(),'branches':s.NumBranches(),'conflicts':s.NumConflicts(),'workers':args.workers}
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        seq=''.join('-' if s.Value(v) else '+' for v in x);e,odd,cs,a,b=base.exact(seq)
        gotka=sum(seq[2*i]==seq[2*i+50] for i in range(25))
        ok=(e==targetE and odd==50 and a==20 and b==0 and gotka==args.ka and all(abs(cs[k])==1 for k in range(1,100,2)))
        out.update(sequence=seq,energy=e,odd_energy=odd,asum=a,bsum=b,actual_ka=gotka,independent_check=ok)
        print(json.dumps(out,sort_keys=True),flush=True);return 0 if ok else 3
    print(json.dumps(out,sort_keys=True),flush=True);return 0 if st==cp_model.INFEASIBLE else 2
if __name__=='__main__':sys.exit(main())
