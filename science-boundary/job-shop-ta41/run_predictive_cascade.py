#!/usr/bin/env python3
"""Reproducible wrapper for C++ predictive cascade vs critical-block tabu.

The only reported candidate is a FULL 20-machine permutation. Every C++
result is rescored independently with the original Few Shots-compatible DAG
evaluator, and improved candidates go through the official upstream verifier.
Source schedules are verified historical 2006 certificates.

The "tabu" arm uses the SAME C++ exact DAG evaluator and machine critical
block insertion generator as "dynamic3" and "static3", giving a stronger
internal comparator than random or static single-move search. It is not a
claim to exactly reproduce the 2026 N7 batch-evaluation author's code.
"""
import argparse,json,subprocess,time
from pathlib import Path
from search import obtain,setup,evaluate
from dynamic_critical_replacement import state

ROOT=Path(__file__).resolve().parent
PARENTS={
  'baseline':None,
  'ninecore':('ninecore-neutral-baseline','neutral-certificate.json','neutral-verdict.json'),
  'gateway124':('gateway-124','certificate.json','upstream-verdict.json')
}
def source_parent(parent,pos,dur,baseline):
    if parent=='baseline':return baseline
    folder,cert,verdict=PARENTS[parent]
    root=ROOT/'results'/folder
    v=json.loads((root/verdict).read_text())
    assert v['valid'] and int(v['score'])==2006,v
    machines=json.loads((root/cert).read_text())['machines']
    assert evaluate(machines,pos,dur)==2006
    return machines

def kendall(a,b):
    count=0
    for m in range(20):
        ranks={j:k for k,j in enumerate(b[m])}
        q=[ranks[j] for j in a[m]]
        count+=sum(q[i]>q[j] for i in range(30) for j in range(i+1,30))
    return count

def main(a):
    routes,rows,base=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    parent=source_parent(a.parent,pos,dur,base)
    a.out.mkdir(parents=True,exist_ok=True)
    data=a.out/'input.txt'
    with data.open('w') as f:
        f.write('30 20\n')
        for j in range(30):
            f.write(' '.join(f'{routes[j][k]} {rows[j][k]}' for k in range(20))+'\n')
        for machine in parent:
            f.write(' '.join(map(str,machine))+'\n')
    raw=a.out/'raw-result.txt'
    start=time.monotonic()
    command=[str(a.binary),str(data),str(raw),a.policy,str(a.seed),
        str(a.evaluations),str(a.tabu_cap),str(a.first_cap),
        str(a.second_cap),str(a.third_cap)]
    subprocess.run(command,check=True)
    lines=raw.read_text().splitlines()
    assert len(lines)==21,len(lines)
    meta=lines[0].split()
    assert len(meta)==12,meta
    score,evals,invalid,accepted,macros,rep,visited,iterations,neutral,worse_first,worse_int=(int(x) for x in meta[:11])
    elapsed=float(meta[11])
    candidate=[list(map(int,line.split())) for line in lines[1:]]
    assert len(candidate)==20 and all(sorted(row)==list(range(30)) for row in candidate)
    independent=evaluate(candidate,pos,dur)
    assert independent==score,(score,independent)
    assert 0<evals<=a.evaluations and 0<=invalid<=evals
    _,new_critical,_=state(candidate,pos,dur)
    _,old_critical,_=state(parent,pos,dur)
    corefile=ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json'
    cc=json.loads(corefile.read_text())['proven_unsat_core']
    reversed_core=[c['index'] for c in cc if
       candidate[c['machine']].index(c['to_job']) <
       candidate[c['machine']].index(c['from_job'])]
    report=dict(
        instance='ta41',source_verified_2006=a.parent,
        policy=a.policy,seed=a.seed,source_code='predictive_cascade_search.cpp',
        algorithm='fully legal critical-block insertion; tabu, static 3-hop, or dynamic replacement 3-hop',
        is_exact_2026_N7_implementation=False,
        unique_experiment_id=f'{a.parent}-{a.policy}-{a.seed}',
        score_evaluation_budget=a.evaluations,exact_DAG_evaluations=evals,
        invalid_cycle_evaluations=invalid,accepted_transitions=accepted,
        accepted_macros=macros,new_bottleneck_macro_events=rep,
        visited_elite_schedules=visited,search_iterations=iterations,
        neutral_accepted=neutral,beneficial_intermediate_macros=worse_first,
        uphill_intermediate_macros=worse_int,
        elapsed_seconds_C_plus_plus=elapsed,
        elapsed_seconds_wrapper=round(time.monotonic()-start,3),
        makespan_reported_by_CPP=score,verified_score_by_Python_DAG=independent,
        Kendall_distance_from_parent=kendall(candidate,parent),
        changed_machine_orders_from_parent=sum(candidate[m]!=parent[m] for m in range(20)),
        critical_machine_edges_replaced=len(new_critical-old_critical),
        reversed_baseline_consensus_cores=reversed_core,
        improved=(score<=2005),
        verification_note='A <=2005 certificate must independently pass Few Shots verify.py and tools/check.py before any shot claim.')
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    if score<=2005:
        (a.out/'certificate.json').write_text(json.dumps({'machines':candidate})+'\n')
    elif candidate!=parent:
        (a.out/'neutral-certificate.json').write_text(json.dumps({'machines':candidate})+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=tuple(PARENTS),required=True)
    p.add_argument('--policy',choices=('tabu','static3','dynamic3'),required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--evaluations',type=int,default=150000)
    p.add_argument('--tabu-cap',type=int,default=90)
    p.add_argument('--first-cap',type=int,default=36)
    p.add_argument('--second-cap',type=int,default=15)
    p.add_argument('--third-cap',type=int,default=10)
    p.add_argument('--binary',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
