#!/usr/bin/env python3
"""Joint implicit hitting-set construction on partial-order resource conflicts.

Precompletion counterfactual: pick one original adjacent machine orientation
to reverse, then *learn necessary resource-retraction clauses* from:
  (a) alternate directed paths creating a cycle under that reversal,
  (b) target-breaking longest precedence paths,
  (c) source-faithful full-resource CP-SAT assumption UNSAT cores.
Every clause C means: at least ONE retained mutable machine arc in C must
be retracted to admit a Cmax<=target completion with the proposed root.

Unlike earlier greedy-monotone release, solve a GLOBAL weighted hitting set
over ALL clauses on EVERY iteration. Re-allow previously released edges to
be fixed if a different joint cover is better. Reject a proposal only
after independent full-NoOverlap target CP completion.
Only a complete independently scored machine order is success.

Standard implicit hitting set / MaxSAT and CP cores have prior art; this
experiment tests precompletion graph conflict explanations and their
transfer benefit. No novelty is claimed for the generic mechanism.
"""
import argparse,json,random,time
from collections import Counter,deque
from pathlib import Path
from ortools.sat.python import cp_model
from counterfactual_joint_cut import (
    immutable_and_resource,dag_graph,hard_completion,counterfactual_closure,
    choose_roots,N)
from partial_resource_pair_repair import parse_case
from search import evaluate

ROOT=Path(__file__).resolve().parent

def path_clause(edges,source,target):
    pred={source:None}
    q=deque([source])
    while q:
        u=q.popleft()
        if u==target:break
        for v,idx in edges[u]:
            if v in pred:continue
            pred[v]=(u,idx)
            q.append(v)
    if target not in pred:return None
    arc=[]
    at=target
    while at!=source:
        u,idx=pred[at]
        if idx is not None and idx>=0:arc.append(idx)
        at=u
    return set(arc)

def longest_path_clause(dur,g,L):
    edges=g['edges'];head=g['head'];tail=g['tail']
    C=g['lb']
    assert C>L
    # Obtain one explicit lower-bound violating job+machine path.
    by_dest=[[] for _ in range(N)]
    for u in range(N):
        for v,idx in edges[u]:
            if head[v]==head[u]+dur[u]:
                by_dest[v].append((u,idx))
    last=max(range(N),key=lambda i:head[i]+dur[i])
    assert head[last]+dur[last]==C
    mask=[]
    while head[last]>0:
        preds=by_dest[last]
        assert preds,(last,head[last])
        u,idx=min(preds,key=lambda x:(x[1] is not None and x[1]>=0,x[0]))
        if idx is not None and idx>=0:mask.append(idx)
        last=u
    return set(mask)

def pair_slack(dur,mutable,g,deadline):
    return [deadline-(g['head'][u]+dur[u]+g['tail'][v]) for u,v,m in mutable]

def weighted_cover(clauses,root,mutable,static_slack,dynamic_slack,
                   policy,rng,seconds):
    model=cp_model.CpModel()
    x=[model.new_bool_var(f'release_{i}') for i in range(580)]
    model.add(x[root]==1)
    for i,c in enumerate(clauses):
        model.add(sum(x[j] for j in c)>=1)
    # Cardinality is the primary term; the policy is a secondary tie break.
    priority=[]
    noise=[rng.randrange(4) for _ in range(580)]
    for i in range(580):
        if policy=='dynamic':z=dynamic_slack[i]
        elif policy=='static':z=static_slack[i]
        elif policy=='random':z=4
        else:raise ValueError(policy)
        if policy=='random':priority.append(1+noise[i])
        else:priority.append(min(12,max(0,z))+1+noise[i])
    model.minimize(20000*sum(x)+sum(priority[i]*x[i] for i in range(580)))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    status=solver.solve(model)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return None,dict(status=solver.status_name(status))
    selected={i for i in range(580) if solver.value(x[i])}
    assert root in selected and all(selected.intersection(c) for c in clauses)
    return selected,dict(status=solver.status_name(status),
        selected_arc_count=len(selected),exact_minimum_cardinality_proven=(
            status==cp_model.OPTIMAL),solver_seconds=solver.wall_time)

def augmented_release_ranking(clauses,chosen,mutable,original_slack,
                              current_slack,policy,rng):
    """Predict surplus coordinated decisions beyond a minimal hitting set.

    Hitting only known UNSAT clauses is necessary, never sufficient. A
    separate completion probe releases extra machine relations expected
    to participate in still-hidden bottleneck replacement conflicts.
    This probe uses no oracle order; it is an independently falsifiable
    experiment over source-observable core/path statistics.
    """
    density=Counter()
    for clause in clauses:
        w=1.0/(len(clause)**0.5)
        for i in clause:
            density[i]+=w
    neighbor=Counter()
    for i in chosen:
        for offset in (-3,-2,-1,1,2,3):
            j=i+offset
            if 0<=j<580 and j//29==i//29:
                neighbor[j]+=1.0/(abs(offset)**0.7)
    def rating(i):
        if policy=='random':
            return rng.random()
        closeness=neighbor[i]
        if policy=='static':
            slack=original_slack[i]
            return (2.0/(1+max(0,slack)) +
                    0.15*density[i]+0.1*closeness+rng.random()*0.01)
        if policy=='dynamic':
            slack=current_slack[i]
            return (2.0/(1+max(0,slack)) +
                    1.25*density[i]+0.6*closeness+rng.random()*0.01)
        raise ValueError(policy)
    return sorted((i for i in range(580) if i not in chosen),
                  key=lambda i:-rating(i))

