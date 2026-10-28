#!/usr/bin/env python3
import argparse, time
from ortools.sat.python import cp_model
N=100
INC="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-"

def exact(seq):
 s=[1 if c=='+' else -1 for c in seq];cs=[]
 for k in range(1,N):cs.append(sum(s[i]*s[i+k] for i in range(N-k)))
 return sum(c*c for c in cs),cs

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--distance',type=int,required=True);ap.add_argument('--target',type=int,default=574);ap.add_argument('--seconds',type=float,default=600);ap.add_argument('--workers',type=int,default=4);ap.add_argument('--odd-perfect',action='store_true');args=ap.parse_args()
 assert exact(INC)[0]==578
 M=cp_model.CpModel();x=[M.NewBoolVar(f'x{i}') for i in range(N)];ib=[0 if c=='+' else 1 for c in INC]
 M.Add(sum(x[i] if ib[i]==0 else 1-x[i] for i in range(N))==args.distance)
 qs=[]
 for k in range(1,N):
  L=N-k;z=[]
  for i in range(L):
   v=M.NewBoolVar(f'z{i}_{k}');M.AddBoolXOr([x[i],x[i+k],v.Not()]);z.append(v)
  m=M.NewIntVar(0,L,f'm{k}');M.Add(m==sum(z));c=M.NewIntVar(-L,L,f'c{k}');M.Add(c==L-2*m)
  if args.odd_perfect and k%2:
   M.AddAllowedAssignments([m],[((L-1)//2,),((L+1)//2,)])
  else:
   q=M.NewIntVar(0,args.target,f'q{k}');M.AddAllowedAssignments([c,q],[(cc,cc*cc) for cc in range(-L,L+1,2) if cc*cc<=args.target]);qs.append(q)
 M.Add(sum(qs)<=args.target-(50 if args.odd_perfect else 0))
 S=cp_model.CpSolver();S.parameters.max_time_in_seconds=args.seconds;S.parameters.num_search_workers=args.workers;S.parameters.random_seed=1;S.parameters.log_search_progress=True
 t=time.time();st=S.Solve(M);print('STATUS',S.StatusName(st),'distance',args.distance,'odd_perfect',args.odd_perfect,'wall',time.time()-t,'conflicts',S.NumConflicts(),'branches',S.NumBranches())
 if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
  seq=''.join('-' if S.Value(v) else '+' for v in x);e,cs=exact(seq);odd=sum(cs[k-1]**2 for k in range(1,N,2));print('FOUND energy',e,'odd',odd,'even',e-odd,'seq',seq)
  if e>args.target:raise SystemExit('exact check failed')
 else:print('NO_CERTIFICATE')
if __name__=='__main__':main()
