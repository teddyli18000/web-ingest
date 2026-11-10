#!/usr/bin/env python3
"""Audit whether CP-SAT group cores convey more information than not-yet-opened machines.

For a 30x20 elite start and three source-chosen machine-open sets:
  - original optimization objective under hard target Cmax-1;
  - same assumptions with feasibility-only (no minimize-sum-flips);
  - greedily *prove* redundancy of individual retained machine-order guards
    under the same full NoOverlap, job precedence and deadline.

A guard is removed from a sufficient core ONLY when another CP-SAT run
proves the corresponding relaxed model INFEASIBLE. If the solver reports
UNKNOWN or FEASIBLE, we retain it. Therefore minimized cores are sound
although not necessarily cardinality-minimal. No oracle machine order
is read, and a timeout is never interpreted as UNSAT.

The experiment explicitly separates the prior "dynamic" group novelty
heuristic from any actual informative resource conflict proof.
"""
from pathlib import Path
import argparse,json,random,time
from machine_group_order_repair import group_static_slack,full_cp
from partial_resource_pair_repair import parse_case

def main(a):
    orders,pos,dur,C=parse_case(a.start)
    static=group_static_slack(orders,dur,pos)
    rng=random.Random(a.seed)
    sets=[]
    for k in a.open_sizes:
        ranked=sorted(range(20),key=lambda m:(-static[m],m))
        sets.append((f'static-{k}',set(ranked[:k])))
        perm=list(range(20));rng.shuffle(perm)
        sets.append((f'random-{k}',set(perm[:k])))
    result=dict(instance=('ta41' if a.start=='ta41' else Path(a.start).parent.name),
        initial=C,target=C-1,guards_are_entire_machine_orders=True,
        original_machine_open_sets_source_only=True,
        source='Full CP-SAT 600 operation intervals, all 20 NoOverlap, job arcs, 580 original adjacency reifications.',
        max_seconds_per_core_check=a.check_seconds,
        runs=[],complete=False)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    for idx,(label,opened) in enumerate(sets):
        prefix=dict(label=label,initial_opened=sorted(opened),initial_closed=sorted(set(range(20))-opened))
        first,cert,core=full_cp(orders,pos,dur,opened,C-1,'static',a.seed+idx, a.initial_seconds,'minimal-change')
        prefix['objective_CP_status']=first['status']
        if cert is not None:
            prefix['original_CP_already_constructed_score']=first['independent_makespan']
            result['runs'].append(prefix)
            print('AUDIT',label,'already feasible',flush=True)
            continue
        if core is None:
            prefix['outcome']='FIRST_SOLVE_UNKNOWN'
            result['runs'].append(prefix)
            print('AUDIT',label,'first UNKNOWN',flush=True)
            continue
        prefix['initial_core_size']=len(core)
        prefix['initial_core_is_entire_closed_machine_set']=core==frozenset(set(range(20))-opened)
        plain,certplain,coreplain=full_cp(orders,pos,dur,opened,C-1,'static',a.seed+idx+77,a.initial_seconds,'feasibility')
        prefix['feasibility_only_CP_status']=plain['status']
        prefix['feasibility_only_core_size']=(len(coreplain) if coreplain is not None else None)
        if coreplain is not None:
            prefix['feasibility_only_core_is_entire_closed_set']=coreplain==frozenset(set(range(20))-opened)
        # If both proved UNSAT, choose the smaller sufficient core; if
        # one is UNKNOWN, the other still suffices. Never trust UNKNOWN.
        chosen=set(min((core,coreplain),key=len) if coreplain is not None else core)
        attempts=[]
        iteration=list(chosen)
        rng.shuffle(iteration)
        for m in iteration:
            if m not in chosen:continue
            trial_closed=chosen-{m}
            # Each closed guard is a full original machine precedence.
            # Reopen all others (possibly newly opened vs the source).
            trial_open=set(range(20))-trial_closed
            t,sc,proven=full_cp(orders,pos,dur,trial_open,C-1,'static',
                a.seed*23+idx*31+m,a.check_seconds,'feasibility')
            if t['status']=='INFEASIBLE':
                assert proven is not None
                chosen=trial_closed
            attempts.append(dict(dropped_guard=m,
                 status=t['status'],can_prove_guard_redundant=t['status']=='INFEASIBLE',
                 remaining_closed_guard_count=len(chosen),
                 solver_seconds=t['wall_seconds']))
        assert chosen.issubset(set(range(20))-opened)
        # Final reproof with independent CP call at larger cap: if
        # UNKNOWN, mark inconclusive and never claim proof.
        last,sol,maybe_core=full_cp(orders,pos,dur,set(range(20))-chosen,C-1,'static',
                                 a.seed*101+idx,a.final_seconds,'feasibility')
        prefix.update(outcome='GREEDY_REDUCED_AND_REPROVED' if last['status']=='INFEASIBLE' else
                      'GREEDY_REPROOF_FAILED_OR_UNKNOWN',
                      final_core_size=len(chosen),
                      final_core_guards=sorted(chosen),
                      full_original_closed_size=20-len(opened),
                      relative_core_information_gain=(20-len(opened))-len(chosen),
                      total_shrink_attempts=len(attempts),
                      deleted_guard_count=sum(x['can_prove_guard_redundant'] for x in attempts),
                      UNKNOWN_checks=sum(x['status']=='UNKNOWN' for x in attempts),
                      final_independent_CP_status=last['status'],
                      checks=attempts)
        result['runs'].append(prefix)
        (a.out).write_text(json.dumps(result,indent=2)+'\n')
        print('AUDIT',label,'initial',len(core),'after',len(chosen),
              'final',last['status'],'UNKNOWN',prefix['UNKNOWN_checks'],flush=True)
    result['complete']=True
    (a.out).write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({r['label']:{k:v for k,v in r.items()
        if k in ('initial_core_size','feasibility_only_core_size','final_core_size','outcome',
                 'initial_core_is_entire_closed_machine_set','final_independent_CP_status')}
        for r in result['runs']}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--open-sizes',nargs='+',type=int,default=[3,5])
    p.add_argument('--initial-seconds',type=float,default=1.0)
    p.add_argument('--check-seconds',type=float,default=0.35)
    p.add_argument('--final-seconds',type=float,default=2.0)
    p.add_argument('--seed',type=int,default=333)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
