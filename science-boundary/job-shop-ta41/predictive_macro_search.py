#!/usr/bin/env python3
"""Ta41 predictive replacement-path compound repair against matched baselines.

Constructive, no fixed-survivor CP model. Every proposed move changes an
entire *feasible* 600-operation disjunctive DAG. A compound move may take
three temporarily uphill steps; only the completed DAG is accepted.

Policies: replacement (NEW critical arcs after speculative first/second
step), current (all current critical arcs), static (initial critical arcs),
core (certified 21-arc obstruction), random, tabu (single-step dynamic
critical-path tabu baseline). All have the same full-DAG score-evaluation
budget; wall-clock is separately reported because exact critical-arc
recalculation is extra overhead. This is not a faithful implementation
of Ba et al.'s 2026 batched N7 algorithm.

No <=2005 score claimed without independent DAG evaluation and official
Few Shots verify.py. Reversible moves and neutral path exploration are
explicit; UNKNOWN is irrelevant because this is constructive search.
"""
import argparse, json, random, time
from pathlib import Path
from search import obtain, setup, evaluate
from dynamic_critical_replacement import state

ROOT = Path(__file__).resolve().parent
DELTAS=(-4,-3,-2,-1,1,2,3,4)

def clone(orders):
    return [x[:] for x in orders]

def apply(orders, move):
    m,i,j=move
    x=orders[m].pop(i)
    orders[m].insert(j,x)

def sample(orders, focus, rng, n):
    moves=set()
    index=[{j:i for i,j in enumerate(seq)} for seq in orders]
    focus=sorted(focus)
    rng.shuffle(focus)
    for m,a,b in focus[:60]:
        for job in (a,b):
            p=index[m][job]
            for d in DELTAS:
                q=p+d
                if 0<=q<30:moves.add((m,p,q))
    pool=list(moves)
    rng.shuffle(pool)
    if not pool:
        for m in range(20):
            for p in range(30):
                for d in DELTAS:
                    q=p+d
                    if 0<=q<30:pool.append((m,p,q))
        rng.shuffle(pool)
    # No fallback to random when a focused pool exists: the focus-policy
    # itself is the causal intervention being compared here.
    return pool[:n]

def load_parent(name,baseline,pos,dur):
    if name=='baseline':return clone(baseline)
    root=ROOT/'results'/('gateway-'+name)
    v=json.loads((root/'upstream-verdict.json').read_text())
    assert v['valid'] and int(v['score'])==2006
    parent=json.loads((root/'certificate.json').read_text())['machines']
    assert evaluate(parent,pos,dur)==2006
    return parent

def key(orders):
    return tuple(j for seq in orders for j in seq)

def critical(orders,pos,dur):
    score,edges,near=state(orders,pos,dur)
    return score,edges,near

def policy_focus(policy,cr,near,initial,core,emerging):
    if policy=='replacement':
        return emerging if emerging else cr
    if policy=='current':return cr
    if policy=='static':return initial
    if policy=='core':return core
    return set()

