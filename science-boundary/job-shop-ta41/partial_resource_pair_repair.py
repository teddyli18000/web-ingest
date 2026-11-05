#!/usr/bin/env python3
"""Constructive partial-order repair from *bidirectionally forbidden* resource pairs.

This is a falsifiable transfer test, not a claimed implementation of IEBO.
A partial schedule consists of all fixed job arcs and SOME incumbent
adjacent-machine precedence arcs. Unlike whole-job or time-window release,
each retained resource arc is an independently retractable decision.

For two operations u,v on one machine, under a target makespan L,
if head[u]+duration[u]+tail[v]>L and
   head[v]+duration[v]+tail[u]>L,
then neither u->v nor v->u can be feasible while keeping the current
partial-order DAG unchanged. Both bounds have explicit longest-path
support witnesses; in any improved completion at least one currently
fixed resource edge in their union must be retracted. This is a sound
necessary DISJUNCTION, NOT a claim that any individual arc is mandatory.

Three matched release policies:
  bidirectional: score retained arcs by appearance in these sound
    precompletion resource-conflict witnesses, updating every round;
  critical: rank by slack on the initial partial-order graph, STATIC;
  random: choose remaining arcs uniformly at random.
Each round releases the same number of incumbent adjacent resource arcs,
then runs the SAME full-NoOverlap CP target model with identical limits.
A legal improved complete machine order is independently DAG rescored.
"""
import argparse,json,random,time
from pathlib import Path
from collections import Counter
from search import obtain,setup,evaluate
from structural_cut import disjunctive_dag,cut_analysis
from ortools.sat.python import cp_model

ROOT=Path(__file__).resolve().parent

def parse_case(source):
    if source=='ta41':
        routes,rows,orders=obtain()
    else:
        a=list(map(int,Path(source).read_text().split()))
        assert a[:2]==[30,20] and len(a)==2+1200+600
        b=a[2:1202];routes=[[b[(j*20+k)*2] for k in range(20)] for j in range(30)]
        rows=[[b[(j*20+k)*2+1] for k in range(20)] for j in range(30)]
        t=a[1202:]
        orders=[t[m*30:(m+1)*30] for m in range(20)]
    assert len(routes)==len(rows)==30 and len(orders)==20
    assert all(sorted(row)==list(range(20)) for row in routes)
    assert all(sorted(row)==list(range(30)) for row in orders)
    pos,dur=setup(routes,rows)
    incumbent=evaluate(orders,pos,dur)
    assert incumbent and incumbent>0
    return orders,pos,dur,incumbent

def partial_witnesses(orders,pos,dur,removed,L):
    edges,arcs,topo,head,tail,lb=disjunctive_dag(orders,pos,dur,removed)
    # Deterministic longest-prefix and suffix support paths, encoded
    # as exact 580-bit masks over baseline adjacent machine precedences.
    prefix=[0]*600
    for u in topo:
        for v,idx in edges[u]:
            if head[u]+dur[u]==head[v]:
                mask=prefix[u]|(0 if idx is None else 1<<idx)
                # Tied routes use stable selection to retain a real witness.
                if prefix[v]==0 or mask.bit_count()<prefix[v].bit_count():
                    prefix[v]=mask
    suffix=[0]*600
    for u in reversed(topo):
        for v,idx in edges[u]:
            if tail[u]==dur[u]+tail[v]:
                mask=suffix[v]|(0 if idx is None else 1<<idx)
                if suffix[u]==0 or mask.bit_count()<suffix[u].bit_count():
                    suffix[u]=mask
    scores=Counter();examples=[];nconf=0
    for m,sequence in enumerate(orders):
        ops=[j*20+pos[j][m] for j in sequence]
        for i in range(30):
            u=ops[i]
            for j in range(i+1,30):
                v=ops[j]
                uv=head[u]+dur[u]+tail[v]
                vu=head[v]+dur[v]+tail[u]
                if uv<=L or vu<=L:continue
                nconf+=1
                # A target completion must invalidate at least one of
                # the two overlength support chains. Union is sufficient
                # for this necessary disjunction.
                support=prefix[u]|suffix[v]|prefix[v]|suffix[u]
                support &= ~sum((1<<z for z in removed),0)
                if not support:
                    examples.append(dict(machine=m,u=u,v=v,uv=uv,vu=vu,empty_resource_support=True))
                    continue
                atoms=support.bit_count()
                # Weight compressed explanations and larger deadline excess.
                w=(1.0+min(uv-L,vu-L)/30.0)/(atoms**0.5)
                while support:
                    bit=support&-support
                    idx=bit.bit_length()-1
                    scores[idx]+=w
                    support-=bit
                if len(examples)<10:
                    examples.append(dict(machine=m,u=u,v=v,uv=uv,vu=vu,
                       support_resource_arc_count=atoms))
    return dict(lb=lb,count=nconf,pressure=scores,examples=examples,head=head,tail=tail,arcs=arcs)

