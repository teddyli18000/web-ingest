#!/usr/bin/env python3
"""Oracle-blind constructive Implicit Hitting Set (IHS) over partial machine orders.

Only sees incumbent machine orders and a hard target Cmax < incumbent.
Each iteration:
  1. Solve the minimum-cost set-cover over ALL prior *sufficient* UNSAT
     cores. x_e=1 says retract incumbent resource-arc precedence e.
  2. Query a full NoOverlap/route CP model with all other incumbent
     machine-adjacent precedences as assumptions; NO completed improved
     schedule is required to obtain an UNSAT core.
  3. If UNSAT, add its new resource-arc core and solve the joint hit-set
     again. If feasible, independently reconstruct exact machine orders
     and DAG-score the result.

This is an established CP/MAX-SAT implicit hitting-set formulation,
NOT a claimed new IEBO implementation. The empirical question is whether
a joint, dynamic conflict family (not a one-core novelty heuristic) can
construct an improvement from an independent strong N7 elite, when the
published better oracle is inaccessible.

Even if all cores are hit, an UNKNOWN full-resource CP solve is NOT UNSAT.
The algorithm never reads reference solution permutations or a hidden
target score. Objective: hit-count first; precompletion slack only breaks
ties in the 'static' comparator, without hard-fixing unchosen moves.
"""
import argparse,json,time,random
from pathlib import Path
from ortools.sat.python import cp_model
from search import evaluate
from partial_resource_pair_repair import parse_case
from structural_cut import disjunctive_dag

ROOT=Path(__file__).resolve().parent

