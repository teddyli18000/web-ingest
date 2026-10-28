#!/usr/bin/env python3
"""Generic exact CP-SAT feasibility model for a fixed low odd-energy LABS-100 layer.

Odd correlations are paired as (C_k,C_{100-k}), k=1,3,...,49. Every pair
has energy 2+8d and sum 4t. If O=50+8D then sum d=D; if the even/odd
position half sums are a,b then sum t=ab/4. The model fixes D,a,b and searches
for total LABS energy <= target, with exact product/energy mod-8 propagation.
"""
from __future__ import annotations
import argparse, time
from ortools.sat.python import cp_model
N=100
SMOKE74="+++++----+---++++-+++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--++--+---+-++-+++-+--+"

def exact(seq):
    s=[1 if c=='+' else -1 for c in seq]
    cs=[0]+[sum(s[i]*s[i+k] for i in range(N-k)) for k in range(1,N)]
    E=sum(c*c for c in cs[1:]); O=sum(cs[k]*cs[k] for k in range(1,N,2))
    a=sum(s[0::2]); b=sum(s[1::2]); p=1
    for v in s:p*=v
    return E,O,cs,a,b,p

def sq_table(model,v,name,lo,hi):
    q=model.NewIntVar(0,max(lo*lo,hi*hi),name)
    model.AddAllowedAssignments([v,q],[(z,z*z) for z in range(lo,hi+1)])
    return q

def odd_rows(k,D):
    rows=[]
    for x in range(-(N-k),N-k+1,2):
        for y in range(-k,k+1,2):
            if (x+y)%4: continue
            pe=x*x+y*y
            if pe<2 or (pe-2)%8: continue
            d=(pe-2)//8
            if 0<=d<=D:
                rows.append((x,y,d,(x+y)//4))
    return rows

def build(D,a,b,target,product='any',fix_seq=None):
    O=50+8*D; budget=target-O
    if D<0 or budget<0: raise ValueError('invalid D/target')
    if a%2 or b%2 or not(-50<=a<=50 and -50<=b<=50): raise ValueError('bad half sums')
    if (a*b)%4: raise ValueError('ab must be divisible by 4')
    m=cp_model.CpModel(); x=[m.NewBoolVar(f'x{i}') for i in range(N)]
    m.Add(50-2*sum(x[0::2])==a); m.Add(50-2*sum(x[1::2])==b)
    corr={}; evenq=[]; evenc=[]
    for k in range(1,N):
        L=N-k; z=[]
        for i in range(L):
            q=m.NewBoolVar(f'z_{k}_{i}')
            m.AddBoolXOr([x[i],x[i+k],q.Not()]); z.append(q)
        mm=m.NewIntVar(0,L,f'm{k}'); m.Add(mm==sum(z))
        c=m.NewIntVar(-L,L,f'c{k}'); m.Add(c==L-2*mm); corr[k]=c
        if k%2==0:
            qq=m.NewIntVar(0,budget,f'q{k}')
            rows=[(v,v*v) for v in range(-L,L+1,2) if v*v<=budget]
            m.AddAllowedAssignments([c,qq],rows); evenq.append(qq); evenc.append(c)
    ds=[]; ts=[]
    for k in range(1,50,2):
        d=m.NewIntVar(0,D,f'd{k}'); t=m.NewIntVar(-D-1,D+1,f't{k}')
        m.AddAllowedAssignments([corr[k],corr[N-k],d,t],odd_rows(k,D))
        ds.append(d); ts.append(t)
    m.Add(sum(ds)==D); m.Add(sum(ts)==a*b//4)
    qsum=m.NewIntVar(0,budget,'qsum'); m.Add(qsum==sum(evenq))
    # Exact N=100 congruence: sign product +1 -> even energy 4 mod 8;
    # sign product -1 -> even energy 0 mod 8.
    negpar=m.NewIntVar(0,1,'negpar'); m.AddModuloEquality(negpar,sum(x),2)
    qmod=m.NewIntVar(0,7,'qmod'); m.AddModuloEquality(qmod,qsum,8)
    m.AddAllowedAssignments([negpar,qmod],[(0,4),(1,0)])
    if product=='+': m.Add(negpar==0)
    elif product=='-': m.Add(negpar==1)
    elif product!='any': raise ValueError('bad product')
    m.Add(sum(evenc)==(a*a+b*b-100)//2)
    # Redundant z=i Fourier identity.
    aa=m.NewIntVar(-50,50,'a_alt'); bb=m.NewIntVar(-50,50,'b_alt')
    m.Add(aa==sum((1 if j%2==0 else -1)*(1-2*x[2*j]) for j in range(50)))
    m.Add(bb==sum((1 if j%2==0 else -1)*(1-2*x[2*j+1]) for j in range(50)))
    aa2=sq_table(m,aa,'aa2',-50,50); bb2=sq_table(m,bb,'bb2',-50,50)
    alt=sum((1 if r%2==0 else -1)*corr[2*r] for r in range(1,50))
    m.Add(aa2+bb2==100+2*alt)
    if fix_seq is not None:
        if len(fix_seq)!=100: raise ValueError('fix sequence length')
        for v,ch in zip(x,fix_seq): m.Add(v==(0 if ch=='+' else 1))
    return m,x

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--D',type=int,required=True)
    ap.add_argument('--asum',type=int,required=True); ap.add_argument('--bsum',type=int,required=True)
    ap.add_argument('--target',type=int,default=574); ap.add_argument('--product',choices=['any','+','-'],default='any')
    ap.add_argument('--seconds',type=float,default=600); ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--seed',type=int,default=1); ap.add_argument('--smoke74',action='store_true')
    args=ap.parse_args(); fix=SMOKE74 if args.smoke74 else None
    if args.smoke74:
        E,O,cs,a,b,p=exact(SMOKE74)
        print(f'SMOKE E={E} O={O} a={a} b={b} product={p}')
        if (E,O,a,b,p)!=(39766,74,2,2,1): raise SystemExit('smoke mismatch')
    model,x=build(args.D,args.asum,args.bsum,args.target,args.product,fix)
    err=model.Validate()
    if err: raise SystemExit('MODEL_INVALID '+err)
    s=cp_model.CpSolver(); s.parameters.max_time_in_seconds=args.seconds; s.parameters.num_search_workers=args.workers
    s.parameters.random_seed=args.seed; s.parameters.randomize_search=True; s.parameters.cp_model_presolve=True; s.parameters.symmetry_level=2
    t=time.time(); status=s.Solve(model)
    print('STATUS',s.StatusName(status),f'wall={time.time()-t:.3f}',f'branches={s.NumBranches()}',f'conflicts={s.NumConflicts()}')
    if status==cp_model.INFEASIBLE: print('PROVED_INFEASIBLE'); return
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL): print('UNRESOLVED'); return
    seq=''.join('-' if s.Value(v) else '+' for v in x); E,O,cs,a,b,p=exact(seq)
    print(f'FOUND E={E} O={O} a={a} b={b} product={p} seq={seq}')
    if E>args.target or O!=50+8*args.D or a!=args.asum or b!=args.bsum: raise SystemExit('exact recheck failed')
    if args.product=='+' and p!=1: raise SystemExit('product recheck failed')
    if args.product=='-' and p!=-1: raise SystemExit('product recheck failed')
if __name__=='__main__': main()
