#!/usr/bin/env python3
"""Joint order-25/order-10 compressed model for the last low11 h20 shards.

This strengthens oddperfect_low11_compressed_h0_cpsat.py in two ways:

1. It keeps the exact lag-0 cross equation sum_i p_i c_i = 0.
2. It does NOT collapse the 95,420 exact order-10 profiles to only 9,450
   coarse (mod-5 sums + low-count) keys.  Instead it retains the ten A and ten
   B residue sums from an exact order-10 profile and couples them to the
   order-25 compression through the exact fibre-lift criterion.

For p_i=(A_i+A_{i+25})/2, in residue class r mod 5 let

    f_r = sum p_i,   z_r = #{i : p_i=0}.

If the order-10 A residue sums are s_r,s_{r+5}, then a binary lift exists in
that class iff

    s_r+s_{r+5} = 2 f_r,
    d=(s_r-s_{r+5})/2 satisfies |d|<=z_r and d == z_r (mod 2).

The five classes are independent, so these local conditions are exact for the
order-10 fibre.  The same condition is applied to q, using c=x^13 q.

UNKNOWN is never an exclusion. FEASIBLE output is independently checked against
all compressed cyclic equations before being emitted.
"""
from __future__ import annotations
import argparse, json, sys
from ortools.sat.python import cp_model

N=25
MASK=(1<<26)-1
ODD=(-5,-3,-1,1,3,5)


def decode10(code:int):
    out=[]
    for _ in range(10):
        out.append(-5+2*(code%6)); code//=6
    return out


def low_counts_from_R(R):
    vals=[0]*6
    x=132-R[0]
    if x%8: return None
    vals[0]=x//8
    x=36-R[5]
    if x%8: return None
    vals[5]=x//8
    for q in range(1,5):
        x=40-R[q]
        if x%4: return None
        vals[q]=x//4
    caps=(2,5,5,5,5,2)
    if any(vals[q]<0 or vals[q]>caps[q] for q in range(6)): return None
    if sum(vals)!=11: return None
    return vals


def load_profile_rows(path:str):
    rows=set()
    with open(path) as f:
        for line in f:
            if not line.strip(): continue
            z,*R=map(int,line.split())
            if len(R)!=6: raise ValueError('bad profile row')
            aa=decode10(z&MASK); bb=decode10(z>>26)
            ns=low_counts_from_R(R)
            if ns is None: continue
            rows.add(tuple(aa+bb+ns))
    return [list(r) for r in sorted(rows)]


def fibre_triples():
    out=[]
    for x in ODD:
        for y in ODD:
            d=(x-y)//2
            for z in range(6):
                if abs(d)<=z and ((d-z)&1)==0:
                    out.append([x,y,z])
    return out


def cat10(r:int)->int:
    q=r%10
    return min(q,10-q)


def build(kp:int, profiles:str, overlap:int|None=None):
    if kp not in (12,14): raise ValueError('kp must be 12 or 14')
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
    m.Add(sum(ps)==kp); m.Add(sum(cs)==kc)
    m.Add(sum(u)==10); m.Add(sum(v)==10)
    m.Add(sum(dot)==0)
    if overlap is not None:
        if overlap<0 or overlap>min(kp,kc) or overlap%2:
            raise ValueError('overlap must be even and within support sizes')
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
        m.Add(sum(pu)==gu); m.Add(sum(pv)==gu)
        G.append(gu)
    m.Add(sum(G)==37)

    low={r:m.NewBoolVar(f'low{r}') for r in range(1,25)}
    m.Add(sum(low.values())==11)
    for r in range(1,13):
        m.Add(G[r-1]==4-low[r]-low[25-r])
    caps=(2,5,5,5,5,2)
    ns=[]
    for q in range(6):
        nv=m.NewIntVar(0,caps[q],f'n{q}')
        m.Add(nv==sum(low[r] for r in range(1,25) if cat10(r)==q))
        ns.append(nv)

    aa=[m.NewIntVar(-5,5,f'Ares{i}') for i in range(10)]
    bb=[m.NewIntVar(-5,5,f'Bres{i}') for i in range(10)]
    rows=load_profile_rows(profiles)
    if not rows: raise ValueError('empty order10 profile table')
    m.AddAllowedAssignments(aa+bb+ns,rows)

    triples=fibre_triples()
    za=[]; zb=[]
    for r in range(5):
        zpa=m.NewIntVar(0,5,f'za{r}')
        g=(r+3)%5  # q class r corresponds to c class r+3 because c=x^13 q.
        zqb=m.NewIntVar(0,5,f'zb{r}')
        m.Add(zpa==5-sum(ps[i] for i in range(N) if i%5==r))
        m.Add(zqb==5-sum(cs[i] for i in range(N) if i%5==g))
        # Sum condition is exact for the compressed nonzero pairs.
        m.Add(aa[r]+aa[r+5]==sum(u[i]+v[i] for i in range(N) if i%5==r))
        m.Add(bb[r]+bb[r+5]==sum(u[i]-v[i] for i in range(N) if i%5==g))
        # Difference condition is exact for orientations of zero compressed pairs.
        m.AddAllowedAssignments([aa[r],aa[r+5],zpa],triples)
        m.AddAllowedAssignments([bb[r],bb[r+5],zqb],triples)
        za.append(zpa); zb.append(zqb)
    m.Add(sum(za)==25-kp)
    m.Add(sum(zb)==25-kc)
    return m,u,v,G,aa,bb,ns,za,zb,len(rows)