def make_full(orders,pos,dur,L):
    model=cp_model.CpModel()
    start=[model.new_int_var(0,L-dur[i],f's{i}') for i in range(600)]
    end=[model.new_int_var(dur[i],L,f'e{i}') for i in range(600)]
    intervals=[model.new_interval_var(start[i],dur[i],end[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(start[j*20+k+1]>=end[j*20+k])
    bits=[]
    for m,seq in enumerate(orders):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
        for k,(a,b) in enumerate(zip(seq,seq[1:])):
            u=a*20+pos[a][m];v=b*20+pos[b][m]
            bit=model.new_bool_var(f'keep_{m}_{k}')
            model.add(start[v]>=end[u]).only_enforce_if(bit)
            bits.append(bit)
    assert len(bits)==580
    return model,bits,start

def solve_hitting_set(cores,weights,rng,seconds):
    if not cores:return set(),dict(status='TRIVIAL',minimum_hits=0)
    hm=cp_model.CpModel()
    bits=[hm.new_bool_var(f'release_{i}') for i in range(580)]
    for core in cores:hm.add(sum(bits[i] for i in core)>=1)
    # Cardinality primary; static / random weighting only tie-breaking.
    # Max sum secondary weights <= 580*6, so factor 5000 dominates.
    hm.minimize(sum((5000+weights[i])*bits[i] for i in range(580)))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=rng.randrange(1,2**30)
    status=solver.solve(hm)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return None,dict(status=solver.status_name(status))
    chosen={i for i,x in enumerate(bits) if solver.value(x)}
    assert all(chosen&set(core) for core in cores)
    return chosen,dict(status=solver.status_name(status),minimum_hits=len(chosen),
      weighted_cost=solver.objective_value,lower_bound=solver.best_objective_bound)

def source_weights(orders,pos,dur,C,policy,seed):
    if policy=='uniform':return [0]*580
    if policy=='random':
        rng=random.Random(seed)
        return [rng.randrange(6) for i in range(580)]
    if policy=='static':
        _,arcs,_,head,tail,_=disjunctive_dag(orders,pos,dur,set())
        # 0 for slack 0, 1 for low slack, 5 for other, as a tie-breaker
        scores=[C-(head[u]+dur[u]+tail[v]) for _,_,u,v in arcs]
        assert len(scores)==580
        return [min(5,max(0,x//3)) for x in scores]
    raise ValueError(policy)

def run(a):
    start_orders,pos,dur,initial=parse_case(a.start)
    L=initial-1
    began=time.monotonic()
    mdl,arc_bits,s=make_full(start_orders,pos,dur,L)
    byindex={x.index:i for i,x in enumerate(arc_bits)}
    rng=random.Random(a.seed)
    weights=source_weights(start_orders,pos,dur,initial,a.policy,a.seed)
    seen=set()
    cores=[]
    events=[]
    report=dict(instance='ta41' if a.start=='ta41' else Path(a.start).parent.name,
        objective='find a complete feasible schedule with score <= incumbent -1',
        initial_score=initial,target=L,
        solver='OR-Tools CP-SAT 9.14.6206',
        method='exact full-resource assumption UNSAT cores + implicit hitting-set coordinated resource release',
        hitset_policy=a.policy,seed=a.seed,remaining_original_machine_arc_choices=580,
        oracle_access=False,full_machine_NoOverlap=True,
        total_time_budget=a.seconds,complete=False,events=events,
        status='ACTIVE')
    a.out.mkdir(parents=True,exist_ok=True)
    def save():
        report['elapsed_seconds']=round(time.monotonic()-began,3)
        report['total_new_verified_unsat_cores']=len(cores)
        report['iterations']=len(events)
        (a.out/'ihs-result.json').write_text(json.dumps(report,indent=2)+'\n')
    prev=None
    for i in range(a.iterations):
        remaining=a.seconds-(time.monotonic()-began)
        if remaining<=1:report['status']='TIME_LIMIT';break
        chosen,hit_info=solve_hitting_set(cores,weights,rng,min(a.hit_seconds,max(0.1,remaining*.15)))
        if chosen is None:
            report['status']='HITSET_UNKNOWN'
            events.append(dict(iteration=i,hit=hit_info));break
        mdl.clear_assumptions()
        mdl.add_assumptions([x for j,x in enumerate(arc_bits) if j not in chosen])
        cp=cp_model.CpSolver()
        cp.parameters.max_time_in_seconds=min(a.cp_seconds,max(.1,remaining*.75))
        cp.parameters.num_search_workers=1
        cp.parameters.random_seed=a.seed
        tic=time.monotonic();status=cp.solve(mdl)
        rec=dict(iteration=i,hit=hit_info,
           released_machine_arcs=len(chosen),released=list(sorted(chosen)),
           prior_core_count=len(cores),status=cp.status_name(status),
           cp_seconds=round(time.monotonic()-tic,3),
           hit_overlap_with_previous=len(chosen&prev) if prev is not None else None)
        if status==cp_model.INFEASIBLE:
            raw=cp.sufficient_assumptions_for_infeasibility()
            if not raw:
                report['status']='INFEASIBLE_WITH_NO_ASSUMPTIONS_CORE'
                events.append(rec);break
            core=frozenset(byindex[x] for x in raw)
            assert core and core.isdisjoint(chosen)
            if core in seen:
                raise AssertionError('Same UNSAT core even though chosen set hits all earlier cores')
            seen.add(core);cores.append(sorted(core))
            rec.update(new_core_size=len(core),
                new_core_machine_count=len({j//29 for j in core}),
                new_core_relation_ids=sorted(core),
                new_core_intersection_with_previous_count=sum(bool(core&set(c)) for c in cores[:-1]))
        elif status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
            candidate=[sorted(range(30),key=lambda j:cp.value(s[j*20+pos[j][m]]))
                       for m in range(20)]
            actual=evaluate(candidate,pos,dur)
            assert actual is not None and actual<=L,(actual,L)
            rec['independent_verified_score']=actual
            rec['full_candidate_machine_orders']=True
            (a.out/'certificate.json').write_text(
                json.dumps({'machines':candidate},separators=(',',':'))+'\n')
            report['status']='CONSTRUCTIVE_IMPROVEMENT'
            report['improvement']=initial-actual
            report['verified_score']=actual
            report['found_released_set']=sorted(chosen)
            report['actual_flipped_adjacent_relations']=[
                m*29+k for m,seq in enumerate(start_orders)
                for k,(aa,bb) in enumerate(zip(seq,seq[1:]))
                if candidate[m].index(aa)>candidate[m].index(bb)]
        else:
            report['status']='UNRESOLVED_CP_UNKNOWN'
        prev=chosen
        events.append(rec)
        save()
        if i%25==0 or report['status']!='ACTIVE':
            print('STEP',report['instance'],a.policy,i,
                  rec['status'],'released',len(chosen),'cores',len(cores),
                  'elapsed',report['elapsed_seconds'],flush=True)
        if report['status']!='ACTIVE':break
    else:
        report['status']='ITERATION_LIMIT'
    report['complete']=True
    save()
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='events'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--policy',choices=('uniform','static','random'),required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--seconds',type=float,default=75)
    p.add_argument('--cp-seconds',type=float,default=0.5)
    p.add_argument('--hit-seconds',type=float,default=0.45)
    p.add_argument('--iterations',type=int,default=10000)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
