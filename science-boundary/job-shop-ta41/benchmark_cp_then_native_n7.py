#!/usr/bin/env python3
"""Source-native N7 continuation from a 5-second joint CP/LNS improved schedule.

All inputs are from published N7's original 20s cold starts, followed by
our fixed five-second CP job-release radius ladder. We subsequently give
the UNMODIFIED published author N7 local search five more seconds starting
from the CP ladder's best complete machine order, with author warmstart
hook only. Independently reconstruct operation start/end times from N7's
CSV and its 600-operation job and machine precedence DAG.

This is a 5s CP -> 5s source native N7 sequential **cross-representation**
candidate, to compare prospectively against original native N7 10s from the
same start. Historical target/oracle permutations are never read.
"""
import argparse,csv,json,subprocess,tempfile,time
from pathlib import Path
from benchmark_hidden_positive import load_start
from search import evaluate
ROOT=Path(__file__).resolve().parent

def main(a):
    cases=sorted(a.cases.glob('ta*js-n7elite*/start.txt'))
    assert len(cases)==12
    ladder=json.loads((ROOT/'results'/f'job-radius-ladder-s{a.seed}'/'results.json').read_text())
    assert ladder['complete'] and ladder['trials']==12
    prior={(x['case'],x['seed']):x for x in ladder['sample']}
    a.out.mkdir(parents=True,exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for path in cases:
            original=path.read_text().splitlines()
            assert len(original)==51
            case=path.parent.name
            entry=prior[case,a.seed]
            pos,durs,source_score=load_start(path)
            assert entry['initial']==source_score
            if entry['best_score']<source_score:
                certificate=ROOT/'results'/f'job-radius-ladder-s{a.seed}'/f'{case}-seed{a.seed}-certificate.json'
                machine_orders=json.loads(certificate.read_text())['machines']
            else:
                machine_orders=[list(map(int,x.split())) for x in original[31:]]
            cp_score=evaluate(machine_orders,pos,durs)
            assert cp_score==entry['best_score']
            instance=tmp/'instance.txt'
            warm=tmp/'warm.txt'
            native=tmp/'native.csv'
            instance.write_text('\n'.join(original[:31])+'\n')
            warm.write_text('\n'.join(' '.join(map(str,row)) for row in machine_orders)+'\n')
            t=time.monotonic()
            process=subprocess.run([str(a.driver),str(instance),str(native),
                  str(a.seconds),str(a.seed),str(warm)],
                  capture_output=True,text=True,check=False,timeout=a.seconds+40)
            assert process.returncode==0,(case,process.stderr[-2500:])
            toks=process.stdout.strip().split()
            assert len(toks)==4 and toks[0]=='RESULT',(case,toks)
            native_score=int(toks[1])
            routes=[[None]*20 for j in range(30)]
            duration=[[None]*20 for j in range(30)]
            ints=list(map(int,path.read_text().split()))
            pointer=2
            for j in range(30):
                for k in range(20):
                    routes[j][k]=ints[pointer];duration[j][k]=ints[pointer+1]
                    pointer+=2
            starts=[[] for _ in range(20)];seen=set()
            with native.open() as f:
                for row in csv.DictReader(f):
                    j=int(row['Job'])-1;k=int(row['Operation'])-1
                    m=int(row['Machine'])
                    st=int(row['StartTime']);end=int(row['EndTime'])
                    assert (j,k) not in seen and m==routes[j][k]
                    assert end-st==duration[j][k]
                    seen.add((j,k));starts[m].append((st,j))
            assert len(seen)==600 and all(len(x)==30 for x in starts)
            candidate=[[j for _,j in sorted(row)] for row in starts]
            independent=evaluate(candidate,pos,durs)
            assert independent==native_score and native_score<=cp_score
            if native_score<source_score:
                (a.out/f'{case}-certificate.json').write_text(
                   json.dumps({'machines':candidate},separators=(',',':'))+'\n')
            record=dict(case=case,seed=a.seed,
                original_initial_score=source_score,
                cp_after_five_seconds=cp_score,
                n7_after_cp_best_score=native_score,
                overall_gain=source_score-native_score,
                native_n7_seconds=float(toks[3]),
                native_n7_iterations=int(toks[2]),
                cp_ladder_solver_seconds=entry['solver_seconds_total'],
                combined_solver_seconds=float(toks[3])+entry['solver_seconds_total'],
                all_600_native_operations_independently_verified=True,
                full_wall_seconds=round(time.monotonic()-t,3))
            results.append(record)
            (a.out/'checkpoint.json').write_text(json.dumps(dict(
                complete=False,trials=results),indent=2)+'\n')
            print('HYBRID',case,a.seed,source_score,cp_score,native_score,flush=True)
    out=dict(mechanism='5s adaptive job-release CP then 5s genuine 2025 author N7 from CP-generated complete machine order',
        seeds=[a.seed],native_n7_seconds_requested=a.seconds,
        all_12_independent_elites_completed=True,
        trials=results,complete=True)
    (a.out/'results.json').write_text(json.dumps(out,indent=2)+'\n')
    print('RESULT',len(results),'independently DAG rescored native hybrid continuations',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cases',type=Path,default=ROOT/'positive-n7-elite-data')
    p.add_argument('--driver',type=Path,required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--seconds',type=int,default=5)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
