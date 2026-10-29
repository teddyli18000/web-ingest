"""LABS basin-geometry reproducibility experiment (N=24..100).
Dependencies: numpy, numba, pandas. Example:
 python geometry_repro.py --lengths 24 32 40 64 100 --bases 150 --seed 151619 --output sweep.csv.gz
 python geometry_repro.py --lengths 48 72 96 --bases 150 --seed 787898 --output holdout.csv.gz
 python geometry_repro.py --descent first --lengths 24 40 64 100 --bases 150 --seed 592104 --output first.csv.gz
 python geometry_repro.py --record --seed 68808 --output record.csv.gz
"""
import argparse, time
import numpy as np
import pandas as pd
from numba import njit

CERT='++++++--+++++-----++-++--+--++++++++++---+-++--++++-+--++----+--+-+-+-+-++---++---++-+-++-+-++--+-+-'
RADII=(2,4,6,8,10,12,16,20,24,32,40)

@njit
def cor(s):
 n=len(s); c=np.zeros(n,np.int32)
 for k in range(1,n):
  for i in range(n-k):c[k]+=s[i]*s[i+k]
 return c
@njit
def energy(s):
 c=cor(s);z=0
 for k in range(1,len(s)):z+=c[k]*c[k]
 return z
@njit
def delta(s,c,i):
 z=0;n=len(s)
 for k in range(1,n):
  v=0
  if i>=k:v+=s[i-k]
  if i+k<n:v+=s[i+k]
  v*=-2*s[i];z+=2*c[k]*v+v*v
 return z
@njit
def flip(s,c,i):
 n=len(s)
 for k in range(1,n):
  v=0
  if i>=k:v+=s[i-k]
  if i+k<n:v+=s[i+k]
  c[k]-=2*s[i]*v
 s[i]=-s[i]
@njit
def descend(s,method):
 s=s.copy();c=cor(s);e=energy(s);steps=0
 while True:
  best=0;idx=-1
  for i in range(len(s)):
   d=delta(s,c,i)
   if d<best:
    best=d;idx=i
    if method==1:break
  if idx<0:return s,e,steps
  flip(s,c,idx);e+=best;steps+=1
  if steps>5*len(s):raise RuntimeError('descending bound exceeded')
@njit
def canonical(s):
 n=len(s);best=np.empty(n,np.int8);first=True
 for rev in range(2):
  for neg in range(2):
   for alt in range(2):
    t=np.empty(n,np.int8)
    for i in range(n):
     v=s[n-1-i] if rev else s[i]
     t[i]=v*(-1 if neg else 1)*(-1 if alt and i%2 else 1)
    if first:best=t;first=False
    else:
     for i in range(n):
      if t[i]<best[i]:best=t;break
      if t[i]>best[i]:break
 return best

def selftest():
 rng=np.random.default_rng(122)
 for n in (8,24,40,64,100):
  for _ in range(50):
   s=rng.choice(np.array([-1,1],np.int8),n);c=cor(s);e=energy(s)
   for j in range(n):
    t=s.copy();t[j]*=-1
    assert delta(s,c,j)==energy(t)-e
    v=s.copy();w=c.copy();flip(v,w,j)
    assert energy(v)==energy(t) and np.array_equal(cor(v),w)
 assert len(CERT)==100
 # Exact mean single-spin barrier sum identity, valid at every sequence.
 for n in (12,24,40,64,100):
  for seed in range(30):
   s=np.array([1 if (i*i+seed*i+seed*seed)%13<6 else -1 for i in range(n)],dtype=np.int8)
   c=cor(s);e=energy(s)
   lhs=sum(delta(s,c,j) for j in range(n))
   rhs=4*n*(n-1)-8*e+8*sum(int(c[k]) for k in range(2,n,2))
   assert lhs==rhs
 s=np.array([1 if v=='+' else -1 for v in CERT],dtype=np.int8)
 assert energy(s)==578
 for method in (0,1):
  z,e,st=descend(s,method)
  assert e==578 and st==0
 print('PASS delta/flip vs independent exact correlation, official E100=578')

