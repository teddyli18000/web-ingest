#!/usr/bin/env python3
"""Leakage-controlled cross-length observational representation ablation for native MTS."""
import argparse,json,pathlib
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import average_precision_score,roc_auc_score,log_loss,brier_score_loss

BASE=['energy_per_spin','energy_density','global_gap_norm','log_record_drought','record_drought_time','log_gen','N']
BITS=['imbalance','adj1','adj2','triplet','parent_gap','child_parent1','child_parent2']
SPECTRAL=['odd_defect_norm']+[f'spec_{i}' for i in range(12)]
FEATURES={'constant':[], 'energy_history':BASE,
          'energy_plus_spectrum':BASE+SPECTRAL,
          'energy_plus_bits':BASE+BITS,
          'combined':BASE+SPECTRAL+BITS}

def scores(y,p):
    y=np.asarray(y,int);p=np.clip(np.asarray(p,float),1e-7,1-1e-7)
    return dict(log_loss=float(log_loss(y,p,labels=[0,1])),brier=float(brier_score_loss(y,p)),
           avg_precision=float(average_precision_score(y,p)) if y.sum()>0 else None,
           auc=float(roc_auc_score(y,p)) if len(set(y))==2 else None)

def run(df,out):
    df['energy_per_spin']=df.startE/df.N
    df['energy_density']=df.startE/(df.N*df.N)
    df['global_gap_norm']=df.globalGap.clip(lower=0)/df.N
    df['log_record_drought']=np.log1p(df.recordDroughtG.clip(lower=0))
    df['record_drought_time']=np.log1p(df.recordDroughtT.clip(lower=0))
    df['log_gen']=np.log1p(df.gen.clip(lower=0))
    df['odd_defect_norm']=df.DoddStart/df.N
    df['parent_gap']=df.parentHamming.clip(lower=0)/df.N
    df['child_parent1']=df.childParent1.clip(lower=0)/df.N
    df['child_parent2']=df.childParent2.clip(lower=0)/df.N
    df['run']=df.N.astype(str)+'_'+df.seed.astype(str)
    train=df[df.N.isin([48,64,80])].copy()
    test=df[df.N.isin([92,99,100])].copy()
    assert set(train.run).isdisjoint(set(test.run))
    assert set(train.N)=={48,64,80} and set(test.N)=={92,99,100}
    # Uniform per-run subsampling does not condition on outcome.
    train=pd.concat([g.sample(n=min(12000,len(g)),random_state=7711) for _,g in train.groupby('run')],ignore_index=True)
    test=pd.concat([g.sample(n=min(16000,len(g)),random_state=7711) for _,g in test.groupby('run')],ignore_index=True)
    result={'protocol':'disjoint heldout lengths, zero test-based hyperparameter tuning',
            'train_N':sorted(train.N.unique().tolist()),'test_N':sorted(test.N.unique().tolist()),
            'train_rows':len(train),'test_rows':len(test),'targets':{}}
    for target,lab in [('local_improve',lambda x:(x.gain>0).astype(int)),
                       ('global_record',lambda x:x.is_global_record.astype(int))]:
        ytrain=lab(train).to_numpy();ytest=lab(test).to_numpy()
        item={'train_positives':int(ytrain.sum()),'test_positives':int(ytest.sum()),
              'train_rate':float(ytrain.mean()),'test_rate':float(ytest.mean()),'models':{}}
        if min(ytrain.sum(),ytest.sum(),len(ytrain)-ytrain.sum(),len(ytest)-ytest.sum())<15:
            item['status']='insufficient class events for defensible cross-length inference'
            result['targets'][target]=item
            continue
        pp={}
        for name,cols in FEATURES.items():
            if not cols:p=np.repeat(float(ytrain.mean()),len(test))
            else:
                model=make_pipeline(StandardScaler(),LogisticRegression(C=.2,max_iter=500))
                model.fit(train[cols].fillna(0),ytrain)
                p=model.predict_proba(test[cols].fillna(0))[:,1]
            pp[name]=p
            item['models'][name]=scores(ytest,p)
        # Entire runs (not event rows) are clustered for uncertainty.
        run_ids=test.run.to_numpy(); runs=sorted(set(run_ids))
        rng=np.random.default_rng(20261104)
        for name in ['energy_plus_spectrum','energy_plus_bits','combined']:
            deltas=[]
            for rid in runs:
                k=run_ids==rid;y=ytest[k]
                p0=np.clip(pp['energy_history'][k],1e-7,1-1e-7)
                p1=np.clip(pp[name][k],1e-7,1-1e-7)
                base=-y*np.log(p0)-(1-y)*np.log(1-p0)
                advanced=-y*np.log(p1)-(1-y)*np.log(1-p1)
                deltas.append(float(np.mean(base-advanced)))
            vec=np.array(deltas)
            boots=vec[rng.integers(len(vec),size=(2000,len(vec)))].mean(axis=1)
            item['models'][name]['mean_run_logloss_benefit_vs_energy']=float(vec.mean())
            item['models'][name]['source_run_boot95']=list(np.quantile(boots,[.025,.975]))
        result['targets'][target]=item
    out.mkdir(parents=True,exist_ok=True)
    (out/'crosslength_ablation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('episodes');p.add_argument('--out',required=True)
    a=p.parse_args();run(pd.read_csv(a.episodes,sep='\t'),pathlib.Path(a.out))
