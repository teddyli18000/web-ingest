"""Analyze three treatment replicates from each frozen base and out-of-fold effect predictability."""
import sys
import numpy as np,pandas as pd
from scipy.stats import spearmanr,pearsonr
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score,mean_absolute_error
def ci(x,seed=20261029):
 rng=np.random.default_rng(seed);x=np.asarray(x);draw=[]
 for _ in range(25):draw.extend(x[rng.integers(len(x),size=(200,len(x)))].mean(axis=1))
 return np.quantile(draw,[.025,.975])
def run(path):
 d=pd.read_csv(path);n=int(d.n.iloc[0])
 table=d.pivot_table(index=["group","rep"],columns="policy",values="final_gain")
 effect=(table[1]-table[0]).unstack("rep")
 print("N",n,"bases",len(effect),"replicate rho",[(a,b,round(spearmanr(effect[a],effect[b]).statistic,3)) for a,b in ((0,1),(0,2),(1,2))])
 diff=effect.mean(axis=1)
 x=d[d.policy==0].groupby("group").first().loc[diff.index].copy()
 x["energy_scaled"]=(x.baseE-x.refE)/n
 x["barrier_avg_scaled"]=x.meanDelta/n;x["barrier_sd_scaled"]=x.sdDelta/n
 x["negative_frac"]=x.negativePairs/(n*(n-1)/2);x["hamming_frac"]=x.base_hamming/n
 x["probe_gain_scaled"]=x.probe_mean_gain/n
 fields={
  "constant":[],
  "energy":["energy_scaled"],
  "math":["energy_scaled","barrier_avg_scaled","barrier_sd_scaled","negative_frac","hamming_frac"],
  "history":["probe_hit","probe_gain_scaled","probe_unique"],
  "math+history":["energy_scaled","barrier_avg_scaled","barrier_sd_scaled","negative_frac","hamming_frac","probe_hit","probe_gain_scaled","probe_unique"]
 }
 cv=KFold(n_splits=5,shuffle=True,random_state=420)
 y=diff.to_numpy();predictions={}
 for name,cols in fields.items():
  pred=np.zeros(len(y))
  for tr,te in cv.split(y):
   if not cols:pred[te]=y[tr].mean()
   else:
    model=make_pipeline(StandardScaler(),Ridge(alpha=10))
    model.fit(x.iloc[tr][cols],y[tr]);pred[te]=model.predict(x.iloc[te][cols])
  predictions[name]=pred
  print("R2",name,round(r2_score(y,pred),4),"MAE",round(mean_absolute_error(y,pred),4))
 for name in ("math","history","math+history"):
  gain=np.abs(y-predictions["energy"])-np.abs(y-predictions[name])
  print("mean absolute error benefit vs energy",name,round(gain.mean(),3),"bootstrapCI",ci(gain))
 for arm in range(1,6):
  dif=(table[arm]-table[0]).unstack("rep").mean(axis=1).to_numpy()
  print("causal contrast",arm,"mean",dif.mean(),"CI",ci(dif,seed=999+arm))
if __name__=="__main__":
 for p in sys.argv[1:]:run(p)
