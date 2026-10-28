#!/usr/bin/env python3
"""Exact LABS-100 E=574, O=58 with the unique odd defect lag fixed.

Exact E=574/O=58 has normalized half sums A_sum=B_sum=2 and exactly one
opposite odd-lag pair of energy 10 with positive pair sum; all other odd pairs
are (+/-1,-/+1).  Fixing the defect lag removes the 25-way disjunction from
the broader low-odd model. Reversal preserves A_sum=B_sum=2, the defect lag,
and energy, so x0<=x99 breaks that residual symmetry.

UNKNOWN is not an exclusion. Any feasible assignment is independently rescored.
"""
from __future__ import annotations
import argparse, time
from ortools.sat.python import cp_model

N=100; TARGET=574; ODD=58; EVEN=516
VALID_K=tuple(range(1,50,2))

def exact(seq):
    s=[1 if c=='+' else -1 for c in seq]
    cs=[0]+[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
    return sum(c*c for c in cs[1:]),sum(cs[k]*cs[k] for k in range(1,N,2)),cs,sum(s[0::2]),sum(s[1::2])

def square(model,v,name,lo,hi):
    q=model.NewIntVar(0,max(lo*lo,hi*hi),name)
    model.AddAllowedAssignments([v,q],[(z,z*z) for z in range(lo,hi+1)])
    return q

def build(defect_k):
    if defect_k not in VALID_K: raise ValueError('defect-k must be odd 1..49')
    model=cp_model.CpModel(); x=[model.NewBoolVar(f'x{i}') for i in range(N)]
    model.Add(50-2*sum(x[0::2])==2); model.Add(50-2*sum(x[1::2])==2)
    # reversal symmetry, since both parity-half sums are equal
    model.Add(x[0] <= x[99])
    corr={}; evenq=[]; evenc=[]
    for k in range(1,N):
        L=N-k; zs=[]
        for i in range(L):
            d=model.NewBoolVar(f'z_{k}_{i}')
            model.AddBoolXOr([x[i],x[i+k],d.Not()]); zs.append(d)
        m=model.NewIntVar(0,L,f'm{k}'); model.Add(m==sum(zs))
        c=model.NewIntVar(-L,L,f'c{k}'); model.Add(c==L-2*m); corr[k]=c
        if k%2==0:
            q=model.NewIntVar(0,EVEN,f'q{k}')
            model.AddAllowedAssignments([c,q],[(v,v*v) for v in range(-L,L+1,2) if v*v<=EVEN])
            evenq.append(q); evenc.append(c)
    for k in VALID_K:
        j=N-k
        if k==defect_k:
            model.AddAllowedAssignments([corr[k],corr[j]],[(1,3),(3,1)])
        else:
            model.AddAllowedAssignments([corr[k],corr[j]],[(-1,1),(1,-1)])
    model.Add(sum(evenq)==EVEN)
    # a=b=2 => 2*sum even C = a^2+b^2-100 = -92
    model.Add(2*sum(evenc)==-92)
    for k in range(2,50,2):
        j=N-k; l1=N-k; l2=k
        rows=[(u,v) for u in range(-l1,l1+1,2) for v in range(-l2,l2+1,2)
              if (u+v)%4==0 and u*u+v*v<=EVEN]
        model.AddAllowedAssignments([corr[k],corr[j]],rows)
    # exact 574 => global product +1 => C50 = 2 mod4
    model.AddAllowedAssignments([corr[50]],[(v,) for v in range(-50,51,2) if v%4==2 and v*v<=EVEN])
    # z=i Fourier identity
    aa=model.NewIntVar(-50,50,'a_alt'); bb=model.NewIntVar(-50,50,'b_alt')
    model.Add(aa==sum((1 if j%2==0 else -1)*(1-2*x[2*j]) for j in range(50)))
    model.Add(bb==sum((1 if j%2==0 else -1)*(1-2*x[2*j+1]) for j in range(50)))
    a2=square(model,aa,'a2',-50,50); b2=square(model,bb,'b2',-50,50)
    alt=sum((1 if r%2==0 else -1)*corr[2*r] for r in range(1,50))
    model.Add(a2+b2==100+2*alt)
    return model,x

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--defect-k',type=int,choices=VALID_K,required=True)
    ap.add_argument('--seconds',type=float,default=120); ap.add_argument('--workers',type=int,default=4); ap.add_argument('--seed',type=int,default=1)
    a=ap.parse_args(); model,x=build(a.defect_k)
    v=model.Validate()
    if v: raise SystemExit('MODEL_INVALID '+v)
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=a.seconds; s.parameters.num_search_workers=a.workers
    s.parameters.random_seed=a.seed; s.parameters.randomize_search=True; s.parameters.cp_model_presolve=True; s.parameters.symmetry_level=2
    t=time.time(); st=s.Solve(model)
    print('STATUS',f'defect_k={a.defect_k}',s.StatusName(st),f'wall={time.time()-t:.3f}',f'branches={s.NumBranches()}',f'conflicts={s.NumConflicts()}')
    if st==cp_model.INFEASIBLE:
        print(f'PROVED_INFEASIBLE defect_k={a.defect_k}'); return
    if st not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        print(f'UNRESOLVED defect_k={a.defect_k}'); return
    seq=''.join('-' if s.Value(vv) else '+' for vv in x); e,o,cs,asum,bsum=exact(seq)
    print(f'FOUND defect_k={a.defect_k} energy={e} odd={o} asum={asum} bsum={bsum} seq={seq}')
    if (e,o,asum,bsum)!=(TARGET,ODD,2,2): raise SystemExit('independent score check failed')
    defects=[k for k in VALID_K if cs[k]*cs[k]+cs[N-k]*cs[N-k]==10]
    if defects!=[a.defect_k] or cs[a.defect_k]+cs[N-a.defect_k]!=4: raise SystemExit('defect check failed')

if __name__=='__main__': main()
