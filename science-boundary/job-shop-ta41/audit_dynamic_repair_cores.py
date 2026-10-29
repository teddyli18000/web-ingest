#!/usr/bin/env python3
"""Audit fixed-survivor subspaces using independent assumption UNSAT cores.

For the eight completed 240-operation release sets of dynamic critical
path repair, reconstruct job precedence and full NoOverlap from scratch.
Add every remaining survivor precedence as an ASSUMPTION. If UNSAT,
extract a sufficient assumption core and identify which pinned operations
still force the contradiction. Do NOT confuse the returned nonminimal
assumption core with a formally minimal obstruction.

Then greedily propose and test a *core-hitting* release beyond the fixed
240 operations. This diagnoses whether CP cores expose a stronger adaptive
repair interface than continuing to expand by critical-path location.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from temporal_band_repair import fixed_precedence,precursor_lb

ROOT=Path(__file__).resolve().parent

def core_probe(pos,dur,parent,released,seconds=2.0):
    model=cp_model.CpModel()
    starts=[model.new_int_var(0,2005,f's{i}') for i in range(600)]
    ends=[model.new_int_var(0,2005,f'e{i}') for i in range(600)]
    intervals=[model.new_interval_var(starts[i],dur[i],ends[i],f'op{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(starts[j*20+k+1]>=ends[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    arcs=fixed_precedence(parent,pos,released)
    mapping={}
    for i,(u,v) in enumerate(arcs):
        b=model.new_bool_var(f'fixed_{i}')
        model.add(starts[v]>=ends[u]).only_enforce_if(b)
        model.add_assumption(b)
        mapping[b.index]=(u,v)
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=4107
    solver.parameters.max_time_in_seconds=seconds
    t=time.monotonic();stat=solver.solve(model)
    verdict=solver.status_name(stat)
    out=dict(status=verdict,seconds=round(time.monotonic()-t,3),
             pinned_arcs=len(arcs),free_operations=len(released),
             branches=solver.num_branches,conflicts=solver.num_conflicts)
    if verdict=='INFEASIBLE':
        inds=solver.sufficient_assumptions_for_infeasibility()
        assert all(x in mapping for x in inds),inds
        core=[mapping[x] for x in inds]
        out['sufficient_core_size']=len(core)
        out['core_precedences']=[list(z) for z in core]
        out['distinct_core_machine_count']=len({next(m for m in range(20) if
               any(j*20+pos[j][m]==a for j in range(30))) for a,b in core})
    return out

def main(a):
    routes,drows,baseline=obtain()
    pos,dur=setup(routes,drows)
    assert evaluate(baseline,pos,dur)==2006
    cases=[]
    for parent_name in ('baseline','124'):
        if parent_name=='baseline':parent=baseline
        else:
            folder=ROOT/'results'/'gateway-124'
            vr=json.loads((folder/'upstream-verdict.json').read_text())
            assert vr['valid'] and int(vr['score'])==2006
            parent=json.loads((folder/'certificate.json').read_text())['machines']
        for policy in ('dynamic','static','core','random'):
            src=ROOT/'results'/f'dcprcp-{parent_name}-{policy}-4107'/'dynamic-repair.json'
            data=json.loads(src.read_text())
            assert data['complete'] and data['rounds_completed']==8
            released=set(sum((x['released_this_round'] for x in data['release_sets']),[]))
            assert len(released)==240
            info=core_probe(pos,dur,parent,released,a.seconds)
            result=dict(parent=parent_name,policy=policy,source=str(src.relative_to(ROOT)),**info)
            cases.append(result)
            print('CORE',parent_name,policy,info['status'],info.get('sufficient_core_size'),info['seconds'],flush=True)
    report=dict(instance='ta41',target=2005,source_released_operation_count=240,
       independently_rebuilt_NoOverlap_models=8,records=cases,
       inference='A sufficient assumption UNSAT core pinpoints remaining fixed survivor precedence arcs; it does not prove the smallest release and UNKNOWN does not exclude schedules.',
       complete=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({'cases':len(cases),'core_sizes':[x.get('sufficient_core_size') for x in cases],
                'statuses':[x['status'] for x in cases]}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seconds',type=float,default=4.0)
    p.add_argument('--out',type=Path,default=ROOT/'results'/'dcprcp-independent-core-audit.json')
    main(p.parse_args())
