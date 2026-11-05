#!/usr/bin/env python3
"""Exact replay / independent verification of unmodified open-source N7 TS.

Run C++ Ming Qi's AGPLv3 2025 Job-Shop-Scheduling at fixed Git commit.
Outputs its original per-operation (1-based job, operation) CSV untouched
within the runtime, converts to canonical Few Shots 20x30 machine orders.
Checks every one of 600 machine-duration-time records against the official
ta41 instance and independently scores with Few Shots-compatible DAG.
Only a fully verified new makespan<=2005 is promoted to certificate.json.
The upstream search is intentionally NOT warmstarted, so it is a
cold-start reference rather than perfectly equal initial conditions.
"""
import argparse,csv,json,subprocess,time
from pathlib import Path
from search import obtain,setup,evaluate

PIN="7e120ebada21cb604c871e0657814bf6e32611f8"

def main(a):
    routes,drows,baseline=obtain()
    pos,dur=setup(routes,drows)
    assert evaluate(baseline,pos,dur)==2006
    sha=subprocess.run(['git','-C',str(a.upstream), 'rev-parse','HEAD'],
                       check=True,capture_output=True,text=True).stdout.strip()
    assert sha==PIN,(sha,PIN)
    a.out.mkdir(parents=True,exist_ok=True)
    inp=a.out/'instance.txt'
    with inp.open('w') as f:
        f.write('30 20\n')
        for j in range(30):
            f.write(' '.join(f'{routes[j][k]} {drows[j][k]}' for k in range(20))+'\n')
    seed_file=None
    if a.warmstart:
        seed_file=a.out/'verified-parent-orders.txt'
        with seed_file.open('w') as f:
            for row in baseline:
                f.write(' '.join(map(str,row))+'\n')
    csvpath=a.out/'upstream-schedule.csv'
    t=time.monotonic()
    command=[str(a.driver),str(inp),str(csvpath),str(a.seconds),str(a.seed)]
    if seed_file is not None:command.append(str(seed_file))
    result=subprocess.run(command,capture_output=True,text=True,check=True)
    print(result.stdout,flush=True)
    assert result.stdout.startswith('RESULT '),result.stdout[-1000:]
    x=result.stdout.strip().split()
    assert len(x)==4,x
    score=int(x[1]);iterations=int(x[2]);secs=float(x[3])
    machine_data=[[] for _ in range(20)]
    seen=set()
    with csvpath.open() as f:
        for row in csv.DictReader(f):
            j=int(row['Job'])-1
            k=int(row['Operation'])-1
            m=int(row['Machine'])
            start=int(row['StartTime']);end=int(row['EndTime'])
            assert 0<=j<30 and 0<=k<20 and 0<=m<20
            assert (j,k) not in seen,(j,k)
            seen.add((j,k))
            assert routes[j][k]==m,(j,k,routes[j][k],m)
            assert end-start==drows[j][k],(j,k,start,end,drows[j][k])
            assert start>=0
            machine_data[m].append((start,j))
    assert len(seen)==600,len(seen)
    assert all(len(row)==30 for row in machine_data),list(map(len,machine_data))
    orders=[[j for start,j in sorted(row)] for row in machine_data]
    assert all(sorted(row)==list(range(30)) for row in orders)
    independent=evaluate(orders,pos,dur)
    assert independent==score,(independent,score)
    report=dict(instance='ta41',baseline=2006,target=2005,
       external_implementation='Ming Qi C++ N7 tabu search 2025, AGPLv3',
       source_repository='https://github.com/Qiming01/Job-Shop-Scheduling',
       upstream_sha=sha,upstream_modified=bool(a.warmstart),
       exact_unmodified_N7_neighborhood_and_search_rules=True,
       starting_schedule=('Few Shots verified 2006' if a.warmstart else 'upstream random Giffler-Thompson'),
       warmstart_source_patch=('patch_original_n7_warmstart.py' if a.warmstart else None),
       original_reference='Zhang et al. 2007, Computers & Operations Research 34(11), 3229-3242',
       independent_python_dag_makespan=independent,original_cpp_makespan=score,
       seed=a.seed,budget_seconds=a.seconds,iterations=iterations,
       elapsed_cpp_seconds=secs,elapsed_total_seconds=round(time.monotonic()-t,3),
       comparison_limitation=('Source N7 search preserved exactly; only initialized with a verified 2006 complete machine order before search, so directly comparable at initial quality but original score-evaluation counts differ.' if a.warmstart else 'Original source initializes with its own random feasible schedule; not matched to incumbent-based experiments.'),
       exact_N7_author_source_reproduced=True,verified_by_official_FewShots_score=a.check,
       improvement=score<=2005)
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    if score<=2005:
        (a.out/'certificate.json').write_text(json.dumps({'machines':orders})+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--upstream',required=True,type=Path)
    p.add_argument('--driver',required=True,type=Path)
    p.add_argument('--seconds',default=120,type=int)
    p.add_argument('--seed',required=True,type=int)
    p.add_argument('--warmstart',action='store_true')
    p.add_argument('--check',default='pending_official_verifier')
    p.add_argument('--out',required=True,type=Path)
    main(p.parse_args())
