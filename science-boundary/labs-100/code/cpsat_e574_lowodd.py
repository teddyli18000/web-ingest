#!/usr/bin/env python3
"""Exact CP-SAT feasibility for LABS-100 E=574 in odd-energy layers O=50,58.

The model uses the exact-E=574 arithmetic classes from target_arithmetic.py.
For O=50, normalize A_sum=0 and B_sum in {0,4,8,12,16,20}; every opposite
odd-lag pair is (+/-1,-/+1).  For O=58, exact arithmetic forces the normalized
half sums A_sum=B_sum=2 and exactly one positive-sum energy-10 odd pair.

Redundant propagation constraints include opposite-even-lag mod-4 tables,
C_50==2 (mod 4), exact even energy, the exact even-correlation sum, and the
z=i Fourier identity.  UNKNOWN is not an exclusion.  Any feasible sequence is
independently rescored before printing.
"""
from __future__ import annotations

import argparse
import time
from ortools.sat.python import cp_model

N=100
TARGET=574
O50_BSUM=(0,4,8,12,16,20)


def exact(seq: str):
    s=[1 if ch=='+' else -1 for ch in seq]
    cs=[0]+[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
    e=sum(c*c for c in cs[1:])
    o=sum(cs[k]*cs[k] for k in range(1,N,2))
    a=sum(s[0::2]); b=sum(s[1::2])
    return e,o,cs,a,b


def add_square(model,v,name,lo,hi):
    q=model.NewIntVar(0,max(lo*lo,hi*hi),name)
    model.AddAllowedAssignments([v,q],[(x,x*x) for x in range(lo,hi+1)])
    return q


def build(odd_energy:int, bsum_value:int):
    if odd_energy not in (50,58): raise ValueError('odd must be 50 or 58')
    if odd_energy==50 and bsum_value not in O50_BSUM: raise ValueError('bad O50 bsum')
    if odd_energy==58 and bsum_value!=2: raise ValueError('O58 requires bsum=2')
    even_energy=TARGET-odd_energy

    model=cp_model.CpModel()
    x=[model.NewBoolVar(f'x{i}') for i in range(N)]
    asum=model.NewIntVar(0 if odd_energy==50 else 2,0 if odd_energy==50 else 2,'asum')
    bsum=model.NewIntVar(bsum_value,bsum_value,'bsum')
    model.Add(asum==50-2*sum(x[0::2]))
    model.Add(bsum==50-2*sum(x[1::2]))
    if odd_energy==50:
        # Alternation flips the A half and leaves A_sum=0/B_sum unchanged.
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
            q=model.NewIntVar(0,even_energy,f'q{k}')
            rows=[(v,v*v) for v in range(-length,length+1,2) if v*v<=even_energy]
            model.AddAllowedAssignments([c,q],rows)
            even_q.append(q); even_corr.append(c)

    if odd_energy==50:
        for k in range(1,50,2):
            model.AddAllowedAssignments([corr[k],corr[N-k]],[(-1,1),(1,-1)])
    else:
        flags=[]
        for k in range(1,50,2):
            h=model.NewBoolVar(f'd10_{k}')
            model.AddAllowedAssignments(
                [corr[k],corr[N-k],h],
                [(-1,1,0),(1,-1,0),(1,3,1),(3,1,1)],
            )
            flags.append(h)
        model.Add(sum(flags)==1)

    model.Add(sum(even_q)==even_energy)
    model.Add(2*sum(even_corr)==(0 if odd_energy==50 else 4)+bsum_value*bsum_value-100)

    # Opposite even lag congruence.
    for k in range(2,50,2):
        j=N-k; l1=N-k; l2=k
        rows=[
            (u,v)
            for u in range(-l1,l1+1,2)
            for v in range(-l2,l2+1,2)
            if (u+v)%4==0 and u*u+v*v<=even_energy
        ]
        model.AddAllowedAssignments([corr[k],corr[j]],rows)

    # Exact E=574 => global product +1 => C50=2 mod4.
    model.AddAllowedAssignments(
        [corr[50]],[(v,) for v in range(-50,51,2) if v%4==2 and v*v<=even_energy]
    )

    # z=i Fourier identity.
    a_alt=model.NewIntVar(-50,50,'a_alt'); b_alt=model.NewIntVar(-50,50,'b_alt')
    model.Add(a_alt==sum((1 if j%2==0 else -1)*(1-2*x[2*j]) for j in range(50)))
    model.Add(b_alt==sum((1 if j%2==0 else -1)*(1-2*x[2*j+1]) for j in range(50)))
    a2=add_square(model,a_alt,'a_alt_sq',-50,50)
    b2=add_square(model,b_alt,'b_alt_sq',-50,50)
    alt_even=sum((1 if r%2==0 else -1)*corr[2*r] for r in range(1,50))
    model.Add(a2+b2==N+2*alt_even)
    return model,x


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--odd',type=int,choices=[50,58],required=True)
    ap.add_argument('--bsum',type=int,required=True)
    ap.add_argument('--seconds',type=float,default=360)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=1)
    args=ap.parse_args()
    model,x=build(args.odd,args.bsum)
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
    print('STATUS',f'odd={args.odd}',f'bsum={args.bsum}',solver.StatusName(status),
          f'wall={time.time()-t0:.3f}',f'branches={solver.NumBranches()}',f'conflicts={solver.NumConflicts()}')
    if status==cp_model.INFEASIBLE:
        print(f'PROVED_INFEASIBLE odd={args.odd} bsum={args.bsum}'); return
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        print(f'UNRESOLVED odd={args.odd} bsum={args.bsum}'); return
    seq=''.join('-' if solver.Value(v) else '+' for v in x)
    e,o,cs,a,b=exact(seq)
    print(f'FOUND odd={args.odd} bsum={args.bsum} energy={e} actual_odd={o} asum={a} actual_bsum={b} seq={seq}')
    if e!=TARGET or o!=args.odd or b!=args.bsum or a!=(0 if args.odd==50 else 2):
        raise SystemExit('independent exact check failed')
    if args.odd==50:
        if any((cs[k],cs[N-k]) not in ((-1,1),(1,-1)) for k in range(1,50,2)):
            raise SystemExit('O50 pair check failed')
    else:
        d=[k for k in range(1,50,2) if cs[k]*cs[k]+cs[N-k]*cs[N-k]==10]
        if len(d)!=1 or cs[d[0]]+cs[N-d[0]]!=4:
            raise SystemExit('O58 defect check failed')

if __name__=='__main__':
    main()