def sweep(args):
 rng=np.random.default_rng(args.seed);rows=[];tic=time.perf_counter()
 for n in args.lengths:
  ks=[k for k in RADII if k<n//2]
  for group in range(args.bases):
   raw=rng.choice(np.array([-1,1],np.int8),size=n)
   cur,en,_=descend(raw,args.method)
   for stage in range(41):
    if stage in args.stages:
     old=canonical(cur)
     for k in ks:
      for j in range(args.candidates):
       ind=rng.choice(n,size=k,replace=False)
       v=cur.copy();c=cor(v)
       for i in ind:flip(v,c,int(i))
       pert=energy(v)
       out,z,steps=descend(v,args.method)
       rows.append((n,group,stage,en,k,j,z,steps,int(z<en),int(not np.array_equal(canonical(out),old)),pert-en))
    if stage==40:break
    ind=rng.choice(n,size=4,replace=False)
    v=cur.copy();c=cor(v)
    for i in ind:flip(v,c,int(i))
    out,z,_=descend(v,args.method)
    if z<en:cur,en=out,z
  print('n',n,'rows',len(rows),'seconds',round(time.perf_counter()-tic,2),flush=True)
 return pd.DataFrame(rows,columns=['n','group','stage','baseE','k','candidate','finalE','steps','improved','changed','immediateDelta'])

def record(args):
 s=np.array([1 if v=='+' else -1 for v in CERT],dtype=np.int8)
 old=canonical(s);rng=np.random.default_rng(args.seed);rows=[]
 for k in (2,4,6,8,10,12,14,16,20,24,32):
  for j in range(args.record_samples):
   v=s.copy();c=cor(v)
   for i in rng.choice(100,k,replace=False):flip(v,c,int(i))
   out,e,steps=descend(v,args.method)
   rows.append((100,0,40,578,k,j,e,steps,int(e<578),int(not np.array_equal(canonical(out),old)),np.nan))
 return pd.DataFrame(rows,columns=['n','group','stage','baseE','k','candidate','finalE','steps','improved','changed','immediateDelta'])

def summarize(df):
 y=df.assign(gain=np.maximum(0,df.baseE-df.finalE),cost=df.steps+1)
 z=y.groupby(['n','stage','k'],as_index=False).agg(p_leave=('changed','mean'),p_improve=('improved','mean'),gain=('gain','mean'),cost=('cost','mean'),count=('improved','size'))
 z['gain_per_sweep']=z.gain/z.cost
 for (n,stage),v in z.groupby(['n','stage']):
  threshold=np.interp(.5,v.p_leave,v.k)
  print('n',n,'stage',stage,'k50',round(threshold,3),'k50/sqrt(n)',round(threshold/np.sqrt(n),3))
 print(z.round(4).to_string(index=False))

if __name__=='__main__':
 ap=argparse.ArgumentParser()
 ap.add_argument('--lengths',type=int,nargs='+',default=[24,32,40,64,100])
 ap.add_argument('--bases',type=int,default=150)
 ap.add_argument('--seed',type=int,default=151619)
 ap.add_argument('--stages',type=int,nargs='+',default=[0,10,40])
 ap.add_argument('--candidates',type=int,default=8)
 ap.add_argument('--descent',choices=['steep','first'],default='steep')
 ap.add_argument('--record',action='store_true')
 ap.add_argument('--record-samples',type=int,default=900)
 ap.add_argument('--output',default='basin-geometry.csv.gz')
 args=ap.parse_args();args.method=0 if args.descent=='steep' else 1
 selftest()
 df=record(args) if args.record else sweep(args)
 df.to_csv(args.output,index=False)
 print('data',args.output,'rows',len(df));summarize(df)
