#!/usr/bin/env python3
"""Exact CP-SAT feasibility for LABS-100 E=570 in the odd-perfect O=50 layer.

Exact E=570 has global sign product -1.  In O=50 every opposite odd-lag
pair is (+/-1,-/+1), so the parity-half sum product is zero.  After standard
normalization the only half-sum classes surviving Cauchy are A_sum=0 and
B_sum in {2,6,10,14,18}.

The model enforces exact even energy 520, opposite-even-lag mod-4 tables,
C_50==0 (mod 4), the exact even-correlation sum, and the z=i Fourier identity.
For the B_sum=10 class, the normalized reverse+alternate symmetry image of the
public E=578 incumbent is supplied as a hint; a linear Hamming-distance >=8
constraint excludes its exhaustively checked radius-7 ball. UNKNOWN is never
treated as a proof.
"""
from __future__ import annotations

import argparse
import time
from ortools.sat.python import cp_model

N=100
TARGET=570
ODD_ENERGY=50
EVEN_ENERGY=520
VALID_BSUM=(2,6,10,14,18)
# reverse+alternate image of the public E=578 record, normalized to
# A_sum=0, B_sum=10 and first sign +.
INC_NORM="+++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-+"


def exact(seq:str):
    s=[1 if ch=='+' else -1 for ch in seq]
    cs=[0]+[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
    e=sum(c*c for c in cs[1:])
    o=sum(cs[k]*cs[k] for k in range(1,N,2))
    a=sum(s[0::2]); b=sum(s[1::2])
    return e,o,cs,a,b


def add_square(model,v,name,lo,hi):
    q=model.NewIntVar(0,max(lo*lo,hi*hi),name)
    model.AddAllowedAssignments([v,q],[(z,z*z) for z in range(lo,hi+1)])
    return q


def build(bsum_value:int):
    if bsum_value not in VALID_BSUM: raise ValueError('invalid bsum')
    model=cp_model.CpModel()
    x=[model.NewBoolVar(f'x{i}') for i in range(N)] # 0=+1,1=-1
    model.Add(50-2*sum(x[0::2])==0)
    model.Add(50-2*sum(x[1::2])==bsum_value)
    # Alternation flips the A half while A_sum=0 and preserves energy/B_sum.
    model.Add(x[0]==0)

    corr={}; even_q=[]; even_corr=[]
    for k in range(1,N):
        length=N-k
        zs=[]
        for i in range(length):
            d=model.NewBoolVar(f'z_{k}_{i}')
            model.AddBoolXOr([x[i],x[i+k],d.Not()])
            zs.append(d)
        m=model.NewIntVar(0,length,f'm{k}')
        model.Add(m==sum(zs))
        c=model.NewIntVar(-length,length,f'c{k}')
        model.Add(c==length-2*m)
        corr[k]=c
        if k%2==0:
            q=model.NewIntVar(0,EVEN_ENERGY,f'q{k}')
            rows=[(v,v*v) for v in range(-length,length+1,2) if v*v<=EVEN_ENERGY]
            model.AddAllowedAssignments([c,q],rows)
            even_q.append(q); even_corr.append(c)

    for k in range(1,50,2):
        model.AddAllowedAssignments([corr[k],corr[N-k]],[(-1,1),(1,-1)])

    model.Add(sum(even_q)==EVEN_ENERGY)
    model.Add(2*sum(even_corr)==bsum_value*bsum_value-100)

    for k in range(2,50,2):
        j=N-k; l1=N-k; l2=k
        rows=[
            (u,v)
            for u in range(-l1,l1+1,2)
            for v in range(-l2,l2+1,2)
            if (u+v)%4==0 and u*u+v*v<=EVEN_ENERGY
        ]
        model.AddAllowedAssignments([corr[k],corr[j]],rows)

    # Exact E=570 => global sign product -1 => C50 == 0 mod4.
    model.AddAllowedAssignments(
        [corr[50]],[(v,) for v in range(-50,51,2) if v%4==0 and v*v<=EVEN_ENERGY]
    )

    a_alt=model.NewIntVar(-50,50,'a_alt'); b_alt=model.NewIntVar(-50,50,'b_alt')
    model.Add(a_alt==sum((1 if j%2==0 else -1)*(1-2*x[2*j]) for j in range(50)))
    model.Add(b_alt==sum((1 if j%2==0 else -1)*(1-2*x[2*j+1]) for j in range(50)))
    a2=add_square(model,a_alt,'a_alt_sq',-50,50)
    b2=add_square(model,b_alt,'b_alt_sq',-50,50)
    alt_even=sum((1 if r%2==0 else -1)*corr[2*r] for r in range(1,50))
    model.Add(a2+b2==N+2*alt_even)

    if bsum_value==10:
        ie,io,_,ia,ib=exact(INC_NORM)
        if (ie,io,ia,ib)!=(578,50,0,10):
            raise RuntimeError('normalized incumbent check failed')
        # The radius-7 exclusion transfers to this standard symmetry image.
        diff=[]
        for i,ch in enumerate(INC_NORM):
            incbit=0 if ch=='+' else 1
            diff.append(x[i] if incbit==0 else 1-x[i])
            model.AddHint(x[i],incbit)
        model.Add(sum(diff)>=8)

    return model,x


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--bsum',type=int,choices=VALID_BSUM,required=True)
    ap.add_argument('--seconds',type=float,default=360)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=1)
    args=ap.parse_args()
    model,x=build(args.bsum)
    validation=model.Validate()
    if validation: raise SystemExit(f'MODEL_INVALID {validation}')
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.seconds
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=args.seed
    solver.parameters.randomize_search=True
    solver.parameters.cp_model_presolve=True
    solver.parameters.symmetry_level=2
    t0=time.time(); status=solver.Solve(model)
    print('STATUS',f'bsum={args.bsum}',solver.StatusName(status),f'wall={time.time()-t0:.3f}',
          f'branches={solver.NumBranches()}',f'conflicts={solver.NumConflicts()}')
    if status==cp_model.INFEASIBLE:
        print(f'PROVED_INFEASIBLE bsum={args.bsum}'); return
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        print(f'UNRESOLVED bsum={args.bsum}'); return
    seq=''.join('-' if solver.Value(v) else '+' for v in x)
    e,o,cs,a,b=exact(seq)
    print(f'FOUND bsum={args.bsum} energy={e} odd={o} asum={a} actual_bsum={b} seq={seq}')
    if e!=TARGET or o!=ODD_ENERGY or a!=0 or b!=args.bsum:
        raise SystemExit('independent exact check failed')
    if any((cs[k],cs[N-k]) not in ((-1,1),(1,-1)) for k in range(1,50,2)):
        raise SystemExit('odd-pair check failed')

if __name__=='__main__':
    main()
