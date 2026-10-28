#!/usr/bin/env python3
import argparse, time
from ortools.sat.python import cp_model

N=100
INC="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-"

def exact_energy(seq):
    s=[1 if c=='+' else -1 for c in seq]
    cs=[]
    for k in range(1,N):
        c=sum(s[i]*s[i+k] for i in range(N-k)); cs.append(c)
    return sum(c*c for c in cs),cs

def build(target:int, odd_perfect:bool, asum=None, bsum=None):
    model=cp_model.CpModel()
    x=[model.NewBoolVar(f'x{i}') for i in range(N)] # 0 => +1, 1 => -1
    if asum is None:
        model.Add(x[0]==0)
        model.Add(x[1]==0)
    else:
        model.Add(50-2*sum(x[0::2]) == asum)
        model.Add(50-2*sum(x[1::2]) == bsum)

    qvars=[]
    odd_pos=[]
    even_corr=[]
    for k in range(1,N):
        L=N-k
        zs=[]
        for i in range(L):
            z=model.NewBoolVar(f'z_{i}_{k}')
            model.AddBoolXOr([x[i],x[i+k],z.Not()])
            zs.append(z)
        m=model.NewIntVar(0,L,f'm{k}')
        model.Add(m==sum(zs))
        c=model.NewIntVar(-L,L,f'c{k}')
        model.Add(c==L-2*m)
        if odd_perfect and (k&1):
            pos=model.NewBoolVar(f'odd_pos{k}')
            model.AddAllowedAssignments([m,pos],[((L-1)//2,1),((L+1)//2,0)])
            odd_pos.append(pos)
        else:
            q=model.NewIntVar(0,target,f'q{k}')
            rows=[]
            for cc in range(-L,L+1,2):
                qq=cc*cc
                if qq<=target: rows.append((cc,qq))
            model.AddAllowedAssignments([c,q],rows)
            qvars.append(q)
            if not (k&1): even_corr.append(c)

    model.Add(sum(qvars) <= (target-50 if odd_perfect else target))
    if odd_perfect and asum is not None:
        # Sum of all odd-lag correlations equals (sum A)(sum B).
        model.Add(sum(odd_pos) == (50 + asum*bsum)//2)
        # Sum of all even-lag correlations equals (a^2+b^2-N)/2.
        model.Add(sum(even_corr) == (asum*asum + bsum*bsum - N)//2)
    return model,x

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--target',type=int,default=574)
    ap.add_argument('--seconds',type=float,default=600)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--general',action='store_true')
    ap.add_argument('--asum',type=int)
    ap.add_argument('--bsum',type=int)
    args=ap.parse_args()
    if (args.asum is None) != (args.bsum is None): raise SystemExit('supply both --asum and --bsum')
    if args.asum is not None and (args.asum<args.bsum or args.bsum<0): raise SystemExit('canonical class requires asum>=bsum>=0')
    e,_=exact_energy(INC); assert e==578
    model,x=build(args.target,not args.general,args.asum,args.bsum)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.seconds
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=args.seed
    solver.parameters.log_search_progress=True
    solver.parameters.cp_model_presolve=True
    solver.parameters.symmetry_level=2
    t=time.time();status=solver.Solve(model);wall=time.time()-t
    tag=f'class={args.asum},{args.bsum}' if args.asum is not None else 'class=unsplit'
    print('STATUS',tag,solver.StatusName(status),'wall',wall,'conflicts',solver.NumConflicts(),'branches',solver.NumBranches())
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        seq=''.join('-' if solver.Value(v) else '+' for v in x)
        ee,cs=exact_energy(seq)
        odd=sum(cs[k-1]**2 for k in range(1,N,2)); even=ee-odd
        print('FOUND',tag,'energy',ee,'odd',odd,'even',even,'seq',seq)
        if ee>args.target: raise SystemExit('solver assignment failed exact target check')
    else:
        print('NO_CERTIFICATE',tag)

if __name__=='__main__': main()
