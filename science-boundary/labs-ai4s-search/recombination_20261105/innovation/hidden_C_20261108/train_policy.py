#!/usr/bin/env python3
"""Train cheap pre-repair post-LABS-repair predictor without using any C identity.

N46 fits parameters. N47 selects regularization only. N50 unseen and entirely
unavailable to this script. No raw bits, parent IDs, or hidden target labels in X.
"""
import argparse,hashlib,json,pathlib,time
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

F=16
BASE=[0,1,2,3,5,12,13,14,15]
FULL=list(range(F))
ALPHAS=[.1,1.,10.,100.]
def load(path,n,exclude_noop=False):
    d=pd.read_csv(path,sep='\t',dtype={'id':str,'repairBits':str,'repairCanon':str})
    assert set(d.n)=={n} and (d.repairSteps==64).all()
    if exclude_noop:d=d[d.proposal_index>0].copy()
    assert d['id'].nunique()>10 and d[['id','round','proposal_index']].duplicated().sum()==0
    assert d.groupby(['id','round']).size().eq(5 if exclude_noop else 6).all()
    assert (d.repairE>0).all()
    return d

def summarize(d,pred):
    arr=pd.DataFrame({'id':d.id.to_numpy(),'round':d['round'].to_numpy(),
      'pred':pred,'raw':d.rawE.to_numpy(),'actual':d.repairE.to_numpy()})
    best=[];raw=[];oracle=[]
    for _,g in arr.groupby(['id','round'],sort=False):
        best.append(float(g.loc[g.pred.idxmin(),'actual']))
        raw.append(float(g.loc[g.raw.idxmin(),'actual']))
        oracle.append(float(g.actual.min()))
    return {'banks':len(best),'selected_mean_repairedE':float(np.mean(best)),
        'rawE_ranking_mean_repairedE':float(np.mean(raw)),
        'unusable_lookahead_oracle_mean_repairedE':float(np.mean(oracle)),
        'ranking_gain_vs_rawE':float(np.mean(raw)-np.mean(best))}
def select(tr,va,idx):
    xtr=tr[[f'f{i}' for i in idx]].to_numpy(float)
    xva=va[[f'f{i}' for i in idx]].to_numpy(float)
    ytr=tr.repairE.to_numpy(float)/tr.n.to_numpy(float)
    yva=va.repairE.to_numpy(float)/va.n.to_numpy(float)
    alternatives=[]
    for alpha in ALPHAS:
        pipe=make_pipeline(StandardScaler(),Ridge(alpha=alpha))
        pipe.fit(xtr,ytr)
        pred=pipe.predict(xva)*va.n.to_numpy(float)
        st=summarize(va,pred)
        st.update(alpha=alpha,valid_mse=float(np.mean((pred-va.repairE.to_numpy(float))**2)))
        alternatives.append((st,pipe))
    alternatives.sort(key=lambda p:(p[0]['selected_mean_repairedE'],p[0]['valid_mse'],p[0]['alpha']))
    chosen,pipe=alternatives[0]
    scaler,ridge=pipe.steps[0][1],pipe.steps[1][1]
    rawcoef=ridge.coef_/scaler.scale_
    intercept=float(ridge.intercept_-np.dot(rawcoef,scaler.mean_))
    coef=np.zeros(F)
    for j,i in enumerate(idx):coef[i]=rawcoef[j]
    # Model predicts E/N; multiplying by N is not needed to rank candidates
    return chosen,coef,intercept,[v[0] for v in alternatives]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--train',required=True);ap.add_argument('--validation',required=True)
    ap.add_argument('--output-dir',required=True)
    ap.add_argument('--exclude-noop',action='store_true')
    a=ap.parse_args();start=time.perf_counter()
    tr=load(a.train,46,a.exclude_noop);va=load(a.validation,47,a.exclude_noop)
    assert set(tr.id).isdisjoint(set(va.id))
    out=pathlib.Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    models={};results={}
    for name,indices in [('base',BASE),('full',FULL)]:
        chosen,coef,intercept,alts=select(tr,va,indices)
        models[name]=(coef,intercept)
        results[name]={'chosen':chosen,'all_validation_alphas':alts,'indices':indices}
    f=out/'frozen_models.tsv'
    with f.open('w') as w:
        w.write('model\tintercept' + ''.join(f'\tf{i}' for i in range(F))+'\n')
        for name in ('base','full'):
            coef,intercept=models[name]
            w.write(name+'\t'+format(intercept,'.17g')+''.join('\t'+format(float(c),'.17g') for c in coef)+'\n')
    info={'train_N':[46],'validation_N':[47],'test_N':[50],
      'C_target_labels_used_in_training_or_validation':False,
      'raw_optimum_target_words_used_in_model':False,
      'source_orbit_identifiers_used_in_features':False,
      'excluded_trivial_original_candidate':a.exclude_noop,
      'train_rows':len(tr),'validation_rows':len(va),
      'train_scenarios':tr.id.nunique(),'validation_scenarios':va.id.nunique(),
      'model_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
      'training_wall_s':float(time.perf_counter()-start),
      'models':results,
      'limitation':'Model predicts postrepair E/N, NOT hidden C identity or probability. Full features add exact signed cross-parent correlation and mask epistasis.'}
    (out/'training_audit.json').write_text(json.dumps(info,indent=2)+'\n')
    print(json.dumps(info,indent=2))
if __name__=='__main__':main()
