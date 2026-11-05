#!/usr/bin/env python3
"""Counterfactual Cycle-and-Deadline Closure (CCDC) for 30x20 JSSP.

Instead of first constructing complete new schedules, tentatively reverse one
incumbent machine precedence a->b. In the *partial resource-order graph*:
1. To avoid a directed cycle created by b->a, exactly minimum-cut all remaining
   a->b dependency paths, with immutable job arcs at infinite capacity.
2. Repeatedly minimum-cut the current longest >target paths in the new DAG,
   rediscovering newly substituted bottlenecks until its optimistic bound is
   <=target. The counterfactual is still not a complete machine schedule.
3. Ask CP-SAT for a full valid completion with all surviving precedences fixed,
   the root precedence forcibly reversed, and the target hard.
4. If no completion, extract remaining sufficient resource-assumption cores,
   release further joint decisions guided by CURRENT partial-path replacement,
   STATIC baseline slack, or RANDOM selection, under matched budgets.

This is an original combination of standard directed mincut, DAG longest-path
bounds, CP-SAT assumption cores, and joint completion. Basic ejection chains,
incremental bottleneck repair, and constraint reasoning have prior art.

NEVER infer from no 2005 certificate that the global ta41 target is impossible.
"""
import argparse,json,random,time
from collections import deque
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from search import evaluate
from structural_cut import Dinic

ROOT=Path(__file__).resolve().parent
N=600;INF=10**7

def immutable_and_resource(orders,pos):
    mutable=[]
    for m,seq in enumerate(orders):
        for k,(a,b) in enumerate(zip(seq,seq[1:])):
            mutable.append((a*20+pos[a][m],b*20+pos[b][m],m))
    assert len(mutable)==580
    return mutable

def dag_graph(dur,mutable,removed,reverse=None):
    edges=[[] for _ in range(N)]
    indeg=[0]*N
    def add(u,v,idx):
        edges[u].append((v,idx));indeg[v]+=1
    for j in range(30):
        for k in range(19):add(j*20+k,j*20+k+1,None)
    for i,(u,v,m) in enumerate(mutable):
        if i not in removed:add(u,v,i)
    if reverse is not None:
        u,v,_=mutable[reverse]
        add(v,u,-1)
    queue=deque(i for i in range(N) if indeg[i]==0)
    head=[0]*N;topo=[]
    while queue:
        u=queue.popleft();topo.append(u)
        for v,idx in edges[u]:
            head[v]=max(head[v],head[u]+dur[u])
            indeg[v]-=1
            if indeg[v]==0:queue.append(v)
    if len(topo)!=N:return None
    tail=dur[:]
    for u in reversed(topo):
        for v,idx in edges[u]:
            tail[u]=max(tail[u],dur[u]+tail[v])
    makespan=max(head[i]+dur[i] for i in range(N))
    return dict(edges=edges,topo=topo,head=head,tail=tail,lb=makespan)

def directed_path_mincut(edges,source,sink):
    flow=Dinic(N)
    for u in range(N):
        for v,idx in edges[u]:
            flow.add(u,v,INF if idx is None or idx<0 else 1)
    cost,side=flow.mincut(source,sink)
    if cost>=INF:return None
    selected=set()
    for u in side:
        for v,idx in edges[u]:
            if v not in side and idx is not None and idx>=0:selected.add(idx)
    assert len(selected)==cost,(cost,len(selected))
    return selected

def overlength_mincut(dur,g):
    edges=g['edges'];head=g['head'];tail=g['tail'];C=g['lb']
    graph=Dinic(N+2);source=N;sink=N+1
    critical=[head[i]+tail[i]==C for i in range(N)]
    for u in range(N):
        if critical[u] and head[u]==0:graph.add(source,u,INF)
        if critical[u] and head[u]+dur[u]==C:graph.add(u,sink,INF)
        if not critical[u]:continue
        for v,idx in edges[u]:
            if not critical[v]:continue
            if head[u]+dur[u]+tail[v]!=C:continue
            graph.add(u,v,INF if idx is None or idx<0 else 1)
    cost,side=graph.mincut(source,sink)
    if cost>=INF:return None
    selected=set()
    for u in side:
        if u>=N:continue
        for v,idx in edges[u]:
            if (v not in side and idx is not None and idx>=0 and
                    critical[u] and critical[v] and
                    head[u]+dur[u]+tail[v]==C):
                selected.add(idx)
    assert len(selected)==cost,(len(selected),cost)
    return selected

