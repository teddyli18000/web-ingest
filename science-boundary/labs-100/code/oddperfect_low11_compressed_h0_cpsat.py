#!/usr/bin/env python3
"""Strengthened compressed low11 model with the missing zero-lag homometry.

The remaining h20 low11 order-25 branches have p,c in {-1,0,1}^25 with
sum p=10, sum c=0, kp+kc=26, and cyclic cross equation

    p c* + c p* = 0.

With u=p+c and v=p-c this is PAF_u=PAF_v at *all* cyclic lags.
The earlier compressed model imposed lags 1..12 but did not explicitly impose
lag 0.  Lag 0 is

    ||u||^2 = ||v||^2  <=>  sum_i p_i c_i = 0.

Because p_i c_i is in {-1,0,1}, this also implies that the support overlap is
even and contains equally many same-sign and opposite-sign overlaps.  This
model adds that exact condition and optionally shards on the overlap size.

UNKNOWN is never an exclusion. Any FEASIBLE result is independently checked
against every original compressed cyclic equation before it is emitted.
"""
from __future__ import annotations
import argparse, json, sys
from ortools.sat.python import cp_model

N=25
MASK=(1<<26)-1


def decode10(code:int):
    out=[]
    for _ in range(10):
        out.append(-5+2*(code%6)); code//=6
    return out


def load_keys(path:str):
    rows=set()
    with open(path) as f:
        for line in f:
            if not line.strip():
                continue
            z,*rv=map(int,line.split())
            if len(rv)!=6:
                raise ValueError('bad profile row')
            aa=decode10(z&MASK); bb=decode10(z>>26)
            a=tuple(aa[r]+aa[r+5] for r in range(5))
            b=tuple(bb[r]+bb[r+5] for r in range(5))
            R=rv
            vals=[0]*6
            x=132-R[0]
            if x%8:
                continue
            vals[0]=x//8
            x=36-R[5]
            if x%8:
                continue
            vals[5]=x//8
            ok=True
            for q in range(1,5):
                x=40-R[q]
                if x%4:
                    ok=False; break
                vals[q]=x//4
            if not ok:
                continue
            caps=(2,5,5,5,5,2)
            if any(vals[q]<0 or vals[q]>caps[q] for q in range(6)):
                continue
            if sum(vals)!=11:
                continue
            rows.add(a+b+tuple(vals))
    return [list(r) for r in sorted(rows)]


def cat10(r:int)->int:
    q=r%10
    return min(q,10-q)


def build(kp:int, profiles:str, overlap:int|None=None):
    if kp not in (12,14):
        raise ValueError('kp must be 12 or 14')
    kc=26-kp
    m=cp_model.CpModel()
    u=[m.NewIntVar(-2,2,f'u{i}') for i in range(N)]
    v=[m.NewIntVar(-2,2,f'v{i}') for i in range(N)]
    ps=[m.NewBoolVar(f'ps{i}') for i in range(N)]
    cs=[m.NewBoolVar(f'cs{i}') for i in range(N)]
    dot=[m.NewIntVar(-1,1,f'dot{i}') for i in range(N)]
    ov=[m.NewBoolVar(f'ov{i}') for i in range(N)]

    legal=[]
    for p in (-1,0,1):
        for c in (-1,0,1):
            legal.append([p+c,p-c,int(p!=0),int(c!=0),p*c,int(p!=0 and c!=0)])
    for i in range(N):
        m.AddAllowedAssignments([u[i],v[i],ps[i],cs[i],dot[i],ov[i]],legal)

    m.Add(sum(ps)==kp)
    m.Add(sum(cs)==kc)
    m.Add(sum(u)==10)
    m.Add(sum(v)==10)

    # Exact lag-0 cross equation. This was absent in the first compressed model.
    m.Add(sum(dot)==0)
    if overlap is not None:
        if overlap<0 or overlap>min(kp,kc) or overlap%2:
            raise ValueError('overlap must be even and between 0 and min(kp,kc)')
        m.Add(sum(ov)==overlap)

    G=[]
    for r in range(1,13):
        gu=m.NewIntVar(2,4,f'G{r}')
        pu=[]; pv=[]
        for i in range(N):
            j=(i+r)%N
            xu=m.NewIntVar(-4,4,f'pu_{r}_{i}')
            xv=m.NewIntVar(-4,4,f'pv_{r}_{i}')
            m.AddMultiplicationEquality(xu,[u[i],u[j]])
            m.AddMultiplicationEquality(xv,[v[i],v[j]])
            pu.append(xu); pv.append(xv)
        m.Add(sum(pu)==gu)
        m.Add(sum(pv)==gu)
        G.append(gu)
    m.Add(sum(G)==37)

    low={r:m.NewBoolVar(f'low{r}') for r in range(1,25)}
    m.Add(sum(low.values())==11)
    for r in range(1,13):
        m.Add(G[r-1]==4-low[r]-low[25-r])

    a=[]; b=[]
    for r in range(5):
        av=m.NewIntVar(-10,10,f'a{r}')
        bv=m.NewIntVar(-10,10,f'b{r}')
        m.Add(av==sum(u[i]+v[i] for i in range(N) if i%5==r))
        g=(r+3)%5  # c=x^13 q, so q class r is c class r+3 mod 5.
        m.Add(bv==sum(u[i]-v[i] for i in range(N) if i%5==g))
        a.append(av); b.append(bv)

    caps=(2,5,5,5,5,2)
    ns=[]
    for q in range(6):
        nv=m.NewIntVar(0,caps[q],f'n{q}')
        m.Add(nv==sum(low[r] for r in range(1,25) if cat10(r)==q))
        ns.append(nv)

    rows=load_keys(profiles)
    if len(rows)!=9450:
        raise ValueError(f'expected 9450 projected keys, got {len(rows)}')
    m.AddAllowedAssignments(a+b+ns,rows)
    return m,u,v,G,a,b,ns,dot,ov,len(rows)


