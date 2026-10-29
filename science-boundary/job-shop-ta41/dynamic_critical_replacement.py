#!/usr/bin/env python3
"""Dynamic Critical-Path Replacement Repair (DCPRR), preregistered pilot.

This is an original synthesis, NOT a claimed implementation of Ba et al.'s
2026 linear-time approximate N7 evaluator or Liu et al.'s unpublished
parameterization/release algorithm. Use exact DAG evaluation to avoid
ranking approximation biases in this first mechanism comparison.

Each strategy gets the SAME maximum number of exact DAG candidate scores
and the same move operator: critical-block-inspired insertion (one
operation moved <=5 positions on a machine). Only the choice of which
machine/positions receive attention differs.

dynamic: after *each accepted move* rebuild the complete critical-path
machine-edge set and focus next insertions on newly emerged bottlenecks;
static: keep the original 2006 critical-edge focus;
core: focus on the 21 certified unsat-core arcs (necessary but not sufficient);
random: pick insertion sites uniformly.

Metrics: best score, equal evaluation budget, feasible candidate rates,
actual critical-path replacements, changed machine permutations, neutral
movement, accepted/rejected changes, and full incumbent-verifiable witness.
"""
import argparse,json,random,time
from pathlib import Path
from search import obtain,setup,evaluate
from structural_cut import disjunctive_dag

ROOT=Path(__file__).resolve().parent

def state(orders,pos,duration):
    edges,arcs,topo,head,tail,score=disjunctive_dag(orders,pos,duration,set())
    critical=set()
    near=set()
    for m,k,u,v in arcs:
        length=head[u]+duration[u]+tail[v]
        if length==score:critical.add((m,orders[m][k],orders[m][k+1]))
        if score-length<=8:near.add((m,orders[m][k],orders[m][k+1]))
    return score,critical,near

def candidate_moves(orders,focus,rng,limit):
    # Center insertions on either endpoint of a machine precedence arc.
    pool=set()
    positions=[{j:i for i,j in enumerate(seq)} for seq in orders]
    seeds=list(focus)
    rng.shuffle(seeds)
    for m,a,b in seeds[:80]:
        for center in (positions[m][a],positions[m][b]):
            for delta in (-5,-4,-3,-2,-1,1,2,3,4,5):
                j=center+delta
                if 0<=j<30:
                    pool.add((m,center,j))
    pool=list(pool)
    rng.shuffle(pool)
    if len(pool)<limit:
        seen=set(pool)
        while len(pool)<limit:
            m=rng.randrange(20);i=rng.randrange(30)
            j=max(0,min(29,i+rng.choice((-5,-4,-3,-2,-1,1,2,3,4,5))))
            tup=(m,i,j)
            if i!=j and tup not in seen:
                pool.append(tup);seen.add(tup)
    return pool[:limit]

def insert(orders,move):
    m,i,j=move
    seq=orders[m]
    x=seq.pop(i);seq.insert(j,x)

def scan(orders,pos,dur,focus,rng,n):
    options=candidate_moves(orders,focus,rng,n)
    cand=[]
    invalid=0
    for move in options:
        insert(orders,move)
        score=evaluate(orders,pos,dur)
        insert(orders,(move[0],move[2],move[1]))
        if score is None:
            invalid+=1
        else:
            cand.append((score,move))
    return cand,invalid,len(options)

