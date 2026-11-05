#!/usr/bin/env python3
"""Blinded constructive 30x20 positive benchmark, no oracle inputs to search.

Compiles the existing C++ full-DAG N7-style critical-block tabu/static3/
dynamic3 algorithm without changing its search operators. Only substitutes
run-time incumbent and stop-bound constants (ta41 hardcodings) so it can
run on other 30x20 Taillard instances. The algorithm sees ONLY the 30x20
instance and degraded starting machine sequences in start.txt.

Independent Python DAG scores every native output. A separate judge, NOT
this script, loads hidden-oracle benchmark metadata and measures recovery.
"""
import argparse,json,re,subprocess,tempfile,time
from pathlib import Path
from search import setup,evaluate

ROOT=Path(__file__).resolve().parent

def compile_generalized(out, wall_seconds=0):
    source=(ROOT/'predictive_cascade_search.cpp').read_text()
    assert source.count('static Result search(')==1
    assert source.count('if(init.score!=2006)')==1
    assert 'int score=2006' in source
    assert 'if(result.score<=2005)' in source
    # Identical search kernel. Parameterize only old ta41-specific initial
    # constants and disable record-target early-stop (blind evaluation).
    source=re.sub(r'\b2006\b','INITIAL_SCORE',source)
    source=re.sub(r'\b2005\b','UNREACHABLE_STOP',source)
    source=source.replace('using namespace std;',
        'using namespace std;\nstatic int INITIAL_SCORE=2006;\nstatic int UNREACHABLE_STOP=-1;',1)
    source=source.replace('Schedule root;read_input(data,root);',
        'Schedule root;read_input(data,root);\n'
        '        INITIAL_SCORE=evaluate(root).score;\n'
        '        if(INITIAL_SCORE<=0)throw runtime_error("start is cyclic");\n'
        '        UNREACHABLE_STOP=-1;',1)
    if wall_seconds>0:
        marker='while(evaluations<budget&&result.score>UNREACHABLE_STOP){'
        assert source.count(marker)==1
        source=source.replace(marker,
            'while(evaluations<budget&&result.score>UNREACHABLE_STOP && '
            'chrono::duration<double>(chrono::steady_clock::now()-begin).count()<'
            +str(float(wall_seconds)) + '){')
    out.write_text(source)
    subprocess.run(['g++','-std=c++17','-O3','-pipe',str(out),'-o',str(out.with_suffix(''))],check=True)
    return out.with_suffix('')

def load_start(path):
    content=path.read_text().split()
    vals=list(map(int,content))
    assert vals[:2]==[30,20]
    route=[[0]*20 for _ in range(30)]
    dur=[[0]*20 for _ in range(30)]
    i=2
    for j in range(30):
        for k in range(20):
            route[j][k]=vals[i];dur[j][k]=vals[i+1];i+=2
    seq=[]
    for m in range(20):
        row=vals[i:i+30];i+=30
        assert sorted(row)==list(range(30))
        seq.append(row)
    assert i==len(vals)
    pos,d=setup(route,dur)
    start=evaluate(seq,pos,d)
    assert start is not None
    return pos,d,start

def benchmark(a):
    a.out.mkdir(parents=True,exist_ok=True)
    records=[]
    with tempfile.TemporaryDirectory() as tmp:
        source=Path(tmp)/'generalized_cascade.cpp'
        binary=compile_generalized(source,a.wall_seconds)
        for folder in sorted(a.cases.glob('ta*js-*')):
            entry=folder/'start.txt'
            assert entry.is_file()
            pos,d,startscore=load_start(entry)
            for seed in a.seeds:
                trial=f'{folder.name}-{seed}'
                output=Path(tmp)/(trial+'.txt')
                began=time.monotonic()
                p=subprocess.run([str(binary),str(entry),str(output),a.policy,str(seed),
                     str(a.evaluations),'48','35','20','20'],
                     capture_output=True,text=True,timeout=a.timeout,check=False)
                elapsed=time.monotonic()-began
                assert p.returncode==0, {'trial':trial,'stderr':p.stderr[-5000:]}
                lines=output.read_text().splitlines()
                stat=lines[0].split()
                assert len(stat)==12,(trial,stat)
                best=int(stat[0])
                orders=[list(map(int,line.split())) for line in lines[1:21]]
                assert len(orders)==20 and all(len(x)==30 for x in orders)
                independent=evaluate(orders,pos,d)
                assert independent==best,(trial,independent,best)
                assert best<=startscore,(trial,best,startscore)
                outcome=dict(case=folder.name,seed=seed,policy=a.policy,
                    start_score=startscore,best_score=best,improvement=startscore-best,
                    full_DAG_candidate_evaluations=int(stat[1]),
                    native_accepted=int(stat[3]),
                    native_macro_steps=int(stat[4]),
                    critical_replacement_events=int(stat[5]),
                    native_wall_seconds=float(stat[11]),
                    harness_wall_seconds=round(elapsed,3),
                    independently_reproduced_score=independent,
                    hidden_answer_not_accessible_to_search=True,\n                    wall_clock_cap=a.wall_seconds)
                records.append(outcome)
                print('CASE',trial,a.policy,startscore,best,'gain',startscore-best,flush=True)
                (a.out/'partial-results.json').write_text(json.dumps({'trials':records,'complete':False},indent=2)+'\n')
        result=dict(experiment='ta41 30x20 positive control counterfactual',
            method=a.policy,case_count=len(records),evaluations_per_trial=a.evaluations,
            trials=records,complete=True,
            semantics='Best makespan from exact original C++ construction scored independently in Python. Hidden oracle not read by search.')
        (a.out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        print('RESULT',a.policy,'trials',len(records),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cases',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--policy',choices=('tabu','static3','dynamic3'),required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[4107,4113])
    p.add_argument('--evaluations',type=int,default=350000)
    p.add_argument('--timeout',type=int,default=80)\n    p.add_argument('--wall-seconds',type=float,default=0)
    benchmark(p.parse_args())
