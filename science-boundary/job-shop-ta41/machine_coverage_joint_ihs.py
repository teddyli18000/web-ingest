#!/usr/bin/env python3
"""Machine-coverage implicit hitting set (MC-IHS), a constructive JSSP probe.

Key prior *independently verified* ta41 theorem:
at makespan <=2005, the original Cmax=2006 baseline must have changed
machine order on >=15 of 20 machines (full NoOverlap CP-SAT k<=14 UNSAT).
A complete changed machine order must reverse >=1 original adjacent arc.

Old root-IHS retained 571-576 of 580 original precedence edges and often
altered only 3-5 machine sequences: mathematically incapable of obtaining
a ta41 record. MC-IHS instead:
  - selects relaxed original adjacent precedence arcs JOINTLY across
    a prescribed number of machine groups (>=15 on ta41);
  - handles 21 certified ta41 baseline gateway clauses as an OR
    (no single root forced);
  - optionally injects prior solver-backed machine group cores;
  - runs full 600-interval, 20 NoOverlap, all 570 job arcs with hard
    target makespan and ONLY currently retained original adjacent arcs;
  - learns necessary UNSAT cores to reselect the entire release set.
  - tests increasingly broad multi-machine release budgets without
    pretending exact conflict hitting alone creates a complete schedule.

This is a constructive heuristic over previously established techniques,
NOT a claimed new generic IHS algorithm or global infeasibility proof.
UNKNOWN is a search timeout; exploration nogoods are NOT logical cuts.
"""
from __future__ import annotations
import argparse,json,time,random,math
from collections import Counter
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import immutable_and_resource,dag_graph
from search import evaluate

ROOT=Path(__file__).resolve().parent
GROUPS=20
ARCS=580
BASELINE_PROOF=ROOT/'results'/'machine-budget14'/'decision.json'
GATEWAY_PROOF=ROOT/'results'/'ta41-mandatory-adjacent-gateways-independently-proved.json'

def validated_ta41_constraints(orders):
    proof=json.loads(BASELINE_PROOF.read_text())
    assert proof['instance']=='ta41' and proof['target']==2005
    assert proof['status']=='INFEASIBLE' and proof['maximum_changed_machine_orders']==14
    assert proof['model']=='independent NoOverlap machine-cardinality decision without core constraints'
    data=json.loads(GATEWAY_PROOF.read_text())
    assert data['independently_rebuilt_full_NoOverlap_model'] and data['solver_status']=='INFEASIBLE'
    gateways=data['asserted_machine_resource_arcs']
    assert len(gateways)==21 and len(set(gateways))==21
    ref=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert len(ref['proven_unsat_core'])==21
    for item in ref['proven_unsat_core']:
        m=item['machine'];a=item['from_job'];b=item['to_job']
        k=orders[m].index(a)
        assert k+1==orders[m].index(b) and (m*29+k) in gateways
    return gateways

def known_machine_cores():
    cores=set()
    for name in ('machine-fast-2026','machine-fast-4107'):
        source=ROOT/'results'/name/'machine-core-fast.json'
        data=json.loads(source.read_text())
        assert data['instance']=='ta41' and data['target']==2005
        for c in data['cores']:
            mask=tuple(sorted(set(c)))
            assert mask and all(0<=m<GROUPS for m in mask)
            cores.add(mask)
    cores.add((1,10,13,15,17,19))
    # Strictly dominating core: smaller set of changed machines
    # meeting at least one condition implies meeting larger ones.
    sorted_cores=sorted(cores,key=lambda c:(len(c),c))
    remaining=[]
    for c in sorted_cores:
        if not any(set(k).issubset(c) for k in remaining):
            remaining.append(c)
    return remaining

