"""Analyze paired mask-search groups using cluster bootstrap. Requires pandas numpy."""
import sys
import numpy as np,pandas as pd
METHODS={0:'random',1:'soft-delta',2:'negative-pair',3:'absolute-pair',4:'window'}

def main(path):
 d=pd.read_csv(path)
 for c in ['repairSteep','repairFirst','excSteep','excFirst']:
  d['gain_'+c]=(d.baseE-d[c]).clip(lower=0)
 d['meanexit_gain']=(d.gain_excSteep+d.gain_excFirst)/2
 d['best_steep']=d[['gain_repairSteep','gain_excSteep']].max(axis=1)
 d['best_first']=d[['gain_repairFirst','gain_excFirst']].max(axis=1)
 d['best_both']=d[['gain_repairSteep','gain_excSteep','gain_repairFirst','gain_excFirst']].max(axis=1)
 d['cpu_seconds']=d.selectionSeconds+d.enumevalSeconds+d.descentSeconds
 g=d.groupby(['group','method']).agg(base=('baseE','first'), best_steep=('best_steep','max'),best_first=('best_first','max'),best_both=('best_both','max'),meanexit_gain=('meanexit_gain','mean'), cost=('cpu_seconds','sum'), enumerations=('enumStates','sum'), immediate_improve=('repairE',lambda x: 0), num_masks=('mask','count')).reset_index()
 assert g.groupby('group').base.nunique().eq(1).all()
 print('\n',path,'N/stage/M/groups',d.n.iloc[0],d.stage.iloc[0],d.m.iloc[0],d.group.nunique(), 'base median',d.groupby('group').baseE.first().median())
 result={}
 for outcome in ['best_steep','best_first','best_both']:
  pivot=g.pivot(index='group',columns='method',values=outcome).sort_index()
  ref=pivot[0].values
  rg=np.random.default_rng(20261029)
  rows=[]
  for j in METHODS:
   y=pivot[j].values;delta=y-ref
   boot=[]
   for _ in range(6):boot.append(delta[rg.integers(len(delta),size=(500,len(delta)))].mean(axis=1))
   ci=np.quantile(np.concatenate(boot),[0.025,0.975])
   rows.append((METHODS[j], round(y.mean(),3),int((y>0).sum()),round(delta.mean(),3),tuple(round(a,3) for a in ci)))
  result[outcome]=rows
  print(outcome,rows)
 times=g.groupby('method').cost.mean()
 print('CPU time seconds per group',dict(zip(METHODS.values(),[round(times[i],5) for i in METHODS])))
 return result
if __name__=='__main__':
 for p in sys.argv[1:]:main(p)
