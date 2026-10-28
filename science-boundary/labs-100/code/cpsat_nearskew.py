#!/usr/bin/env python3
"""Exact CP-SAT feasibility model for the canonical N=100 near-skew manifold.

Fix s_0=+1 and require positions 1..99 to form a length-99 skew-symmetric
tail. Then every odd-lag autocorrelation has magnitude one, so E<=574 is
equivalent to even-lag energy <=524. Only 50 tail coordinates are free.

For a length-99 skew tail t, every even correlation C_{2r}(t) is 3 mod 4.
Since the length-100 extension obeys C_{2r}(s)=t_{2r-1}+C_{2r}(t),

    C_{2r}(s) == 1-s_{2r} (mod 4).

Thus d_r=C_{2r}/2 is odd exactly when even-position sign s_{2r}=-1.
This redundant exact relation is stated explicitly for propagation.
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


def _balanced_integer_squares(n, total):
    """Minimum sum z_i^2 over n integers with sum total."""
    if n==0:
        return 0 if total==0 else 10**18
    q,r=divmod(total,n)
    return (n-r)*q*q + r*(q+1)*(q+1)


def _same_parity_group_bound(n, total, parity):
    """Minimum squares for n integers all congruent to parity mod 2."""
    if n==0:
        return 0 if total==0 else 10**18
    if (total-n*parity)&1:
        return 10**18
    zsum=(total-n*parity)//2
    return 4*_balanced_integer_squares(n,zsum)+4*parity*zsum+n*parity


def class_arithmetic(asum, cap):
    """Return (effective_cap, rigorous_min_even_energy) for one sign-sum class."""
    m=(50-asum)//2  # negatives among full even positions; s0 is fixed +
    if not 0<=m<=49:
        return -1,10**18
    target_d_sum=(asum*asum-100)//4
    # Because exactly m of the 49 d_r=C_{2r}/2 are odd, even energy
    # 4*sum d_r^2 has residue 4m (mod 8). Tighten the requested cap to the
    # largest attainable energy residue at or below it.
    residue=4*(m&1)
    effective=cap-((cap-residue)%8)
    best=10**18
    # Split the required d-sum between the m odd and 49-m even integers.
    # A modest finite range is more than enough: any value relevant to cap<=528
    # has |d|<=11; this wider range keeps the helper general for our use here.
    for odd_sum in range(-600,601):
        v=_same_parity_group_bound(m,odd_sum,1)
        v+=_same_parity_group_bound(49-m,target_d_sum-odd_sum,0)
        if v<best: best=v
    return effective,4*best


def build(target=574, smoke=False, asum=None):
    model=cp_model.CpModel()
    x=[model.NewBoolVar(f'x{i}') for i in range(N)]  # 0=+1, 1=-1
    model.Add(x[0]==0)
    model.Add(x[1]==0)  # alternating-sign symmetry preserves direct near-skew
    for p in range(1,50):
        q=100-p
        if p&1: model.Add(x[q] != x[p])
        else:   model.Add(x[q] == x[p])

    model.Add(50 - 2*sum(x[1::2]) == 0)
    a=model.NewIntVar(-50,50,'a_even_half_sum')
    model.Add(a == 50 - 2*sum(x[0::2]))
    aa=model.NewIntVar(0,400,'a2')
    model.AddAllowedAssignments([a,aa],[(v,v*v) for v in range(-20,21,2)])
    if asum is not None:
        model.Add(a==asum)

    raw_cap=target-50
    cap=raw_cap
    arithmetic_lb=None
    if asum is not None:
        cap,arithmetic_lb=class_arithmetic(asum,raw_cap)
        if cap<0 or arithmetic_lb>cap:
            # Deliberately leave a tiny contradictory model. This is a strict
            # arithmetic exclusion, not a solver timeout conclusion.
            model.Add(0==1)

    even_corr=[]
    qvars=[]
    for k in range(2,N,2):
        L=N-k
        z=[]
        for i in range(L):
            v=model.NewBoolVar(f'z_{i}_{k}')
            model.AddBoolXOr([x[i],x[i+k],v.Not()])
            z.append(v)
        mism=model.NewIntVar(0,L,f'm{k}')
        model.Add(mism==sum(z))
        c=model.NewIntVar(-L,L,f'c{k}')
        model.Add(c==L-2*mism)

        # Exact near-skew residue: c = 4h + 2*x[k]. When s_k=+1 (x=0),
        # c is 0 mod 4; when s_k=-1, c is 2 mod 4.
        h=model.NewIntVar(-L,L,f'h{k}')
        model.Add(c == 4*h + 2*x[k])

        q=model.NewIntVar(0,raw_cap,f'q{k}')
        model.AddAllowedAssignments([c,q],[(cc,cc*cc) for cc in range(-L,L+1,2) if cc*cc<=raw_cap])
        even_corr.append(c);qvars.append(q)

    model.Add(sum(qvars) <= cap)
    model.Add(2*sum(even_corr) == aa-100)

    if smoke:
        for i,ch in enumerate(INC): model.Add(x[i] == (1 if ch=='-' else 0))
    else:
        for i,ch in enumerate(INC): model.AddHint(x[i],1 if ch=='-' else 0)
    return model,x,cap,arithmetic_lb


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
    model,x,cap,arithmetic_lb=build(args.target,args.smoke,args.asum)
    print('CLASS','asum',args.asum,'raw_even_cap',args.target-50,'effective_even_cap',cap,'arithmetic_lb',arithmetic_lb)
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
        e,o,cs=exact(seq)
        aa=sum(1 if seq[i]=='+' else -1 for i in range(0,N,2))
        b=sum(1 if seq[i]=='+' else -1 for i in range(1,N,2))
        print('FOUND energy',e,'odd',o,'even',e-o,'asum',aa,'bsum',b,'nss',direct_nss(seq),'seq',seq)
        if not direct_nss(seq) or o!=50 or e>args.target: raise SystemExit('exact validation failed')
    else:
        print('NO_CERTIFICATE')

if __name__=='__main__': main()
