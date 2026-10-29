"""Counterfactual two-descent action value learning with held-out N100.
Requires numpy, pandas, numba, scikit-learn, geometry_repro.py.
Run: python ensemble_probe.py
"""
import numpy as np, pandas as pd, pathlib
from geometry_repro import cor,flip,delta,energy,descend,canonical
from sklearn.ensemble import HistGradientBoostingRegressor,HistGradientBoostingClassifier
P=pathlib.Path(__file__).resolve().parent
rng=np.random.default_rng(4411907)
rows=[]
for n in (40,64,100):
 for group in range(150):
  s=rng.choice(np.array([-1,1],np.int8),size=n)
  base,be,_=descend(s,0)
  for step in range(40):
   z=base.copy();c=cor(z)
   for i in rng.choice(n,4,replace=False):flip(z,c,int(i))
   candidate,ee,_=descend(z,0)
   if ee<be:base,be=candidate,ee
  cs=cor(base)
  ds=np.array([delta(base,cs,i) for i in range(n)])
  for k in (2,4,6,8,12):
   for j in range(12):
    ind=np.sort(rng.choice(n,k,replace=False));z=base.copy();c=cor(z)
    for i in ind:flip(z,c,int(i))
    immed=energy(z)-be
    a,ea,sa=descend(z,0);b,eb,sb=descend(z,1)
    sd=ds[ind]
    rows.append((n,group,k,j,be,be/n**2,immed/n,np.sum(sd)/n,np.min(sd)/n,np.max(sd)/n,np.std(sd)/n,(ind[-1]-ind[0])/n,int(ea),int(eb),sa,sb))
 print('N',n,'rows',len(rows),flush=True)
cols=['n','group','k','j','baseE','baseE_ratio','immed','sumd','mind','maxd','sdd','span','steepE','firstE','steepSteps','firstSteps']
df=pd.DataFrame(rows,columns=cols)
df['gain_steep']=np.maximum(0,df.baseE-df.steepE)/df.n
df['gain_first']=np.maximum(0,df.baseE-df.firstE)/df.n
df['gain_ensemble']=.5*(df.gain_steep+df.gain_first)
df['target_either']=(df.gain_ensemble>0).astype(int)
df.to_csv(P/'ensemble_probe.csv.gz',index=False)
train=df[df.n.isin([40,64])]
test=df[df.n==100].copy()
features={'basic':['k','baseE_ratio','immed','sumd','mind','maxd','sdd'],'plus_spatial':['k','baseE_ratio','immed','sumd','mind','maxd','sdd','span']}
for fn,ff in features.items():
 reg=HistGradientBoostingRegressor(max_iter=90,max_leaf_nodes=7,min_samples_leaf=60,l2_regularization=10,learning_rate=.04,random_state=14)
 reg.fit(train[ff],train.gain_ensemble)
 test['reg_'+fn]=reg.predict(test[ff])
 clf=HistGradientBoostingClassifier(max_iter=90,max_leaf_nodes=7,min_samples_leaf=60,l2_regularization=10,learning_rate=.04,random_state=14)
 clf.fit(train[ff],train.target_either)
 test['prob_'+fn]=clf.predict_proba(test[ff])[:,1]
 print('trained',fn,'positive rate',train.target_either.mean())
methods={'random':('j',False),'immediate':('immed',False),'single_sum':('sumd',False),
         'learned_reg':('reg_basic',True),'learned_prob':('prob_basic',True),
         'learned_spatial':('reg_plus_spatial',True),'oracle_ensemble':('gain_ensemble',True)}
sel=[]
for (n,g,k),f in test.groupby(['n','group','k']):
 for method,(c,maximize) in methods.items():
  i=f[c].idxmax() if maximize else f[c].idxmin()
  z=f.loc[i]
  sel.append((g,k,method,z.gain_ensemble,z.gain_steep,z.gain_first,int(z.gain_steep>0),int(z.gain_first>0)))
r=pd.DataFrame(sel,columns=['group','k','method','gain_ensemble','gain_steep','gain_first','hit_steep','hit_first'])
r.to_csv(P/'ensemble_selection.csv',index=False)
print('\nN100 held-out N40/64 training, 150 group pools of 12 fixed radius candidates:')
print(r.groupby(['k','method']).agg(e_gain=('gain_ensemble','mean'),s_hits=('hit_steep','sum'),f_hits=('hit_first','sum')).round(4).to_string())
rs=np.random.default_rng(773)
for k in (4,6,8,12):
 f=r[r.k==k];base=f[f.method=='single_sum'].sort_values('group').gain_ensemble.to_numpy()
 print('\nk',k,'cheap baseline',round(base.mean(),4))
 for method in ('learned_reg','learned_prob','learned_spatial','immediate','oracle_ensemble'):
  v=f[f.method==method].sort_values('group').gain_ensemble.to_numpy();d=v-base
  ci=np.quantile(rs.choice(d,(5000,len(d)),replace=True).mean(axis=1),[.025,.975])
  print(method,'avg_gain_diff',round(d.mean(),4),'95CI',np.round(ci,4))
