#!/usr/bin/env python3
"""Search for a standalone machine energetic overload certificate for ta41.

Given a small subset of fixed baseline machine orders, compute earliest
and latest operation starts from job arcs and *only those fixed machine arcs*.
For each machine and time interval [a,b], sum the MINIMUM processing that
must occur inside [a,b] over all starts consistent with the time windows.
If the sum exceeds b-a, NoOverlap becomes impossible independently of any
CP-SAT internals. All data are integers and the proof is reproducible.

A negative does not imply feasibility: pairwise disjunctions and edge-finding
can prove subspaces impossible without a one-window energetic overload.
"""
import argparse,json
from pathlib import Path
from search import obtain,setup,evaluate
from structural_cut import disjunctive_dag

def overlap(s,p,a,b):
    return max(0,min(s+p,b)-max(s,a))

def analyze(fixed,target,out):
    routes,ds,orders=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    removed={m*29+k for m in range(20) if m not in fixed for k in range(29)}
    edges,arcs,topo,es,tail,lower_bound=disjunctive_dag(orders,pos,dur,removed)
    latest=[target-tail[i] for i in range(600)]
    immediate=[i for i in range(600) if es[i]>latest[i]]
    result=dict(instance='ta41',target=target,baseline=2006,
      fixed_machine_order_groups=sorted(fixed),
      fixed_arc_partial_order_longest_path=lower_bound,
      immediate_window_violations=immediate,
      best_energetic_excess=-10**9,
      best_interval=None,
      found_proof=False,
      method='exact integer mandatory load in all release/deadline endpoint windows',
      limitations='Only one machine-window energetic overload; not complete for NoOverlap infeasibility')
    if immediate:
        result['found_proof']=True
        result['type']='precedence-only contradiction'
    else:
        for m in range(20):
            ids=[j*20+pos[j][m] for j in range(30)]
            ends=sorted({0,target,*[t for i in ids for t in (es[i],es[i]+dur[i],latest[i],latest[i]+dur[i])]})
            for ai,a in enumerate(ends):
                for b in ends[ai+1:]:
                    total=0
                    contributions=[]
                    for i in ids:
                        amt=min(overlap(es[i],dur[i],a,b),
                                overlap(latest[i],dur[i],a,b))
                        total+=amt
                        if amt:contributions.append([i//20,i%20,amt,es[i],latest[i],dur[i]])
                    excess=total-(b-a)
                    if excess>result['best_energetic_excess']:
                        result.update(best_energetic_excess=excess,
                           best_interval=dict(machine=m,from_time=a,to_time=b,
                           duration=b-a,mandatory_processing=total,
                           contributions=contributions))
        result['found_proof']=result['best_energetic_excess']>0
        result['type']='energetic-overload' if result['found_proof'] else 'no-energetic-overload-found'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    brief={k:v for k,v in result.items() if k!='best_interval'}
    if result['best_interval']:
        brief['witness_machine']=result['best_interval']['machine']
        brief['witness_interval']=[result['best_interval']['from_time'],result['best_interval']['to_time']]
    print('RESULT',json.dumps(brief),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--fixed',type=str,default='0,4,7,8')
    p.add_argument('--target',type=int,default=2005)
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'energetic-fixed4.json')
    a=p.parse_args()
    analyze({int(x) for x in a.fixed.split(',') if x},a.target,a.out)