def compressed_check(p,c,kp):
    if len(p)!=25 or len(c)!=25: return False,{}
    if any(x not in (-1,0,1) for x in p+c): return False,{}
    if sum(p)!=10 or sum(c)!=0: return False,{}
    if sum(x*x for x in p)!=kp or sum(x*x for x in c)!=26-kp: return False,{}
    H=[]; G=[]
    for r in range(25):
        H.append(sum(p[i]*c[(i-r)%25]+c[i]*p[(i-r)%25] for i in range(25)))
    for r in range(1,13):
        G.append(sum(p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25] for i in range(25)))
    ok=all(x==0 for x in H) and all(2<=x<=4 for x in G) and sum(G)==37
    return ok,{'H':H,'G':G,'overlap':sum(p[i]!=0 and c[i]!=0 for i in range(25)),
               'dot':sum(p[i]*c[i] for i in range(25))}


def fibre_check_from_profile(p,c,aa,bb):
    # Independent arithmetic check of the local order10 lifting criteria.
    for r in range(5):
        inds=[i for i in range(25) if i%5==r]
        f=sum(p[i] for i in inds); z=sum(p[i]==0 for i in inds)
        if aa[r]+aa[r+5] != 2*f: return False
        d=(aa[r]-aa[r+5])//2
        if abs(d)>z or ((d-z)&1): return False
        g=(r+3)%5; inds=[i for i in range(25) if i%5==g]
        f=sum(c[i] for i in inds); z=sum(c[i]==0 for i in inds)
        if bb[r]+bb[r+5] != 2*f: return False
        d=(bb[r]-bb[r+5])//2
        if abs(d)>z or ((d-z)&1): return False
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--kp',type=int,required=True,choices=[12,14])
    ap.add_argument('--profiles',required=True)
    ap.add_argument('--overlap',type=int)
    ap.add_argument('--seconds',type=float,default=120)
    ap.add_argument('--workers',type=int,default=1)
    ap.add_argument('--seed',type=int,default=1)
    args=ap.parse_args()
    model,u,v,G,aa,bb,ns,za,zb,nrows=build(args.kp,args.profiles,args.overlap)
    err=model.Validate()
    if err: raise SystemExit('MODEL_INVALID '+err)
    s=cp_model.CpSolver()
    s.parameters.max_time_in_seconds=args.seconds
    s.parameters.num_search_workers=args.workers
    s.parameters.random_seed=args.seed
    s.parameters.randomize_search=True
    s.parameters.cp_model_presolve=True
    s.parameters.symmetry_level=2
    st=s.Solve(model)
    out={'kp':args.kp,'kc':26-args.kp,'overlap_shard':args.overlap,
         'profile_rows':nrows,'status':s.StatusName(st),'wall_time':s.WallTime(),
         'branches':s.NumBranches(),'conflicts':s.NumConflicts(),'workers':args.workers}
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        uu=[s.Value(x) for x in u]; vv=[s.Value(x) for x in v]
        p=[(uu[i]+vv[i])//2 for i in range(25)]
        c=[(uu[i]-vv[i])//2 for i in range(25)]
        aaa=[s.Value(x) for x in aa]; bbb=[s.Value(x) for x in bb]
        ok,detail=compressed_check(p,c,args.kp)
        ok=ok and fibre_check_from_profile(p,c,aaa,bbb)
        if args.overlap is not None: ok=ok and detail.get('overlap')==args.overlap
        out.update(independent_check=ok,p=p,c=c,G=detail.get('G'),
                   actual_overlap=detail.get('overlap'),dot=detail.get('dot'),
                   Ares=aaa,Bres=bbb,low_counts=[s.Value(x) for x in ns],
                   za=[s.Value(x) for x in za],zb=[s.Value(x) for x in zb])
        print(json.dumps(out,sort_keys=True),flush=True)
        return 0 if ok else 3
    print(json.dumps(out,sort_keys=True),flush=True)
    return 0 if st==cp_model.INFEASIBLE else 2


if __name__=='__main__': sys.exit(main())
