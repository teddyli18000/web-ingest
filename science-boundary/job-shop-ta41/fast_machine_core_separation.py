#!/usr/bin/env python3
"""Fast accumulated machine-core separation; avoids 5-second greedy shrinking.

Starting with independently persisted machine UNSAT cores, solve a
20-variable exact min hitting set and test its complement in a full
600-operation NoOverlap CP model. Every INFEASIBLE result contributes
a valid group clause. UNKNOWN proposals are blocked ONLY for exploratory
candidate diversification, never treated as proven exclusions.

This directly searches the hypergraph boundary while preserving a
stronger standalone certified machine-distance bound as the core set grows.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from machine_core_separation import build_oracle,oracle,cover


def propose(cores,blocked):
    model=cp_model.CpModel()
    changed=[model.new_bool_var('changed%d'%i) for i in range(20)]
    for c in cores:
        model.add(sum(changed[i] for i in c)>=1)
    for mask in blocked:
        model.add(sum(changed[i].Not() if i in mask else changed[i]
                      for i in range(20))>=1)
    model.minimize(sum(changed))
    s=cp_model.CpSolver()
    s.parameters.max_time_in_seconds=10
    s.parameters.num_search_workers=1
    status=s.solve(model)
    if status!=cp_model.OPTIMAL:
        return None,s.status_name(status)
    freed=frozenset(i for i in range(20) if s.value(changed[i]))
    assert all(freed.intersection(core) for core in cores)
    assert freed not in blocked
    return freed,'OPTIMAL'


def solve(a):
    routes,durs,base=obtain()
    pos,duration=setup(routes,durs)
    assert evaluate(base,pos,duration)==2006
    cp,keep,starts,indexmap=build_oracle(base,pos,duration,2005)
    init=json.loads(a.initial.read_text())
    assert init['target']==2005 and init['baseline']==2006
    cores=[tuple(c) for c in init['cores']]
    unique=set(cores)
    assert len(cores)==len(unique)
    blocked=set()
    attempts=[];now=time.monotonic();found=False
    a.out.mkdir(parents=True,exist_ok=True)
    def write():
        free,lower,cover_status=cover(cores)
        summary={
          'instance':'ta41','target':2005,'baseline':2006,
          'method':'fast 20-machine UNSAT core separation with unknown-only exploratory blocking',
          'cores':[list(c) for c in cores],
          'proven_core_count':len(cores),
          'exact_core_cover_lower_bound':lower,
          'exact_core_cover_status':cover_status,
          'unblocked_cover_witness':sorted(free) if free is not None else None,
          'unknown_oracle_count':len(blocked),
          'new_vs_initial_core_count':len(cores)-len(init['cores']),
          'found_candidate':found,
          'elapsed_seconds':round(time.monotonic()-now,3),
          'last_experiments':attempts[-15:],
          'interpretation':'Every INFEASIBLE oracle core is a valid necessary machine-group change disjunction. ONLY unblocked exact cover over proven cores is a lower-bound witness; UNKNOWN exclusions are exploratory only.'
        }
        (a.out/'machine-core-fast.json').write_text(json.dumps(summary,indent=2)+'\n')
        return summary
    for step in range(a.iterations):
        if time.monotonic()-now>a.seconds-15:
            break
        release,hit_status=propose(cores,blocked)
        if release is None:
            print('STOP cover solver',hit_status,flush=True)
            break
        fixed=set(range(20))-set(release)
        remaining=max(2,a.seconds-(time.monotonic()-now)-10)
        status,solver=oracle(cp,keep,a.seed+step,fixed,
                             seconds=min(a.oracle_seconds,remaining))
        line={'step':step,'proposed_changed':len(release),
              'oracle_status':solver.status_name(status),
              'elapsed':round(time.monotonic()-now,2)}
        if status==cp_model.INFEASIBLE:
            literal=solver.sufficient_assumptions_for_infeasibility()
            if not literal:
                line['fatal']='empty infeasible core: possible global no-2005 proof'
                attempts.append(line);break
            group=tuple(sorted({indexmap[t] for t in literal}))
            assert not set(group).intersection(release)
            assert group not in unique
            unique.add(group);cores.append(group)
            line['new_core']=list(group)
        elif status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            new=[sorted(range(30),key=lambda j:solver.value(starts[j*20+pos[j][m]]))
                 for m in range(20)]
            score=evaluate(new,pos,duration)
            assert score is not None and score<=2005
            line['independently_evaluated_score']=score
            (a.out/'certificate.json').write_text(json.dumps({'machines':new},separators=(',',':'))+'\n')
            found=True;attempts.append(line);break
        else:
            blocked.add(release)
            line['unknown_blocked_only_in_exploratory_cover']=sorted(release)
        attempts.append(line)
        if step%25==0 or step%100==99:
            summary=write()
            print('HEARTBEAT',json.dumps({
                  'step':step,'cores':len(cores),'cover_lb':summary['exact_core_cover_lower_bound'],
                  'unknowns':len(blocked),'elapsed':summary['elapsed_seconds']}),flush=True)
    summary=write()
    print('RESULT',json.dumps({k:v for k,v in summary.items()
                               if k not in ('cores','last_experiments')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--initial',type=Path,default=Path(__file__).parent/'results'/'machine-cores'/'machine-core-analysis.json')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seconds',type=int,default=580)
    p.add_argument('--oracle-seconds',type=float,default=5)
    p.add_argument('--iterations',type=int,default=2000)
    p.add_argument('--seed',type=int,default=40)
    solve(p.parse_args())
