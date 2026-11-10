#!/usr/bin/env python3
"""Whole-machine keep/release LNS with complete reorientation and target CP.

Motivation: ta41's independently rechecked (<=2005) schedule MUST change
at least 15 of 20 machine order permutations. Selecting 30-80 isolated
baseline adjacent edges across 15 machines freezes much too much.
Instead, release a whole machine's 29 original adjacent decisions jointly.

All cases: jobs, full 20-machine NoOverlap and target Cmax<=incumbent-1
are hard. For a CLOSED machine, all 29 original adjacent precedences are
assumptions of one keep[m] variable; on an OPEN machine, their orientations
are free, with a soft cost for inversions of original adjacent pairs.
Thus no artificial fixed order exists inside an opened machine.

For CP INFEASIBLE, a sufficient core of closed-machine keep literals is
a valid clause: at least one of those machines must be opened in any
target-feasible completion. The master reoptimizes its entire open set
under those clauses and, on ta41, independently proven machine cores.
For CP UNKNOWN, no logical clause is learned; the exact mask is skipped
as exploration only.

Methods: dynamic ranks machines using accumulated sufficient core counts;
static uses initial DAG arc criticality; random ignores structure.
Do not claim originality for LNS, CP group assumptions or IHS. This
experiment asks if learned cross-machine conflict supports beat static
machine selection, and tests independently known positive 30x20 basins.
"""
import argparse,json,random,time
from collections import Counter
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import immutable_and_resource,dag_graph
from search import evaluate

HERE=Path(__file__).resolve().parent
SHAPE=(30,20)
MACHINES=20

