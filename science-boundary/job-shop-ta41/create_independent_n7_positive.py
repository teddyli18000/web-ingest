#!/usr/bin/env python3
"""Build independent N7 local-optimum 30x20 positive benchmark starts.

Search *starts from the author's random active constructor* and is NOT
seeded with the published reference answer. Each start is a full
time-stamped native genuine published N7 schedule and is independently
validated. The original published oracle is read by this generator ONLY
for later evaluation and ensuring that at least one better legal schedule
is known to exist. No oracle machine-order sequence is emitted anywhere.

This tests genuine independent high-quality basins, rather than trivially
undoing mutations of a published answer.
"""
import argparse,csv,json,subprocess,time
from pathlib import Path
from create_hidden_positive_cases import SELECTED,load_case
from search import evaluate

def main(a):
    data=json.loads((a.reference_root/'jobshop'/'solutions'/'solutions.json').read_text())
    cases=[]
    a.out.mkdir(parents=True,exist_ok=True)
    for name in SELECTED:
        routes,durs,oracle,known,pos,duration=load_case(a.reference_root,name,data)
        for seed in a.seeds:
            folder=a.out/f'{name}-n7elite{seed}'
            folder.mkdir(parents=True,exist_ok=True)
            instance=folder/'instance.txt'
            with instance.open('w') as f:
                f.write('30 20\n')
                for j in range(30):
                    f.write(' '.join(f'{routes[j][k]} {durs[j][k]}' for k in range(20))+'\n')
            out=folder/'native.csv'
            command=[str(a.driver),str(instance),str(out),str(a.seconds),str(seed)]
            p=subprocess.run(command,text=True,capture_output=True,check=False,timeout=a.seconds+40)
            assert p.returncode==0,(name,seed,p.stderr[-2000:])
            stats=p.stdout.strip().split()
            assert len(stats)==4 and stats[0]=='RESULT'
            native_score=int(stats[1])
            starttimes=[[] for _ in range(20)];seen=set()
            with out.open() as f:
                for row in csv.DictReader(f):
                    j=int(row['Job'])-1;k=int(row['Operation'])-1
                    m=int(row['Machine']);start=int(row['StartTime']);end=int(row['EndTime'])
                    assert (j,k) not in seen and routes[j][k]==m
                    assert end-start==durs[j][k]
                    seen.add((j,k));starttimes[m].append((start,j))
            assert len(seen)==600 and all(len(x)==30 for x in starttimes)
            orders=[[j for t,j in sorted(x)] for x in starttimes]
            independent=evaluate(orders,pos,duration)
            assert independent==native_score and independent>0
            assert independent>known,(name,seed,independent,known)
            with (folder/'start.txt').open('w') as f:
                f.write(instance.read_text())
                for row in orders:f.write(' '.join(map(str,row))+'\n')
            out.unlink();instance.unlink()
            cases.append(dict(case=folder.name,instance=name,
                independently_constructed_start=independent,
                hidden_oracle_makespan=known,
                certified_positive_gap=independent-known,
                actual_source='Qiming01/Job-Shop-Scheduling published N7 2025',
                source_pin='7e120ebada21cb604c871e0657814bf6e32611f8',
                cold_initialization_seed=seed,
                original_N7_seconds=a.seconds,
                iterations=int(stats[2]),
                cross_checked_native_and_python=True,
                hidden_oracle_never_passed_to_search=True))
            print('INDEPENDENT-ELITE',folder.name,'native',native_score,'oracle',known,
                  'known improvable',independent-known,flush=True)
    (a.out/'manifest.json').write_text(json.dumps({'independent_elites':True,'cases':cases,
        'hiding':'Only 30x20 instance and N7 native solution passed to downstream algorithms; oracle metadata remains for judging.'},indent=2)+'\n')
    assert len(cases)==len(SELECTED)*len(a.seeds)
    print('RESULT',len(cases),'independently generated genuine N7 elite starts',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--reference-root',type=Path,required=True)
    p.add_argument('--driver',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=20)
    p.add_argument('--seeds',nargs='+',type=int,default=[1701,1711])
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
