#!/usr/bin/env python3
"""Reduced exact CP-SAT search with one parity half fixed.

Write s=(A0,B0,A1,B1,...).  If A is fixed, every odd-lag LABS
correlation is linear in B, while each even-lag correlation is
C_A(r)+C_B(r).  Thus only the 1225 within-B XOR products are needed.
The fixed-B case is obtained by the same formulas with A/B exchanged.
"""
import argparse,time
from ortools.sat.python import cp_model
N=50

def full_energy(seq):
 s=[1 if c=='+' else -1 for c in seq]
 cs=[sum(s[i]*s[i+k] for i in range(100-k)) for k in range(1,100)]
 return sum(c*c for c in cs),cs

def split(seq):
 vals=[1 if c=='+' else -1 for c in seq]
 return vals[0::2],vals[1::2]

def build(fixed, variable_hint, target):
 M=cp_model.CpModel()
 x=[M.NewBoolVar(f'x{i}') for i in range(N)] # variable half: 0=>+1
 M.Add(x[0]==0) # independent sign flip of this parity half is an energy symmetry
 qs=[]
 # Odd lags 2r+1.  Formula is symmetric in the two halves, so treating
 # `fixed` as A and variable as B is sufficient even if the original fixed
 # half was B (swap the names A/B).
 for r in range(N):
  coeff=[]
  for j in range(N):
   w=(fixed[j-r] if j>=r else 0)+(fixed[j+r+1] if j+r+1<N else 0)
   coeff.append(w)
  const=sum(coeff)
  # C = sum_j coeff[j]*(1-2*x_j)
  maxabs=sum(abs(w) for w in coeff)
  c=M.NewIntVar(-maxabs,maxabs,f'co{r}')
  M.Add(c==const-2*sum(coeff[j]*x[j] for j in range(N)))
  q=M.NewIntVar(0,target,f'qo{r}')
  vals=[v for v in range(-maxabs,maxabs+1) if (v-(99-2*r))%2==0 and v*v<=target]
  M.AddAllowedAssignments([c,q],[(v,v*v) for v in vals])
  qs.append(q)
 # Even lags 2r: C_A(r)+C_B(r), r=1..49.
 for r in range(1,N):
  L=N-r
  ca=sum(fixed[i]*fixed[i+r] for i in range(L))
  zs=[]
  for i in range(L):
   z=M.NewBoolVar(f'z_{r}_{i}')
   M.AddBoolXOr([x[i],x[i+r],z.Not()]) # z=xor
   zs.append(z)
  m=M.NewIntVar(0,L,f'm{r}')
  M.Add(m==sum(zs))
  cmin=ca-L;cmax=ca+L
  c=M.NewIntVar(cmin,cmax,f'ce{r}')
  M.Add(c==ca+L-2*m)
  q=M.NewIntVar(0,target,f'qe{r}')
  M.AddAllowedAssignments([c,q],[(v,v*v) for v in range(cmin,cmax+1,2) if v*v<=target])
  qs.append(q)
 M.Add(sum(qs)<=target)
 for v,h in zip(x,variable_hint):M.AddHint(v,0 if h==1 else 1)
 return M,x

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seed',required=True);ap.add_argument('--fix',choices=['even','odd'],required=True);ap.add_argument('--target',type=int,default=574);ap.add_argument('--seconds',type=float,default=600);ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
 if len(args.seed)!=100 or any(c not in '+-' for c in args.seed):raise SystemExit('bad seed')
 A,B=split(args.seed)
 fixed,var=(A,B) if args.fix=='even' else (B,A)
 M,x=build(fixed,var,args.target)
 S=cp_model.CpSolver();S.parameters.max_time_in_seconds=args.seconds;S.parameters.num_search_workers=args.workers;S.parameters.random_seed=1;S.parameters.log_search_progress=True;S.parameters.symmetry_level=2
 t=time.time();st=S.Solve(M);print('STATUS',S.StatusName(st),'fix',args.fix,'target',args.target,'wall',time.time()-t,'branches',S.NumBranches(),'conflicts',S.NumConflicts())
 if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
  V=[-1 if S.Value(v) else 1 for v in x]
  AA,BB=(fixed,V) if args.fix=='even' else (V,fixed)
  seq=''.join(('+' if AA[i]>0 else '-')+('+' if BB[i]>0 else '-') for i in range(N))
  e,cs=full_energy(seq);odd=sum(cs[k-1]**2 for k in range(1,100,2));print('FOUND energy',e,'odd',odd,'even',e-odd,'seq',seq)
  if e>args.target:raise SystemExit('independent exact check failed')
 else:print('NO_CERTIFICATE')
if __name__=='__main__':main()
