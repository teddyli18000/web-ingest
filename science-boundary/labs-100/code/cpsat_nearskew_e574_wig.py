#!/usr/bin/env python3
"""Strengthened exact E=574 model for the full N=100 near-skew subspace.

Compared with cpsat_nearskew_e574.py, this formulation omits every odd-lag
correlation from the CP model because the skew-tail relation proves their
energy is exactly 50.  It models only the 49 even correlations and adds the
exact per-lag boundary-product congruence behind the Wiggenbrock bound:

For L=N-k and w=min(k,L), the product of all L terms in C_k equals the product
of the first w and last w sequence signs.  If that boundary product is +1,
C_k == L (mod 4); if it is -1, C_k == L-2 (mod 4).

This connects each correlation residue directly to sequence boundary parity,
which is stronger propagation than using only opposite-lag pair congruences.
UNKNOWN is not an exclusion; any witness is independently rescored.
"""
from __future__ import annotations
import argparse,time
from ortools.sat.python import cp_model

N=100; TARGET=574; ODD=50; EVEN=524
VALID_ASUM=tuple(range(-20,21,4))

def exact(seq):
    s=[1 if c=='+' else -1 for c in seq]
    cs=[0]+[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
    return sum(c*c for c in cs[1:]),sum(cs[k]*cs[k] for k in range(1,N,2)),cs,sum(s[0::2]),sum(s[1::2])

def is_nearskew(seq):
    if len(seq)!=100 or seq[0]!='+': return False
    s=[1 if c=='+' else -1 for c in seq]; t=s[1:]
    return all(t[98-v]==((-1)**(v+1))*t[v] for v in range(49))

def square(model,v,name,lo,hi):
    q=model.NewIntVar(0,max(lo*lo,hi*hi),name)
    model.AddAllowedAssignments([v,q],[(z,z*z) for z in range(lo,hi+1)])
    return q

def add_boundary_residue(model,x,c,k):
    L=N-k; w=min(k,L)
    p=model.NewBoolVar(f'boundary_neg_{k}')
    # XOR(boundary bits) == p.  AddBoolXOr enforces XOR(literals)==1.
    model.AddBoolXOr(list(x[:w])+list(x[N-w:])+[p.Not()])
    rows=[]
    for pv in (0,1):
        residue=(L-2*pv)%4
        for v in range(-L,L+1,2):
            if v%4==residue:
                rows.append((pv,v))
    model.AddAllowedAssignments([p,c],rows)

def build(asum_value):
    if asum_value not in VALID_ASUM: raise ValueError('asum must be -20..20 step4')
    model=cp_model.CpModel(); x=[model.NewBoolVar(f'x{i}') for i in range(N)]
    model.Add(x[0]==0)
    for v in range(49):
        p=1+v; q=99-v
        if v%2: model.Add(x[q]==x[p])
        else: model.Add(x[q]+x[p]==1)
    model.Add(50-2*sum(x[0::2])==asum_value)
    model.Add(50-2*sum(x[1::2])==0)

    corr={}; dq=[]; dc=[]
    for k in range(2,N,2):
        L=N-k; zs=[]
        for i in range(L):
            d=model.NewBoolVar(f'z_{k}_{i}')
            model.AddBoolXOr([x[i],x[i+k],d.Not()]); zs.append(d)
        m=model.NewIntVar(0,L,f'm{k}'); model.Add(m==sum(zs))
        c=model.NewIntVar(-L,L,f'c{k}'); model.Add(c==L-2*m); corr[k]=c
        add_boundary_residue(model,x,c,k)
        dvar=model.NewIntVar(-(L//2),L//2,f'd{k}'); model.Add(c==2*dvar)
        q=model.NewIntVar(0,EVEN//4,f'dq{k}')
        model.AddAllowedAssignments([dvar,q],[(v,v*v) for v in range(-(L//2),L//2+1) if v*v<=EVEN//4])
        dq.append(q); dc.append(c)

    # even energy 524 = 4*131
    model.Add(sum(dq)==131)
    model.Add(2*sum(dc)==asum_value*asum_value-100)
    # Opposite-lag congruence remains as an intentionally redundant global link.
    for k in range(2,50,2):
        j=N-k; l1=N-k; l2=k
        rows=[(u,v) for u in range(-l1,l1+1,2) for v in range(-l2,l2+1,2)
              if (u+v)%4==0 and u*u+v*v<=EVEN]
        model.AddAllowedAssignments([corr[k],corr[j]],rows)
    # exact E574 product +1 => C50 == 2 mod4
    model.AddAllowedAssignments([corr[50]],[(v,) for v in range(-50,51,2) if v%4==2 and v*v<=EVEN])

    aa=model.NewIntVar(-50,50,'a_alt'); bb=model.NewIntVar(-50,50,'b_alt')
    model.Add(aa==sum((1 if j%2==0 else -1)*(1-2*x[2*j]) for j in range(50)))
    model.Add(bb==sum((1 if j%2==0 else -1)*(1-2*x[2*j+1]) for j in range(50)))
    a2=square(model,aa,'a2',-50,50); b2=square(model,bb,'b2',-50,50)
    alt=sum((1 if r%2==0 else -1)*corr[2*r] for r in range(1,50))
    model.Add(a2+b2==100+2*alt)
    return model,x

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--asum',type=int,choices=VALID_ASUM,required=True)
    ap.add_argument('--seconds',type=float,default=180); ap.add_argument('--workers',type=int,default=4); ap.add_argument('--seed',type=int,default=1)
    a=ap.parse_args(); model,x=build(a.asum); val=model.Validate()
    if val: raise SystemExit('MODEL_INVALID '+val)
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=a.seconds; s.parameters.num_search_workers=a.workers
    s.parameters.random_seed=a.seed; s.parameters.randomize_search=True; s.parameters.cp_model_presolve=True; s.parameters.symmetry_level=2
    t=time.time(); st=s.Solve(model)
    print('STATUS',f'asum={a.asum}',s.StatusName(st),f'wall={time.time()-t:.3f}',f'branches={s.NumBranches()}',f'conflicts={s.NumConflicts()}')
    if st==cp_model.INFEASIBLE:
        print(f'PROVED_INFEASIBLE asum={a.asum}'); return
    if st not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        print(f'UNRESOLVED asum={a.asum}'); return
    seq=''.join('-' if s.Value(v) else '+' for v in x); e,o,_,asum,bsum=exact(seq)
    print(f'FOUND asum={a.asum} energy={e} odd={o} actual_asum={asum} bsum={bsum} seq={seq}')
    if (e,o,asum,bsum)!=(TARGET,ODD,a.asum,0) or not is_nearskew(seq):
        raise SystemExit('independent exact/near-skew check failed')

if __name__=='__main__': main()
