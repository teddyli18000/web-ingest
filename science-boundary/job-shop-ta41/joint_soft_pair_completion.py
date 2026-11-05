#!/usr/bin/env python3
"""Constructive global macro repair at deadline Cmax(incumbent)-1.

The entire machine order is FREE, no survivor restrictions; all 600
operations and full 20-machine NoOverlap are unconditional. An explicit
Boolean is attached to each of the 580 incumbent adjacent machine pairs:
false means keep the original orientation, true means reverse it. Any
legal machine permutation is representable, so these are preferences,
NOT a limited neighborhood.

We minimize weighted violated-incumbent pairs subject to hard improvement.
Weights use one of:
  uniform   : no partial-order information;
  static    : near-critical original machine arcs;
  energetic : precompletion multi-operation overload support;
  cp-core   : a sufficient assumptions UNSAT core of the target-constrained
              NoOverlap model, extracted BEFORE any improved full schedule.

This is a matched mechanism comparison of selection bias; no novelty
claim about interval models or UNSAT cores. Every candidate is DAG
rescored from its full machine orders, and ta41 candidates must pass
the official Few Shots verifier before any record claim.
"""
import argparse,json,random,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import evaluate
from structural_cut import disjunctive_dag,cut_analysis
from partial_resource_pair_repair import parse_case,partial_witnesses,energetic_conflicts

ROOT=Path(__file__).resolve().parent

def original_arc_data(orders,pos):
    return [(m,k,a*20+pos[a][m],b*20+pos[b][m])
            for m,seq in enumerate(orders)
            for k,(a,b) in enumerate(zip(seq,seq[1:]))]

def cheap_arc_set(orders,pos,dur,C,L,policy,seed):
    rng=random.Random(seed)
    arcs=original_arc_data(orders,pos)
    if policy=='uniform':
        return set(),dict(selection='none')
    if policy=='static':
        _,_,_,h,t,_=disjunctive_dag(orders,pos,dur,set())
        slack={i:C-(h[u]+dur[u]+t[v]) for i,(m,k,u,v) in enumerate(arcs)}
        selected=set(sorted(range(580),key=lambda i:(slack[i],rng.random()))[:120])
        return selected,dict(selection='initial critical slack',min_slack=min(slack.values()),
                 cheap_arcs=len(selected))
    if policy=='energetic':
        removed=set()
        while True:
            obs=partial_witnesses(orders,pos,dur,removed,L)
            if obs['lb']<=L:break
            cut=cut_analysis(orders,pos,dur,removed,rng,weighted=False)
            removed.update(cut['cut_arcs'])
        group=energetic_conflicts(orders,pos,dur,removed,L,obs)
        score=group['pressure']
        selected=set(removed)
        selected.update(sorted((i for i in range(580) if i not in selected),
               key=lambda i:(-score.get(i,0),rng.random()))[:max(0,120-len(selected))])
        return selected,dict(selection='precompletion energetic overload',
                precompletion_overload_machines=group['count'],
                precompletion_biggest_energy_excess=group['maximum_excess'],
                relaxed_for_longest_path=len(removed),cheap_arcs=len(selected))
    raise AssertionError(policy)

