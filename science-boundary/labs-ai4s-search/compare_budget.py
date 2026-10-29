import pandas as pd,numpy as np,sys
p=sys.argv[1];df=pd.read_csv(p)
for c in ['repairSteep','repairFirst','excSteep','excFirst']:df[c]=(df.baseE-df[c]).clip(lower=0)
df['best']=df[['repairSteep','repairFirst','excSteep','excFirst']].max(axis=1)
df['cpu']=df.selectionSeconds+df.enumevalSeconds+df.descentSeconds
S={}
for m,k in [(0,4),(0,6),(0,8),(1,4),(1,6),(1,8),(2,4),(2,6),(2,8)]:
 a=df[(df.method==m)&(df['mask']<k)]
 v=a.groupby('group').agg(gain=('best','max'),time=('cpu','sum'))
 S[m,k]=v
for(m,k),v in S.items():
 print(m,k,'mean_gain',v.gain.mean(),'hits',(v.gain>0).sum(),'time(ms)',v.time.mean()*1000,'gain/ms',v.gain.mean()/(1000*v.time.mean()))
for ka,kb in [(4,6),(4,8),(6,8)]:
 for mb in [0,1]:
  a=S[2,ka];b=S[mb,kb];d=a.gain.values-b.gain.values;r=np.random.default_rng(544)
  arr=np.empty(10000)
  for i in range(0,10000,500):
   arr[i:i+500]=d[r.integers(len(d),size=(500,len(d)))].mean(axis=1)
  print('negative',ka,'vs',mb,kb,'mean_difference',d.mean(),'95CI',np.quantile(arr,[.025,.975]),'times(ms)',a.time.mean()*1000,b.time.mean()*1000)
for m in range(5):
 a=df[(df.method==m)&(df['mask']<4)]
 v=a.groupby('group').agg(initgain=('repairSteep','max'),exc_gain=('excSteep','max'),steps=('stepsExcSteep','mean'),etime=('enumevalSeconds','sum'))
 print('method',m,'purerepair hit',np.count_nonzero(v.initgain),'excursion hit',np.count_nonzero(v.exc_gain),'average pure repair',v.initgain.mean(),'avg excursion',v.exc_gain.mean())