def complete(orders,pos,dur,mutable,released,L,seconds,seed):
    cp=cp_model.CpModel()
    st=[cp.new_int_var(0,L-dur[i],f's{i}') for i in range(600)]
    en=[cp.new_int_var(dur[i],L,f'e{i}') for i in range(600)]
    inter=[cp.new_interval_var(st[i],dur[i],en[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):cp.add(st[j*20+k+1]>=en[j*20+k])
    for m in range(GROUPS):
        cp.add_no_overlap([inter[j*20+pos[j][m]] for j in range(30)])
    assumption_index={}
    for i,(u,v,m) in enumerate(mutable):
        if i in released:continue
        b=cp.new_bool_var(f'keep_{i}')
        cp.add(st[v]>=en[u]).only_enforce_if(b)
        cp.add_assumption(b)
        assumption_index[b.index]=i
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=seed
    solver.parameters.max_time_in_seconds=seconds
    tic=time.monotonic();status=solver.solve(cp)
    result=dict(status=solver.status_name(status),seconds=round(time.monotonic()-tic,3),
        branches=solver.num_branches,conflicts=solver.num_conflicts)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        machines=[sorted(range(30),key=lambda j:solver.value(st[j*20+pos[j][m]]))
                 for m in range(GROUPS)]
        value=evaluate(machines,pos,dur)
        assert value is not None and value<=L
        result['independently_verified_score']=value
        return result,machines,None
    if status==cp_model.INFEASIBLE:
        lit=solver.sufficient_assumptions_for_infeasibility()
        assert all(x in assumption_index for x in lit)
        core=frozenset(assumption_index[x] for x in lit)
        result['core_size']=len(core)
        return result,None,core
    return result,None,None

def master_selection(gateways,machine_cores,learned,unknown_nogoods,
                     original_slack,dynamic_slack,policy,
                     min_groups,per_group,budget,seconds,seed):
    cp=cp_model.CpModel()
    x=[cp.new_bool_var(f'release_{i}') for i in range(ARCS)]
    y=[cp.new_bool_var(f'open_{m}') for m in range(GROUPS)]
    cp.add(sum(x)==budget)
    for m in range(GROUPS):
        count=sum(x[m*29:(m+1)*29])
        cp.add(count>=per_group*y[m])
        cp.add(count<=29*y[m])
    cp.add(sum(y)>=min_groups)
    if gateways:cp.add(sum(x[i] for i in gateways)>=1)
    for c in machine_cores:cp.add(sum(y[m] for m in c)>=1)
    for core in learned:
        cp.add(sum(x[i] for i in core)>=1)
    for closed in unknown_nogoods:
        assert len(closed)==budget
        cp.add(sum(x[i] for i in closed)<=budget-1)
    rng=random.Random(seed)
    degrees=Counter()
    for clause in learned:
        for arc in clause:
            degrees[arc]+=1/(len(clause)**0.5)
    scores=[]
    for i in range(ARCS):
        if policy=='random':priority=rng.randrange(0,1000)
        else:
            sl=original_slack[i] if policy=='static' else dynamic_slack[i]
            near=int(500/(1+max(0,sl)))
            support=int(350*degrees[i]) if policy=='dynamic' else 0
            priority=near+support+rng.randrange(0,5)
        scores.append(priority)
    # Fixed budget; favor high precompletion pressure, not min number of
    # released arcs. Credit diverse machines via group variables.
    cp.maximize(sum(scores[i]*x[i] for i in range(ARCS))+
                12*sum(y))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    status=solver.solve(cp)
    out=dict(status=solver.status_name(status),seconds=solver.wall_time,
             branches=solver.num_branches)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return None,out
    released={i for i in range(ARCS) if solver.value(x[i])}
    open_group={m for m in range(GROUPS) if solver.value(y[m])}
    assert len(released)==budget and len(open_group)>=min_groups
    assert all(sum(i//29==m for i in released)>=per_group for m in open_group)
    assert not gateways or released.intersection(gateways)
    assert all(released.intersection(c) for c in learned)
    out.update(released=sorted(released),open_machines=sorted(open_group),
               released_by_machine=[sum(i//29==m for i in released) for m in range(GROUPS)])
    return released,out

def run(a):
    orders,pos,dur,initial=parse_case(a.start)
    target=initial-1
    is_ta41=a.start=='ta41'
    mutable=immutable_and_resource(orders,pos)
    base=dag_graph(dur,mutable,set())
    assert base is not None and base['lb']==initial
    gateways=validated_ta41_constraints(orders) if is_ta41 else []
    groups=known_machine_cores() if is_ta41 and not a.no_group_cores else []
    stages=([dict(machines=15,per=2,budget=30),
             dict(machines=17,per=2,budget=46),
             dict(machines=19,per=2,budget=60),
             dict(machines=20,per=2,budget=80)]
            if is_ta41 else
            [dict(machines=2,per=1,budget=4),
             dict(machines=3,per=1,budget=8),
             dict(machines=5,per=1,budget=16),
             dict(machines=8,per=1,budget=28)])
    orig_slack=[initial-(base['head'][u]+dur[u]+base['tail'][v])
              for u,v,m in mutable]
    dynamic_slack=orig_slack[:]
    learned=[];learned_set=set();unknown_nogoods=[]
    timeline=[]
    start=time.monotonic()
    a.out.mkdir(parents=True,exist_ok=True)
    output=dict(instance='ta41' if is_ta41 else Path(a.start).parent.name,
        method='joint 20-machine coverage-aware implicit hitting set with full-resource conditional completion',
        policy=a.policy,incumbent=initial,target=target,
        certified_min_changed_machine_orders=15 if is_ta41 else None,
        known_gateway_count=len(gateways),known_machine_group_cores=len(groups),
        no_oracle_solutions_read=True,
        stages=stages,seed=a.seed,status='UNRESOLVED',timeline=timeline)
    def save(final=False):
        output['complete']=final
        output['elapsed_seconds']=round(time.monotonic()-start,3)
        (a.out/'results.json').write_text(json.dumps(output,indent=2)+'\n')
    for stage_index,stage in enumerate(stages):
        stage_unknown=[]
        for it in range(a.iterations_per_stage):
            if time.monotonic()-start>a.seconds:
                output['outcome']='GLOBAL_TIME_LIMIT';save(final=True);return
            selected,info=master_selection(
                gateways,groups,learned,stage_unknown,
                orig_slack,dynamic_slack,a.policy,
                stage['machines'],stage['per'],stage['budget'],
                a.master_seconds,a.seed*100003+stage_index*1777+it)
            row=dict(stage=stage_index,iteration=it,
                     machine_quota=stage['machines'],release_budget=stage['budget'],
                     learned_core_count=len(learned),master=info)
            timeline.append(row)
            if selected is None:
                row['outcome']='MASTER_INFEASIBLE_OR_UNKNOWN'
                break
            trial,machines,core=complete(orders,pos,dur,mutable,
                selected,target,a.cp_seconds,a.seed*137+stage_index*77+it)
            row['completion']=trial
            if machines is not None:
                score=evaluate(machines,pos,dur)
                assert score<=target
                (a.out/'certificate.json').write_text(
                    json.dumps({'machines':machines},separators=(',',':'))+'\n')
                output['status']='CONSTRUCTIVE_IMPROVEMENT'
                output['verified_makespan']=score
                save(final=True)
                print('CONSTRUCTIVE',output['instance'],a.policy,
                      'stage',stage_index,'trial',it,'score',score,flush=True)
                return
            if core is not None:
                if not core:
                    row['outcome']='UNCONDITIONAL_INFEASIBLE_REQUIRES_INDEPENDENT_REPROOF'
                    output['outcome']=row['outcome']
                    save(final=True)
                    return
                assert not selected.intersection(core)
                if core not in learned_set:
                    learned_set.add(core);learned.append(core)
                    row['outcome']='LEARNED_VALID_TARGET_RESOURCE_UNSAT_CORE'
                else:
                    raise AssertionError('duplicate unhit core despite master constraints')
            else:
                stage_unknown.append(frozenset(selected))
                row['outcome']='CP_UNKNOWN_EXPLORATION_NOGOOD_ONLY'
            partial=dag_graph(dur,mutable,selected)
            assert partial is not None
            dynamic_slack=[target-(partial['head'][u]+dur[u]+partial['tail'][v])
                           for u,v,m in mutable]
            if it%10==0:
                save()
                print('ROUND',output['instance'],a.policy,'stage',stage_index,'trial',it,
                      'groups',len(info.get('open_machines',[])),
                      'cores',len(learned),'CP',trial['status'],flush=True)
    output['outcome']='BUDGET_EXHAUSTED_WITHOUT_FEASIBLE_SCHEDULE'
    save(final=True)
    print('RESULT',json.dumps({k:v for k,v in output.items() if k!='timeline'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',choices=['dynamic','static','random'],required=True)
    p.add_argument('--seed',type=int,default=20261108)
    p.add_argument('--iterations-per-stage',type=int,default=30)
    p.add_argument('--master-seconds',type=float,default=.35)
    p.add_argument('--cp-seconds',type=float,default=.50)
    p.add_argument('--seconds',type=float,default=150)
    p.add_argument('--no-group-cores',action='store_true')
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
