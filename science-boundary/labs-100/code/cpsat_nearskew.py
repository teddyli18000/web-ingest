#!/usr/bin/env python3
"""Exact CP-SAT feasibility model for the canonical N=100 near-skew manifold.

Fix s_0=+1 and require positions 1..99 to form a length-99 skew-symmetric
tail.  Then every odd-lag autocorrelation has magnitude one, so E<=574 is
equivalent to even-lag energy <=524.  Only 50 tail coordinates are free
(and a standard alternation symmetry lets us also fix s_1=+1).
"""
import argparse, time
from ortools.sat.python import cp_model

N=100
INC="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-"


def exact(seq):
    s=[1 if c=='+' else -1 for c in seq]
    cs=[]
    for k in range(1,N):
        cs.append(sum(s[i]*s[i+k] for i in range(N-k)))
    e=sum(c*c for c in cs)
    o=sum(cs[k-1]**2 for k in range(1,N,2))
    return e,o,cs


def direct_nss(seq):
    s=[1 if c=='+' else -1 for c in seq]
    return all(s[p]*s[100-p] == (-1 if p&1 else 1) for p in range(1,50))


def build(target=574, smoke=False, asum=None):
    model=cp_model.CpModel()
    # Keep explicit full-sequence bit variables because the product/XOR
    # correlations are then compact; reflection equations reduce the degrees
    # of freedom to positions 1..50 plus fixed position 0.
    x=[model.NewBoolVar(f'x{i}') for i in range(N)]  # 0=+1, 1=-1
    model.Add(x[0]==0)
    model.Add(x[1]==0)  # alternating-sign symmetry preserves direct near-skew
    for p in range(1,50):
        q=100-p
        # s[p]s[q]=(-1)^p: unequal bits for odd p, equal for even p.
        if p&1: model.Add(x[q] != x[p])
        else:   model.Add(x[q] == x[p])

    # Direct near-skew implies the odd-index parity half has zero sign sum.
    model.Add(50 - 2*sum(x[1::2]) == 0)
    a=model.NewIntVar(-50,50,'a_even_half_sum')
    model.Add(a == 50 - 2*sum(x[0::2]))
    aa=model.NewIntVar(0,400,'a2')
    model.AddAllowedAssignments([a,aa],[(v,v*v) for v in range(-20,21,2)])
    if asum is not None:
        model.Add(a==asum)

    even_corr=[]
    qvars=[]
    cap=target-50
    for k in range(2,N,2):
        L=N-k
        z=[]
        for i in range(L):
            v=model.NewBoolVar(f'z_{i}_{k}')
            # v=1 exactly when the two signs disagree.
            model.AddBoolXOr([x[i],x[i+k],v.Not()])
            z.append(v)
        m=model.NewIntVar(0,L,f'm{k}')
        model.Add(m==sum(z))
        c=model.NewIntVar(-L,L,f'c{k}')
        model.Add(c==L-2*m)
        q=model.NewIntVar(0,cap,f'q{k}')
        model.AddAllowedAssignments([c,q],[(cc,cc*cc) for cc in range(-L,L+1,2) if cc*cc<=cap])
        even_corr.append(c);qvars.append(q)

    model.Add(sum(qvars) <= cap)
    # Exact identity for parity halves.  The other half has sum zero in this
    # orientation: sum_{r=1}^{49} C_{2r}=(a^2-100)/2.
    model.Add(2*sum(even_corr) == aa-100)

    # Cauchy with the target already implies |a|<=20; the aa table above
    # states this explicitly and avoids leaving impossible sign-sum values.
    if smoke:
        for i,ch in enumerate(INC): model.Add(x[i] == (1 if ch=='-' else 0))
    else:
        # A high-quality hint is useful even though E=578 lies just outside
        # the target; it gives CP-SAT a consistent low-energy neighborhood.
        for i,ch in enumerate(INC): model.AddHint(x[i],1 if ch=='-' else 0)
    return model,x


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--target',type=int,default=574)
    ap.add_argument('--seconds',type=float,default=600)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--asum',type=int)
    ap.add_argument('--smoke',action='store_true')
    args=ap.parse_args()
    ie,io,_=exact(INC);assert (ie,io)==(578,50) and direct_nss(INC)
    if args.asum is not None and (args.asum < -20 or args.asum > 20 or args.asum%2):
        raise SystemExit('--asum must be even in [-20,20]')
    model,x=build(args.target,args.smoke,args.asum)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.seconds
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=args.seed
    solver.parameters.cp_model_presolve=True
    solver.parameters.symmetry_level=2
    solver.parameters.log_search_progress=True
    t=time.time();st=solver.Solve(model);wall=time.time()-t
    print('STATUS',solver.StatusName(st),'asum',args.asum,'wall',wall,'conflicts',solver.NumConflicts(),'branches',solver.NumBranches())
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        seq=''.join('-' if solver.Value(v) else '+' for v in x)
        e,o,cs=exact(seq);a=sum(1 if seq[i]=='+' else -1 for i in range(0,N,2));b=sum(1 if seq[i]=='+' else -1 for i in range(1,N,2))
        print('FOUND energy',e,'odd',o,'even',e-o,'asum',a,'bsum',b,'nss',direct_nss(seq),'seq',seq)
        if not direct_nss(seq) or o!=50 or e>args.target: raise SystemExit('exact validation failed')
    else:
        print('NO_CERTIFICATE')

if __name__=='__main__': main()