def cp_core_at_partial_order(orders,pos,dur,L,seconds):
    # Every incumbent adjacent resource precedence is a separately
    # retractable *assumption*. The solver sees a partial schedule with
    # hard job orders, full NoOverlap, and deadline, not a known new order.
    model=cp_model.CpModel()
    st=[model.new_int_var(0,L-dur[i],f's{i}') for i in range(600)]
    en=[model.new_int_var(dur[i],L,f'e{i}') for i in range(600)]
    ints=[model.new_interval_var(st[i],dur[i],en[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(st[j*20+k+1]>=en[j*20+k])
    keep=[]
    for m,seq in enumerate(orders):
        model.add_no_overlap([ints[j*20+pos[j][m]] for j in range(30)])
        for k,(a,b) in enumerate(zip(seq,seq[1:])):
            x=model.new_bool_var(f'keep_{m}_{k}')
            u=a*20+pos[a][m];v=b*20+pos[b][m]
            model.add(st[v]>=en[u]).only_enforce_if(x)
            keep.append(x)
    model.add_assumptions(keep)
    s=cp_model.CpSolver()
    s.parameters.max_time_in_seconds=seconds
    s.parameters.num_search_workers=1
    stat=s.solve(model)
    report=dict(oracle='hard full NoOverlap and job arcs, partial precedence assumptions',
       status=s.status_name(stat),elapsed=s.wall_time)
    result=set()
    if stat==cp_model.INFEASIBLE:
        by_idx={bit.index:i for i,bit in enumerate(keep)}
        raw=s.sufficient_assumptions_for_infeasibility()
        assert raw and all(x in by_idx for x in raw)
        result={by_idx[x] for x in raw}
        report.update(sufficient_unsat_core_size=len(result),
                      sufficient_core_arc_ids=sorted(result))
    return result,report

def run(a):
    orders,pos,dur,C=parse_case(a.start)
    L=C-1
    begin=time.monotonic()
    if a.policy=='cp-core':
        selected,src=cp_core_at_partial_order(orders,pos,dur,L,a.core_seconds)
        if not selected:src['core_fallback']='none; uniformly weight all arcs'
    else:
        selected,src=cheap_arc_set(orders,pos,dur,C,L,a.policy,a.seed)
    model=cp_model.CpModel()
    s=[model.new_int_var(0,L-dur[i],f's_{i}') for i in range(600)]
    e=[model.new_int_var(dur[i],L,f'e_{i}') for i in range(600)]
    ints=[model.new_interval_var(s[i],dur[i],e[i],f'o{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    flips=[]
    for m,seq in enumerate(orders):
        model.add_no_overlap([ints[j*20+pos[j][m]] for j in range(30)])
        for k,(job_a,job_b) in enumerate(zip(seq,seq[1:])):
            idx=m*29+k
            x=model.new_bool_var(f'reverse_{m}_{k}')
            u=job_a*20+pos[job_a][m]
            v=job_b*20+pos[job_b][m]
            model.add(s[v]>=e[u]).only_enforce_if(x.Not())
            model.add(s[u]>=e[v]).only_enforce_if(x)
            flips.append(x)
    assert len(flips)==580
    # Penalize unpromising departures while allowing ALL pair changes
    # whenever required. Not a fixed survivor-order subspace.
    weights=[1 if a.policy=='uniform' or i in selected else 8
             for i in range(580)]
    model.minimize(sum(weights[i]*flips[i] for i in range(580)))
    # Warm hints from incumbent (which itself exceeds target by one);
    # hints may violate the stricter horizon but never impose a constraint.
    _,_,_,head,tail,_=disjunctive_dag(orders,pos,dur,set())
    for i in range(600):
        v=min(head[i],L-dur[i])
        model.add_hint(s[i],v)
        model.add_hint(e[i],v+dur[i])
    for bit in flips:model.add_hint(bit,0)
    cp=cp_model.CpSolver()
    cp.parameters.random_seed=a.seed
    cp.parameters.num_search_workers=4
    cp.parameters.max_time_in_seconds=a.seconds
    st=time.monotonic()
    status=cp.solve(model)
    rec=dict(instance=('ta41' if a.start=='ta41' else Path(a.start).parent.name),
      method='full joint completion of 580 soft adjacent resource-orientation variables',
      policy=a.policy,seed=a.seed,incumbent_makespan=C,
      hard_target_makespan=L,all_machine_permutations_allowed=True,
      original_adjacencies_hard_fixed=0,
      source_diagnostic=src,cheap_arc_count=len(selected),
      status=cp.status_name(status),
      branch_count=cp.num_branches,conflicts=cp.num_conflicts,
      cp_seconds=round(time.monotonic()-st,3),
      total_wall_seconds=round(time.monotonic()-begin,3),
      objective_bound=cp.best_objective_bound,
      claimed_global_infeasibility=(status==cp_model.INFEASIBLE))
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        completed=[sorted(range(30),key=lambda j:cp.value(s[j*20+pos[j][m]]))
                   for m in range(20)]
        score=evaluate(completed,pos,dur)
        assert score is not None and score<=L
        rec['independent_verified_makespan']=score
        rec['flipped_adjacent_resource_pairs']=sum(cp.value(x) for x in flips)
        rec['favored_flipped_pairs']=sum(cp.value(x) for i,x in enumerate(flips) if i in selected)
        (a.out/'certificate.json').write_text(json.dumps({'machines':completed},separators=(',',':'))+'\n')
    (a.out/'joint-completion.json').write_text(json.dumps(rec,indent=2)+'\n')
    print('RESULT',json.dumps(rec),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',required=True,choices=['uniform','static','energetic','cp-core'])
    p.add_argument('--seconds',type=float,default=55.0)
    p.add_argument('--core-seconds',type=float,default=3.0)
    p.add_argument('--seed',type=int,default=101)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
