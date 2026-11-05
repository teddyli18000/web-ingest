#!/usr/bin/env python3
"""Pre-transition structure-only prediction of parity-compensation *direction*.
Exploratory conditional diagnostic, not deployable improvement probability:
only native TS_BEST events with gap>=16 and directional compensation are labeled.
Stratify by independent run and hold entire lengths 92/99/100 out.
"""
import argparse,json,pathlib
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,log_loss,brier_score_loss

def calc(bits):
    n=len(bits)
    a=np.frombuffer(bits.encode('ascii'),dtype=np.uint8)
    s=np.where(a==49,1,-1).astype(np.int16)
    c=np.correlate(s,s,'full')[n:].astype(np.float64)
    k=np.arange(1,n)
    out={}
    power=c*c/(n-k)
    for parity in (0,1):
        sel=(k%2)==parity
        for idx in range(6):
            inbin=(6*(k-1)//(n-1))==idx
            vals=power[sel&inbin]
            out[f'spec_{parity}_{idx}']=float(vals.mean()) if len(vals) else 0.
    out['bit_imbalance']=abs(float(s.mean()))
    for step in (1,2,3,4):
        out[f'bit_local_lag_{step}']=abs(float((s[:-step]*s[step:]).mean()))
    out['bit_run_variation']=abs(float(np.mean(s[1:]!=s[:-1]))-.5)
    return out

BASE=['E_per_n','E_density','step_per_n','startE_per_n','global_gap_per_n']
SPECTRAL=['Dodd_per_n','odd_share']+[f'spec_{p}_{j}' for p in (0,1) for j in range(6)]
BITS=['bit_imbalance','bit_run_variation']+[f'bit_local_lag_{i}' for i in (1,2,3,4)]
FEATURES={'constant':[], 'energy_history':BASE,
          'energy_plus_odd_share':BASE+['odd_share'],
          'energy_plus_parity_scalars':BASE+['odd_share','Dodd_per_n'],
          'energy_plus_spectrum_bins':BASE+[f'spec_{p}_{j}' for p in (0,1) for j in range(6)],
          'energy_plus_spectrum':BASE+SPECTRAL,
          'energy_plus_bits':BASE+BITS,
          'dual_branch':BASE+SPECTRAL+BITS}

def score(y,p):
    p=np.clip(p,1e-7,1-1e-7)
    return dict(logloss=float(log_loss(y,p,labels=[0,1])),
                brier=float(brier_score_loss(y,p)),
                auc=float(roc_auc_score(y,p)) if len(set(y))==2 else None)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--out',required=True)
    args=ap.parse_args()
    x=pd.read_csv(args.input,sep='\t',dtype={'oldSeq':str,'newSeq':str})
    assert (x.deltaOdd+x.deltaEven==-x.improvement).all()
    x=x[x.gap_steps>=16]
    x=x[((x.deltaOdd>0)&(x.deltaEven<0))|((x.deltaOdd<0)&(x.deltaEven>0))].copy()
    x['target']=(x.deltaOdd>0).astype(int)
    assert ((x.step-x.gap_steps)>=0).all()
    x['run']=x.N.astype(str)+'_'+x.seed.astype(str)
    x['E_per_n']=x.oldE/x.N
    x['E_density']=x.oldE/(x.N*x.N)
    x['step_per_n']=(x.step-x.gap_steps)/x.N  # previous known TS_BEST step; NEVER future event step
    x['startE_per_n']=x.startE/x.N
    x['global_gap_per_n']=(x.oldE-x.global_at_start).clip(lower=0)/x.N
    x['Dodd_per_n']=x.oldDodd/x.N
    x['odd_share']=x.oldOdd/x.oldE
    extra=pd.DataFrame([calc(z) for z in x.oldSeq],index=x.index)
    x=pd.concat([x,extra],axis=1)
    train=x[x.N.isin([48,64,80])].copy()
    test=x[x.N.isin([92,99,100])].copy()
    assert len(train)>200 and len(test)>200
    assert set(train.run).isdisjoint(set(test.run))
    results=dict(scope='Conditional mode of actual native TS_BEST transition after at least 16 accepted moves; predictor input only PRE-transition previous-best state; future gap used solely for offline cohort filtering, NOT predictive features; NOT a prediction of success nor a generator',
                 nTrain=len(train),nTest=len(test),
                 labels_train=dict(odd_cost=int(train.target.sum()),even_cost=int(len(train)-train.target.sum())),
                 labels_test=dict(odd_cost=int(test.target.sum()),even_cost=int(len(test)-test.target.sum())),
                 length_train=[48,64,80],length_test=[92,99,100],models={})
    ytrain=train.target.values;ytest=test.target.values
    predictions={}
    for name,columns in FEATURES.items():
        if not columns:p=np.full(len(test),float(ytrain.mean()))
        else:
            model=make_pipeline(StandardScaler(),LogisticRegression(C=.2,max_iter=500))
            model.fit(train[columns],ytrain)
            p=model.predict_proba(test[columns])[:,1]
        predictions[name]=p
        results['models'][name]=score(ytest,p)
    for name in FEATURES:
        if name in ('constant','energy_history'):continue
        deltas=[]
        for rid,g in test.groupby('run'):
            idx=np.where(test.run.values==rid)[0]
            yy=ytest[idx]
            p0=np.clip(predictions['energy_history'][idx],1e-7,1-1e-7)
            pp=np.clip(predictions[name][idx],1e-7,1-1e-7)
            losses0=-(yy*np.log(p0)+(1-yy)*np.log(1-p0))
            losses1=-(yy*np.log(pp)+(1-yy)*np.log(1-pp))
            deltas.append(float(np.mean(losses0-losses1)))
        v=np.array(deltas);rg=np.random.default_rng(20261104)
        sim=v[rg.integers(len(v),size=(10000,len(v)))].mean(axis=1)
        results['models'][name]['per_run_logloss_gain_vs_energy']=float(v.mean())
        results['models'][name]['CI95_by_6_heldout_runs']=[float(z) for z in np.quantile(sim,[.025,.975])]
    p=pathlib.Path(args.out);p.mkdir(parents=True,exist_ok=True)
    (p/'pretransition_compensation_transfer.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
if __name__=='__main__':main()
