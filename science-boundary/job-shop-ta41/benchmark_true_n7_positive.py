#!/usr/bin/env python3
"""True published N7 Tabu on exact same hidden-answer 30x20 starts.

Only author code changes: an AGPL-compatible start-machine-order loading
hook (already published and audited), plus *driver-only* removal of
ta41-specific initial=2006 and early-stop=2005 assumptions. NO changes
to the original N7 find_move, score approximation, tabu memory or search.

Verify native output's complete 600 timed operations against independent
source route/duration and DAG, not merely the C++ reported makespan.
The search never reads source oracle solutions or manifest.
"""
import argparse,csv,json,subprocess,tempfile,time
from pathlib import Path
from search import evaluate
from benchmark_hidden_positive import load_start

ROOT=Path(__file__).resolve().parent

def main(a):
    a.out.mkdir(parents=True,exist_ok=True)
    trials=[]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for folder in sorted(p for p in a.cases.iterdir() if p.is_dir() and (p/'start.txt').is_file()):
            path=folder/'start.txt'
            data=path.read_text().splitlines()
            assert len(data)==51 and data[0].strip()=='30 20'
            pos,durs,initial=load_start(path)
            instance=tmp/'instance.txt'
            orders=tmp/'warm-orders.txt'
            native=tmp/'operations.csv'
            instance.write_text('\n'.join(data[:31])+'\n')
            orders.write_text('\n'.join(data[31:])+'\n')
            for seed in a.seeds:
                t=time.monotonic()
                output=subprocess.run(
                    [str(a.driver),str(instance),str(native),str(a.seconds),str(seed),str(orders)],
                    text=True,capture_output=True,check=False,timeout=a.seconds+40)
                assert output.returncode==0,(folder.name,seed,output.stderr[-3000:])
                stats=output.stdout.strip().split()
                assert stats[0]=='RESULT' and len(stats)==4,stats
                score=int(stats[1])
                starts=[[] for _ in range(20)]
                routes=[[None]*20 for _ in range(30)]
                durations=[[None]*20 for _ in range(30)]
                tokens=list(map(int,path.read_text().split()))
                cursor=2
                for j in range(30):
                    for k in range(20):
                        routes[j][k]=tokens[cursor];durations[j][k]=tokens[cursor+1];cursor+=2
                seen=set()
                with native.open() as f:
                    for row in csv.DictReader(f):
                        j=int(row['Job'])-1;k=int(row['Operation'])-1
                        m=int(row['Machine'])
                        st=int(row['StartTime']);en=int(row['EndTime'])
                        assert (j,k) not in seen
                        seen.add((j,k))
                        assert routes[j][k]==m
                        assert en-st==durations[j][k]
                        starts[m].append((st,j))
                assert len(seen)==600 and all(len(v)==30 for v in starts)
                candidate=[[j for _,j in sorted(v)] for v in starts]
                verified=evaluate(candidate,pos,durs)
                assert verified==score and verified<=initial,(folder.name,seed,verified,score,initial)
                result={'case':folder.name,'seed':seed,'policy':'true-n7',
                        'start_score':initial,'best_score':score,'improvement':initial-score,
                        'native_iterations':int(stats[2]),
                        'native_seconds':float(stats[3]),
                        'wall_seconds':round(time.monotonic()-t,3),
                        'verified_all_600_operation_start_end_times':True,
                        'independent_DAG_makespan':verified,
                        'authors_original_N7_search_unchanged':True,
                        'warmstart_hook_only':True}
                trials.append(result)
                (a.out/'partial-results.json').write_text(json.dumps({'trials':trials,'complete':False},indent=2)+'\n')
                print('N7',folder.name,seed,'initial',initial,'score',score,flush=True)
    result={'experiment':'30x20 held-out positive controls',
            'source':'Qiming01/Job-Shop-Scheduling@7e120ebada21cb604c871e0657814bf6e32611f8',
            'original_author_N7_kernel_unmodified':True,'runtime_seconds_per_case':a.seconds,
            'complete':True,'trials':trials}
    (a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',len(trials),'original N7 comparisons',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cases',type=Path,required=True)
    p.add_argument('--driver',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=5)
    p.add_argument('--seeds',type=int,nargs='+',default=[4107,4113])
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