def cp_repair(orders,pos,dur,removed,L,seconds,seed):
    mdl=cp_model.CpModel()
    s=[mdl.new_int_var(0,L-dur[i],f's_{i}') for i in range(600)]
    e=[mdl.new_int_var(dur[i],L,f'e_{i}') for i in range(600)]
    inter=[mdl.new_interval_var(s[i],dur[i],e[i],f'iv_{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            mdl.add(s[j*20+k+1]>=e[j*20+k])
    for m,seq in enumerate(orders):
        mdl.add_no_overlap([inter[j*20+pos[j][m]] for j in seq])
        for k,(a,b) in enumerate(zip(seq,seq[1:])):
            idx=m*29+k
            if idx not in removed:
                mdl.add(s[b*20+pos[b][m]]>=e[a*20+pos[a][m]])
    slv=cp_model.CpSolver()
    slv.parameters.max_time_in_seconds=seconds
    slv.parameters.random_seed=seed
    slv.parameters.num_search_workers=4
    t=time.monotonic()
    st=slv.solve(mdl)
    result=dict(status=slv.status_name(st),seconds=round(time.monotonic()-t,3),
       branches=slv.num_branches,conflicts=slv.num_conflicts)
    if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        witness=[sorted(range(30),key=lambda j:slv.value(s[j*20+pos[j][m]]))
                 for m in range(20)]
        score=evaluate(witness,pos,dur)
        assert score is not None and score<=L,(score,L)
        result['independent_makespan']=score
        return result,witness
    return result,None

def run(a):
    orders,pos,dur,incumbent=parse_case(a.start)
    L=incumbent-1
    rng=random.Random(a.seed)
    removed=set()
    starts=time.monotonic()
    # Identical, sound first-stage relaxation for every arm: cut all
    # incumbent overlong paths before invoking the full-resource solver.
    cuts=[]
    while True:
        witness=partial_witnesses(orders,pos,dur,removed,L)
        if witness['lb']<=L:break
        cut=cut_analysis(orders,pos,dur,removed,rng,weighted=False)
        new=set(cut['cut_arcs'])-removed
        assert new
        removed.update(new)
        cuts.append(dict(lb_before=cut['makespan'],arcs=sorted(new)))
        assert len(cuts)<=580
    initial_cuts=sorted(removed)
    initial_witness=partial_witnesses(orders,pos,dur,removed,L)
    # STATIC reference: initial machine arcs nearest target deadline.
    static_scores={}
    for idx,(m,k,u,v) in enumerate(initial_witness['arcs']):
        slack=L-(initial_witness['head'][u]+dur[u]+initial_witness['tail'][v])
        static_scores[idx]=-abs(slack)
    out=dict(instance=('ta41' if a.start=='ta41' else Path(a.start).parent.name),
        method=a.method,seed=a.seed,initial_score=incumbent,target=L,
        initial_critical_path_cut_count=len(initial_cuts),
        initial_critical_path_cut_arcs=initial_cuts,
        initial_critical_path_cut_steps=len(cuts),
        initial_partial_order_longest_path=initial_witness['lb'],
        initial_double_forbidden_machine_pairs=initial_witness['count'],
        initial_conflict_examples=initial_witness['examples'][:3],
        arcs_per_round=a.growth,round_limit=a.rounds,
        cp_seconds_per_round=a.cp_seconds,rounds=[],
        source='Partial-order head/tail necessary resource conflicts; complete CP only for final constructive repair.',
        status='UNRESOLVED',
        caveat='INFEASIBLE excludes only the tested retained-edge partial order. UNKNOWN does not exclude any schedule. An empty witness is not evidence that the global target is impossible.')
    a.out.mkdir(parents=True,exist_ok=True)
    def save():
        out['elapsed_seconds']=round(time.monotonic()-starts,3)
        (a.out/'partial-repair.json').write_text(json.dumps(out,indent=2)+'\n')
    for round_id in range(a.rounds+1):
        obs=partial_witnesses(orders,pos,dur,removed,L)
        assert obs['lb']<=L
        record=dict(iteration=round_id,released_adjacent_arcs=len(removed),
             partial_order_longest_path=obs['lb'],
             double_forbidden_machine_pairs=obs['count'])
        cp,witness=cp_repair(orders,pos,dur,removed,L,a.cp_seconds,a.seed*19+round_id)
        record.update(cp)
        out['rounds'].append(record)
        if witness is not None:
            score=evaluate(witness,pos,dur)
            assert score<=L and score<incumbent
            out['status']='CONSTRUCTIVE_IMPROVEMENT'
            (a.out/'certificate.json').write_text(json.dumps({'machines':witness},separators=(',',':'))+'\n')
        else:
            out['status']='EXHAUSTED_ROUNDS' if round_id==a.rounds else 'ACTIVE'
        save()
        print('ROUND',out['instance'],a.method,round_id,'released',len(removed),
              'double_forbidden',obs['count'],'cp',record['status'],
              'score',record.get('independent_makespan'),flush=True)
        if witness is not None or round_id==a.rounds:break
        remaining=[i for i in range(580) if i not in removed]
        if a.method=='bidirectional':
            power=obs['pressure']
            selection=sorted(remaining,key=lambda x:(-power.get(x,0),rng.random()))[:a.growth]
        elif a.method=='critical':
            selection=sorted(remaining,key=lambda x:(-static_scores[x],rng.random()))[:a.growth]
        else:
            rng.shuffle(remaining);selection=remaining[:a.growth]
        assert len(selection)==a.growth
        record['next_released_resource_arc_ids']=selection
        removed.update(selection)
    out['complete']=True
    save()
    print('RESULT',json.dumps({k:v for k,v in out.items()
             if k not in ('rounds','initial_conflict_examples','initial_critical_path_cut_arcs')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True,
                   help='validated local 30x20 start.txt; or ta41')
    p.add_argument('--method',required=True,
                   choices=['bidirectional','critical','random'])
    p.add_argument('--seed',type=int,default=709)
    p.add_argument('--growth',type=int,default=20)
    p.add_argument('--rounds',type=int,default=10)
    p.add_argument('--cp-seconds',type=float,default=2.5)
    p.add_argument('--out',type=Path,required=True)
    x=p.parse_args()
    assert x.growth*x.rounds<=550 and x.cp_seconds>0
    run(x)
