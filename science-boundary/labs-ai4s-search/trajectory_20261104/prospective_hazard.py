#!/usr/bin/env python3
"""Prospective LABS breakthrough hazard from native Tabu state snapshots.

At TS_STEP t, condition solely on *past* stall >=64 accepted flips.
Label: a new TS_BEST event at time (t,t+64] in same episode.
Require TS_END >= t+64, exclude censored horizons. No GA record jumps.
Train on 48/64/80; test all 92/99/100 independent runs. No target bits.
"""
import argparse,csv,gzip,json,pathlib
from bisect import bisect_right
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score,average_precision_score,log_loss,brier_score_loss

def spec(bits):
    n=len(bits)
    s=np.where(np.frombuffer(bits.encode('ascii'),dtype=np.uint8)==49,1,-1).astype(np.int16)
    c=np.correlate(s,s,'full')[n:].astype(np.int64)
    k=np.arange(1,n)
    power=c*c/(n-k)
    odd=(k%2==1)
    a={'odd_share':float((c[odd]**2).sum()/(c*c).sum()),
       'Dodd_norm':float(((c[odd]**2).sum()-((n-k[odd])&1).sum())/n),
       'imbalance':float(abs(s.sum())/n),
       'bit_adj1':float((s[:-1]*s[1:]).mean()),'bit_adj2':float((s[:-2]*s[2:]).mean())}
    for p in (0,1):
        for b in range(6):
            v=power[((k&1)==p)&((6*(k-1)//(n-1))==b)]
            a[f'spec_{p}_{b}']=float(v.mean()) if len(v) else 0.
    return a

def process(root,job,horizon,stalled):
    path=root/job['trace'];n=job['n'];seed=job['seed']
    episodes={};samples=[];starts=0
    with gzip.open(path,'rt') as f:
        for z in csv.DictReader(f,delimiter='\t'):
            typ=z['event'];ep=int(z['episode']);step=int(z['step'])
            if typ=='TS_START':
                assert ep not in episodes
                episodes[ep]={'best_steps':[],'snaps':[],'end':None,'last_best':0}
                starts+=1
            elif typ=='TS_BEST':
                state=episodes[ep]
                state['best_steps'].append(step);state['last_best']=step
            elif typ=='TS_STEP':
                state=episodes[ep];age=step-state['last_best']
                if age<stalled:continue
                a=spec(z['seq'])
                tabu=z['tabu_remaining']
                active=sum(int(v)>0 for v in tabu.split(',')) if tabu!='-' else 0
                row={'N':n,'seed':seed,'episode':ep,'t':step,'stall_age':age,
                     'bestE':int(z['best_energy']),'currentE':int(z['energy']),
                     'E_gap':int(z['energy'])-int(z['best_energy']),
                     'tabu_active':active,'run':f'{n}_{seed}'}
                row.update(a)
                state['snaps'].append(row)
            elif typ=='TS_END':
                state=episodes.pop(ep)
                end=step;steps=state['best_steps']
                for row in state['snaps']:
                    if row['t']+horizon>end:continue
                    j=bisect_right(steps,row['t'])
                    row['positive']=int(j<len(steps) and steps[j]<=row['t']+horizon)
                    samples.append(row)
    assert not episodes and starts==job['events']['TS_START']
    return samples,starts

BASE=['N','bestE_per_n','currentE_per_n','gap_per_n','stall_per_n','tabu_active_per_n']
PARITY=['odd_share','Dodd_norm']
SPECTRAL=[f'spec_{p}_{b}' for p in (0,1) for b in range(6)]
BITS=['imbalance','bit_adj1','bit_adj2']
GROUPS={'constant':[],'history':BASE,'parity':BASE+PARITY,'spectrum':BASE+SPECTRAL,
        'bits':BASE+BITS,'full_spectrum_bits':BASE+PARITY+SPECTRAL+BITS}

def metrics(y,p):
    p=np.clip(p,1.e-6,1-1.e-6)
    return {'logloss':float(log_loss(y,p,labels=[0,1])),
            'brier':float(brier_score_loss(y,p)),
            'auprc':float(average_precision_score(y,p)) if sum(y)>0 else None,
            'auc':float(roc_auc_score(y,p)) if len(set(y))==2 else None}

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument('root')
    arg.add_argument('--out',required=True)
    arg.add_argument('--horizon',type=int,default=64)
    arg.add_argument('--stall',type=int,default=64)
    a=arg.parse_args()
    root=pathlib.Path(a.root);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((root/'manifest.json').read_text())
    data=[];epcount=0
    for job in meta['jobs']:
        x,c=process(root,job,a.horizon,a.stall);epcount+=c;data.extend(x)
        print('RUN',job['n'],job['seed'],'eligible',len(x),'positive',sum(q['positive'] for q in x),flush=True)
    df=pd.DataFrame(data)
    if df.empty:raise RuntimeError('no uncensored stalled episodes')
    df['bestE_per_n']=df.bestE/df.N
    df['currentE_per_n']=df.currentE/df.N
    df['gap_per_n']=df.E_gap/df.N
    df['stall_per_n']=df.stall_age/df.N
    df['tabu_active_per_n']=df.tabu_active/df.N
    assert (df.stall_age>=a.stall).all()
    assert set(df.N)=={48,64,80,92,99,100},'must contain all six lengths'
    df.to_csv(out/'prospective_hazard_samples.tsv.gz',sep='\t',index=False,compression='gzip')
    train=df[df.N.isin([48,64,80])].copy()
    test=df[df.N.isin([92,99,100])].copy()
    assert set(train.run).isdisjoint(set(test.run))
    result={'scope':'Prospective next-64-accepted-move TS_BEST improvement from TS_STEP stalled >=64; fully uncensored windows only',
       'all_rows':len(df),'episodes':epcount,'train_rows':len(train),'test_rows':len(test),
       'train_positives':int(train.positive.sum()),'test_positives':int(test.positive.sum()),
       'by_run':{},'models':{}}
    for (n,seed),sub in df.groupby(['N','seed']):
        result['by_run'][f'{n}_{seed}']={'eligible':len(sub),'positive':int(sub.positive.sum()),'rate':float(sub.positive.mean())}
    if min(int(train.positive.sum()),int(test.positive.sum()),
           len(train)-int(train.positive.sum()),len(test)-int(test.positive.sum()))<20:
        result['gate']='insufficient positive or negative hazard labels; no model trained'
    else:
        ytrain=train.positive.to_numpy();ytest=test.positive.to_numpy()
        preds={}
        for name,cols in GROUPS.items():
            if not cols:p=np.repeat(float(ytrain.mean()),len(test))
            else:
                model=make_pipeline(StandardScaler(),LogisticRegression(C=.2,max_iter=500))
                model.fit(train[cols],ytrain);p=model.predict_proba(test[cols])[:,1]
            preds[name]=p
            result['models'][name]=metrics(ytest,p)
        base=preds['history']
        for name in GROUPS:
            if name in ('constant','history'):continue
            gain=[]
            for rid,sub in test.groupby('run'):
                idx=np.where(test.run.to_numpy()==rid)[0]
                y=ytest[idx]
                b=np.clip(base[idx],1.e-6,1-1.e-6)
                p=np.clip(preds[name][idx],1.e-6,1-1.e-6)
                lb=-(y*np.log(b)+(1-y)*np.log(1-b))
                lp=-(y*np.log(p)+(1-y)*np.log(1-p))
                gain.append(float((lb-lp).mean()))
            rg=np.random.default_rng(20261104);v=np.array(gain)
            sims=v[rg.integers(len(v),size=(10000,len(v)))].mean(axis=1)
            result['models'][name]['mean_run_logloss_gain_vs_history']=float(v.mean())
            result['models'][name]['CI95_6_independent_heldout_runs']=list(np.quantile(sims,[.025,.975]).astype(float))
        result['gate']='observational label only, not a demonstrated intervention policy'
    (out/'prospective_hazard.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
