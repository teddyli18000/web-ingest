#!/usr/bin/env python3
"""Exact CP-SAT feasibility for E=574 inside the full N=100 near-skew subspace.

A canonical near-skew sequence has s_0=+1 and tail t=s_1..s_99 skew-symmetric:
    t[98-v] = (-1)^(v+1) t[v], v=0..48,
with t[49] free.  This leaves exactly 50 free signs.  All 50 odd-lag
correlations then have magnitude one, so odd energy is exactly 50.  The odd
parity-position half sum is identically zero.  For exact E=574, the other
half sum must be a multiple of four; Cauchy bounds its magnitude by 20.

The model splits on that half sum, enforces exact even energy 524, redundant
opposite-even-lag congruences, C_50 == 2 mod 4, the even-correlation sum, and
the z=i Fourier identity.  Any feasible assignment is independently checked
for energy and the skew-tail invariant.  UNKNOWN is not an exclusion.
"""
from __future__ import annotations
import argparse, time
from ortools.sat.python import cp_model

N=100; TARGET=574; ODD=50; EVEN=524
VALID_ASUM=tuple(range(-20,21,4))

def exact(seq:str):
    s=[1 if c=='+' else -1 for c in seq]
    cs=[0]+[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
    e=sum(c*c for c in cs[1:]); o=sum(cs[k]*cs[k] for k in range(1,N,2))
    a=sum(s[0::2]); b=sum(s[1::2])
    return e,o,cs,a,b

def is_nearskew(seq:str)->bool:
    if len(seq)!=100 or seq[0]!='+': return False
    s=[1 if c=='+' else -1 for c in seq]; t=s[1:]
    return all(t[98-v]==((-1)**(v+1))*t[v] for v in range(49))

def square(model,v,name,lo,hi):
    q=model.NewIntVar(0,max(lo*lo,hi*hi),name)
    model.AddAllowedAssignments([v,q],[(z,z*z) for z in range(lo,hi+1)])
    return q

def build(asum_value:int):
    if asum_value not in VALID_ASUM: raise ValueError('asum must be -20..20 step4')
    model=cp_model.CpModel(); x=[model.NewBoolVar(f'x{i}') for i in range(N)]
    model.Add(x[0]==0)  # canonical global sign: s0=+1
    # Tail free variables are full positions 1..50. Mirror positions 99..51.
    for v in range(49):
        p=1+v; q=99-v
        if v%2==1: model.Add(x[q]==x[p])       # mirror sign +
        else: model.Add(x[q]+x[p]==1)          # mirror sign -
    model.Add(50-2*sum(x[0::2])==asum_value)
    model.Add(50-2*sum(x[1::2])==0)

    corr={}; evenq=[]; evenc=[]
    for k in range(1,N):
        L=N-k; zs=[]
        for i in range(L):
            d=model.NewBoolVar(f'z_{k}_{i}')
            model.AddBoolXOr([x[i],x[i+k],d.Not()]); zs.append(d)
        m=model.NewIntVar(0,L,f'm{k}'); model.Add(m==sum(zs))
        c=model.NewIntVar(-L,L,f'c{k}'); model.Add(c==L-2*m); corr[k]=c
        if k%2:
            model.AddAllowedAssignments([c],[(-1,),(1,)])
        else:
            q=model.NewIntVar(0,EVEN,f'q{k}')
            model.AddAllowedAssignments([c,q],[(v,v*v) for v in range(-L,L+1,2) if v*v<=EVEN])
            evenq.append(q); evenc.append(c)
    model.Add(sum(evenq)==EVEN)
    # B_sum=0, so 2*sum(C_even)=A_sum^2-100.
    model.Add(2*sum(evenc)==asum_value*asum_value-100)
    # Opposite even-lag mod-4 relation.
    for k in range(2,50,2):
        j=N-k; l1=N-k; l2=k
        rows=[(u,v) for u in range(-l1,l1+1,2) for v in range(-l2,l2+1,2)
              if (u+v)%4==0 and u*u+v*v<=EVEN]
        model.AddAllowedAssignments([corr[k],corr[j]],rows)
    # Exact E574 has product +1.
    model.AddAllowedAssignments([corr[50]],[(v,) for v in range(-50,51,2) if v%4==2 and v*v<=EVEN])
    # z=i Fourier identity.
    aa=model.NewIntVar(-50,50,'a_alt'); bb=model.NewIntVar(-50,50,'b_alt')
    model.Add(aa==sum((1 if j%2==0 else -1)*(1-2*x[2*j]) for j in range(50)))
    model.Add(bb==sum((1 if j%2==0 else -1)*(1-2*x[2*j+1]) for j in range(50)))
    a2=square(model,aa,'a2',-50,50); b2=square(model,bb,'b2',-50,50)
    alt=sum((1 if r%2==0 else -1)*corr[2*r] for r in range(1,50))
    model.Add(a2+b2==100+2*alt)
    return model,x

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--asum',type=int,choices=VALID_ASUM,required=True)
    ap.add_argument('--seconds',type=float,default=240); ap.add_argument('--workers',type=int,default=4); ap.add_argument('--seed',type=int,default=1)
    a=ap.parse_args(); model,x=build(a.asum); validation=model.Validate()
    if validation: raise SystemExit('MODEL_INVALID '+validation)
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=a.seconds; s.parameters.num_search_workers=a.workers
    s.parameters.random_seed=a.seed; s.parameters.randomize_search=True; s.parameters.cp_model_presolve=True; s.parameters.symmetry_level=2
    t=time.time(); st=s.Solve(model)
    print('STATUS',f'asum={a.asum}',s.StatusName(st),f'wall={time.time()-t:.3f}',f'branches={s.NumBranches()}',f'conflicts={s.NumConflicts()}')
    if st==cp_model.INFEASIBLE:
        print(f'PROVED_INFEASIBLE asum={a.asum}'); return
    if st not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        print(f'UNRESOLVED asum={a.asum}'); return
    seq=''.join('-' if s.Value(v) else '+' for v in x); e,o,cs,asum,bsum=exact(seq)
    print(f'FOUND asum={a.asum} energy={e} odd={o} actual_asum={asum} bsum={bsum} seq={seq}')
    if (e,o,asum,bsum)!=(TARGET,ODD,a.asum,0) or not is_nearskew(seq):
        raise SystemExit('independent exact/near-skew check failed')

if __name__=='__main__': main()
