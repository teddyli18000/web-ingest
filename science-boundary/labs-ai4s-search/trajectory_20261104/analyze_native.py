#!/usr/bin/env python3
"""Exact native MTS trajectory inspection; source-orbit/run boundaries retained."""
import argparse,collections,csv,gzip,json,pathlib,hashlib
import numpy as np

def characterize(bits):
    n=len(bits)
    s=np.fromiter((1 if c=='1' else -1 for c in bits),dtype=np.int16,count=n)
    c=np.correlate(s,s,'full')[n:];k=np.arange(1,n);squared=c.astype(np.int64)**2
    odd=(k%2==1);eodd=int(squared[odd].sum());eeven=int(squared[~odd].sum())
    defect=eodd-int(((n-k[odd])%2).sum())
    if defect<0:raise AssertionError("odd-parity floor violation")
    powers={}
    for p in range(2):
        for b in range(6):
            mask=(odd==(p==0))&(((k-1)*6//(n-1))==b)
            powers[f'spec_{p*6+b}']=float((squared[mask]/(n-k[mask])).mean()) if mask.any() else 0.
    return dict(E=eodd+eeven,odd=eodd,even=eeven,Dodd=defect,
       imbalance=abs(int(s.sum()))/n,
       adj1=sum(bits[i]!=bits[i+1] for i in range(n-1))/(n-1),
       adj2=sum(bits[i]!=bits[i+2] for i in range(n-2))/(n-2),
       triplet=sum(bits[i]==bits[i+1]==bits[i+2] for i in range(n-2))/(n-2),
       **powers)

def hamming(a,b):return sum(x!=y for x,y in zip(a,b))

def near_skew(s):
    def skew(t):
        if len(t)%2==0:return False
        m=len(t)//2
        return all((t[m+j]==t[m-j])==(j%2==0) for j in range(1,m+1))
    return skew(s) if len(s)%2 else skew(s[:-1]) or skew(s[1:])

def dump(path,items,fields):
    with gzip.open(path,'wt',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore')
        w.writeheader();w.writerows(items)

def inspect(path,entry):
    assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
    n=entry['n'];seed=entry['seed']
    starts={};parents=collections.defaultdict(dict);rows=[];records=[];snapshots=[]
    seen=collections.Counter();global_E=10**9;record_time=0.;record_gen=0
    with gzip.open(path,'rt') as f:
        reader=csv.DictReader(f,delimiter='\t')
        assert reader.fieldnames==['event','gen','episode','step','n','energy','best_energy','wall_s','seq','best_seq','tabu_remaining']
        for z in reader:
            tag=z['event'];seen[tag]+=1;g=int(z['gen']);ep=int(z['episode']);t=float(z['wall_s'])
            seq=z['seq'];best=z['best_seq'];assert len(seq)==len(best)==n==int(z['n'])
            curr=characterize(seq);bf=characterize(best)
            if curr['E']!=int(z['energy']) or bf['E']!=int(z['best_energy']):
                raise RuntimeError(f'false energy in {path} {tag} {ep}')
            if tag in ('PARENT_1','PARENT_2'):
                parents[g][tag]=seq
            elif tag=='GA_RECORD':
                assert curr['E']<global_E
                global_E=curr['E'];record_time=t;record_gen=g
                records.append(dict(N=n,seed=seed,gen=g,episode=ep,t=t,E=curr['E'],
                   Eodd=curr['odd'],Eeven=curr['even'],Dodd=curr['Dodd'],near=int(near_skew(seq)),bits=seq))
                if rows and rows[-1]['episode']==ep:rows[-1]['is_global_record']=1
            elif tag=='TS_START':
                starts[ep]=dict(gen=g,seq=seq,E=curr['E'],t=t,feat=curr,
                    gap=curr['E']-global_E,drought_g=g-record_gen,drought_t=t-record_time,
                    parents=parents.pop(g,{}))
            elif tag=='TS_STEP':
                st=starts.get(ep)
                if st:
                    tabu=z['tabu_remaining']
                    active=sum(int(v)>0 for v in tabu.split(',')) if tabu!='-' else 0
                    snapshots.append(dict(N=n,seed=seed,episode=ep,gen=g,step=int(z['step']),
                       t=t,E=curr['E'],Eodd=curr['odd'],Eeven=curr['even'],Dodd=curr['Dodd'],
                       startE=st['E'],startOdd=st['feat']['odd'],startEven=st['feat']['even'],
                       hamming=hamming(st['seq'],seq),tabu_active=active,currentSeq=seq,tabuVector=tabu))
            elif tag=='TS_END':
                st=starts.pop(ep,None)
                if not st:raise RuntimeError('TS_END without TS_START')
                p1=st['parents'].get('PARENT_1');p2=st['parents'].get('PARENT_2')
                gain=st['E']-bf['E'];assert gain>=0
                rows.append(dict(N=n,seed=seed,gen=g,episode=ep,
                    startSeq=st['seq'],endBestSeq=best,endCurrentSeq=seq,
                    parent1Seq=p1 or '',parent2Seq=p2 or '',endTabuRemaining=z['tabu_remaining'],
                    start_time=st['t'],end_time=t,startE=st['E'],endE=bf['E'],
                    endCurrentE=curr['E'],gain=gain,is_global_record=0,
                    oddStart=st['feat']['odd'],oddEnd=bf['odd'],
                    evenStart=st['feat']['even'],evenEnd=bf['even'],
                    deltaOdd=bf['odd']-st['feat']['odd'],deltaEven=bf['even']-st['feat']['even'],
                    DoddStart=st['feat']['Dodd'],DoddEnd=bf['Dodd'],
                    nearStart=int(near_skew(st['seq'])),nearEnd=int(near_skew(best)),
                    hammingBest=hamming(st['seq'],best),hammingCurrent=hamming(st['seq'],seq),
                    parentHamming=hamming(p1,p2) if p1 and p2 else -1,
                    childParent1=hamming(st['seq'],p1) if p1 else -1,
                    childParent2=hamming(st['seq'],p2) if p2 else -1,
                    globalGap=st['gap'] if st['gap']<10**8 else -1,
                    recordDroughtG=st['drought_g'],recordDroughtT=st['drought_t'],
                    imbalance=st['feat']['imbalance'],adj1=st['feat']['adj1'],
                    adj2=st['feat']['adj2'],triplet=st['feat']['triplet'],
                    **{k:st['feat'][k] for k in st['feat'] if k.startswith('spec_')}))
    assert not starts
    assert len(rows)==seen['TS_START']==seen['TS_END']
    assert records and records[-1]['E']==entry['score']
    improvements=[r for r in rows if r['gain']>0]
    comp=[r for r in improvements if r['deltaOdd']>0 and r['deltaEven']<0]
    st=dict(N=n,seed=seed,sampled_episodes=len(rows),ga_records=len(records),
        sampled_local_improvements=len(improvements),
        global_records_from_sampled=sum(r['is_global_record'] for r in rows),
        local_improvement_rate=len(improvements)/len(rows),
        positive_odd_negative_even_ratio=len(comp)/len(improvements) if improvements else None,
        median_best_hamming=float(np.median([r['hammingBest'] for r in improvements])) if improvements else None,
        sampled_steps=len(snapshots),events=dict(seen),finalE=entry['score'])
    return rows,records,snapshots,st

def main():
    p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('--out',required=True)
    a=p.parse_args();root=pathlib.Path(a.root);out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    meta=json.loads((root/'manifest.json').read_text());allrows=[];allrecords=[];allsteps=[];stats=[]
    for entry in meta['jobs']:
        r,c,s,t=inspect(root/entry['trace'],entry)
        allrows.extend(r);allrecords.extend(c);allsteps.extend(s);stats.append(t)
        print('VALIDATED',t['N'],t['seed'],t['sampled_episodes'],'sampled local episodes; record',t['finalE'],flush=True)
    assert allrows and allrecords and allsteps
    dump(out/'episodes.tsv.gz',allrows,list(allrows[0]))
    dump(out/'steps.tsv.gz',allsteps,list(allsteps[0]))
    with (out/'global_records.tsv').open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(allrecords[0]),delimiter='\t');wr.writeheader();wr.writerows(allrecords)
    report={'source_commit':meta['source_commit'],'runs':len(stats),'sampled_episodes':len(allrows),
        'global_records':len(allrecords),'intermediate_snapshots':len(allsteps),'per_run':stats,
        'limits':['native older 2009-era MTS, not 2025 GPU-MTS','global GA record jumps are not consecutive physical spin-flip paths',
          'only gen%4==0 complete episodes, all global records retained','step snapshots every 32 accepted flips',
          'observational labels cannot establish a causal generative improvement']}
    (out/'structural_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS all native frame energies; episodes',len(allrows),'global records',len(allrecords),
        'snapshots',len(allsteps))
if __name__=='__main__':main()
