#!/usr/bin/env python3
"""Dual-sided time-split machine-keep conflict learning, a sound precompletion test.

Inspired by Vilim/Laborie/Shaw 2015 Failure-Directed Search (FDS) start-time
domain choices (startOf(op)<=t OR >=t+1), not a reimplementation of FDS.

For each source-A critical operation and its source-known earliest start t:
  G(target) AND choice-left AND keep(C_left) is UNSAT,
  G(target) AND choice-right AND keep(C_right) is UNSAT.
Then resolution on exhaustive integer-time alternatives proves
  G(target) AND keep(C_left UNION C_right) is UNSAT.
Thus the union is a necessary *machine-group release* clause that does
not depend on knowing any better complete schedule.

We keep ALL 600 intervals, 570 immutable job arcs and 20 machine
NoOverlap hard. Original incumbent machine arcs are guarded by single
keep_m assumption each, exactly as in the existing joint group LNS.
We also run a separate unbranched CP audit with ONLY the union keep
constraints to confirm the logically resolved clause when affordable.

No CP UNKNOWN is interpreted as a proof. A proven clause is not a
constructive improvement, and is not evidence that a 2005 schedule exists.
"""
import argparse,json,time,random
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from counterfactual_joint_cut import dag_graph,immutable_and_resource
from search import evaluate

HERE=Path(__file__).resolve().parent
def build_and_solve(orders,pos,duration,L,side=None,op=None,t=None,
                    assumed_machines=None,seconds=.3,seed=101):
    model=cp_model.CpModel()
    s=[model.new_int_var(0,L-duration[i],f's{i}') for i in range(600)]
    e=[model.new_int_var(duration[i],L,f'e{i}') for i in range(600)]
    iv=[model.new_interval_var(s[i],duration[i],e[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    if assumed_machines is None:assumed_machines=range(20)
    kept=set(assumed_machines)
    assumptions={}
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        if m not in kept:continue
        b=model.new_bool_var(f'keep_{m}')
        model.add_assumption(b)
        assumptions[b.index]=m
        for a,c in zip(orders[m],orders[m][1:]):
            u=a*20+pos[a][m];v=c*20+pos[c][m]
            model.add(s[v]>=e[u]).only_enforce_if(b)
    if side=='early':
        assert op is not None and t is not None
        model.add(s[op]<=t)
    elif side=='late':
        assert op is not None and t is not None
        model.add(s[op]>=t+1)
    else:assert side is None
    cp=cp_model.CpSolver()
    cp.parameters.num_search_workers=1
    cp.parameters.random_seed=int(seed%2147483647)
    cp.parameters.max_time_in_seconds=seconds
    start=time.monotonic()
    status=cp.solve(model)
    out=dict(status=cp.status_name(status),
         wall_seconds=round(time.monotonic()-start,4),
         branches=cp.num_branches,conflicts=cp.num_conflicts,
         total_assumptions=len(assumptions),side=side)
    if status==cp_model.INFEASIBLE:
        raw=cp.sufficient_assumptions_for_infeasibility()
        assert all(i in assumptions for i in raw)
        out['sufficient_machine_core']=sorted(assumptions[i] for i in raw)
    elif status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        schedule=[[j for j in sorted(range(30),key=lambda j:cp.value(s[j*20+pos[j][m]]))]
                 for m in range(20)]
        verified=evaluate(schedule,pos,duration)
        assert verified is not None and verified<=L
        out['independent_full_schedule_makespan']=verified
    return out

def experiment(args):
    orders,pos,dur,C=parse_case(args.start)
    L=C-1
    g=dag_graph(dur,immutable_and_resource(orders,pos),set())
    assert g is not None and g['lb']==C
    # Exact source critical operations and source-computable earliest times;
    # no hidden improving schedule, archived target orientation or expert
    # labels used to choose split points.
    crit=[u for u in range(600)
          if g['head'][u]+g['tail'][u]==C
          and 0<g['head'][u]<L-dur[u]]
    crit.sort(key=lambda u:(g['head'][u],u))
    if len(crit)>args.splits:
        steps=[(i*(len(crit)-1))//(args.splits-1) for i in range(args.splits)]
        crit=[crit[i] for i in sorted(set(steps))]
    a=args.out
    a.parent.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    baseline=build_and_solve(orders,pos,dur,L,seconds=args.seconds,seed=args.seed)
    report=dict(case=('ta41' if args.start=='ta41' else Path(args.start).parent.name),
        source_start_makespan=C,hard_target=L,
        original_machine_keeping_assumptions=20,
        original_complete_600_operation_jobshop_hard_constraints=True,
        time_choices='startOf(operation)<=earliestOriginalStart OR > earliestOriginalStart',
        source_only_critical_candidates=len(crit),
        direct_unsat_core=baseline,
        split_tests=[],
        fully_resolved_splits=0,
        independently_reproduced_resolved_machine_cores=0,
        no_hidden_schedule_used=True,
        source_concept='Vilim/Laborie/Shaw 2015 FDS start-time choices + elementary resolution of conditional machine-core conflicts; NOT FDS reproduction',
        proven_global_impossibility_claimed=False)
    for i,u in enumerate(crit):
        threshold=g['head'][u]
        left=build_and_solve(orders,pos,dur,L,'early',u,threshold,
                     seconds=args.seconds,seed=args.seed*71+i*3)
        right=build_and_solve(orders,pos,dur,L,'late',u,threshold,
                     seconds=args.seconds,seed=args.seed*71+i*3+1)
        row=dict(op=u,job=u//20,job_step=u%20,machine=next(m for m in range(20)
                    if pos[u//20][m]==u%20),
                 split_start_time=threshold,early=left,late=right)
        if (left['status']=='INFEASIBLE' and right['status']=='INFEASIBLE'):
            core=set(left['sufficient_machine_core'])|set(right['sufficient_machine_core'])
            row['logical_union_machine_release_clause']=sorted(core)
            row['union_core_size']=len(core)
            report['fully_resolved_splits']+=1
            # Independently audit the implied unsplit necessary clause.
            audit=build_and_solve(orders,pos,dur,L,assumed_machines=core,
                          seconds=args.audit_seconds,seed=args.seed*331+i)
            row['unbranched_independent_audit']=audit
            if audit['status']=='INFEASIBLE':
                report['independently_reproduced_resolved_machine_cores']+=1
            elif audit['status'] in ('FEASIBLE','OPTIMAL'):
                raise AssertionError('unsound dual-time-branch resolution')
        report['split_tests'].append(row)
        if i%4==0:
            a.write_text(json.dumps(dict(complete=False,**report),indent=2)+'\n')
        print('SPLIT',i,u,C,'=>',left['status'],right['status'],
              'union',row.get('union_core_size'),flush=True)
    report['complete']=True
    report['elapsed_seconds']=round(time.monotonic()-started,3)
    a.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='split_tests'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--splits',type=int,default=20)
    p.add_argument('--seconds',type=float,default=.3)
    p.add_argument('--audit-seconds',type=float,default=.6)
    p.add_argument('--seed',type=int,default=20261109)
    p.add_argument('--out',type=Path,required=True)
    experiment(p.parse_args())
