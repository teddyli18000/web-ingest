"""Frozen-state Tabu intervention statistical audit, base-orbit clustered uncertainty.
Requires pandas/numpy. Printed numbers are comparisons in this diagnostic solver,
not evidence of superiority to published GPU MTS.
"""
import argparse, json, pathlib
import numpy as np
import pandas as pd
NAMES={0:"continue_tabu",1:"random_lns_preserve",2:"random_lns_reset",
       3:"pair_lns_preserve",4:"pair_lns_reset",
       5:"kick8_preserve",6:"kick8_reset"}
def ci(x,B=4000,seed=20261029):
 x=np.asarray(x,dtype=float)
 if not len(x):return [None,None]
 rng=np.random.default_rng(seed)
 parts=[]
 for k in range(0,B,200):
  parts.append(x[rng.integers(len(x),size=(min(200,B-k),len(x)))].mean(axis=1))
 return np.quantile(np.concatenate(parts),[.025,.975]).round(6).tolist()
def audit(path):
 df=pd.read_csv(path,sep="\t")
 keys=["source_id","rep"]
 assert (df.groupby(keys).size()==7).all(), "missing arm"
 assert (df.groupby(keys).frozenBestE.nunique()==1).all()
 assert (df.groupby(keys).frozenCurE.nunique()==1).all()
 assert (df.groupby(keys).frozenStall.nunique()==1).all()
 assert (df.groupby(keys).warmSteps.nunique()==1).all()
 assert (df.gain>=0).all() and (df.bestE<=df.frozenBestE).all()
 assert (df.elapsed_seconds>0).all()
 assert (df.arm.isin(range(7))).all()
 out={"source":path,"states":int(df.source_id.nunique()),"rows":len(df),
      "reps":int(df.rep.nunique()),"overall":{}}
 for label,group in [("all",df),("public_boundary",df[df.provenance.isin(["QOBLIB_snapshot","published_GPU_MTS_v2"])]),
                     ("historical_solver",df[df.provenance=="published_lMAts"])]:
  if group.empty:continue
  v=group.pivot_table(index=["source_id","rep"],columns="arm",values="gain")
  g=v.groupby(level=0).mean() # independent source-orbit is CI unit
  baseline=g[0].values
  arm_stats={}
  for arm in range(7):
   x=g[arm].values
   d=x-baseline
   arm_stats[NAMES[arm]]={"mean_gain":float(x.mean()),"mean_minus_tabu":float(d.mean()),
      "ci95_cluster":ci(d),"source_orbits":len(g),
      "hit_orbits":int((x>0).sum()),"hit_runs":int((v[arm]>0).sum())}
  out["overall"][label]=arm_stats
  print("\n",label,"source-orbits",len(g),"pairs",len(v))
  for k,r in arm_stats.items():
   print(k,"gain",round(r["mean_gain"],4),"delta",round(r["mean_minus_tabu"],4),
         "95CI",r["ci95_cluster"],"hit-runs",r["hit_runs"])
  wr=group.groupby("arm").agg(mean_clock_ms=("elapsed_seconds",lambda x:1000*x.mean()),
           mean_injection_ms=("injection_seconds",lambda x:1000*x.mean()),
           average_calls=("tabu_calls","mean"),average_overshoot=("overshoot_ms","mean"))
  print(wr.round(3).to_string())
 for n,v in df.groupby("N"):
  if n not in (64,80,92,96,99,100):continue
  print("N",n,"runs",v.groupby("arm").size().iloc[0],
        "mean gains by arm",v.groupby("arm").gain.mean().round(3).to_dict())
 return out
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("inputs",nargs="+");p.add_argument("--out")
 a=p.parse_args()
 out=[audit(x) for x in a.inputs]
 if a.out:pathlib.Path(a.out).write_text(json.dumps(out,indent=2)+"\n")
