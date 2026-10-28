#!/usr/bin/env python3
"""Independent hard-constraint audit of all mined ta41 group UNSAT cores.

Rebuild from scratch each 600-interval model with ONLY the selected
machine groups pinned. Unlike assumption-core extraction, all checked
precedence constraints are unconditional.

Finite enumeration of all 2^20 changed-machine masks against the
INDEPENDENTLY REVERIFIED subset yields a separately auditable lower
bound. UNKNOWN cores are omitted; their existence never contributes.
"""
import argparse,json,time
from pathlib import Path
from search import obtain,setup,evaluate
import compact_machine_proof as cmp

def run(a):
    raw=json.loads(a.input.read_text())
    assert raw['target']==2005 and raw['baseline']==2006
    cores=[sorted(set(c)) for c in raw['cores']]
    routes,ds,orders=obtain();cmp.INSTANCE=(routes,ds,orders)
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    reports=[];good=[]
    started=time.monotonic()
    for i,c in enumerate(cores):
        status,seconds=cmp.hard_status(set(c),pos,dur,2005,a.seconds)
        reports.append(dict(index=i,fixed_machines=c,status=status,seconds=seconds))
        if status=='INFEASIBLE':good.append(c)
        if i%15==0 or i==len(cores)-1:
            print('PROGRESS',i+1,'/',len(cores),'independently verified',len(good),flush=True)
    masks=[sum(1<<i for i in core) for core in good]
    counts=[0]*21;first=None;witness=None
    for released in range(1<<20):
        if all(released & core for core in masks):
            k=released.bit_count();counts[k]+=1
            if first is None or k<first:first=k;witness=released
    result={
      'instance':'ta41','target':2005,'baseline':2006,
      'source_core_count':len(cores),'hard_verified_unsat_core_count':len(good),
      'unknown_or_nonproved_core_count':len(cores)-len(good),
      'exact_20bit_subsets_enumerated':1<<20,
      'certified_changed_machine_lower_bound_from_verified_only_cores':first,
      'witness_changed_machine_groups':[i for i in range(20) if witness&(1<<i)],
      'cover_count_per_group_change_cardinality':counts,
      'independent_hard_statuses':reports,
      'elapsed_seconds':round(time.monotonic()-started,3),
      'semantics':'Finite hitting set of independently verified hard-constraint infeasible machine group sets. UNKNOWN cores are excluded from the theorem.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='independent_hard_statuses'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,default=Path(__file__).parent/'results'/'machine-cores'/'machine-core-analysis.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-core-independent-all.json')
    p.add_argument('--seconds',type=float,default=4)
    run(p.parse_args())
