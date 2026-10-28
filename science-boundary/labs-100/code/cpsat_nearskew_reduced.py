#!/usr/bin/env python3
"""Reduced exact CP-SAT model for N=100 direct near-skew LABS target.

Normalize s0=s1=+1 using global sign and alternating-sign symmetry.  Positions
1..99 form a length-99 skew tail.  Let y_v encode s_{v+1} for v=0..49;
positions 51..99 are reflected copies, so only 49 Boolean degrees of freedom
remain after fixing y_0=0.

For r=1..49 the direct skew identity gives

  C_{2r}(s) = s_{2r} + (-1)^r
               + 2 * sum_{i=0}^{48-r} s_{i+1}s_{i+2r+1}.

Thus d_r=C_{2r}/2 is an affine sum of pairwise XORs of the 50 tail variables.
Odd-lag energy is identically 50, so E<=574 is exactly sum d_r^2<=131,
with a tighter per-class cap from the known energy residue mod 8.
"""
import argparse, time
from ortools.sat.python import cp_model

N=100
INC="++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-"


def exact(seq):
    s=[1 if c=='+' else -1 for c in seq]
    cs=[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
    e=sum(c*c for c in cs)
    o=sum(cs[k-1]**2 for k in range(1,N,2))
    return e,o,cs


def direct_nss(seq):
    s=[1 if c=='+' else -1 for c in seq]
    return all(s[p]*s[100-p] == (-1 if p&1 else 1) for p in range(1,50))


def sign_ref(p):
    """Return (free-index, factor) for s_p=factor*(1-2*y[index])."""
    if p==0:
        return None,1
    if p<=50:
        return p-1,1
    q=100-p
    return q-1,(-1 if q&1 else 1)


def linear_sign_terms(p):
    idx,f=sign_ref(p)
    if idx is None:
        return f,{}
    return f,{idx:-2*f}


def class_cap(asum, raw_even_cap):
    m=(50-asum)//2
    residue=4*(m&1)
    rem=(raw_even_cap-residue)%8
    return raw_even_cap-rem


def build(asum, target=574, smoke=False):
    if asum%2 or not -20<=asum<=20:
        raise ValueError('asum must be even in [-20,20]')
    model=cp_model.CpModel()
    # y_v=1 means s_{v+1}=-1 for direct positions 1..50.
    y=[model.NewBoolVar(f'y{v}') for v in range(50)]
    model.Add(y[0]==0)  # s1=+1 by alternating-sign symmetry.

    # Fixed even-position half sum a.  Use sign_ref so reflected even positions
    # are handled identically to the correlation equations.
    const=0; coeff={}
    for p in range(0,100,2):
        c,t=linear_sign_terms(p); const+=c
        for j,v in t.items(): coeff[j]=coeff.get(j,0)+v
    model.Add(const + sum(v*y[j] for j,v in coeff.items()) == asum)

    raw_even_cap=target-50
    even_cap=class_cap(asum,raw_even_cap)
    qcap=even_cap//4
    # Pure arithmetic exclusion already proved independently.
    if asum in (-20,20):
        model.Add(0==1)

    xor_cache={}
    def product_linear(p,q):
        """Return (constant, {bool-index:coef}) for sign product s_p*s_q.

        The dictionary keys are either ('y',i) or ('z',a,b).  XOR variables
        are cached globally because the same free-variable product can recur.
        """
        ia,fa=sign_ref(p); ib,fb=sign_ref(q); factor=fa*fb
        if ia is None and ib is None:
            return factor,{}
        if ia is None:
            return factor,{('y',ib):-2*factor}
        if ib is None:
            return factor,{('y',ia):-2*factor}
        if ia==ib:
            return factor,{}
        a,b=sorted((ia,ib))
        key=(a,b)
        if key not in xor_cache:
            z=model.NewBoolVar(f'z_{a}_{b}')
            # z = y[a] XOR y[b].
            model.AddBoolXOr([y[a],y[b],z.Not()])
            xor_cache[key]=z
        return factor,{('z',a,b):-2*factor}

    dvars=[]; qvars=[]
    for r in range(1,50):
        k=2*r
        c0=0; terms={}
        # Sum paired tail products.
        for i in range(0,49-r):
            c,t=product_linear(i+1,i+k+1); c0+=c
            for key,v in t.items(): terms[key]=terms.get(key,0)+v
        # Boundary term (s_{2r}+(-1)^r)/2.
        idx,f=sign_ref(k)
        parity=-1 if r&1 else 1
        if idx is None:
            c0+=(f+parity)//2
        else:
            # f*(1-2y)+parity, divided by 2.
            c0+=(f+parity)//2
            terms[('y',idx)]=terms.get(('y',idx),0)-f

        d=model.NewIntVar(-11,11,f'd{r}')
        expr=c0
        for key,v in terms.items():
            if key[0]=='y': expr += v*y[key[1]]
            else: expr += v*xor_cache[(key[1],key[2])]
        model.Add(d==expr)

        # Exact residue C_{2r}=2d == 1-s_{2r} mod 4: d parity equals the
        # indicator that s_{2r} is negative.
        idx,f=sign_ref(k)
        neg = y[idx] if f==1 else 1-y[idx]
        h=model.NewIntVar(-6,6,f'h{r}')
        model.Add(d == 2*h + neg)

        q=model.NewIntVar(0,qcap,f'q{r}')
        model.AddAllowedAssignments([d,q],[(v,v*v) for v in range(-11,12) if v*v<=qcap])
        dvars.append(d);qvars.append(q)

    model.Add(sum(qvars)<=qcap)
    model.Add(sum(dvars)==(asum*asum-100)//4)

    if smoke:
        # Pin every free direct tail coordinate to the incumbent.
        for v in range(50): model.Add(y[v] == (1 if INC[v+1]=='-' else 0))
    else:
        for v in range(50): model.AddHint(y[v],1 if INC[v+1]=='-' else 0)
    return model,y,dvars,even_cap,len(xor_cache)


def reconstruct(solver,y):
    s=[0]*100;s[0]=1
    for p in range(1,51): s[p]=-1 if solver.Value(y[p-1]) else 1
    for p in range(51,100):
        q=100-p;s[p]=(-1 if q&1 else 1)*s[q]
    return ''.join('+' if v>0 else '-' for v in s)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--asum',type=int,required=True)
    ap.add_argument('--target',type=int,default=574)
    ap.add_argument('--seconds',type=float,default=240)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--smoke',action='store_true')
    args=ap.parse_args()
    ie,io,_=exact(INC);assert (ie,io)==(578,50) and direct_nss(INC)
    model,y,dvars,cap,nxor=build(args.asum,args.target,args.smoke)
    print('MODEL asum',args.asum,'even_cap',cap,'scaled_cap',cap//4,'free_bool',49,'xor_bool',nxor)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.seconds
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=args.seed
    solver.parameters.cp_model_presolve=True
    solver.parameters.symmetry_level=2
    solver.parameters.log_search_progress=True
    t=time.time();status=solver.Solve(model);wall=time.time()-t
    print('STATUS',solver.StatusName(status),'asum',args.asum,'wall',wall,'conflicts',solver.NumConflicts(),'branches',solver.NumBranches())
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        seq=reconstruct(solver,y);e,o,cs=exact(seq)
        a=sum(1 if seq[p]=='+' else -1 for p in range(0,100,2))
        print('FOUND energy',e,'odd',o,'even',e-o,'asum',a,'nss',direct_nss(seq),'seq',seq)
        # Cross-check each reduced d variable against independently rescored C.
        for r,d in enumerate(dvars,1):
            if solver.Value(d)*2 != cs[2*r-1]: raise SystemExit(f'd mismatch at {r}')
        if not direct_nss(seq) or o!=50 or e>args.target or a!=args.asum:
            raise SystemExit('independent validation failed')
    else:
        print('NO_CERTIFICATE')

if __name__=='__main__': main()
