"""Same-action LABS basin outcomes under different deterministic local descents.
Requires numpy, pandas, scipy, numba and geometry_repro.py in same directory.
Run: python operator_agreement.py
"""
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from geometry_repro import cor,flip,canonical,descend
from pathlib import Path
rng=np.random.default_rng(4411907);rows=[]
for n in (40,64,100):
 for group in range(150):
  s=rng.choice(np.array([-1,1],np.int8),size=n)
  base,be,_=descend(s,0)
  for step in range(40):
   z=base.copy();c=cor(z)
   for i in rng.choice(n,4,replace=False):flip(z,c,int(i))
   candidate,ee,_=descend(z,0)
   if ee<be:base,be=candidate,ee
  old=canonical(base)
  for k in (2,4,6,8,12):
   for j in range(12):
    z=base.copy();c=cor(z)
    for i in rng.choice(n,k,replace=False):flip(z,c,int(i))
    a,ea,_=descend(z,0)
    b,eb,_=descend(z,1)
    rows.append((n,group,k,j,be,ea,eb,int(not np.array_equal(canonical(a),old)),int(not np.array_equal(canonical(b),old))))
 print('n',n,'done',len(rows),flush=True)
df=pd.DataFrame(rows,columns=['n','group','k','candidate','baseE','steepE','firstE','steepLeave','firstLeave'])
p=Path(__file__).resolve().parent
df.to_csv(p/'operator_agreement.csv.gz',index=False)
for n in (40,64,100):
 print('N',n)
 for k in (2,4,6,8,12):
  sub=df[(df.n==n)&(df.k==k)]
  s=sub.steepE<sub.baseE;f=sub.firstE<sub.baseE
  corr=[]
  for _,z in sub.groupby('group'):
   x=spearmanr(z.steepE,z.firstE).statistic
   if np.isfinite(x):corr.append(x)
  print('k',k,'leave S/F',round(sub.steepLeave.mean(),3),round(sub.firstLeave.mean(),3),
       'improve S/F',round(s.mean(),3),round(f.mean(),3),
       'both-improve',round((s&f).mean(),3),'rankrho',round(float(np.mean(corr)),3),'Npair',len(sub))
