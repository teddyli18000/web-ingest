#!/usr/bin/env python3
"""Native plateau-breaking best-event changes, not episode-level easy repair.

Input: already committed exact-verified lossless native MTS traces.
Condition on each episode's actual accepted one-spin step count between
consecutive TS_BEST events. Do not conflate GA global records or endpoints.
"""
import argparse, csv, gzip, json, pathlib, collections
import numpy as np
import pandas as pd

def features(bits):
    a=np.frombuffer(bits.encode('ascii'),dtype=np.uint8)
    assert np.all((a==48)|(a==49))
    z=np.where(a==49,1,-1).astype(np.int16)
    c=np.correlate(z,z,'full')[len(z):].astype(np.int64)
    odd=int(np.dot(c[::2],c[::2]))
    even=int(np.dot(c[1::2],c[1::2]))
    floor=sum(((len(z)-k)&1) for k in range(1,len(z),2))
    return odd,even,odd-floor

def stream_events(root,job):
    n=int(job['n']);seed=int(job['seed'])
    path=root/job['trace']
    active={};results=[];all_starts=0;global_best=10**9
    with gzip.open(path,'rt') as f:
        for rec in csv.DictReader(f,delimiter='\t'):
            event=rec['event'];ep=int(rec['episode']);step=int(rec['step']);g=int(rec['gen'])
            if event=='GA_RECORD':
                global_best=min(global_best,int(rec['energy']))
            elif event=='TS_START':
                bits=rec['best_seq'];o,e,d=features(bits)
                assert o+e==int(rec['best_energy'])
                assert ep not in active
                active[ep]=dict(N=n,seed=seed,episode=ep,gen=g,
                    prevE=o+e,odd=o,even=e,Dodd=d,seq=bits,
                    prevstep=0,startE=o+e,global_at_start=global_best,
                    events=0,late_events=0)
                all_starts+=1
            elif event=='TS_BEST':
                prev=active.get(ep)
                if prev is None:raise AssertionError('missing TS_START')
                bits=rec['best_seq'];o,e,d=features(bits)
                newE=o+e
                delta_odd=o-prev['odd'];delta_even=e-prev['even']
                gap=step-prev['prevstep']
                assert newE==int(rec['best_energy']) and newE<prev['prevE']
                assert delta_odd+delta_even==newE-prev['prevE']
                hd=sum(a!=b for a,b in zip(prev['seq'],bits))
                if gap<0:raise AssertionError('nonmonotone TS_BEST steps')
                results.append(dict(N=n,seed=seed,gen=g,episode=ep,step=step,
                    gap_steps=gap,changed_positions=hd,
                    oldE=prev['prevE'],newE=newE,improvement=prev['prevE']-newE,
                    oldSeq=prev['seq'],newSeq=bits,
                    startE=prev['startE'],global_at_start=prev['global_at_start'],
                    oldOdd=prev['odd'],newOdd=o,deltaOdd=delta_odd,
                    oldEven=prev['even'],newEven=e,deltaEven=delta_even,
                    oldDodd=prev['Dodd'],newDodd=d,
                    odd_cost_even_repair=int(delta_odd>0 and delta_even<0),
                    even_cost_odd_repair=int(delta_even>0 and delta_odd<0),
                    both_decrease=int(delta_odd<0 and delta_even<0),
                    evolved_with_multi_steps=int(gap>1),
                    distance_ge4=int(hd>=4)))
                prev.update(prevE=newE,odd=o,even=e,Dodd=d,seq=bits,prevstep=step)
                prev['events']+=1
                prev['late_events']+=int(gap>=32)
            elif event=='TS_END':
                prev=active.pop(ep,None)
                assert prev is not None
                assert int(rec['best_energy'])==prev['prevE']
    assert not active and all_starts==job['events']['TS_START']
    return results,all_starts

def summarize(df):
    for threshold in [1,2,4,8,16,32,64,128]:
        sub=df[df.gap_steps>=threshold]
        if sub.empty:continue
        print('gap>=',threshold,'events',len(sub),'runs',sub.run.nunique(),
            'odd-cost-even-repair',round(sub.odd_cost_even_repair.mean(),4),
            'even-cost-odd-repair',round(sub.even_cost_odd_repair.mean(),4),
            'both-decrease',round(sub.both_decrease.mean(),4),
            'mean_hd',round(sub.changed_positions.mean(),2))
    result={}
    for threshold in [1,8,16,32,64,128]:
        sub=df[df.gap_steps>=threshold]
        r=[]
        for (n,seed),g in sub.groupby(['N','seed']):
            r.append(dict(N=int(n),seed=int(seed),n=len(g),
                odd_cost_even_repair=float(g.odd_cost_even_repair.mean()),
                mean_hamming=float(g.changed_positions.mean()),
                both_decrease=float(g.both_decrease.mean()),
                median_gain=float(g.improvement.median())))
        result[str(threshold)]=r
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument('root')
    p.add_argument('--output',required=True)
    args=p.parse_args()
    root=pathlib.Path(args.root);out=pathlib.Path(args.output);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((root/'manifest.json').read_text())
    rows=[];episode_total=0
    for job in manifest['jobs']:
        r,c=stream_events(root,job);rows.extend(r);episode_total+=c
        print('N',job['n'],'seed',job['seed'],'best updates',len(r),'episodes',c,flush=True)
    df=pd.DataFrame(rows)
    assert len(df)==sum(j['events']['TS_BEST'] for j in manifest['jobs'])
    df['run']=df.N.astype(str)+'_'+df.seed.astype(str)
    assert (df.improvement>0).all()
    assert (df.deltaOdd+df.deltaEven==-df.improvement).all()
    df.to_csv(out/'native_best_transitions.tsv.gz',sep='\t',index=False,compression='gzip')
    b=summarize(df)
    result={'source':'pinned original native lMAts, exact TS_BEST accepted local-best events',
       'runs':df.run.nunique(),'episodes':episode_total,'events':len(df),
       'threshold_descriptives':b,
       'caveats':[
        'TS_BEST updates are local episode bests, not all global breakthroughs',
        'gap_steps counts accepted single-spin moves between native best events',
        'intermediate TS_STEP samples are incomplete, but every TS_BEST is stored in sampled generations',
        'sampling generations every128 means no exact population-level episode representativeness',
        'correlation compensation is descriptive, not a learned policy or rare-record causal advantage']}
    (out/'native_plateau_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(df),'exact native best transitions from',episode_total,'sampled episodes')

if __name__=='__main__':main()
