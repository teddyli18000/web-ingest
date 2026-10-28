#!/usr/bin/env python3
"""Exact hard-NoOverlap test of the 304 surviving 15-machine change subsets.

The 4,773 earlier valid machine UNSAT cores only rule out most machine
release masks. We use them to select ALL 304 surviving size-15 masks,
then **independently** solve each of those fully restricted subproblems
with hard incumbent precedences (not assumptions).

This is an active separation process, not a claim that the 304 masks
exhaust all possible schedules unless every earlier core remains valid.
INFEASIBLE is conclusive for each tested mask. UNKNOWN is not.
"""
import argparse,itertools,json,time
from pathlib import Path
from search import obtain,setup,evaluate
from machine_interface_cp import probe


def bitmask(c):
    return sum(1<<x for x in c)

def main(a):
    sources=[json.loads(x.read_text()) for x in a.inputs]
    assert all(d['target']==2005 and d['baseline']==2006 for d in sources)
    group_masks={bitmask(c) for s in sources for c in s['cores']}
    last=bitmask((1,10,13,15,17,19))
    group_masks.add(last)
    surviv=[bitmask(c) for c in itertools.combinations(range(20),15)
            if all((bitmask(c)&g)!=0 for g in group_masks)]
    assert len(surviv)==304,len(surviv)
    routes,ds,orders=obtain();pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    result=dict(target=2005,baseline=2006,source_group_unsat_core_count=len(group_masks),
                cardinality=15,candidate_machine_release_masks=304,
                shard=a.shard,shards=a.shards,
                tested=0,hard_infeasible=0,unknown=0,feasible=0,
                outcomes=[],assumption='An UNSAT core from the earlier machine-group oracle must be a valid infeasibility implication; selected 304 masks are independently hard-checked.',
                complete=False)
    candidates=[(i,freed) for i,freed in enumerate(surviv) if i%a.shards==a.shard]
    a.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    for i,freed in candidates:
        if time.monotonic()-start>a.total_seconds-3:break
        free={m for m in range(20) if freed&(1<<m)}
        outcome,cert=probe(orders,pos,dur,free,2005,
                            min(a.per_case_seconds,max(1,a.total_seconds-(time.monotonic()-start)-2)),
                            a.seed+i)
        st=outcome['status']
        record=dict(global_index=i,free_machine_mask=freed,
                    fixed_machines=sorted(set(range(20))-free),
                    status=st,elapsed_seconds=outcome['elapsed'])
        result['outcomes'].append(record)
        if st=='INFEASIBLE':result['hard_infeasible']+=1
        elif st in ('FEASIBLE','OPTIMAL'):
            result['feasible']+=1
            val=evaluate(cert,pos,dur)
            assert val is not None and val<=2005,val
            record['independent_dag_score']=val
            (a.out/'certificate.json').write_text(
                json.dumps({'machines':cert},separators=(',',':'))+'\n')
            break
        else:result['unknown']+=1
        result['tested']+=1
        if result['tested']%10==0:
            print('PROGRESS',result['tested'],len(candidates),
                'unknown',result['unknown'],'elapsed',round(time.monotonic()-start,1),flush=True)
    result['tested']=len(result['outcomes'])
    result['complete']=result['tested']==len(candidates)
    result['elapsed']=round(time.monotonic()-start,3)
    (a.out/'shard-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='outcomes'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,nargs=2,default=[
      Path(__file__).parent/'results'/'machine-fast-2026'/'machine-core-fast.json',
      Path(__file__).parent/'results'/'machine-fast-4107'/'machine-core-fast.json'])
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,default=4)
    p.add_argument('--seed',type=int,default=202614)
    p.add_argument('--per-case-seconds',type=float,default=5)
    p.add_argument('--total-seconds',type=int,default=550)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
