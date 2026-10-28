#!/usr/bin/env python3
"""Finish the exact 20-machine hypergraph distance certificate for ta41.

Two fast independent core-generation runs have ~4,772 UNSAT group clauses.
Their union permits a single 14-machine release mask. We MUST independently
test the six machine orders left fixed by that witness, instead of treating
the oracle's UNKNOWN as infeasibility. A separate hard-constraint interval
model either proves the missing subspace INFEASIBLE, yields an independently
DAG-verified <=2005 candidate, or honestly returns UNKNOWN.

Then enumerate all 2^20 binary masks against the union of proven
machine-UNSAT clauses to establish the exact finite-group cover bound.
"""
import argparse,json,time
from pathlib import Path
from search import obtain,setup,evaluate
from machine_interface_cp import probe

def reduced_masks(cores):
    masks=sorted({sum(1<<m for m in c) for c in cores},
                 key=lambda x:(x.bit_count(),x))
    filtered=[]
    for mask in masks:
        if not any(mask&other==other for other in filtered):
            filtered.append(mask)
    return filtered

def enumerate_covers(masks):
    counts=[0]*21
    first_masks=[None]*21
    for freed in range(1<<20):
        if all(freed&core for core in masks):
            k=freed.bit_count()
            counts[k]+=1
            if first_masks[k] is None:first_masks[k]=freed
    return counts, first_masks

def main(a):
    sources=[json.loads(p.read_text()) for p in a.inputs]
    assert all(src['baseline']==2006 and src['target']==2005 for src in sources)
    base_cores=[tuple(sorted(set(c))) for src in sources for c in src['cores']]
    masks=reduced_masks(base_cores)
    before, witnesses=enumerate_covers(masks)
    first=next(i for i,n in enumerate(before) if n)
    assert first==14 and before[14]==1,(first,before[14])
    w=witnesses[14]
    fixed={m for m in range(20) if not (w&(1<<m))}
    assert fixed=={1,10,13,15,17,19},fixed
    routes,ds,orders=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    outcome,candidate=probe(orders,pos,dur,set(range(20))-fixed,2005,
                            a.seconds,a.seed)
    new_masks=masks[:]
    if outcome['status']=='INFEASIBLE':
        new_masks=reduced_masks(base_cores+[tuple(sorted(fixed))])
    after,witnesses_after=enumerate_covers(new_masks)
    after_min=next(i for i,n in enumerate(after) if n)
    if outcome['status']=='INFEASIBLE':
        assert after_min>=15,(after_min,after[14])
    a.out.mkdir(parents=True,exist_ok=True)
    if candidate is not None:
        s=evaluate(candidate,pos,dur)
        assert s is not None and s<=2005,s
        (a.out/'certificate.json').write_text(json.dumps({'machines':candidate},separators=(',',':'))+'\n')
    report=dict(
        instance='ta41',target=2005,baseline=2006,
        source_core_counts=[len(x['cores']) for x in sources],
        unique_source_group_core_count=len(set(base_cores)),
        nondominated_source_group_core_masks=len(masks),
        all_machine_change_masks_enumerated=1<<20,
        original_machine_group_core_cover_minimum=first,
        original_14_group_cover_count=before[14],
        sole_remaining_14_machine_change_mask=w,
        witness_free_machines=[m for m in range(20) if w&(1<<m)],
        missing_fixed_machine_core=sorted(fixed),
        hard_no_overlap_verification=outcome,
        extended_machine_group_core_cover_minimum=after_min,
        extended_cover_count_at_14=after[14],
        new_minimum_cover_count=after[after_min],
        status='finite_15_machine_certificate_complete' if outcome['status']=='INFEASIBLE'
               else 'incomplete: missing core was not proved infeasible',
        proof_note='All earlier clauses originate from exact solver UNSAT assumption cores; final six-machine clause is independently hard checked. The finite 20-bit proof itself is exhaustive but earlier clauses are not all independently rechecked.'
    )
    (a.out/'finite-cover-completion.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,nargs=2,
       default=[Path(__file__).parent/'results'/'machine-fast-2026'/'machine-core-fast.json',
                Path(__file__).parent/'results'/'machine-fast-4107'/'machine-core-fast.json'])
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-core-15-completion')
    p.add_argument('--seconds',type=float,default=420)
    p.add_argument('--seed',type=int,default=24242)
    main(p.parse_args())
