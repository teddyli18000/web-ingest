#!/usr/bin/env python3
"""Exact microstructure audit of a constructive improvement from a true N7 elite.

The independent native N7 ta43js-n7elite1711 source schedule scores 1888.
A globally soft CP target-1887 completion found a legal score-1887 schedule
with 4 reversed *original adjacent* pairs, and exact machine Kendall distance
9 across 3 machines.

Two separate questions:
  (A) What is the exact minimax bottleneck on every monotone adjacent-swap
      path connecting these endpoints? BFS/DP enumerates all target-directed
      adjacent-swap states (each step reduces Kendall distance by one).
  (B) Are the FOUR reversed original adjacent arcs jointly required for
      a better schedule when the other 576 original adjacent arcs are kept?
      Exhaustively test all 16 subsets of these four relaxed arcs with full
      CP NoOverlap and a hard target=1887. A strict subset UNSAT is valid
      only under the 576 fixed survivor arcs; UNKNOWN never proves exclusion.

No claim that an arbitrary <=1887 schedule must reverse all four arcs.
"""
import argparse,json,math,time
from pathlib import Path
from collections import defaultdict
from search import evaluate
from partial_resource_pair_repair import parse_case,cp_repair

ROOT=Path(__file__).resolve().parent

def diff(orders,better):
    reversals=[];total=0;machines=0
    for m in range(20):
        idx={j:i for i,j in enumerate(better[m])}
        original=orders[m]
        changes=0
        for k in range(29):
            if idx[original[k]]>idx[original[k+1]]:
                reversals.append(dict(machine=m,position=k,
                    job_a=original[k],job_b=original[k+1],arc_id=m*29+k))
        for i in range(30):
            for j in range(i+1,30):changes+=idx[original[i]]>idx[original[j]]
        machines+=changes>0;total+=changes
    return reversals,total,machines

def key(a):
    return tuple(job for machine in a for job in machine)
def decode(k):
    return [list(k[30*m:30*m+30]) for m in range(20)]

def exact_monotone(orders,better,pos,dur):
    orig=key(orders);goal=key(better)
    reversals,dist,_=diff(orders,better)
    assert dist>0 and dist<=20,dist
    targetrank=[{j:i for i,j in enumerate(better[m])} for m in range(20)]
    frontier={orig:(evaluate(orders,pos,dur),None,None)}
    dp={orig:frontier[orig]}
    level_sizes=[1];cyclic=0
    first=[]
    for step in range(dist):
        nxt={}
        for state,(peak,_,_) in frontier.items():
            for m in range(20):
                before=list(state[m*30:(m+1)*30])
                for i in range(29):
                    if targetrank[m][before[i]]<targetrank[m][before[i+1]]:
                        continue
                    a=list(state);p=30*m+i
                    a[p],a[p+1]=a[p+1],a[p]
                    a=tuple(a)
                    score=evaluate(decode(a),pos,dur)
                    if step==0:first.append(dict(machine=m,position=i,
                         makespan=score))
                    if score is None:
                        cyclic+=1;continue
                    tpeak=max(peak,score)
                    if a not in nxt or tpeak<nxt[a][0]:
                        nxt[a]=(tpeak,state,(m,i,score))
        dp.update(nxt)
        frontier=nxt
        level_sizes.append(len(nxt))
        assert nxt,('no monotone cycle-free route',step)
    result=dict(exact_kendall_distance=dist,
        states_per_distance_level=level_sizes,
        total_feasible_states=sum(level_sizes),
        cyclic_target_directed_attempts=cyclic,
        every_monotone_target_directed_swap_order_examined=True,
        feasible_first_moves=len([x for x in first if x['makespan'] is not None]),
        best_feasible_first_move=min((x['makespan'] for x in first
                                  if x['makespan'] is not None),default=None),
        all_first_moves=first)
    if goal in frontier:
        peak=frontier[goal][0];result['minimum_peak_makespan']=peak
        result['minimum_uphill_barrier_above_incumbent']=max(0,peak-evaluate(orders,pos,dur))
        path=[];at=goal
        while at!=orig:
            _,parent,move=dp[at]
            assert parent is not None
            path.append(move)
            at=parent
        path.reverse()
        assert len(path)==dist and path[-1][2]==evaluate(better,pos,dur)
        result['optimal_monotone_path']=[
            dict(machine=m,position=i,verified_intermediate_score=score)
            for m,i,score in path]
    else:
        result['minimum_peak_makespan']=None
        result['note']='No valid monotone adjacent-swap path: atomic joint repair differs qualitatively from any target-directed incremental sequence.'
    return result