def compressed_check(p,c,kp):
    if len(p)!=25 or len(c)!=25:
        return False,{}
    if any(x not in (-1,0,1) for x in p+c):
        return False,{}
    if sum(p)!=10 or sum(c)!=0:
        return False,{}
    if sum(x*x for x in p)!=kp or sum(x*x for x in c)!=26-kp:
        return False,{}
    H=[]; G=[]
    for r in range(25):
        h=sum(p[i]*c[(i-r)%25]+c[i]*p[(i-r)%25] for i in range(25))
        H.append(h)
    for r in range(1,13):
        G.append(sum(p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25] for i in range(25)))
    ok=all(x==0 for x in H) and all(2<=x<=4 for x in G) and sum(G)==37
    return ok,{'H':H,'G':G,'overlap':sum(p[i]!=0 and c[i]!=0 for i in range(25)),
               'dot':sum(p[i]*c[i] for i in range(25))}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--kp',type=int,required=True,choices=[12,14])
    ap.add_argument('--profiles',required=True)
    ap.add_argument('--overlap',type=int)
    ap.add_argument('--seconds',type=float,default=120)
    ap.add_argument('--workers',type=int,default=1)
    ap.add_argument('--seed',type=int,default=1)
    args=ap.parse_args()

    model,u,v,G,a,b,ns,dot,ov,nkeys=build(args.kp,args.profiles,args.overlap)
    err=model.Validate()
    if err:
        raise SystemExit('MODEL_INVALID '+err)
    s=cp_model.CpSolver()
    s.parameters.max_time_in_seconds=args.seconds
    s.parameters.num_search_workers=args.workers
    s.parameters.random_seed=args.seed
    s.parameters.randomize_search=True
    s.parameters.cp_model_presolve=True
    s.parameters.symmetry_level=2
    st=s.Solve(model)
    out={'kp':args.kp,'kc':26-args.kp,'overlap_shard':args.overlap,
         'projected_keys':nkeys,'status':s.StatusName(st),'wall_time':s.WallTime(),
         'branches':s.NumBranches(),'conflicts':s.NumConflicts(),'workers':args.workers}
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        uu=[s.Value(x) for x in u]; vv=[s.Value(x) for x in v]
        p=[(uu[i]+vv[i])//2 for i in range(25)]
        c=[(uu[i]-vv[i])//2 for i in range(25)]
        ok,detail=compressed_check(p,c,args.kp)
        got_overlap=detail.get('overlap')
        if args.overlap is not None:
            ok=ok and got_overlap==args.overlap
        out.update(independent_check=ok,p=p,c=c,G=detail.get('G'),
                   actual_overlap=got_overlap,dot=detail.get('dot'),
                   a=[s.Value(x) for x in a],b=[s.Value(x) for x in b],
                   low_counts=[s.Value(x) for x in ns])
        print(json.dumps(out,sort_keys=True),flush=True)
        return 0 if ok else 3
    print(json.dumps(out,sort_keys=True),flush=True)
    return 0 if st==cp_model.INFEASIBLE else 2


if __name__=='__main__':
    sys.exit(main())
