#!/usr/bin/env python3
"""Independent frame-by-frame exact LABS verifier for native GA+Tabu trajectories.
Uses numpy C-level correlation rather than expensive nested Python loops.
"""
import argparse,csv,gzip,hashlib,json,pathlib,time
from collections import Counter
import numpy as np

def score(bits):
    a=np.frombuffer(bits.encode('ascii'),dtype=np.uint8)
    if not np.all((a==48)|(a==49)):raise ValueError('non-binary state')
    s=np.where(a==49,1,-1).astype(np.int16)
    c=np.correlate(s,s,'full')[len(s):].astype(np.int64)
    return int(c@c)

def inspect_trace(file,expected_n,declared_events=None):
    counters=Counter();episodes={};records=[];steps=0
    with gzip.open(file,'rt',newline='') as f:
        reader=csv.DictReader(f,delimiter='\t')
        assert reader.fieldnames==['event','gen','episode','step','n','energy','best_energy','wall_s','seq','best_seq','tabu_remaining']
        for row in reader:
            kind=row['event'];counters[kind]+=1
            n=int(row['n']);assert n==expected_n
            seq=row['seq'];best=row['best_seq']
            assert len(seq)==len(best)==n
            ce=score(seq);be=score(best)
            if ce!=int(row['energy']) or be!=int(row['best_energy']):
                raise AssertionError(f'{file.name} {kind}: recomputed {ce}/{be}, reported {row["energy"]}/{row["best_energy"]}')
            ep=int(row['episode']);step=int(row['step'])
            if kind=='TS_START':
                assert ep not in episodes and step==0 and ce==be
                episodes[ep]={'best':ce,'laststep':0}
            elif kind in ('TS_STEP','TS_BEST','TS_END'):
                assert ep in episodes,(kind,ep)
                e=episodes[ep]
                assert step>=e['laststep'],(kind,step,e['laststep'])
                assert be<=e['best'],(kind,be,e['best'])
                if kind=='TS_BEST':assert be<e['best']
                e['best']=be;e['laststep']=step
                if kind=='TS_END':del episodes[ep]
                if kind=='TS_STEP':steps+=1
            elif kind=='GA_RECORD':
                assert not records or ce<records[-1]
                records.append(ce)
            if kind in ('TS_START','TS_STEP','TS_BEST','TS_END'):
                expiry=row['tabu_remaining'].split(',')
                assert len(expiry)==n
                assert all(int(x)>=0 for x in expiry)
    assert not episodes and counters['TS_START']==counters['TS_END']>0
    assert records
    if declared_events is not None:assert counters==Counter(declared_events)
    return dict(events=sum(counters.values()),event_counts=dict(counters),episodes=counters['TS_START'],
        records=len(records),global_best=records[-1],sampled_steps=steps)

def main():
    p=argparse.ArgumentParser();p.add_argument('roots',nargs='+');p.add_argument('--summary',required=True)
    a=p.parse_args();output={};start=time.monotonic()
    for source in a.roots:
        root=pathlib.Path(source);manifest=json.loads((root/'manifest.json').read_text())
        details=[]
        for job in manifest['jobs']:
            path=root/job['trace']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==job['sha256']
            t=inspect_trace(path,int(job['n']),job['events'])
            assert t['global_best']==int(job['score']) and t['events']==int(job['total_events'])
            details.append(dict(source=path.name,n=job['n'],seed=job['seed'],**t))
            print('VERIFIED',path.name,'events',t['events'],'episodes',t['episodes'],'records',t['records'],flush=True)
        output[str(root)]=dict(runs=len(details),verified_events=sum(z['events'] for z in details),details=details)
    output['elapsed_s']=time.monotonic()-start
    pathlib.Path(a.summary).write_text(json.dumps(output,indent=2)+'\n')
    print('PASS full independent frame verification, elapsed seconds',output['elapsed_s'])

if __name__=='__main__':main()
