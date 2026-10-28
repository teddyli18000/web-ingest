#!/usr/bin/env python3
"""A compact and independently checkable 15-machine escape-distance proof.

Problem: at the <=2005 deadline for Taillard ta41, can 14 of the 20
machine orders be modified while six stay as in the verified 2006 schedule?

Previously mined grouped UNSAT cores are ONLY proposed hypotheses. Select
a small subset that hits ALL 38,760 possible changed-machine subsets of
size exactly 14. Independently rebuild the hard-constraint 600-interval
NoOverlap model for EVERY selected core. UNKNOWN cores cannot contribute
to the final claim. Once they all prove INFEASIBLE, a finite integer-only
test verifies each of the 38,760 subsets violates a certified core.

Testing only size 14 suffices for <=14 because any smaller changed set
can be extended to a size-14 set, while core hitting is monotone upward.

This incumbent-relative theorem is distinct from a global bound on
the minimum makespan of ta41.
"""
import argparse
import itertools
import json
import time
from pathlib import Path
from search import obtain, setup, evaluate
from compact_machine_proof import hard_status
import compact_machine_proof as original


def bitmask(seq):
    return sum(1 << x for x in seq)


def covers_all(universe, selected):
    for mask in universe:
        if all(mask & c for c in selected):
            return False, mask
    return True, None


def select_small_cover(candidates, universe):
    # An exact set cover is not required: the cardinality of a sound
    # proof is small but need not be proven minimum.
    universe_n=len(universe)
    full=(1 << universe_n)-1
    coverage={}
    for core in candidates:
        if core.bit_count()>6:
            continue
        bits=bytearray((universe_n+7)//8)
        for i, freed in enumerate(universe):
            if not (freed & core):
                bits[i>>3] |= 1 << (i&7)
        val=int.from_bytes(bits,'little')
        if val:
            coverage[core]=val
    assert coverage
    uncovered=full
    chosen=[]
    while uncovered:
        gains=[(uncovered & bits).bit_count() for bits in coverage.values()]
        score=max(gains)
        if score==0:
            raise ValueError('source cores do not cover every 14-machine release set')
        # Prefer the shortest, easiest-to-check core among tied gain.
        best=min((core for core, bits in coverage.items()
                  if (uncovered & bits).bit_count()==score),
                 key=lambda c:(c.bit_count(),c))
        chosen.append(best)
        uncovered &= ~coverage.pop(best)
        print('COVER',len(chosen),'core',best,'machines',best.bit_count(),
              'gain',score,'left',uncovered.bit_count(),flush=True)
    assert covers_all(universe, chosen)[0]
    # Reverse deletion pruning, preserves full logical coverage.
    for core in chosen[::-1]:
        trial=[c for c in chosen if c!=core]
        if covers_all(universe,trial)[0]:
            chosen=trial
    assert covers_all(universe,chosen)[0]
    return chosen


def main(args):
    sources=[json.loads(x.read_text()) for x in args.inputs]
    assert all(x['target']==2005 and x['baseline']==2006 for x in sources)
    raw=[tuple(sorted(set(core))) for src in sources for core in src['cores']]
    for c in raw: assert c and all(0<=m<20 for m in c)
    # Separately proved as a hard-constraint subproblem on 2026-10-28.
    final_core=(1,10,13,15,17,19)
    raw.append(final_core)
    core_masks=set(map(bitmask,raw))
    # Monotone domination: if core C1 is a subset of C2, the clause
    # 'change at least one machine in C1' implies the C2 clause.
    ordered=sorted(core_masks,key=lambda c:(c.bit_count(),c))
    candidates=[]
    for c in ordered:
        if not any((c & d)==d for d in candidates):
            candidates.append(c)
    universe=[bitmask(changed) for changed in itertools.combinations(range(20),14)]
    assert len(universe)==38760
    assert covers_all(universe,candidates)[0]
    selected=select_small_cover(candidates,universe)
    assert len(selected)<1000
    routes,durations_by_job,orders=obtain()
    pos,durations=setup(routes,durations_by_job)
    assert evaluate(orders,pos,durations)==2006
    original.INSTANCE=(routes,durations_by_job,orders)
    cases=[]
    start=time.monotonic()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    for i,mask in enumerate(selected):
        core=[m for m in range(20) if mask & (1<<m)]
        verdict,seconds=hard_status(set(core),pos,durations,2005,args.per_core_seconds)
        cases.append(dict(fixed_machines=core,hard_cp_verdict=verdict,
                          wall_seconds=seconds))
        print('VERIFY',i+1,'of',len(selected),core,verdict,seconds,flush=True)
        if verdict!='INFEASIBLE':
            break
    complete=(len(cases)==len(selected) and
              all(x['hard_cp_verdict']=='INFEASIBLE' for x in cases))
    verified=[bitmask(x['fixed_machines']) for x in cases
              if x['hard_cp_verdict']=='INFEASIBLE']
    finite_good, uncovered=covers_all(universe,verified)
    result=dict(
        instance='Taillard ta41',target_makespan=2005,baseline=2006,
        machine_orders=20,core_source_sizes=[len(x['cores']) for x in sources],
        additional_independently_checked_six_machine_core=list(final_core),
        raw_unique_machine_core_count=len(core_masks),
        nondominated_source_core_count=len(candidates),
        changed_machine_subsets_of_size_14_checked=len(universe),
        greedy_proposed_proof_core_count=len(selected),
        hard_cp_verified_core_count=len(verified),
        all_selected_core_checks_complete=complete,
        exact_finite_coverage_of_verified_only_cores=finite_good,
        unexcluded_fourteen_machine_release_mask=uncovered,
        certified_min_changed_machines=15 if complete and finite_good else None,
        independent_hard_core_verdicts=cases,
        elapsed_seconds=round(time.monotonic()-start,3),
        reasoning=('Every schedule with <=14 changed machine orders is extended '
                   'to one of the 38,760 size-14 release masks. Every such '
                   'mask preserves all machine orders in at least one independently '
                   'verified UNSAT core. Contradiction at Cmax<=2005.'),
        provenance=('Machine cores were selected from two earlier oracle runs, '
                    'but each selected core was independently rebuilt with '
                    'unconditional job and resource precedence and NoOverlap '
                    'before inclusion in the proof.'),
        scope='Incumbent-relative distance only; not global optimum makespan.'
    )
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='independent_hard_core_verdicts'}),flush=True)
    if not complete or not finite_good:
        raise RuntimeError('The compact 15-machine proof has not been independently certified')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',nargs=2,type=Path,default=[
        Path(__file__).parent/'results'/'machine-fast-2026'/'machine-core-fast.json',
        Path(__file__).parent/'results'/'machine-fast-4107'/'machine-core-fast.json'])
    p.add_argument('--out',type=Path,default=Path(__file__).parent/
                   'results'/'compact-15-machine-proof.json')
    p.add_argument('--per-core-seconds',type=float,default=55)
    main(p.parse_args())
