"""Compare balanced-motif and random 4-flip candidates under identical pool sizes.
Inputs: CSV from motif_vs_random.cpp. Requires numpy, pandas.
Example: python motif_compare.py motif100_stage40.csv motif100_stage40_confirm.csv
For each start select min-immediate in each 12-candidate pool, AND run a separate
exact-immediate-energy matched test (tie broken by closeness in singles sum).
Bootstrap resamples independent *starts*, not candidate rows.
"""
import sys
import pandas as pd
import numpy as np

def analyze(filename):
 d=pd.read_csv(filename)
 d["sgain"]=(d.baseE-d.steepE).clip(lower=0)
 d["fgain"]=(d.baseE-d.firstE).clip(lower=0)
 d=d.sort_values(["group","type","candidate"]).reset_index(drop=True)
 groups=d.group.nunique()
 assert len(d)==groups*24 and (d.groupby(["group","type"]).size()==12).all()
 rand=d[d.type==0][["exactDelta","singles","sgain","fgain"]].to_numpy().reshape(groups,12,4)
 motif=d[d.type==1][["exactDelta","singles","sgain","fgain"]].to_numpy().reshape(groups,12,4)
 ia=rand[:,:,0].argmin(axis=1);ib=motif[:,:,0].argmin(axis=1)
 best_a=rand[np.arange(groups),ia];best_b=motif[np.arange(groups),ib]
 gap=np.abs(rand[:,:,None,0]-motif[:,None,:,0])
 single_gap=np.abs(rand[:,:,None,1]-motif[:,None,:,1])
 # Any equal-energy pair takes precedence. Among equal energies, match closest singles.
 rank=gap*10000+single_gap
 selected=rank.reshape(groups,-1).argmin(axis=1)
 pair_a=rand[np.arange(groups),selected//12]
 pair_b=motif[np.arange(groups),selected%12]
 equal=np.abs(pair_a[:,0]-pair_b[:,0])==0
 print("\n",filename,"groups",groups,"exact ties",int(equal.sum()))
 for title,a,b in (("best of 12 by exact immediate",best_a,best_b),
                   ("exact instant-energy tied",pair_a[equal],pair_b[equal])):
  print(title,"groups",len(a))
  for j,op in ((2,"steepest"),(3,"first-improvement")):
   diff=b[:,j]-a[:,j]
   rng=np.random.default_rng(20261029)
   boot=[]
   for _ in range(0,3000,250):
    boot.extend(diff[rng.integers(len(diff),size=(250,len(diff)))].mean(axis=1))
   print(op,"random mean",round(a[:,j].mean(),4),"motif mean",round(b[:,j].mean(),4),
         "difference",round(diff.mean(),4),"CI95",np.quantile(boot,[.025,.975]),
         "hits rand/motif",np.count_nonzero(a[:,j]),np.count_nonzero(b[:,j]))

if __name__=="__main__":
 for path in sys.argv[1:]:analyze(path)
