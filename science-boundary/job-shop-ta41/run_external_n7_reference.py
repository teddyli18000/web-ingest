#!/usr/bin/env python3
"""Original open-source N7 C++ tabu (Qiming01/Job-Shop-Scheduling), ta41.

This is an **external algorithm**, not the project's in-house tabu or a
reimplementation. The native C++ 2025 N7/tabu implementation is built
from pinned public commit 7e120eba. The native solver starts from its
own random solution (no official 2006 warmstart exposed), so its initial
condition differs from the new 2006-seeded predictive macro. Report this
as a separately reproducible external reference, NOT a fair matched-start
victory if it performs worse. Export all 600 starts and reconstruct exact
machine orders for independent Few Shots DAG and official verification.
"""
import argparse,csv,json,time
from pathlib import Path
from search import obtain,setup,evaluate

def main(a):
    import jsp
    routes,rows,baseline=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(baseline,pos,dur)==2006
    a.out.mkdir(parents=True,exist_ok=True)
    instance=a.out/'ta41.txt'
    with instance.open('w') as f:
        f.write('30 20\n')
        for j in range(30):
            f.write(' '.join(f'{routes[j][k]} {rows[j][k]}' for k in range(20))+'\n')
    loaded=jsp.load_instance(str(instance))
    assert loaded.job_num==30 and loaded.operation_num==20
    # Instance file was written directly from the hash-checked Few Shots data.
    # Upstream cold-start pybind omits stl.h and cannot expose loaded.data;
    # validation by the source generator and native scores remains independent.
    if a.parent=='ninecore':
        root=Path(__file__).resolve().parent/'results'/'ninecore-neutral-baseline'
        v=json.loads((root/'neutral-verdict.json').read_text())
        assert v['valid'] and int(v['score'])==2006
        baseline=json.loads((root/'neutral-certificate.json').read_text())['machines']
        assert evaluate(baseline,pos,dur)==2006
    jsp.set_seed(a.seed)
    solver=jsp.TabuSearch(loaded)
    if a.warmstart:
        solver.seed_machine_orders(baseline)
        assert solver.makespan()==2006,solver.makespan()
    start=time.monotonic()
    solver.search_for_seconds(a.seconds,100000000)
    spent=time.monotonic()-start
    csvpath=a.out/'native-operations.csv'
    solver.export_result(str(csvpath))
    starts={}
    with csvpath.open() as f:
        rd=csv.DictReader(f)
        for rec in rd:
            j=int(rec['Job'])-1;k=int(rec['Operation'])-1
            m=int(rec['Machine']); st=int(rec['StartTime'])
            assert 0<=j<30 and 0<=k<20 and routes[j][k]==m
            assert (j,k) not in starts
            starts[j,k]=st
    assert len(starts)==600,len(starts)
    machines=[]
    for m in range(20):
        machines.append(sorted(range(30),key=lambda j:starts[j,pos[j][m]]))
    native=solver.makespan()
    independent=evaluate(machines,pos,dur)
    assert independent==native,(independent,native)
    result={'instance':'ta41','upstream':'Qiming01/Job-Shop-Scheduling',
      'upstream_sha':'7e120ebada21cb604c871e0657814bf6e32611f8',
      'algorithm':'upstream C++ tabu N7/approximate Balas-style evaluation',
      'seed':a.seed,'parent':a.parent,'seconds_budget':a.seconds,'elapsed_seconds':round(spent,3),
      'iterations':solver.get_iter(),'native_makespan':native,
      'independently_verified_DAG_score':independent,
      'known_official_incumbent':2006,
      'source_instance_validated':True,
      'cold_start_native_random_initialization':not a.warmstart,
      'upstream_initializer_instrumentation':a.warmstart,
      'fairness':('Native N7 tabu starting from same official baseline; time budget comparable but incumbent construction and N7 move evaluation are not identical.'
                 if a.warmstart else
                 'External reproducible strong N7 tabu reference with different initial state; NOT paired warm-start comparison.'),
      'officially_verifiable_candidate':independent<=2005}
    (a.out/'external-n7.json').write_text(json.dumps(result,indent=2)+'\n')
    (a.out/'candidate.json').write_text(json.dumps({'machines':machines},separators=(',',':'))+'\n')
    if independent<=2005:
        (a.out/'certificate.json').write_text(json.dumps({'machines':machines},separators=(',',':'))+'\n')
    print('RESULT',json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--warmstart',action='store_true')
    p.add_argument('--parent',choices=('baseline','ninecore'),default='baseline')
    p.add_argument('--seconds',type=int,default=120)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