def verified_ta41_sources(orders):
    e=json.loads((HERE/'results'/'machine-budget14'/'decision.json').read_text())
    assert e['instance']=='ta41' and e['target']==2005
    assert e['status']=='INFEASIBLE' and e['maximum_changed_machine_orders']==14
    raw=json.loads((HERE/'results'/'ta41-mandatory-adjacent-gateways-independently-proved.json').read_text())
    assert raw['solver_status']=='INFEASIBLE'
    original=json.loads((HERE/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    gateways=set(raw['asserted_machine_resource_arcs'])
    assert len(gateways)==21
    for x in original['proven_unsat_core']:
        m=x['machine'];k=orders[m].index(x['from_job'])
        assert orders[m][k+1]==x['to_job'] and m*29+k in gateways
    clause=set(i//29 for i in gateways)
    # Complete source-verified prior machine group cores. Reduce to
    # inclusion-minimal subsets; these are necessary group-open clauses.
    old=set()
    for name in ('machine-fast-2026','machine-fast-4107'):
        r=json.loads((HERE/'results'/name/'machine-core-fast.json').read_text())
        assert r['target']==2005 and r['instance']=='ta41'
        for c in r['cores']:
            assert c and all(isinstance(m,int) and 0<=m<20 for m in c)
            old.add(tuple(sorted(set(c))))
    old.add(tuple(sorted(clause)))
    keep=[]
    for c in sorted(old,key=lambda c:(len(c),c)):
        if not any(set(sub).issubset(c) for sub in keep):
            keep.append(c)
    return [frozenset(c) for c in keep],sorted(gateways)

def group_static_slack(orders,dur,pos):
    mutable=immutable_and_resource(orders,pos)
    graph=dag_graph(dur,mutable,set())
    assert graph
    C=graph['lb']
    vals=[[] for _ in range(MACHINES)]
    for u,v,m in mutable:
        sl=C-(graph['head'][u]+dur[u]+graph['tail'][v])
        assert sl>=0,(sl,m)
        vals[m].append(sl)
    # Multiple distinct near-critical arcs on a machine suggest
    # the machine is influential, not merely a single fragile link.
    return [sum(1/(1+s/12)**2 for s in a) for a in vals]

def parent_disagreement_signal(orders,pos,dur,second_parent,mode,seed):
    """Source-only A/B critical disagreement, with exactly count-matched fake B.

    On each machine m, inspect A's 29 adjacent job pairs. A real B flag
    marks pairs whose relative order is reversed in a DIFFERENT independently
    N7-generated elite machine permutation B for this same instance.
    The fake B marks uniformly random pairs with the EXACT SAME number
    of flags per machine, preserving marginal disagreement counts but
    destroying the location of B's structural information. No archived
    optimal certificate, target score, or reference start times are read.
    """
    assert mode in ('real','count-matched-fake')
    alt,posb,durb,_=parse_case(str(second_parent))
    assert posb==pos and durb==dur,'B must schedule the identical 30x20 instance'
    g=dag_graph(dur,immutable_and_resource(orders,pos),set())
    assert g is not None
    C=g['lb']
    rng=random.Random(seed*89101+53)
    feature=[]
    flip_counts=[]
    # Compute the same source-only causal pressure along the original
    # DAG critical/slack resource arcs for both true and fake B.
    for m,seq in enumerate(orders):
        ranks={j:i for i,j in enumerate(alt[m])}
        actual=[k for k in range(29)
                if ranks[seq[k]]>ranks[seq[k+1]]]
        flip_counts.append(len(actual))
        if mode=='real':selected=actual
        else:selected=rng.sample(range(29),len(actual))
        score=0.
        for k in selected:
            u=seq[k]*20+pos[seq[k]][m]
            v=seq[k+1]*20+pos[seq[k+1]][m]
            slack=C-(g['head'][u]+dur[u]+g['tail'][v])
            assert slack>=0
            score+=1/(1+max(0,slack)/12)**2
        feature.append(score)
    return feature,flip_counts

def machine_master(k,clauses,exploration_nogoods,prior_score,policy,seed,budget):
    mdl=cp_model.CpModel()
    x=[mdl.new_bool_var(f'open_{m}') for m in range(MACHINES)]
    mdl.add(sum(x)==k)
    for c in clauses:
        assert c
        mdl.add(sum(x[m] for m in c)>=1)
    for seen in exploration_nogoods:
        if len(seen)==k:
            mdl.add(sum(x[m] for m in seen)<=k-1)
    rng=random.Random(seed)
    # Since k fixed, objective is only ranking (no mathematical
    # exclusion from heuristic weights); all policies use same constraints.
    if policy=='random':
        weights=[rng.randrange(1,10000) for m in range(MACHINES)]
    else:
        weights=[int(prior_score[m]*200)+rng.randrange(0,100)
                 for m in range(MACHINES)]
    mdl.maximize(sum(weights[m]*x[m] for m in range(MACHINES)))
    slv=cp_model.CpSolver()
    slv.parameters.num_search_workers=4
    slv.parameters.random_seed=int(seed%2147483647)
    slv.parameters.max_time_in_seconds=budget
    status=slv.solve(mdl)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return None,dict(status=slv.status_name(status),wall_seconds=slv.wall_time)
    opened={m for m in range(MACHINES) if slv.value(x[m])}
    assert len(opened)==k and all(opened.intersection(c) for c in clauses)
    return opened,dict(status=slv.status_name(status),
        wall_seconds=slv.wall_time,opened=sorted(opened),master_heuristic_score=int(slv.objective_value))

def full_cp(orders,pos,dur,opened,L,policy,seed,seconds,repair_objective='minimal-change'):
    """Honest full-resource completion with ONLY group-level frozen orders."""
    mdl=cp_model.CpModel()
    start=[mdl.new_int_var(0,L-dur[i],f's{i}') for i in range(600)]
    end=[mdl.new_int_var(dur[i],L,f'e{i}') for i in range(600)]
    intervals=[mdl.new_interval_var(start[i],dur[i],end[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            mdl.add(start[j*20+k+1]>=end[j*20+k])
    # 580 soft original orientation variables are a compact simultaneous
    # objective even though the actual relative order is globally decided.
    flips=[]
    closed_literals={}
    for m,seq in enumerate(orders):
        mdl.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        if m not in opened:
            keep=mdl.new_bool_var(f'keep_machine_{m}')
            mdl.add_assumption(keep)
            closed_literals[keep.index]=m
        for k,(ja,jb) in enumerate(zip(seq,seq[1:])):
            u=ja*20+pos[ja][m]
            v=jb*20+pos[jb][m]
            f=mdl.new_bool_var(f'flip_{m}_{k}')
            mdl.add(start[v]>=end[u]).only_enforce_if(f.Not())
            mdl.add(start[u]>=end[v]).only_enforce_if(f)
            if m not in opened:
                mdl.add(f==0).only_enforce_if(keep)
            flips.append((m,f))
    # Every open machine can form any permutation. Cost is a preference,
    # never restricts a machine order.
    if repair_objective=='minimal-change':
        mdl.minimize(sum(bit for m,bit in flips))
    elif repair_objective!='feasibility':
        raise ValueError('unknown repair objective: '+str(repair_objective))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1 if closed_literals else 4
    solver.parameters.random_seed=int(seed%2147483647)
    solver.parameters.max_time_in_seconds=seconds
    t=time.monotonic()
    status=solver.solve(mdl)
    trace=dict(status=solver.status_name(status),
        wall_seconds=round(time.monotonic()-t,3),
        conflicts=solver.num_conflicts,branches=solver.num_branches,
        open_machine_count=len(opened),closed_machine_assumptions=len(closed_literals))
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        completed=[sorted(range(30),key=lambda j:solver.value(start[j*20+pos[j][m]]))
                    for m in range(MACHINES)]
        value=evaluate(completed,pos,dur)
        assert value is not None and value<=L
        trace['independent_makespan']=value
        trace['changed_machine_permutations']=sum(
            completed[m]!=orders[m] for m in range(MACHINES))
        trace['reversed_baseline_adjacent_relations']=sum(
            solver.value(bit) for m,bit in flips)
        return trace,completed,None
    if status==cp_model.INFEASIBLE:
        ids=solver.sufficient_assumptions_for_infeasibility()
        assert all(idx in closed_literals for idx in ids)
        core=frozenset(closed_literals[idx] for idx in ids)
        trace['sufficient_machine_conflict']=sorted(core)
        return trace,None,core
    return trace,None,None

def run(a):
    orders,pos,dur,C=parse_case(a.start)
    target_drop=getattr(a,'target_drop',1)
    target=C-target_drop
    assert target_drop>=1 and target>max(dur)
    istarget=a.start=='ta41'
    static=group_static_slack(orders,dur,pos)
    auxiliary=getattr(a,'auxiliary_start',None)
    auxiliary_mode=getattr(a,'auxiliary_mode','none')
    auxiliary_weight=getattr(a,'auxiliary_weight',3.)
    if auxiliary_mode!='none':
        assert auxiliary and a.policy=='dynamic'
        extra_signal,aux_disagreement_counts=parent_disagreement_signal(
            orders,pos,dur,auxiliary,auxiliary_mode,a.seed)
    else:
        assert not auxiliary
        extra_signal=[0.]*20
        aux_disagreement_counts=None
    prior_cores,gateways=(verified_ta41_sources(orders)
                          if istarget else ([],[]))
    # Target on known positives is one makespan unit below independent N7.
    # Hidden oracle is NOT loaded by the search.
    stages=([15,17,19,20] if istarget else [3,5,8,12,16,20])
    if a.only_groups:stages=a.only_groups
    assert all(0<k<=20 for k in stages)
    rng=random.Random(a.seed)
    learned=set(prior_cores)
    traces=[]
    state=dict(instance='ta41' if istarget else Path(a.start).parent.name,
        incumbent=C,target=target,target_drop=target_drop,policy=a.policy,
        auxiliary_mode=auxiliary_mode,auxiliary_weight=auxiliary_weight,
        auxiliary_parent_source=(str(auxiliary) if auxiliary else None),
        auxiliary_disagreement_count_by_machine=aux_disagreement_counts,
        auxiliary_critical_disagreement_scores=extra_signal,
        group_released_all_29_resource_adjacencies=True,
        complete_NoOverlap_and_job_precedence_hard=True,
        all_open_machine_permutations_allowed=True,
        ta41_minimum_changed_machines_independently_proved=(15 if istarget else None),
        initial_valid_machine_conflict_count=len(learned),
        mandatory_ta41_adjacent_gateway_ids=gateways,
        stages=stages,traces=traces,status='UNRESOLVED')
    a.out.mkdir(parents=True,exist_ok=True)
    begin=time.monotonic()
    def flush(done=False):
        state['wall_seconds']=round(time.monotonic()-begin,3)
        state['complete']=done
        (a.out/'results.json').write_text(json.dumps(state,indent=2)+'\n')
    if a.fixed_open_machines:
        # Explicit oracle-aware representation CAPACITY check only.
        # NEVER count this as blind discovery or comparative evaluation.
        opened=set(a.fixed_open_machines)
        assert len(opened)==len(a.fixed_open_machines)
        assert all(0<=m<20 for m in opened)
        state['oracle_aware_diagnostic_only']=True
        state['fixed_open_machines']=sorted(opened)
        result,schedule,core=full_cp(orders,pos,dur,opened,target,a.policy,
                                     a.seed,a.cp_seconds,a.repair_objective)
        traces.append(dict(stage=len(opened),trial=0,
                           opened=sorted(opened),completion=result))
        if schedule is not None:
            state['status']='DIAGNOSTIC_FEASIBLE'
            state['verified_makespan']=evaluate(schedule,pos,dur)
            (a.out/'certificate.json').write_text(
                json.dumps({'machines':schedule},separators=(',',':'))+'\n')
        else:
            state['outcome']=result['status']
        flush(True)
        print('DIAGNOSTIC',state['instance'],result['status'],
              state.get('verified_makespan'),flush=True)
        return
    for stage_index,k in enumerate(stages):
        unknown_masks=[]
        for iteration in range(a.trials_per_stage):
            remaining=a.total_seconds-(time.monotonic()-begin)
            if remaining<=0.03:
                state['outcome']='GLOBAL_TIME_LIMIT';flush(True);return
            degree=Counter()
            for core in learned:
                weight=1/(len(core)**0.5)
                for m in core:degree[m]+=weight
            if a.policy=='dynamic':
                priority=[static[m]*0.12+2.5*degree[m]+
                    auxiliary_weight*extra_signal[m] for m in range(20)]
            elif a.policy=='static':
                priority=static
            else:
                priority=[0.0]*20
            chosen,machine_info=machine_master(
                k,sorted(learned,key=lambda c:(len(c),sorted(c))),
                unknown_masks,priority,a.policy,
                a.seed+10007*stage_index+iteration*193,
                min(a.master_seconds,max(0.01,remaining-0.01)))
            row=dict(stage=k,trial=iteration,master=machine_info,
                     known_proven_machine_clauses=len(learned))
            traces.append(row)
            if chosen is None:
                row['outcome']='MASTER_INFEASIBLE_OR_UNKNOWN'
                break
            remaining=a.total_seconds-(time.monotonic()-begin)
            if remaining<=0.03:
                row['outcome']='GLOBAL_TIME_LIMIT_BEFORE_CP'
                state['outcome']='GLOBAL_TIME_LIMIT';flush(True);return
            result,schedule,core=full_cp(
                orders,pos,dur,chosen,target,a.policy,
                a.seed*7+stage_index*1009+iteration*11,
                min(a.cp_seconds,max(0.01,remaining-0.01)),
                a.repair_objective)
            row['completion']=result
            if schedule is not None:
                v=evaluate(schedule,pos,dur)
                assert v<=target
                (a.out/'certificate.json').write_text(
                    json.dumps({'machines':schedule},separators=(',',':'))+'\n')
                state['status']='CONSTRUCTIVE_IMPROVEMENT'
                state['verified_makespan']=v
                flush(True)
                print('IMPROVE',state['instance'],a.policy,'groups',k,
                      'trial',iteration,'score',v,flush=True)
                return
            if core is not None:
                if not core:
                    row['outcome']='UNCONDITIONAL_FULL_RESOURCE_INFEASIBLE_CERTIFIED'
                    state['outcome']=row['outcome'];flush(True);return
                assert core.isdisjoint(chosen),(core,chosen)
                row['outcome']='VALID_MACHINE_CORE'
                learned.add(core)
            else:
                unknown_masks.append(frozenset(chosen))
                row['outcome']='UNKNOWN_SKIP_THIS_MASK_ONLY'
            if iteration%4==0:flush()
            print('TRIAL',state['instance'],a.policy,'open',k,
                'trial',iteration,'CP',result['status'],
                'core',len(core) if core is not None else None,flush=True)
    state['outcome']='BUDGET_EXHAUSTED'
    flush(True)
    print('RESULT',state['instance'],a.policy,'trials',len(traces),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',choices=['dynamic','static','random'],required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--target-drop',type=int,default=1)
    p.add_argument('--auxiliary-start',type=Path,default=None)
    p.add_argument('--auxiliary-mode',choices=['none','real','count-matched-fake'],default='none')
    p.add_argument('--auxiliary-weight',type=float,default=3.)
    p.add_argument('--trials-per-stage',type=int,default=12)
    p.add_argument('--only-groups',nargs='+',type=int,default=[])
    p.add_argument('--repair-objective',choices=['minimal-change','feasibility'],default='minimal-change')
    p.add_argument('--fixed-open-machines',nargs='+',type=int,default=[])
    p.add_argument('--cp-seconds',type=float,default=1.5)
    p.add_argument('--master-seconds',type=float,default=.3)
    p.add_argument('--total-seconds',type=float,default=120)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
