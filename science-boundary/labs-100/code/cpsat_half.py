#!/usr/bin/env python3
import argparse,time
from ortools.sat.python import cp_model
N=100

def exact(seq):
 s=[1 if c=='+' else -1 for c in seq];cs=[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)];return sum(c*c for c in cs),cs

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--seed',required=True);ap.add_argument('--fix',choices=['even','odd'],required=True);ap.add_argument('--bound',type=int,default=574);ap.add_argument('--seconds',type=float,default=240);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--optimize',action='store_true');args=ap.parse_args()
 if len(args.seed)!=100 or any(c not in '+-' for c in args.seed):raise SystemExit('bad seed')
 M=cp_model.CpModel();x=[M.NewBoolVar(f'x{i}') for i in range(N)];bits=[0 if c=='+' else 1 for c in args.seed]
 parity=0 if args.fix=='even' else 1
 for i in range(parity,N,2):M.Add(x[i]==bits[i])
 qs=[]
 for k in range(1,N):
  L=N-k;z=[]
  for i in range(L):
   v=M.NewBoolVar(f'z{i}_{k}');M.AddBoolXOr([x[i],x[i+k],v.Not()]);z.append(v)
  h=M.NewIntVar(0,L,f'h{k}');M.Add(h==sum(z));c=M.NewIntVar(-L,L,f'c{k}');M.Add(c==L-2*h);q=M.NewIntVar(0,L*L,f'q{k}');M.AddMultiplicationEquality(q,[c,c]);qs.append(q)
 total=M.NewIntVar(0,20000,'energy');M.Add(total==sum(qs))
 if args.optimize:M.Minimize(total)
 else:M.Add(total<=args.bound)
 for i,v in enumerate(x):M.AddHint(v,bits[i])
 S=cp_model.CpSolver();S.parameters.max_time_in_seconds=args.seconds;S.parameters.num_search_workers=args.workers;S.parameters.random_seed=1;S.parameters.log_search_progress=True
 t=time.time();st=S.Solve(M);print('STATUS',S.StatusName(st),'fix',args.fix,'optimize',args.optimize,'wall',time.time()-t,'branches',S.NumBranches(),'conflicts',S.NumConflicts())
 if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
  seq=''.join('-' if S.Value(v) else '+' for v in x);e,cs=exact(seq);odd=sum(cs[k-1]**2 for k in range(1,N,2));print('FOUND energy',e,'odd',odd,'even',e-odd,'seq',seq)
  if not args.optimize and e>args.bound:raise SystemExit('check failed')
 else:print('NO_CERTIFICATE')
if __name__=='__main__':main()