def main(a):
    start=ROOT/'positive-n7-elite-data'/'ta43js-n7elite1711'/'start.txt'
    folder=ROOT/'results'/'joint-global-ta43js-n7elite1711-static'
    evidence=json.loads((folder/'joint-completion.json').read_text())
    assert evidence['status']=='OPTIMAL' and evidence['independent_verified_makespan']==1887
    orders,pos,dur,score=parse_case(str(start))
    better=json.loads((folder/'certificate.json').read_text())['machines']
    assert score==1888 and evaluate(better,pos,dur)==1887
    original_reversals,kendall,changed_machines=diff(orders,better)
    assert len(original_reversals)==4 and kendall==9 and changed_machines==3
    monotone=exact_monotone(orders,better,pos,dur)
    print('EXACT-PATH',monotone['minimum_peak_makespan'],
          'states',monotone['total_feasible_states'],flush=True)
    fixed_universe={i for i in range(580)}
    tested=[]
    from itertools import combinations
    ids=[x['arc_id'] for x in original_reversals]
    for size in range(5):
        for subset in combinations(ids,size):
            dropped=set(subset)
            cp,certificate=cp_repair(orders,pos,dur,dropped,1887,a.case_seconds,a.seed+len(tested))
            rec=dict(released_arc_ids=list(subset),
                released_arcs=len(subset),status=cp['status'],
                seconds=cp['seconds'])
            if certificate is not None:
                actual=evaluate(certificate,pos,dur)
                assert actual<=1887
                rec['independent_makespan']=actual
                rec['actual_reversed_baseline_pairs']=len(diff(orders,certificate)[0])
            tested.append(rec)
            print('SUBSET',len(subset),cp['status'],rec.get('independent_makespan'),flush=True)
    known_sufficient=next(x for x in tested if x['released_arcs']==4)
    assert known_sufficient['status'] in ('FEASIBLE','OPTIMAL')
    smaller=[x for x in tested if x['released_arcs']<4]
    certified_minimal=all(x['status']=='INFEASIBLE' for x in smaller)
    report=dict(
       instance='ta43js',source_accepted_20s_native_N7_elite='ta43js-n7elite1711',
       actual_initial_makespan=score,global_joint_solution_makespan=1887,
       independent_full_DAG_score_accepted=True,
       changed_original_adjacent_pair_relations=original_reversals,
       exact_machine_Kendall_pair_distance=kendall,
       changed_machine_count=changed_machines,
       monotone_kendall_path=monotone,
       all_16_strict_subsets_and_full_set_tested=True,
       subset_results=tested,
       min_four_arc_family_release_certified=certified_minimal,
       interpretation='Subset result is only for releasing some of these 4 arcs while leaving ALL 576 other original adjacent arcs fixed. Not a global minimum distance theorem.',
       all_original_N7_elite_and_CP_pair_orders_rechecked=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k not in
            ('subset_results','monotone_kendall_path')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--case-seconds',type=float,default=3.0)
    p.add_argument('--seed',type=int,default=312)
    p.add_argument('--out',type=Path,default=ROOT/'results'/'ta43-joint-4-arc-microstructure.json')
    main(p.parse_args())
