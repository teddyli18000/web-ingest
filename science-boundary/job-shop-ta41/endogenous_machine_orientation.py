#!/usr/bin/env python3
"""Endogenous 20-machine joint reorientation under proven ta41 conditions.

Unlike fixed machine/edge-release neighborhoods, ALL machine order
variables are simultaneous CP-SAT decisions; no original machine
precedence is frozen. Each of the 580 original adjacent pair orientations
has a reified Boolean flip, each of 20 original machine-order change
indicators is EXACTLY the OR of its 29 corresponding adjacent flips.

For ta41 target <=2005, independently verified necessary constraints:
- >=15 of the 20 original machine permutations must change;
- >=1 of 21 specific adjacent original machine arcs must reverse;
- for each sufficient original schedule machine group UNSAT core, >=1
  member must change. The latter are pure implied constraints and can
  be switched on/off as a controlled CP propagation experiment.

This does NOT make CP-SAT a novelty. The test asks whether jointly
modeling the higher-order necessary structure makes an improvement
possible where edge-deletion LNS cannot.
"""
import argparse,json,time,random
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import immutable_and_resource,dag_graph
from machine_group_order_repair import verified_ta41_sources
from search import evaluate

HERE=Path(__file__).resolve().parent

def run(a):
    orders,pos,dur,C=parse_case(a.start)
    target=C-1
    is_ta41=a.start=='ta41'
    if a.structure!='none' and not is_ta41:
        raise ValueError('Certified 15-machine/cardinality constraints refer only to original ta41 baseline')
    mdl=cp_model.CpModel()
    starts=[mdl.new_int_var(0,target-dur[i],f's{i}') for i in range(600)]
    ends=[mdl.new_int_var(dur[i],target,f'e{i}') for i in range(600)]
    iv=[mdl.new_interval_var(starts[i],dur[i],ends[i],f'v{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):mdl.add(starts[j*20+k+1]>=ends[j*20+k])
    mutable=immutable_and_resource(orders,pos)
    assert len(mutable)==580
    original=dag_graph(dur,mutable,set())
    assert original['lb']==C
    flips=[];changed=[]
    weights=[]
    for m,seq in enumerate(orders):
        mdl.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        local=[]
        for k,(a_job,b_job) in enumerate(zip(seq,seq[1:])):
            idx=m*29+k
            u=a_job*20+pos[a_job][m]
            v=b_job*20+pos[b_job][m]
            bit=mdl.new_bool_var(f'flip_{idx}')
            mdl.add(starts[v]>=ends[u]).only_enforce_if(bit.Not())
            mdl.add(starts[u]>=ends[v]).only_enforce_if(bit)
            flips.append(bit);local.append(bit)
            sl=C-(original['head'][u]+dur[u]+original['tail'][v])
            assert sl>=0
            weights.append(1 if a.objective=='uniform'
                else min(60,1+int(sl//8)))
        # A different complete machine permutation iff >=1 original
        # adjacent precedence pair has reversed orientation.
        diff=mdl.new_bool_var(f'changed_machine_{m}')
        mdl.add_max_equality(diff,local)
        changed.append(diff)
    assert len(flips)==580 and len(changed)==20

    old_proofs=[]
    gateways=[]
    if a.structure!='none':
        old_proofs,gateways=verified_ta41_sources(orders)
        mdl.add(sum(changed)>=15)
        mdl.add_bool_or([flips[i] for i in gateways])
        if a.structure=='all':
            for core in old_proofs:
                mdl.add_bool_or([changed[m] for m in core])
    if a.objective=='none':
        pass
    elif a.objective=='uniform':
        mdl.minimize(20*sum(changed)+sum(flips))
    elif a.objective=='static':
        mdl.minimize(20*sum(changed)+sum(weights[i]*flips[i] for i in range(580)))
    else:raise ValueError(a.objective)

    # Hint original head/times and orientation as a near-feasible
    # Cmax=2006 elite; all target constraints remain hard.
    for i in range(600):
        begin=min(original['head'][i],target-dur[i])
        mdl.add_hint(starts[i],begin)
        mdl.add_hint(ends[i],begin+dur[i])
    for bit in flips:mdl.add_hint(bit,0)
    for bit in changed:mdl.add_hint(bit,0)

    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=a.workers
    solver.parameters.random_seed=a.seed
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.cp_model_presolve=True
    tic=time.monotonic()
    status=solver.solve(mdl)
    rec=dict(instance=('ta41' if is_ta41 else Path(a.start).parent.name),
        incumbent=C,target=target,
        structure=a.structure,objective=a.objective,seed=a.seed,
        model='Full 600 interval and 20 machine NoOverlap; all 580 pair orientation variables live, 20 exact group-change indicators, no frozen old machine order',
        certified_machine_cardinality_bound=(15 if a.structure!='none' else None),
        added_21_gateway_clause=(a.structure!='none'),
        added_solver_verified_machine_group_core_clauses=(len(old_proofs) if a.structure=='all' else 0),
        status=solver.status_name(status),
        cp_seconds=round(time.monotonic()-tic,3),
        conflicts=solver.num_conflicts,
        branches=solver.num_branches,
        max_workers=a.workers,
        lower_bound=solver.best_objective_bound if a.objective!='none' else None,
        no_global_infeasibility_claim_unless_CP_PROVES_UNSAT=True)
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        full=[sorted(range(30),key=lambda j:solver.value(starts[j*20+pos[j][m]]))
              for m in range(20)]
        Cnew=evaluate(full,pos,dur)
        assert Cnew is not None and Cnew<=target
        ng=sum(full[m]!=orders[m] for m in range(20))
        nf=sum(solver.value(b) for b in flips)
        assert ng==sum(solver.value(b) for b in changed)
        if a.structure!='none':
            assert ng>=15 and sum(solver.value(flips[i]) for i in gateways)>=1
        rec.update(verified_makespan=Cnew,changed_machine_permutations=ng,
            reversed_baseline_adjacent_relations=nf,improved=True)
        (a.out/'certificate.json').write_text(
            json.dumps({'machines':full},separators=(',',':'))+'\n')
    else:rec['improved']=False
    (a.out/'results.json').write_text(json.dumps(rec,indent=2)+'\n')
    print('RESULT',json.dumps(rec),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',default='ta41')
    p.add_argument('--structure',choices=['none','cardinality','all'],required=True)
    p.add_argument('--objective',choices=['none','uniform','static'],required=True)
    p.add_argument('--seed',type=int,default=101)
    p.add_argument('--seconds',type=float,default=90.0)
    p.add_argument('--workers',type=int,default=8)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
