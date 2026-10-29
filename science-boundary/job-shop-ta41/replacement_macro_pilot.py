#!/usr/bin/env python3
"""Adaptive critical-path REPLACEMENT inside a *single coordinated macro-move*.

Unlike a CP subspace that freezes 340 survivor arcs, each macro-move
temporarily inserts one critical operation, *recomputes* the new critical
machine arcs, then inserts a second operation chosen by one of 4 selectors.
Only the final full-DAG score of the 2-move macro determines acceptance.
The first move can be harmful by up to 200 time units; it is NOT evaluated
as an independent candidate for acceptance.

Four matched arms:
 dynamic: second move on NEWLY created critical edges of tentative state
 static:  second move on original critical edges at initial incumbent
 core:    second move near proven 21 core precedence edges
 random:  second move on uniformly chosen machine positions
All arms have identical first moves, insertion ranges, candidate-score
budget, first-step temperature, acceptance rules, and initial seed.

This is explicitly N7-inspired bounded insertion, NOT exact N7, and
does not implement Ba-Liu-Yuan's 2026 approximate batch evaluator.
"""
import argparse,json,random,time
from collections import Counter
from pathlib import Path
from search import obtain,setup,evaluate
from dynamic_critical_replacement import state,candidate_moves,insert

ROOT=Path(__file__).resolve().parent

def snapshot(orders):
    return tuple(tuple(seq) for seq in orders)

def load_parent(name,pos,dur,baseline):
    if name=='baseline':
        return [seq[:] for seq in baseline]
    folder=ROOT/'results'/('gateway-'+name)
    v=json.loads((folder/'upstream-verdict.json').read_text())
    assert v['valid'] and int(v['score'])==2006
    parent=json.loads((folder/'certificate.json').read_text())['machines']
    assert evaluate(parent,pos,dur)==2006
    return parent

