#!/usr/bin/env python3
"""Independent hard-constraint validation of replacement UNSAT cores.

A first independent assumption-based oracle showed that attacking each
of eight old ta41 2005-UNSAT cores with two released operations immediately
exposes new cores, for both exact hitting-set and matched random controls.

This verifier re-constructs 600 mandatory intervals, 570 job arcs, 20 hard
machine NoOverlap constraints, and ONLY each newly returned core's machine
precedence arcs as unconditional constraints. It rechecks infeasibility
independently from the original assumption-based oracle and its release
subspaces. No other incumbent machine precedence is kept.

If a recheck is UNKNOWN, the claimed replacement core is NOT certified.
If it is FEASIBLE, a counterexample disproves its sufficiency; stop.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate

ROOT=Path(__file__).resolve().parent

def recheck(routes,pos,duration,core,seconds):
    model=cp_model.CpModel()
    tmax=2005
    starts=[model.new_int_var(0,tmax,'s%d'%i) for i in range(600)]
    ends=[model.new_int_var(0,tmax,'e%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(starts[i],duration[i],ends[i],'iv%d'%i)
               for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j*20+k+1]>=ends[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    for u,v in core:
        ju,ku=divmod(u,20);jv,kv=divmod(v,20)
        assert ju!=jv and routes[ju][ku]==routes[jv][kv],(u,v)
        model.add(starts[v]>=ends[u])
    slv=cp_model.CpSolver()
    slv.parameters.num_search_workers=4
    slv.parameters.max_time_in_seconds=seconds
    slv.parameters.random_seed=2917
    t=time.monotonic()
    status=slv.solve(model)
    return {'status':slv.status_name(status),
            'seconds':round(time.monotonic()-t,3),
            'conflicts':slv.num_conflicts,'branches':slv.num_branches}

def main(a):
    routes,durs,baseline=obtain()
    pos,duration=setup(routes,durs)
    assert evaluate(baseline,pos,duration)==2006
    data=json.loads((ROOT/'results'/'dynamic-core-hinge-replacement.json').read_text())
    assert data['hitting_set_minimal_cardinality']==2 and len(data['tests'])==8
    records=[];start=time.monotonic()
    for row in data['tests']:
        for method in ('hinge','random'):
            target=row['interventions'][method]
            assert target['new_status']=='INFEASIBLE',(row,method)
            # Assumption-core arcs are not in the first report to avoid
            # persisting large duplicative lists. Rebuild the exact new
            # release set and re-extract the UNSAT core with a new solve.
            from audit_dynamic_repair_cores import core_probe
            parent_name=row['parent'];policy=row['policy']
            parent=baseline
            if parent_name=='124':
                folder=ROOT/'results'/'gateway-124'
                v=json.loads((folder/'upstream-verdict.json').read_text())
                assert v['valid'] and int(v['score'])==2006
                parent=json.loads((folder/'certificate.json').read_text())['machines']
                assert evaluate(parent,pos,duration)==2006
            source=json.loads((ROOT/'results'/f'dcprcp-{parent_name}-{policy}-4107'/'dynamic-repair.json').read_text())
            release=set(u for r in source['release_sets'] for u in r['released_this_round'])
            release.update(target['newly_released_operations'])
            assert len(release)==242
            proof=core_probe(pos,duration,parent,release,a.assumption_seconds)
            record=dict(parent=parent_name,policy=policy,release_method=method,
                        source_new_core_size=target['new_sufficient_unsat_core_size'],
                        independent_assumption_status=proof['status'])
            if proof['status']=='INFEASIBLE':
                core=[tuple(e) for e in proof['core_precedences']]
                record['newly_extracted_core_size']=len(core)
                record['independent_hard_constraint_check']=recheck(
                    routes,pos,duration,core,a.hard_seconds)
            else:
                record['independent_hard_constraint_check']={'status':'NOT_RUN'}
            records.append(record)
            print('CHECK',parent_name,policy,method,
                  proof['status'],record['independent_hard_constraint_check']['status'],flush=True)
    complete=all(x['independent_hard_constraint_check']['status']=='INFEASIBLE' for x in records)
    report={
      'instance':'ta41','baseline_score':2006,'target_score':2005,
      'independent_hard_core_reconstructions':len(records),
      'all_replacement_cores_independently_certified':complete,
      'source':'results/dynamic-core-hinge-replacement.json',
      'results':records,
      'elapsed_seconds':round(time.monotonic()-start,3),
      'inference':'Each cited new core alone renders Cmax<=2005 infeasible with full machine resources; only the cited specific conditional subspaces are excluded, not globally all ta41 schedules.',
      'limitation':'Different 240-op release sets are independently UNSAT and not logically nested. This does not prove that two operations are the minimum needed to improve makespan.'
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)
    if not complete:
        raise RuntimeError('At least one purported core replacement was not independently proven')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--assumption-seconds',type=float,default=5)
    p.add_argument('--hard-seconds',type=float,default=12)
    p.add_argument('--out',type=Path,default=ROOT/'results'/'dynamic-core-hinge-independent-hard.json')
    main(p.parse_args())
