"""Analyze matched-treatment CSVs; Python with numpy,pandas,scikit-learn."""
import sys
import numpy as np,pandas as pd
from sklearn.ensemble import RandomForestRegressor
POLICY={0:"random4",1:"tabu7",2:"random-LNS",3:"pair-LNS",4:"runtime-Thompson",5:"stagnation-portfolio"}
def interval(v,rng,B=5000):
 v=np.asarray(v,float);out=[]
 for i in range(0,B,200):
  out.extend(v[rng.integers(len(v),size=(min(200,B-i),len(v)))].mean(axis=1))
 return np.quantile(out,[.025,.975])
def summarise(d):
 assert d.groupby("group").policy.nunique().eq(6).all()
 assert d.groupby("group").baseE.nunique().eq(1).all()
 rng=np.random.default_rng(412005);n=int(d.n.iloc[0])
 print("N",n,"groups",d.group.nunique(),"reference",d.refE.iloc[0],"start median",d.groupby("group").baseE.first().median())
 for target in ("phase_gain","final_gain"):
  base=d[d.policy==0].sort_values("group")[target].to_numpy()
  for p in range(6):
   y=d[d.policy==p].sort_values("group")[target].to_numpy()
   print(target,POLICY[p],"mean",round(y.mean(),3),"hit",int((y>0).sum()),"difference",round((y-base).mean(),3),"CI",interval(y-base,rng))
def crosslength(train,hold):
 for d in (train,hold):
  d["energy_ratio"]=(d.baseE-d.refE)/d.n
  d["E_density"]=d.baseE/d.n**2
  d["barrier_mean"]=d.meanDelta/d.n
  d["barrier_sd"]=d.sdDelta/d.n
  d["negative_frac"]=d.negativePairs/(d.n*(d.n-1)/2)
  d["hamming_frac"]=d.base_hamming/d.n
  d["probe_gain_norm"]=d.probe_mean_gain/d.n
 feature_sets={
  "structure":["energy_ratio","E_density","barrier_mean","barrier_sd","negative_frac","hamming_frac"],
  "history":["probe_hit","probe_gain_norm","probe_unique"],
  "combined":["energy_ratio","E_density","barrier_mean","barrier_sd","negative_frac","hamming_frac","probe_hit","probe_gain_norm","probe_unique"]
 }
 results={}
 piv=hold.pivot(index="group",columns="policy",values="final_gain").sort_index()
 train_best=int(train.groupby("policy").final_gain.mean().idxmax())
 for label,cols in feature_sets.items():
  preds=[]
  for p in range(6):
   data=train[train.policy==p]
   mod=RandomForestRegressor(n_estimators=100,min_samples_leaf=10,max_features=.8,random_state=710+p,n_jobs=1)
   mod.fit(data[cols],data.final_gain/data.n)
   preds.append(mod.predict(hold[hold.policy==p].sort_values("group")[cols]))
  choice=np.argmax(np.vstack(preds),axis=0)
  outcome=piv.to_numpy()[np.arange(len(piv)),choice]
  diff=outcome-piv[train_best].to_numpy()
  results[label]=(dict(zip(*np.unique(choice,return_counts=True))),outcome.mean(),diff.mean(),interval(diff,np.random.default_rng(1117)))
 print("training-best fixed policy",train_best,"holdout means",piv.mean().to_dict())
 for label,x in results.items():print("model",label,x)
 print("oracle upper bound (unavailable)",piv.max(axis=1).mean())
if __name__=="__main__":
 files=[pd.read_csv(p) for p in sys.argv[1:]]
 for d in files:summarise(d)
 if {int(d.n.iloc[0]) for d in files}>={64,80,100}:
  a=pd.concat([d for d in files if d.n.iloc[0] in (64,80)],ignore_index=True)
  b=next(d for d in files if d.n.iloc[0]==100)
  crosslength(a,b)
