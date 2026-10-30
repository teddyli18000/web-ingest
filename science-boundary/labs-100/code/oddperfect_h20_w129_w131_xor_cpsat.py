#!/usr/bin/env python3
"""Exact full-sequence feasibility model for the (20,0) odd-perfect W129/W131 cases.

The sparse near-NGP classification fixes the multiset of even correlations and
how opposite even-lag pairs can differ.  This model encodes all 100 original
signs as Booleans, every LABS correlation as an XOR disagreement cardinality,
all odd correlations as +/-1 with opposite odd signs, and one exact structural
case for the even correlations.

FEASIBLE is independently rescored from the original LABS definition and is a
true record candidate (E=566 for W129 or E=574 for W131). INFEASIBLE exactly
excludes the selected structural case. UNKNOWN is not evidence of exclusion.
"""
from __future__ import annotations
import argparse,json,sys
from ortools.sat.python import cp_model

N=100

CASES={
 # middle C50, group counts over 24 opposite even-lag pairs.
 # Groups are oriented pattern families listed below.
 'W129-A':  (566,2, {'E1':10,'E2':13,'D02':1}),
 'W129-B0': (566,6, {'E1':12,'E2':12}),
 'W129-B1': (566,2, {'E1':11,'E2':12,'D13':1}),
 'W131-A0': (574,2, {'E0':1,'E1':9,'E2':14}),
 'W131-A2': (574,2, {'E1':9,'E2':13,'D02':2}),
 'W131-B3': (574,6, {'E1':11,'E2':12,'D02':1}),
 'W131-B1': (574,2, {'E1':10,'E2':12,'D02':1,'D13':1}),
 'W131-C0': (574,2, {'E1':12,'E2':11,'E3':1}),
 'W131-C2': (574,2, {'E1':11,'E2':11,'D13':2}),
 'W131-C3': (574,6, {'E1':12,'E2':11,'D13':1}),
}
# Correlation values are C=2d.
PATTERNS={
 'E0':[(0,0)], 'E1':[(2,2)], 'E2':[(4,4)], 'E3':[(6,6)],
 'D02':[(0,4),(4,0)],
 'D13':[(2,6),(6,2)],
}

def exact(seq:str):
 s=[1 if ch=='+' else -1 for ch in seq]
 cs=[0]+[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
 return sum(c*c for c in cs[1:]),sum(cs[k]*cs[k] for k in range(1,N,2)),cs,sum(s[0::2]),sum(s[1::2])

def xor_var(m,x,y,name):
 d=m.NewBoolVar(name);m.AddBoolXOr([x,y,d.Not()]);return d

def build(case):
 targetE,mid,need=CASES[case]
 m=cp_model.CpModel();x=[m.NewBoolVar(f'x{i}') for i in range(N)]
 m.Add(sum(x[0::2])==15);m.Add(sum(x[1::2])==25) # sums A=20,B=0
 corr={};oddneg={}
 for k in range(1,N):
  z=[xor_var(m,x[i],x[i+k],f'z_{k}_{i}') for i in range(N-k)]
  q=m.NewIntVar(0,N-k,f'q{k}');m.Add(q==sum(z))
  c=m.NewIntVar(-(N-k),N-k,f'c{k}');m.Add(c==(N-k)-2*q);corr[k]=c
  if k&1:
   r=(k-1)//2;u=m.NewBoolVar(f'oddneg_{r}');m.Add(q==49-r+u);oddneg[r]=u
 for r in range(25):m.Add(oddneg[r]+oddneg[49-r]==1)
 m.Add(corr[50]==mid)
 groups={g:[] for g in need}
 allowed_groups=list(need)
 for r in range(1,25):
  a,b=corr[2*r],corr[100-2*r]
  opts=[]
  for g in allowed_groups:
   for p in PATTERNS[g]:opts.append((g,p))
  sels=[]
  for j,(g,(va,vb)) in enumerate(opts):
   s=m.NewBoolVar(f'pair_{r}_{g}_{j}');sels.append(s)
   m.Add(a==va).OnlyEnforceIf(s);m.Add(b==vb).OnlyEnforceIf(s)
   groups[g].append(s)
  m.AddExactlyOne(sels)
 for g,n in need.items():m.Add(sum(groups[g])==n)
 return m,x,corr,targetE

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--case',required=True,choices=sorted(CASES));ap.add_argument('--seconds',type=float,default=180);ap.add_argument('--workers',type=int,default=1);ap.add_argument('--seed',type=int,default=1);args=ap.parse_args()
 m,x,corr,targetE=build(args.case);err=m.Validate()
 if err:raise SystemExit('MODEL_INVALID '+err)
 s=cp_model.CpSolver();s.parameters.max_time_in_seconds=args.seconds;s.parameters.num_search_workers=args.workers;s.parameters.random_seed=args.seed;s.parameters.randomize_search=True;s.parameters.cp_model_presolve=True;s.parameters.symmetry_level=2
 st=s.Solve(m);out={'case':args.case,'target_energy':targetE,'status':s.StatusName(st),'wall_time':s.WallTime(),'branches':s.NumBranches(),'conflicts':s.NumConflicts(),'workers':args.workers}
 if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
  seq=''.join('-' if s.Value(v) else '+' for v in x);e,odd,cs,a,b=exact(seq)
  ok=(e==targetE and odd==50 and a==20 and b==0 and all(abs(cs[k])==1 for k in range(1,100,2)))
  out.update(sequence=seq,energy=e,odd_energy=odd,asum=a,bsum=b,independent_check=ok,even=[cs[k] for k in range(2,100,2)])
  print(json.dumps(out,sort_keys=True),flush=True);return 0 if ok else 3
 print(json.dumps(out,sort_keys=True),flush=True);return 0 if st==cp_model.INFEASIBLE else 2
if __name__=='__main__':sys.exit(main())
