#!/usr/bin/env python3
"""Analyze original lMAts vs stall-triggered macros on same seed/CPU limit.

Positive difference = macro reaches lower final exact LABS E.
Cluster unit = independent solver run/seed. No claims vs 2025 GPU MTS.
"""
import argparse,csv,json,pathlib
import numpy as np
ARMS={0:"original_lMAts",1:"one_random12",2:"best_of_8_random12",3:"spectral_pairs_parity_corridor",
      4:"random_pairs_parity_corridor",5:"spectral_pairs_best_E"}
def boot(x,seed=113121,B=10000):
 x=np.asarray(x,float)
 rng=np.random.default_rng(seed)
 vals=np.empty(B)
 for i in range(0,B,250):
  vals[i:i+250]=x[rng.integers(len(x),size=(250,len(x)))].mean(axis=1)
 return np.quantile(vals,[.025,.975]).round(4).tolist()
def run(path,out):
 rows=list(csv.DictReader(open(path),delimiter='\t'))
 assert rows
 bykey={}
 for row in rows:
  assert not row['error']
  n=int(row['n']);seed=int(row['seed']);arm=int(row['arm']);e=int(row['bestE'])
  assert int(row['oddE'])+int(row['evenE'])==e
  assert int(row['macro_proposals'])>0 or arm==0
  key=(n,seed)
  bykey.setdefault(key,{})[arm]=dict(E=e,odd=int(row['oddE']),even=int(row['evenE']),
       near=int(row['near_skew']),macros=int(row['macro_proposals']),elapsed=float(row['actual_seconds']))
 assert all(set(v)==set(ARMS) for v in bykey.values())
 result={'scope':'Observed terminal best within original source-pinned lMAts GA; proposal scoring and native Tabu repairs count inside wall time',
  'source_csv':str(path),'runs':len(bykey),'by_length':{},'warning':['No comparison to stronger 2025 GPU MTS or 2026 GPU SAW',
  'RNG streams diverge after interventions despite matching initial seed',
  'Exploratory comparisons across five macros and lengths: confidence intervals are descriptive, not familywise adjusted']}
 for n in sorted({n for n,_ in bykey}):
  group=[v for (z,_),v in sorted(bykey.items()) if z==n]
  record={'n_runs':len(group),'baseline_bestE_mean':np.mean([r[0]['E'] for r in group]),'arms':{}}
  for arm,title in ARMS.items():
   delta=np.array([r[0]['E']-r[arm]['E'] for r in group])
   record['arms'][title]={'mean_bestE':round(float(np.mean([r[arm]['E'] for r in group])),3),
      'mean_gain_against_baseline':round(float(delta.mean()),3),
      'paired_95CI':boot(delta,seed=23451+n+arm),
      'win_tie_loss':[int((delta>0).sum()),int((delta==0).sum()),int((delta<0).sum())],
      'avg_macros':round(float(np.mean([r[arm]['macros'] for r in group])),3),
      'avg_actual_wall_s':round(float(np.mean([r[arm]['elapsed'] for r in group])),3),
      'best_observed_E':int(min(r[arm]['E'] for r in group)),
      'near_skew_finishes':int(sum(r[arm]['near'] for r in group))}
  result['by_length'][str(n)]=record
 pathout=pathlib.Path(out);pathout.parent.mkdir(parents=True,exist_ok=True)
 pathout.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('results');a.add_argument('--out',required=True)
 x=a.parse_args();run(x.results,x.out)
