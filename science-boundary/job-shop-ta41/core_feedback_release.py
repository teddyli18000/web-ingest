#!/usr/bin/env python3
"""Second-generation ta41 repair: CP UNSAT-core driven dynamic release.

Starts with exactly the 240 released operations from a completed dynamic
critical-path feedback trial. Then uses an INDEPENDENT hard-NoOverlap
assumption CP model to identify still-pinned machine precedence clauses
sufficient to block makespan <=2005.

At each round release 24 more operation variables. This is an actual
decision-variable interface reformulation, NOT simply more random
critical-path perturbation. Compare three selection methods:
  degree: release operations which hit most machine precedences in a CP core.
  core_random: release uniformly among endpoints in that CP core.
  random: ignore the CP core and release uniformly among all remaining ops.

Every method has same initial seed schedule, initial 240 released operations,
time budget, and release count. If an assumption decision is UNKNOWN, use
a separate hard NoOverlap feasibility attempt for candidate extraction.
UNKNOWN never means infeasible.
"""
import argparse,json,random,time
from collections import Counter
from pathlib import Path
from search import obtain,setup,evaluate
from audit_dynamic_repair_cores import core_probe
from temporal_band_repair import check_band,fixed_precedence

ROOT=Path(__file__).resolve().parent

def run(a):
    routes,rows,baseline=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(baseline,pos,dur)==2006
    parent=[r[:] for r in baseline]
    if a.parent!='baseline':
        root=ROOT/'results'/('gateway-'+a.parent)
        vr=json.loads((root/'upstream-verdict.json').read_text())
        assert vr['valid'] and int(vr['score'])==2006
        parent=json.loads((root/'certificate.json').read_text())['machines']
    trial=ROOT/'results'/f'dcprcp-{a.parent}-dynamic-4107'/'dynamic-repair.json'
    original=json.loads(trial.read_text())
    assert original['complete'] and original['rounds_completed']==8
    release=set(sum((x['released_this_round'] for x in original['release_sets']),[]))
    assert len(release)==240
    rng=random.Random(a.seed)
    progress=[]
    a.out.mkdir(parents=True,exist_ok=True)
    begin=time.monotonic()
    report=dict(instance='ta41',target=2005,source_parent=a.parent,seed=a.seed,
        original_released_operations=240,method=a.method,
        additional_operations_per_round=a.growth,round_limit=a.rounds,
        oracle_model='full NoOverlap + job arcs + survivor arcs as CP assumptions',
        rationale='Assumption core feedback adaptively changes which coupled operation variables are unlocked.',
        records=progress,status='ACTIVE')
    def save():
        report['elapsed_seconds']=round(time.monotonic()-begin,3)
        report['rounds_completed']=len(progress)
        (a.out/'core-release.json').write_text(json.dumps(report,indent=2)+'\n')
    for step in range(a.rounds+1):
        oracle=core_probe(pos,dur,parent,release,a.cp_seconds)
        rec=dict(round=step,free_operations=len(release),status=oracle['status'],
                 elapsed_seconds=oracle['seconds'],
                 remaining_survivor_arcs=oracle['pinned_arcs'],
                 core_arc_count=oracle.get('sufficient_core_size'),
                 distinct_core_machines=oracle.get('distinct_core_machine_count'))
        progress.append(rec)
        print('ROUND',a.parent,a.method,step,oracle['status'],
              'free',len(release),'core',rec['core_arc_count'],flush=True)
        save()
        if oracle['status']!='INFEASIBLE':
            if oracle['status'] in ('UNKNOWN','FEASIBLE','OPTIMAL'):
                fixed=fixed_precedence(parent,pos,release)
                result,cert=check_band(parent,pos,dur,fixed,a.hard_seconds,a.seed+step)
                rec['hard_feasibility_status']=result['status']
                if cert is not None:
                    score=evaluate(cert,pos,dur)
                    assert score is not None and score<=2005
                    rec['verified_dag_score']=score
                    (a.out/'certificate.json').write_text(json.dumps({'machines':cert},separators=(',',':'))+'\n')
                    report['status']='CANDIDATE_FOUND'
                else:
                    report['status']='UNRESOLVED'
            save()
            break
        if step==a.rounds:
            report['status']='ALL_TESTED_SUBSPACES_INFEASIBLE'
            save()
            break
        core=[tuple(x) for x in oracle['core_precedences']]
        endpoints={u for arc in core for u in arc}
        available=[u for u in range(600) if u not in release]
        core_available=[u for u in endpoints if u not in release]
        # All core arcs lie between still-fixed survivor operations.
        assert core_available and all(u in available for u in core_available)
        freq=Counter(u for edge in core for u in edge)
        if a.method=='degree':
            new=sorted(available,key=lambda u:(-freq[u],rng.random()))[:a.growth]
        elif a.method=='core_random':
            rng.shuffle(core_available)
            new=core_available[:a.growth]
            if len(new)<a.growth:
                rng.shuffle(available)
                new+=next((available[i:i+1] for i in range(len(available)) if available[i] not in new),[])
                # Fill the rest deterministically without duplication.
                new+= [u for u in available if u not in new][:a.growth-len(new)]
        else:
            rng.shuffle(available)
            new=available[:a.growth]
        assert len(new)==a.growth and not release.intersection(new)
        rec['newly_released_in_core']=sum(u in core_available for u in new)
        rec['released_this_round']=new
        release.update(new)
        save()
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='records'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=['baseline','124'],required=True)
    p.add_argument('--method',choices=['degree','core_random','random'],required=True)
    p.add_argument('--seed',type=int,default=2081)
    p.add_argument('--growth',type=int,default=24)
    p.add_argument('--rounds',type=int,default=10)
    p.add_argument('--cp-seconds',type=float,default=2)
    p.add_argument('--hard-seconds',type=float,default=12)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
