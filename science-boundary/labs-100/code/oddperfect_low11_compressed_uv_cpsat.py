#!/usr/bin/env python3
"""Compressed order-25 homometric model for the last low11 h20 shards.

The remaining W129-A / W131-A2 / W131-B1 cases all have

  p,c in {-1,0,1}^25, sum p=10, sum c=0,
  kp+kc=26,
  H=p c* + c p*=0,
  G_r=PAF_p(r)+PAF_c(r) in {2,3,4}, r=1..12, sum G=37.

Write u=p+c and v=p-c.  Then H=0 is exactly PAF_u=PAF_v.  Each coordinate
(u_i,v_i) has only nine legal states (coming from p_i,c_i in {-1,0,1}).
This model searches that 25-coordinate representation instead of the original
100 binary signs.

It also projects the exact low11 order-10 quotient table to a much smaller
necessary table on:
  a_r = 2 sum_{i == r (mod 5)} p_i,
  b_r = 2 sum_{i == r+3 (mod 5)} c_i,
and the six counts n_q of low (=1) periodic weights in the order-10 residue
classes.  The 95,420 exact full residue profiles collapse to 9,450 such keys.

Any FEASIBLE result is independently checked against the defining compressed
identities before being emitted.  UNKNOWN is never an exclusion.
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
            if not line.strip(): continue
            z,*rv=map(int,line.split())
            if len(rv)!=6: raise ValueError('bad profile row')
            aa=decode10(z&MASK); bb=decode10(z>>26)
            a=tuple(aa[r]+aa[r+5] for r in range(5))
            b=tuple(bb[r]+bb[r+5] for r in range(5))
            R=rv
            vals=[0]*6
            x=132-R[0]
            if x%8: continue
            vals[0]=x//8
            x=36-R[5]
            if x%8: continue
            vals[5]=x//8
            ok=True
            for q in range(1,5):
                x=40-R[q]
                if x%4: ok=False; break
                vals[q]=x//4
            if not ok: continue
            caps=(2,5,5,5,5,2)
            if any(vals[q]<0 or vals[q]>caps[q] for q in range(6)): continue
            if sum(vals)!=11: continue
            rows.add(a+b+tuple(vals))
    return [list(r) for r in sorted(rows)]

def cat10(r:int)->int:
    q=r%10
    return min(q,10-q)

def build(kp:int,profiles:str,state:int|None=None):
    if kp not in (12,14): raise ValueError('kp must be 12 or 14')
    kc=26-kp
    m=cp_model.CpModel()
    u=[m.NewIntVar(-2,2,f'u{i}') for i in range(N)]
    v=[m.NewIntVar(-2,2,f'v{i}') for i in range(N)]
    ps=[m.NewBoolVar(f'ps{i}') for i in range(N)]
    cs=[m.NewBoolVar(f'cs{i}') for i in range(N)]
    legal=[]
    for p in (-1,0,1):
        for c in (-1,0,1):
            legal.append([p+c,p-c,int(p!=0),int(c!=0)])
    for i in range(N): m.AddAllowedAssignments([u[i],v[i],ps[i],cs[i]],legal)
    if state is not None:
        if not 0 <= state < 9: raise ValueError('state must be 0..8')
        m.AddAllowedAssignments([u[0],v[0],ps[0],cs[0]],[legal[state]])
    m.Add(sum(ps)==kp); m.Add(sum(cs)==kc)
    m.Add(sum(u)==10); m.Add(sum(v)==10)

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

    a=[]; b=[]
    for r in range(5):
        av=m.NewIntVar(-10,10,f'a{r}')
        bv=m.NewIntVar(-10,10,f'b{r}')
        m.Add(av==sum(u[i]+v[i] for i in range(N) if i%5==r))
        g=(r+3)%5
        m.Add(bv==sum(u[i]-v[i] for i in range(N) if i%5==g))
        a.append(av); b.append(bv)
    caps=(2,5,5,5,5,2)
    ns=[]
    for q in range(6):
        nv=m.NewIntVar(0,caps[q],f'n{q}')
        m.Add(nv==sum(low[r] for r in range(1,25) if cat10(r)==q))
        ns.append(nv)
    rows=load_keys(profiles)
    if len(rows)!=9450: raise ValueError(f'expected 9450 projected keys, got {len(rows)}')
    m.AddAllowedAssignments(a+b+ns,rows)
    return m,u,v,G,a,b,ns,len(rows)

def compressed_check(p,c,kp):
    if len(p)!=25 or len(c)!=25: return False,{}
    if any(x not in (-1,0,1) for x in p+c): return False,{}
    if sum(p)!=10 or sum(c)!=0: return False,{}
    if sum(x*x for x in p)!=kp or sum(x*x for x in c)!=26-kp: return False,{}
    H=[]; G=[]
    for r in range(25):
        h=sum(p[i]*c[(i-r)%25]+c[i]*p[(i-r)%25] for i in range(25))
        H.append(h)
    for r in range(1,13):
        G.append(sum(p[i]*p[(i+r)%25]+c[i]*c[(i+r)%25] for i in range(25)))
    ok=all(x==0 for x in H) and all(2<=x<=4 for x in G) and sum(G)==37
    return ok,{'H':H,'G':G}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--kp',type=int,required=True,choices=[12,14])
    ap.add_argument('--profiles',required=True)
    ap.add_argument('--seconds',type=float,default=180)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--state',type=int)
    args=ap.parse_args()
    model,u,v,G,a,b,ns,nkeys=build(args.kp,args.profiles,args.state)
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
    out={'kp':args.kp,'kc':26-args.kp,'projected_keys':nkeys,'state':args.state,
         'status':s.StatusName(st),'wall_time':s.WallTime(),'branches':s.NumBranches(),
         'conflicts':s.NumConflicts(),'workers':args.workers}
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        uu=[s.Value(x) for x in u]; vv=[s.Value(x) for x in v]
        p=[(uu[i]+vv[i])//2 for i in range(25)]
        c=[(uu[i]-vv[i])//2 for i in range(25)]
        ok,detail=compressed_check(p,c,args.kp)
        out.update(independent_check=ok,p=p,c=c,G=detail.get('G'),
                   a=[s.Value(x) for x in a],b=[s.Value(x) for x in b],
                   low_counts=[s.Value(x) for x in ns])
        print(json.dumps(out,sort_keys=True),flush=True)
        return 0 if ok else 3
    print(json.dumps(out,sort_keys=True),flush=True)
    return 0 if st==cp_model.INFEASIBLE else 2
if __name__=='__main__': sys.exit(main())