def run(a):
    routes,ds,base=obtain();pos,dur=setup(routes,ds)
    assert evaluate(base,pos,dur)==2006
    original=load_parent(a.parent,pos,dur,base)
    curr=[seq[:] for seq in original]
    _,fixed_critical,_=state(original,pos,dur)
    cons=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert cons['status']=='INFEASIBLE' and len(cons['proven_unsat_core'])==21
    core={(v['machine'],v['from_job'],v['to_job']) for v in cons['proven_unsat_core']}
    rng=random.Random(a.seed)
    seen={snapshot(curr)}
    current_score=2006;best=2006;best_orders=[x[:] for x in curr]
    stats=Counter()
    switches=[]
    improvements=[]
    exact_evaluations=0
    attempts=0
    begins=time.monotonic()
    a.out.mkdir(parents=True,exist_ok=True)
    while exact_evaluations<a.evaluations:
        attempts+=1
        _,old_critical,_=state(curr,pos,dur)
        first_moves=candidate_moves(curr,old_critical,rng,a.first)
        options=[]
        for first in first_moves:
            if exact_evaluations>=a.evaluations:break
            insert(curr,first)
            first_score=evaluate(curr,pos,dur);exact_evaluations+=1
            if first_score is None:
                stats['first_cyclic']+=1
                insert(curr,(first[0],first[2],first[1]))
                continue
            if first_score>best+a.first_uphill:
                stats['first_over_threshold']+=1
                insert(curr,(first[0],first[2],first[1]))
                continue
            first_crit=state(curr,pos,dur)[1]
            newly=first_crit-old_critical
            if newly:stats['tentative_new_path_count']+=1
            if a.policy=='dynamic':focus=newly if newly else first_crit
            elif a.policy=='static':focus=fixed_critical
            elif a.policy=='core':focus=core
            else:focus=set()
            second_moves=candidate_moves(curr,focus,rng,a.second)
            for second in second_moves:
                if exact_evaluations>=a.evaluations:break
                insert(curr,second)
                final=evaluate(curr,pos,dur);exact_evaluations+=1
                if final is not None:
                    stats['final_acyclic']+=1
                    if final<=best+a.accept_uphill:
                        key=snapshot(curr)
                        novelty=key not in seen
                        options.append(dict(score=final,first=first,second=second,
                            first_score=first_score,new_critical=len(newly),
                            novelty=novelty))
                    if final<best:
                        best=final
                        best_orders=[seq[:] for seq in curr]
                        improvements.append({'evaluations':exact_evaluations,'makespan':best})
                        (a.out/'certificate.json').write_text(
                            json.dumps({'machines':best_orders},separators=(',',':'))+'\n')
                        print('IMPROVEMENT',a.parent,a.policy,a.seed,exact_evaluations,best,flush=True)
                        if best<=2005:
                            break
                else:stats['second_cyclic']+=1
                insert(curr,(second[0],second[2],second[1]))
            if best<=2005:
                # Keep the correct certified best; return before undoing a
                # move whose index may have changed under the second move.
                break
            insert(curr,(first[0],first[2],first[1]))
        if best<=2005:break
        if options:
            # Score is primary, then prefer unseen neutral states to prevent
            # a single 2006 plateau node from swallowing exploration.
            options.sort(key=lambda z:(z['score'],not z['novelty'],rng.random()))
            choice=options[0] if rng.random()<0.80 else rng.choice(options[:min(len(options),8)])
            insert(curr,choice['first'])
            insert(curr,choice['second'])
            current_score=evaluate(curr,pos,dur)
            assert current_score==choice['score']
            seen.add(snapshot(curr))
            stats['macros_accepted']+=1
            stats['macros_neutral']+=int(current_score==2006)
            stats['macros_uphill']+=int(current_score>2006)
            stats['accepted_with_harmful_first']+=int(choice['first_score']>choice['score'])
            stats['accepted_first_step_above_2006']+=int(choice['first_score']>2006)
            switches.append({'attempt':attempts,'evaluations':exact_evaluations,
                             'first_intermediate_makespan':choice['first_score'],
                             'final_makespan':current_score,
                             'new_bottleneck_edges_after_first':choice['new_critical'],
                             'first':choice['first'],'second':choice['second']})
        else:stats['macros_without_candidate']+=1
        if attempts%a.reset_period==0:
            curr=[x[:] for x in best_orders]
            current_score=best
            stats['restarts']+=1
        if attempts%80==0:
            print('PROGRESS',a.parent,a.policy,a.seed,exact_evaluations,
                  'best',best,'accepted',stats['macros_accepted'],flush=True)
    assert evaluate(best_orders,pos,dur)==best
    report=dict(instance='ta41',target=2005,baseline_makespan=2006,
        parent=a.parent,policy=a.policy,seed=a.seed,
        operator='two coupled bounded insertions with new critical path recomputed after first tentative move',
        acceptance='evaluate macro endpoints only; intermediate may be strictly worse',
        exact_score_evaluations=exact_evaluations,
        score_evaluation_budget=a.evaluations,first_options=a.first,
        second_options=a.second,first_uphill=a.first_uphill,
        accepted_final_uphill=a.accept_uphill,
        initial_critical_edges=len(fixed_critical),
        verified_best_score=best,
        distinct_accepted_schedule_count=len(seen),
        statistics=dict(stats),
        improvement_events=improvements,
        last_80_accepted_macros=switches[-80:],
        elapsed_seconds=round(time.monotonic()-begins,3),
        status='IMPROVED' if best<=2005 else 'NO_IMPROVEMENT')
    (a.out/'macro-pilot.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k not in ('last_80_accepted_macros','improvement_events')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--policy',required=True,choices=['dynamic','static','core','random'])
    p.add_argument('--parent',default='baseline',choices=['baseline','124'])
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--first',type=int,default=8)
    p.add_argument('--second',type=int,default=14)
    p.add_argument('--evaluations',type=int,default=22000)
    p.add_argument('--first-uphill',type=int,default=180)
    p.add_argument('--accept-uphill',type=int,default=24)
    p.add_argument('--reset-period',type=int,default=120)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