def run(args):
    orders,pos,dur,initial=parse_case(args.start)
    target=initial-1
    mutable=immutable_and_resource(orders,pos)
    roots,static_slack=choose_roots(dur,mutable,orders,args.seed,
         max(args.roots,args.root_pool))
    if args.root_ids:
        roots=args.root_ids
    rng=random.Random(args.seed)
    # Root selection is entirely oracle-blind. Rank candidate seed
    # reversals by the MINIMUM number of partial-order resource arcs
    # needed to eliminate the counterfactual cycle and deadline
    # obstructions; then by remaining optimistic makespan. A root which
    # already needs 30 releases is less attractive than one needing 1.
    prelim={}
    for root in roots:
        prelim[root]=counterfactual_closure(
            dur,mutable,root,target,args.max_preliminary_cut)
    if not args.root_ids:
        jitter={root:rng.random() for root in roots}
        roots.sort(key=lambda root:(
            prelim[root][0] is None,
            len(prelim[root][0][0]) if prelim[root][0] is not None else 999,
            prelim[root][0][1]['lb'] if prelim[root][0] is not None else 999999,
            static_slack[root],jitter[root]))
        roots=roots[:args.roots]
    begin=time.monotonic()
    output=dict(instance=('ta41' if args.start=='ta41'
            else Path(args.start).parent.name),
        target=target,incumbent=initial,policy=args.policy,
        experimental_design='counterfactual reversal, online path cycle/deadline/resource UNSAT clauses, reoptimized nonmonotone joint hitting set, complete full NoOverlap CP',
        root_selection=('FIXED ORACLE-AWARE DIAGNOSTIC: NOT BLIND' if args.root_ids
            else 'oracle-blind near-critical root set reordered by minimal counterfactual cycle+deadline closure'),
        root_ids=roots,root_screened=len(prelim),root_limit=args.roots,max_iterations_per_root=args.iterations,
        full_CP_seconds=args.cp_seconds,hitting_set_seconds=args.hit_seconds,
        global_wall_budget=args.seconds,records=[],
        status='UNRESOLVED')
    args.out.mkdir(parents=True,exist_ok=True)
    for root_index,root in enumerate(roots):
        if time.monotonic()-begin>=args.seconds:break
        # Use closure only to cheaply identify roots whose reversed
        # precedence cannot fit even in any partial order; do not
        # *permanently* accept its arbitrary mincut selections.
        closure,proof=prelim[root]
        record=dict(root=root,machine=mutable[root][2],
                    initial_slack=static_slack[root],
                    preliminary=proof,iterations=[])
        output['records'].append(record)
        if closure is None:
            record['outcome']='PROVEN_IMPOSSIBLE_INITIAL_PARTIAL_ORDER'
            continue
        seen=set();clauses=[]
        chosen={root}
        latest=dag_graph(dur,mutable,chosen,reverse=None)
        assert latest is not None
        for trial in range(args.iterations):
            if time.monotonic()-begin>args.seconds:
                record['outcome']='GLOBAL_TIME_LIMIT'
                break
            proposed=dag_graph(dur,mutable,chosen,reverse=root)
            trace=dict(iteration=trial,release_size=len(chosen),clauses=len(clauses))
            clause=None;category=None
            if proposed is None:
                # The only new edge is reverse(root): cycle iff u can
                # reach v through fixed surviving original resource arcs.
                u,v,_=mutable[root]
                base=dag_graph(dur,mutable,chosen,reverse=None)
                assert base is not None
                clause=path_clause(base['edges'],u,v)
                category='cycle_precedence'
            elif proposed['lb']>target:
                clause=longest_path_clause(dur,proposed,target)
                category='partial_overlong_path'
            else:
                rec,cert,core=hard_completion(
                    dur,mutable,orders,pos,chosen,root,target,
                    args.cp_seconds,args.seed+100000*root_index+trial)
                trace['completion']=rec
                if cert is not None:
                    val=evaluate(cert,pos,dur)
                    assert val<initial and val<=target
                    (args.out/'certificate.json').write_text(
                        json.dumps({'machines':cert},separators=(',',':'))+'\n')
                    trace.update(candidate_makespan=val)
                    output['status']='IMPROVED'
                    record['outcome']='IMPROVED'
                    record['iterations'].append(trace)
                    break
                if core is None:
                    record['outcome']='COMPLETION_UNKNOWN'
                    record['iterations'].append(trace)
                    break
                clause=core
                category='hard_resource_unsat_core'
            if not clause:
                record['outcome']='ROOT_REVERSE_IMPOSSIBLE_WITHOUT_JOB_REORDER'
                record['iterations'].append(trace)
                break
            clause=frozenset(clause)
            assert clause.isdisjoint(chosen),(category,root,trial)
            if clause in seen:
                raise RuntimeError('duplicate unhit necessary clause')
            seen.add(clause)
            clauses.append(clause)
            trace.update(category=category,necessary_clause_size=len(clause))
            # Dynamic weights reflect the newly changed partial
            # critical structure. Static ones remain at original score.
            reference=proposed if proposed is not None else latest
            dynamic_slack=pair_slack(dur,mutable,reference,target)
            next_set,meta=weighted_cover(clauses,root,mutable,static_slack,
                dynamic_slack,args.policy,rng,args.hit_seconds)
            trace['hitting_set']=meta
            record['iterations'].append(trace)
            if next_set is None:
                record['outcome']='HITTING_SET_TIMEOUT'
                break
            # A new optimally coordinated release may KEEP edges from the
            # prior iteration. This nonmonotonicity is the point of study.
            trace['released_from_previous_set']=len(chosen-next_set)
            trace['newly_released']=len(next_set-chosen)
            chosen=next_set

            # Precompletion hypothesis: a minimum hitting set is often too
            # brittle. Periodically ask the same full CP completion oracle
            # about a coordinated, source-only group of EXTRA future
            # replacement conflicts. Keep fixed assignments only for this
            # constructive probe; resume the optimal hitting-set solver
            # unchanged if the augmented group does not improve.
            if args.augment_every and (trial+1)%args.augment_every==0:
                ranking=augmented_release_ranking(
                    clauses,chosen,mutable,static_slack,dynamic_slack,
                    args.policy,rng)
                trace['augmented_probes']=[]
                for count in args.augment_budgets:
                    if count<=len(chosen):continue
                    augmented=chosen|set(ranking[:count-len(chosen)])
                    if len(augmented)>args.max_release:continue
                    probe,found,core=hard_completion(
                        dur,mutable,orders,pos,augmented,root,target,
                        args.cp_seconds,args.seed+2000000+root_index*5000+
                        trial*20+count)
                    trace['augmented_probes'].append(dict(
                        total_released_arcs=len(augmented),
                        status=probe['status'],
                        sufficient_core_size=(len(core) if core is not None else None),
                        wall_seconds=probe['wall_seconds']))
                    if found is not None:
                        val=evaluate(found,pos,dur)
                        assert val<initial and val<=target
                        (args.out/'certificate.json').write_text(
                            json.dumps({'machines':found},separators=(',',':'))+'\\n')
                        output['status']='IMPROVED'
                        record['outcome']='AUGMENTED_CONSTRUCTIVE_IMPROVEMENT'
                        trace['candidate_makespan']=val
                        break
                    if core:
                        c=frozenset(core)
                        if c not in seen:
                            assert c.isdisjoint(chosen)
                            clauses.append(c);seen.add(c)
                if output['status']=='IMPROVED':
                    break
            latest=dag_graph(dur,mutable,chosen,reverse=None)
            assert latest is not None
            if len(chosen)>args.max_release:
                record['outcome']='RELEASE_BUDGET_EXCEEDED'
                break
            if trial==args.iterations-1:record['outcome']='ITERATION_LIMIT'
        print('ROOT',output['instance'],args.policy,root,record.get('outcome'),
             'clauses',len(clauses),'released',len(chosen),flush=True)
        output['records'][-1]['necessary_clause_category_counts']=dict(
            Counter(x.get('category') for x in record['iterations'] if x.get('category')))
        (args.out/'partial-results.json').write_text(
            json.dumps(output,indent=2)+'\n')
        if output['status']=='IMPROVED':break
    output['complete']=True
    output['elapsed_seconds']=round(time.monotonic()-begin,3)
    output['roots_tested']=len(output['records'])
    output['partial_conflicts_learned']=sum(
        len(r['iterations']) for r in output['records'])
    (args.out/'results.json').write_text(json.dumps(output,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in output.items() if k!='records'}),
          flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',choices=['dynamic','static','random'],required=True)
    p.add_argument('--seed',type=int,default=333)
    p.add_argument('--roots',type=int,default=18)
    p.add_argument('--root-pool',type=int,default=80)
    p.add_argument('--root-ids',type=int,nargs='*',default=[])
    p.add_argument('--iterations',type=int,default=80)
    p.add_argument('--cp-seconds',type=float,default=1.0)
    p.add_argument('--hit-seconds',type=float,default=1.0)
    p.add_argument('--augment-every',type=int,default=0)
    p.add_argument('--augment-budgets',type=int,nargs='+',default=[12,24,48])
    p.add_argument('--seconds',type=float,default=120.0)
    p.add_argument('--max-release',type=int,default=120)
    p.add_argument('--max-preliminary-cut',type=int,default=120)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
