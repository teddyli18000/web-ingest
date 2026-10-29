"""Audit exact 4-spin fixed-pool experiments, including paired group bootstrap.
Run from topic:
 python analyze_interactions.py fresh_n100_stage0.csv fresh_n64_stage40.csv ...
Outputs JSON; source CSV is regenerated using fresh_interactions.cpp.
Dependencies: numpy, pandas.
"""
import argparse,json
import numpy as np
import pandas as pd

SEED=20261029
METHODS={"singles":"singles","pairapprox":"pairapprox","immediate":"exactDelta"}

def analyze(path,bootstrap=3000):
 d=pd.read_csv(path)
 d["pairapprox"]=d.singles+d.pairs
 d["gain_steep"]=(d.baseE-d.steepE).clip(lower=0)
 d["gain_first"]=(d.baseE-d.firstE).clip(lower=0)
 d["gain_mean"]=(d.gain_steep+d.gain_first)/2
 sizes=d.groupby("group").size()
 assert sizes.nunique()==1 and sizes.iloc[0]==6,("incomplete pool",path)
 assert not d.duplicated(["group","candidate"]).any()
 assert (d.exactDelta==d.singles+d.pairs+d.higher).all()
 assert d.n.nunique()==d.stage.nunique()==1
 d=d.reset_index(drop=True)
 sel={}
 for method,col in METHODS.items():
  ix=d.groupby("group")[col].idxmin()
  sel[method]=d.loc[ix].sort_values("group")
 rng=np.random.default_rng(SEED)
 records=[]
 for operator,target,steps in (("steep","gain_steep","steepSteps"),
                                ("first","gain_first","firstSteps"),
                                ("ensemble","gain_mean",None)):
  ref=sel["singles"][target].to_numpy()
  for method,s in sel.items():
   y=s[target].to_numpy()
   delta=y-ref
   samples=[]
   for _ in range(0,bootstrap,250):
    batch=min(250,bootstrap-_)
    samples.extend(delta[rng.integers(len(delta),size=(batch,len(delta)))].mean(axis=1))
   lo,hi=np.quantile(samples,[.025,.975])
   rec=dict(method=method,operator=operator,groups=len(s),hits=int((y>0).sum()),
        mean_gain=float(y.mean()),gain_vs_singles=float(delta.mean()),
        ci95_gain=[float(lo),float(hi)])
   if steps:
    rec["mean_relax_sweeps"]=float((s[steps]+1).mean())
    rec["gain_per_relax_sweep"]=float(y.sum()/(s[steps]+1).sum())
   records.append(rec)
 # Fixed immediate-energy tied comparison: one chosen pair per group, chosen by
 # maximal pair-coupling separation WITHOUT consulting the descent outcomes.
 pair_rows=[]
 for group,g in d.groupby("group"):
  best=None
  for immediate,t in g.groupby("exactDelta"):
   lo=t.loc[t.pairs.idxmin()]
   hi=t.loc[t.pairs.idxmax()]
   if best is None or (hi.pairs-lo.pairs)>best[0]:best=(hi.pairs-lo.pairs,lo,hi)
  if best and best[0]>0:pair_rows.append(best)
 tied=[]
 for op in ("steep","first"):
  if not pair_rows:continue
  lo=np.array([max(0,int(t[1].baseE)-int(t[1][op+"E"])) for t in pair_rows])
  hi=np.array([max(0,int(t[2].baseE)-int(t[2][op+"E"])) for t in pair_rows])
  dif=lo-hi
  samples=[]
  for _ in range(0,bootstrap,250):
   samples.extend(dif[rng.integers(len(dif),size=(min(250,bootstrap-_),len(dif)))].mean(axis=1))
  tied.append(dict(operator=op,tied_pairs=len(dif),low_pair_gain=float(lo.mean()),
    high_pair_gain=float(hi.mean()),difference=float(dif.mean()),
    ci95=[float(t) for t in np.quantile(samples,[.025,.975])]))
 return dict(file=path,n=int(d.n.iloc[0]),stage=int(d.stage.iloc[0]),
   pools=int(d.group.nunique()),median_baseE=float(d.groupby("group").baseE.first().median()),
   higher_sd=float(d.higher.std()),pair_sd=float(d.pairs.std()),records=records,tied=tied)

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("csv",nargs="+");p.add_argument("--output")
 a=p.parse_args()
 z=[analyze(x) for x in a.csv]
 out=json.dumps(z,indent=2)
 if a.output:open(a.output,"w").write(out+"\n")
 else:print(out)
