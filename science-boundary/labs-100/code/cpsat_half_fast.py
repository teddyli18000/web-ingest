#!/usr/bin/env python3
"""Reduced exact CP-SAT search with one parity half fixed."""
import argparse,time
from ortools.sat.python import cp_model
N=50

def full_energy(seq):
 s=[1 if c=='+' else -1 for c in seq]
 cs=[sum(s[i]*s[i+k] for i in range(100-k)) for k in range(1,100)]
 return sum(c*c for c in cs),cs

def split(seq):
 vals=[1 if c=='+' else -1 for c in seq];return vals[0::2],vals[1::2]

def build(fixed, variable_hint, target, variable_is_B):
 M=cp_model.CpModel();x=[M.NewBoolVar(f'x{i}') for i in range(N)]
 M.Add(x[0]==0)  # independent half-sign symmetry
 qs=[]
 for r in range(N):
  coeff=[]
  for j in range(N):
   if variable_is_B:
    # C_{2r+1}=sum A_t B_{t+r}+sum B_t A_{t+r+1}
    w=(fixed[j-r] if j>=r else 0)+(fixed[j+r+1] if j+r+1<N else 0)
   else:
    w=(fixed[j+r] if j+r<N else 0)+(fixed[j-r-1] if j>=r+1 else 0)
   coeff.append(w)
  const=sum(coeff);maxabs=sum(abs(w) for w in coeff)
  c=M.NewIntVar(-maxabs,maxabs,f'co{r}')
  M.Add(c==const-2*sum(coeff[j]*x[j] for j in range(N)))
  q=M.NewIntVar(0,target,f'qo{r}')
  vals=[v for v in range(-maxabs,maxabs+1) if (v-(99-2*r))%2==0 and v*v<=target]
  M.AddAllowedAssignments([c,q],[(v,v*v) for v in vals]);qs.append(q)
 for r in range(1,N):
  L=N-r;cf=sum(fixed[i]*fixed[i+r] for i in range(L));zs=[]
  for i in range(L):
   z=M.NewBoolVar(f'z_{r}_{i}');M.AddBoolXOr([x[i],x[i+r],z.Not()]);zs.append(z)
  m=M.NewIntVar(0,L,f'm{r}');M.Add(m==sum(zs));cmin=cf-L;cmax=cf+L
  c=M.NewIntVar(cmin,cmax,f'ce{r}');M.Add(c==cf+L-2*m)
  q=M.NewIntVar(0,target,f'qe{r}');M.AddAllowedAssignments([c,q],[(v,v*v) for v in range(cmin,cmax+1,2) if v*v<=target]);qs.append(q)
 M.Add(sum(qs)<=target)
 for v,h in zip(x,variable_hint):M.AddHint(v,0 if h==1 else 1)
 return M,x

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seed',required=True);ap.add_argument('--fix',choices=['even','odd'],required=True);ap.add_argument('--target',type=int,default=574);ap.add_argument('--seconds',type=float,default=600);ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
 if len(args.seed)!=100 or any(c not in '+-' for c in args.seed):raise SystemExit('bad seed')
 A,B=split(args.seed)
 if args.fix=='even': fixed,var,variable_is_B=A,B,True
 else: fixed,var,variable_is_B=B,A,False
 M,x=build(fixed,var,args.target,variable_is_B)
 S=cp_model.CpSolver();S.parameters.max_time_in_seconds=args.seconds;S.parameters.num_search_workers=args.workers;S.parameters.random_seed=1;S.parameters.log_search_progress=True;S.parameters.symmetry_level=2
 t=time.time();st=S.Solve(M);print('STATUS',S.StatusName(st),'fix',args.fix,'target',args.target,'wall',time.time()-t,'branches',S.NumBranches(),'conflicts',S.NumConflicts())
 if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
  V=[-1 if S.Value(v) else 1 for v in x];AA,BB=(fixed,V) if args.fix=='even' else (V,fixed)
  seq=''.join(('+' if AA[i]>0 else '-')+('+' if BB[i]>0 else '-') for i in range(N));e,cs=full_energy(seq);odd=sum(cs[k-1]**2 for k in range(1,100,2));print('FOUND energy',e,'odd',odd,'even',e-odd,'seq',seq)
  if e>args.target:raise SystemExit('independent exact check failed')
 else:print('NO_CERTIFICATE')
if __name__=='__main__':main()
