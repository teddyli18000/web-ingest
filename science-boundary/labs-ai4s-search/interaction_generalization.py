"""Held-out-length N100 test of whether pair/higher-order features improve action choice.
Inputs from fresh_interactions.cpp: N40/64 stage40 training and N100 stage40/120 test.
Requires numpy, pandas, scikit-learn; one candidate from six is chosen per group.
Run: OPENBLAS_NUM_THREADS=1 python interaction_generalization.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score,average_precision_score
from pathlib import Path
P=Path(__file__).resolve().parent
train=pd.concat([pd.read_csv(P/f"fresh_n{n}_stage40.csv") for n in (40,64)],ignore_index=True)
test=pd.concat([pd.read_csv(P/name) for name in
 ("fresh_n100_stage40_final.csv","fresh_n100_stage120_final.csv")],ignore_index=True)
for d in (train,test):
 d["energy_density"]=d.baseE/d.n**2
 d["single_per_n"]=d.singles/d.n
 d["instant_per_n"]=d.exactDelta/d.n
 d["pair_per_sqrt_n"]=d.pairs/np.sqrt(d.n)
 d["pos_st"]=np.maximum(0,d.baseE-d.steepE)
 d["pos_fi"]=np.maximum(0,d.baseE-d.firstE)
 d["pos_both"]=.5*(d.pos_st+d.pos_fi)
 d["hit"]=((d.pos_st>0)|(d.pos_fi>0)).astype(int)
features={
 "cheap":["energy_density","single_per_n","instant_per_n"],
 "multispin":["energy_density","single_per_n","instant_per_n","pair_per_sqrt_n","higher"]}
print("train",len(train),"positives",train.hit.mean())
for name,fs in features.items():
 for task in ("hit","gain"):
  kwargs=dict(max_iter=125,max_leaf_nodes=7,min_samples_leaf=120,
      learning_rate=.045,l2_regularization=20,random_state=420)
  m=HistGradientBoostingClassifier(**kwargs) if task=="hit" else HistGradientBoostingRegressor(**kwargs)
  m.fit(train[fs],train.hit if task=="hit" else train.pos_both/train.n)
  pred=m.predict_proba(test[fs])[:,1] if task=="hit" else m.predict(test[fs])
  test[name+"_"+task]=pred
  print(name,task,"AUC",roc_auc_score(test.hit,pred),
        "AP",average_precision_score(test.hit,pred))
for stage in (40,120):
 d=test[test.stage==stage].copy().reset_index(drop=True)
 scores={
  "single":("singles",True),"immediate":("exactDelta",True),
  "cheap_hit":("cheap_hit",False),"multispin_hit":("multispin_hit",False),
  "cheap_gain":("cheap_gain",False),"multispin_gain":("multispin_gain",False),
  "oracle":("pos_both",False)}
 selections={}
 for k,(col,smallest) in scores.items():
  idx=d.groupby("group")[col].idxmin() if smallest else d.groupby("group")[col].idxmax()
  selections[k]=d.loc[idx].sort_values("group")
 ref=selections["immediate"]
 print("\nstage",stage,"N100 groups",d.group.nunique())
 for k,s in selections.items():
  dif=s.pos_both.to_numpy()-ref.pos_both.to_numpy()
  rng=np.random.default_rng(2026);b=[]
  for _ in range(10):
   b.extend(dif[rng.integers(len(dif),size=(100,len(dif)))].mean(axis=1))
  print(k,"hits",int((s.pos_both>0).sum()),
        "mean_gain",round(s.pos_both.mean(),4),
        "vs_immediate",round(dif.mean(),4),
        "ci95",np.round(np.quantile(b,[.025,.975]),4))