def run(a):
    routes,drows,base=obtain()
    pos,dur=setup(routes,drows)
    assert evaluate(base,pos,dur)==2006
    parent=load_parent(a.parent,base,pos,dur)
    rng=random.Random(a.seed)
    _,initial_critical,initial_near=critical(parent,pos,dur)
    core_data=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert core_data['status']=='INFEASIBLE' and len(core_data['proven_unsat_core'])==21
    core={(x['machine'],x['from_job'],x['to_job']) for x in core_data['proven_unsat_core']}
    orders=clone(parent);current=2006
    best=2006;best_orders=clone(parent)
    scores=0;scored_valid=0;scored_cyclic=0
    accepted=0;neutral=0;uphill=0;restarted=0
    detected_new_edges=0;speculative_replacements=0
    staged_history=[];attempted_macros=0
    state_recomputations=0
    seen={key(orders)};stalled=0;tabu={}
    start=time.monotonic();last_save=0
    a.out.mkdir(parents=True,exist_ok=True)
    def score_move(b,m):
        nonlocal scores,scored_valid,scored_cyclic
        q=clone(b);apply(q,m)
        v=evaluate(q,pos,dur)
        scores+=1
        if v is None:scored_cyclic+=1
        else:scored_valid+=1
        return v,q
    def snapshot():
        out=dict(instance='ta41',parent=a.parent,policy=a.policy,seed=a.seed,
             score_budget=a.budget,scored_candidates=scores,
             complete=(scores>=a.budget),valid_candidates=scored_valid,
             cyclic_candidates=scored_cyclic,best_score=best,
             current_score=current,accepted_macros=accepted,
             neutral_accepts=neutral,uphill_accepts=uphill,
             restarts=restarted,distinct_states=len(seen),
             speculative_new_critical_edge_count=detected_new_edges,
             speculative_states_with_path_replacement=speculative_replacements,
             critical_state_recomputations=state_recomputations,
             actual_compound_iterations=attempted_macros,
             best_events=staged_history,
             elapsed_seconds=round(time.monotonic()-start,3),
             method='speculative up-to-three-step critical-path replacement compound moves'
               if a.policy!='tabu' else 'incumbent critical-path N7-inspired tabu insertions',
             limitations='Same exact DAG scoring budget; critical-edge recomputations are extra and wall time differs; one-step generator is insertion radius4 not complete N7.')
        (a.out/'constructive.json').write_text(json.dumps(out,indent=2)+'\n')
    while scores<a.budget and best>2005:
        attempted_macros+=1
        root_score,root_cr,root_near=critical(orders,pos,dur)
        state_recomputations+=1
        assert root_score==current
        frontier=policy_focus(a.policy,root_cr,root_near,initial_critical,core,root_cr)
        n=min(a.first,a.budget-scores)
        stage1=[]
        for move in sample(orders,frontier,rng,n):
            v,q=score_move(orders,move)
            if v is not None and v<=best+a.uphill:
                # For tabu, make immediate reversal difficult, aspirate on new best.
                if a.policy=='tabu' and key(q) in tabu and tabu[key(q)]>attempted_macros and v>=best:
                    continue
                stage1.append((v,q,[move],[v],0))
        stage1.sort(key=lambda x:(x[0],rng.random()))
        options=stage1[:max(1,a.width)]
        if a.policy!='tabu' and options:
            stage2=[]
            for oldscore,q,path,vals,oldborn in options:
                if scores>=a.budget:break
                _,qcr,_=critical(q,pos,dur);state_recomputations+=1
                born=qcr-root_cr
                detected_new_edges+=len(born)
                speculative_replacements+=bool(born)
                focus=policy_focus(a.policy,qcr,set(),initial_critical,core,born)
                for move in sample(q,focus,rng,min(a.second,a.budget-scores)):
                    v,qq=score_move(q,move)
                    if v is not None and v<=best+a.uphill:
                        if qq==orders:continue
                        stage2.append((v,qq,path+[move],vals+[v],len(born),qcr))
            stage2.sort(key=lambda x:(x[0],rng.random()))
            options.extend((v,q,p,vals,n) for v,q,p,vals,n,_ in stage2[:a.width])
            # Third move is a corrective action against new bottlenecks
            # of the SECOND speculative schedule (replacement of replacement).
            for oldscore,q,path,vals,oldborn,priorcr in stage2[:a.width]:
                if scores>=a.budget:break
                _,qcr,_=critical(q,pos,dur);state_recomputations+=1
                emerging=qcr-priorcr
                detected_new_edges+=len(emerging)
                speculative_replacements+=bool(emerging)
                focus=policy_focus(a.policy,qcr,set(),initial_critical,core,emerging)
                for move in sample(q,focus,rng,min(a.third,a.budget-scores)):
                    v,qq=score_move(q,move)
                    if v is not None and v<=best+a.uphill:
                        if qq==orders:continue
                        options.append((v,qq,path+[move],vals+[v],len(emerging)))
        if not options:
            stalled+=1
        else:
            # Final outcome first; neutral diversity second; high penalty
            # for revisiting. Never require intermediates to improve.
            unique={}
            for cand in options:
                identity=key(cand[1])
                if identity not in unique or cand[0]<unique[identity][0]:
                    unique[identity]=cand
            ranked=sorted(unique.values(),key=lambda x:(
                x[0] + (4 if key(x[1]) in seen else 0),rng.random()))
            chosen=ranked[0] if rng.random()<0.82 else rng.choice(ranked[:min(5,len(ranked))])
            v,q,path,vals,newcount=chosen
            old=current
            orders=q;current=v;accepted+=1
            if v==old:neutral+=1
            if v>old:uphill+=1
            seen.add(key(q))
            if a.policy=='tabu':tabu[key(orders)]=attempted_macros+rng.randint(6,15)
            if v<best:
                best=v;best_orders=clone(q)
                event=dict(evaluations=scores,score=best,compound_depth=len(path),
                           intermediate_scores=vals,new_critical_edges=newcount,
                           wall_seconds=round(time.monotonic()-start,3))
                staged_history.append(event)
                if best<=2005:
                    (a.out/'certificate.json').write_text(json.dumps({'machines':best_orders},separators=(',',':'))+'\n')
                print('IMPROVEMENT',a.parent,a.policy,a.seed,event,flush=True)
                stalled=0
            else:stalled+=1
        if stalled>=a.restart:
            orders=clone(best_orders);current=best;stalled=0;restarted+=1
            tabu.clear()
            # Small feasible random kick, applied to all policies equally.
            for _ in range(3):
                moves=sample(orders,set(),rng,4)
                if scores>=a.budget:break
                for mv in moves[:min(4,a.budget-scores)]:
                    v,q=score_move(orders,mv)
                    if v is not None and v<=best+a.uphill:
                        orders=q;current=v;seen.add(key(q));break
        if scores-last_save>=1000:
            snapshot()
            print('HEARTBEAT',a.parent,a.policy,a.seed,'eval',scores,'best',best,
                  'wall',round(time.monotonic()-start,1),flush=True)
            last_save=scores
    assert evaluate(best_orders,pos,dur)==best
    snapshot()
    print('RESULT',json.dumps({'parent':a.parent,'policy':a.policy,'seed':a.seed,
          'evals':scores,'best':best,'valid':scored_valid,'cycles':scored_cyclic,
          'wall':round(time.monotonic()-start,2)}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=['baseline','124'],required=True)
    p.add_argument('--policy',choices=['replacement','current','static','core','random','tabu'],required=True)
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--budget',type=int,default=16000)
    p.add_argument('--first',type=int,default=16)
    p.add_argument('--second',type=int,default=10)
    p.add_argument('--third',type=int,default=10)
    p.add_argument('--width',type=int,default=3)
    p.add_argument('--restart',type=int,default=60)
    p.add_argument('--uphill',type=int,default=70)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