def execute(a):
    routes,durs,baseline=obtain()
    pos,duration=setup(routes,durs)
    assert evaluate(baseline,pos,duration)==2006
    orders=[x[:] for x in baseline]
    if a.parent!='baseline':
        folder=ROOT/'results'/('gateway-'+a.parent)
        verdict=json.loads((folder/'upstream-verdict.json').read_text())
        assert verdict['valid'] and int(verdict['score'])==2006
        orders=json.loads((folder/'certificate.json').read_text())['machines']
    assert evaluate(orders,pos,duration)==2006
    rng=random.Random(a.seed)
    original=[x[:] for x in orders]
    start_score,static_critical,static_near=state(orders,pos,duration)
    assert start_score==2006
    coredata=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert coredata['status']=='INFEASIBLE' and len(coredata['proven_unsat_core'])==21
    core_focus={(c['machine'],c['from_job'],c['to_job'])
                for c in coredata['proven_unsat_core']}
    current_critical=static_critical.copy()
    previous_critical=current_critical.copy()
    frontier=current_critical.copy()
    global_best=2006
    best=[x[:] for x in orders]
    now=2006
    stage=0;steps=0;valid_count=0;invalid_count=0;accepted=0
    newly_created=0;replacements=0;neutral_accepts=0;uphill_accepts=0
    improvement_events=[]
    max_chain=5
    budget=a.evaluations
    started=time.monotonic()
    log=[]
    path_signature_hits=0
    stall=0
    seen_best={tuple(j for machine in orders for j in machine)}
    while steps<budget:
        # The dynamic policy uses the previous state's newly generated
        # critical edges first, falling back to the whole current bottleneck.
        if a.policy=='dynamic':
            focus=frontier if frontier else current_critical
            if len(focus)<5:focus=focus|current_critical
        elif a.policy=='static':
            focus=static_near
        elif a.policy=='core':
            focus=core_focus
        else:
            focus=set()
        n=min(a.batch,budget-steps)
        candidates,invalid,used=scan(orders,pos,duration,focus,rng,n)
        invalid_count+=invalid;valid_count+=len(candidates);steps+=used
        if not candidates:
            stall+=1
            continue
        # Same objective and bounded perturbation rule for every arm.
        feasible=[v for v in candidates if v[0]<=max(now,global_best)+a.max_uphill]
        if not feasible:
            stall+=1
            continue
        # Avoid immediate rollback, favor diversity at equal makespan.
        feasible.sort(key=lambda x:(x[0],rng.random()))
        chosen=feasible[0] if rng.random()<0.82 else rng.choice(feasible[:min(7,len(feasible))])
        score,move=chosen
        insert(orders,move)
        verified=evaluate(orders,pos,duration)
        assert verified==score
        accepted+=1
        if score==now:neutral_accepts+=1
        if score>now:uphill_accepts+=1
        now=score
        stage+=1
        if a.policy=='dynamic' or (stage%4==0):
            _,critical,_=state(orders,pos,duration)
            emerging=critical-previous_critical
            if emerging:newly_created+=len(emerging);replacements+=1
            if a.policy=='dynamic':
                frontier=emerging if emerging else critical
            previous_critical=critical
            current_critical=critical
        if now<global_best:
            global_best=now
            best=[x[:] for x in orders]
            improvement_events.append(dict(evaluations=steps,score=now,elapsed=round(time.monotonic()-started,3)))
            print('IMPROVE',a.policy,a.parent,a.seed,steps,now,flush=True)
            a.out.mkdir(parents=True,exist_ok=True)
            (a.out/'certificate.json').write_text(json.dumps({'machines':best},separators=(',',':'))+'\n')
            stall=0
            if now<=2005:break
        else:stall+=1
        if accepted%25==0:
            log.append(dict(evaluations=steps,current=now,best=global_best,
                            critical_machine_edges=len(current_critical),
                            critical_replacement_count=replacements))
        # Soft partial restart: reset to verified best but keep the same
        # policy, random stream, and evaluation budget.
        if stall>=a.stall:
            orders=[x[:] for x in best];now=global_best
            _,current_critical,_=state(orders,pos,duration)
            previous_critical=current_critical.copy()
            frontier=current_critical.copy()
            stall=0
    assert evaluate(best,pos,duration)==global_best
    final_score,final_critical,_=state(orders,pos,duration)
    results=dict(instance='ta41',baseline=2006,target=2005,
        policy=a.policy,parent=a.parent,seed=a.seed,
        evaluated_candidates=steps,valid_candidates=valid_count,
        rejected_cyclic_candidates=invalid_count,evaluation_budget=a.evaluations,
        final_current_score=final_score, best_score=global_best,
        accepted_moves=accepted,neutral_accepted=neutral_accepts,
        uphill_accepted=uphill_accepts,
        detected_new_critical_machine_edges=newly_created,
        accepted_steps_with_critical_path_replacement=replacements,
        initial_critical_machine_edges=len(static_critical),
        final_critical_machine_edges=len(final_critical),
        improvement_events=improvement_events,
        status='IMPROVED' if global_best<=2005 else 'NOT_IMPROVED',
        method='N7-inspired bounded operation insertion; each candidate exact DAG evaluated; no 2026 paper batch-slack implementation',
        comparison='All policies use identical candidate score budget, candidate operator, uphill limit, restart trigger, and acceptance heuristic; only focus differs.',
        wall_seconds=round(time.monotonic()-started,3),
        progress=log[-15:])
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'pilot.json').write_text(json.dumps(results,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in results.items() if k not in ('progress','improvement_events')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--policy',choices=['dynamic','static','core','random'],required=True)
    p.add_argument('--parent',choices=['baseline','124'],default='baseline')
    p.add_argument('--seed',type=int,default=11)
    p.add_argument('--batch',type=int,default=24)
    p.add_argument('--evaluations',type=int,default=18000)
    p.add_argument('--max-uphill',type=int,default=65)
    p.add_argument('--stall',type=int,default=220)
    p.add_argument('--out',type=Path,required=True)
    execute(p.parse_args())