def counterfactual_closure(dur,mutable,root,target,limit):
    removed={root}
    u,v,_=mutable[root]
    base=dag_graph(dur,mutable,removed)
    assert base is not None
    cycle_break=directed_path_mincut(base['edges'],u,v)
    if cycle_break is None:return None,dict(reason='immutable_dependency_cycle')
    removed|=cycle_break
    g=dag_graph(dur,mutable,removed,reverse=root)
    assert g is not None
    history=[]
    while g['lb']>target and len(removed)<=limit:
        cut=overlength_mincut(dur,g)
        if not cut:return None,dict(reason='unavoidable_partial_overlength',history=history)
        assert cut.isdisjoint(removed)
        history.append(dict(before=g['lb'],broken_arcs=sorted(cut)))
        removed|=cut
        g=dag_graph(dur,mutable,removed,reverse=root)
        assert g is not None
    return (removed,g),dict(cycle_cut_arcs=sorted(cycle_break),
         deadline_cut_rounds=history,
         initial_released_arcs=len(removed),initial_new_order_lb=g['lb'])

def hard_completion(dur,mutable,orders,pos,removed,reverse,L,seconds,seed):
    model=cp_model.CpModel()
    s=[model.new_int_var(0,L-dur[i],f's{i}') for i in range(N)]
    e=[model.new_int_var(dur[i],L,f'e{i}') for i in range(N)]
    interval=[model.new_interval_var(s[i],dur[i],e[i],f'iv{i}') for i in range(N)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([interval[j*20+pos[j][m]] for j in range(30)])
    root_u,root_v,_=mutable[reverse]
    model.add(s[root_u]>=e[root_v])
    assumptions={}
    for i,(u,v,m) in enumerate(mutable):
        if i in removed:continue
        b=model.new_bool_var(f'keep{i}')
        model.add(s[v]>=e[u]).only_enforce_if(b)
        model.add_assumption(b)
        assumptions[b.index]=i
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=seed
    t=time.monotonic()
    st=solver.solve(model)
    rec=dict(status=solver.status_name(st),
         wall_seconds=round(time.monotonic()-t,3),
         branches=solver.num_branches,conflicts=solver.num_conflicts,
         num_assumed_resource_arcs=len(assumptions))
    if st in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        order=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
            for m in range(20)]
        score=evaluate(order,pos,dur)
        assert score is not None and score<=L,(score,L)
        assert (order[mutable[reverse][2]].index(root_v//20)<
                order[mutable[reverse][2]].index(root_u//20))
        rec['independent_makespan']=score
        return rec,order,None
    if st==cp_model.INFEASIBLE:
        raw=solver.sufficient_assumptions_for_infeasibility()
        assert all(x in assumptions for x in raw)
        core={assumptions[x] for x in raw}
        rec['sufficient_core_size']=len(core)
        return rec,None,core
    return rec,None,None

def choose_roots(dur,mutable,orders,seed,maxroots):
    rng=random.Random(seed)
    g=dag_graph(dur,mutable,set())
    C=g['lb']
    slack=[C-(g['head'][u]+dur[u]+g['tail'][v])
        for u,v,m in mutable]
    # Choose a stable, non-oracle-supplied near-critical frontier, with
    # diversity across machines; controls receive identical selected roots.
    ordered=sorted(range(580),key=lambda i:(slack[i],rng.random()))
    heads=[];seen=set()
    for i in ordered:
        if slack[i]>0:break
        heads.append(i)
        if len(heads)>=maxroots//2:break
    for i in ordered:
        if len(heads)>=maxroots:break
        if i not in heads and mutable[i][2] not in seen:
            heads.append(i);seen.add(mutable[i][2])
    for i in ordered:
        if len(heads)>=maxroots:break
        if i not in heads:heads.append(i)
    assert heads
    return heads,slack

def main(a):
    orders,pos,dur,initial=parse_case(a.start)
    L=initial-1;mutable=immutable_and_resource(orders,pos)
    roots,static_slack=choose_roots(dur,mutable,orders,a.seed,a.roots)
    rng=random.Random(a.seed)
    report=dict(instance=('ta41' if a.start=='ta41' else Path(a.start).parent.name),
        incumbent=initial,target=L,policy=a.policy,seed=a.seed,
        selection='candidate root adjacent resource reversal; cycle mincut; replacement deadline mincut; assumption core release; exact CP completion',
        no_full_schedule_needed_for_conflict_prediction=True,
        root_count_limit=a.roots,CP_seconds_per_trial=a.cp_seconds,
        max_repair_rounds_per_root=a.rounds,release_per_core=a.growth,
        max_released_resource_arcs=a.max_released,
        roots=[],status='UNRESOLVED')
    a.out.mkdir(parents=True,exist_ok=True)
    start=time.monotonic()
    for ki,root in enumerate(roots):
        if time.monotonic()-start>a.total_seconds:break
        closure,pre=counterfactual_closure(dur,mutable,root,L,a.max_released)
        rr=dict(root_id=root,root_machine=mutable[root][2],
            baseline_slack=static_slack[root],
            preliminary=pre,rounds=[])
        report['roots'].append(rr)
        if closure is None or len(closure[0])>a.max_released:
            rr['terminal']='INFEASIBLE_INITIAL_CLOSURE'
            continue
        removed,g=closure
        original_count=len(removed)
        for step in range(a.rounds):
            rec,order,core=hard_completion(dur,mutable,orders,pos,removed,
                 root,L,a.cp_seconds,a.seed*1000+ki*100+step)
            rec.update(round=step,freed_resource_arcs=len(removed),
                       partial_order_lb=g['lb'])
            rr['rounds'].append(rec)
            if order is not None:
                rec['score']=evaluate(order,pos,dur)
                (a.out/'certificate.json').write_text(
                    json.dumps({'machines':order},separators=(',',':'))+'\n')
                report['status']='IMPROVED'
                rr['terminal']='IMPROVED'
                break
            if core is None:
                rr['terminal']='UNKNOWN'
                break
            if not core:
                rr['terminal']='FORCED_ROOT_GLOBALLY_INFEASIBLE'
                break
            if step==a.rounds-1:rr['terminal']='EXHAUSTED_CONDITIONED_REPAIRS';break
            dynamic_slack=[
                L-(g['head'][u]+dur[u]+g['tail'][v])
                for u,v,m in mutable]
            if a.policy=='dynamic':
                priority=sorted(core,key=lambda i:
                    (dynamic_slack[i],rng.random()))
            elif a.policy=='static':
                priority=sorted(core,key=lambda i:
                    (static_slack[i],rng.random()))
            elif a.policy=='random':
                priority=list(core);rng.shuffle(priority)
            else:raise AssertionError(a.policy)
            new=priority[:min(a.growth,len(priority))]
            rec['released_core_precedences']=new
            removed.update(new)
            # Every new relaxation weakens, never breaks, the partial DAG.
            g=dag_graph(dur,mutable,removed,reverse=root)
            assert g is not None and g['lb']<=L
            if len(removed)>a.max_released:
                rr['terminal']='RELEASE_BUDGET_EXCEEDED'
                break
        print('ROOT',a.policy,report['instance'],root,
            rr.get('terminal'),len(removed),'calls',len(rr['rounds']),flush=True)
        (a.out/'partial-results.json').write_text(
            json.dumps(dict(complete=False,**report),indent=2)+'\n')
        if report['status']=='IMPROVED':break
    report['complete']=True
    report['elapsed_seconds']=round(time.monotonic()-start,3)
    report['CP_calls']=sum(len(r['rounds']) for r in report['roots'])
    report['roots_tested']=len(report['roots'])
    report['globally_infeasible_claimed']=False
    (a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='roots'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',choices=('dynamic','static','random'),required=True)
    p.add_argument('--seed',type=int,default=333)
    p.add_argument('--roots',type=int,default=18)
    p.add_argument('--rounds',type=int,default=8)
    p.add_argument('--growth',type=int,default=5)
    p.add_argument('--cp-seconds',type=float,default=1.5)
    p.add_argument('--total-seconds',type=float,default=160)
    p.add_argument('--max-released',type=int,default=90)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
