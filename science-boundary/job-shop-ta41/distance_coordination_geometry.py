#!/usr/bin/env python3
"""Probe whether ta41's 2006 plateau is geometrically distant or coordination-limited.

Part 1: measure EXACT machine-pair Kendall inversion distance between
independently verified score-2006 schedules, and the number of previously
certified 21 consensus-UNSAT precedence arcs they already reverse.

Part 2: find a *monotone adjacent-swap path* from baseline to two verified
neutral schedules. At every step, one adjacent transposition reduces
Kendall distance to target by exactly one, and the full disjunctive graph
is checked independently. Minimax beam search gives a constructive UPPER
bound on the path's maximum makespan. Complete enumeration of possible
first moves gives a separate LOWER bound on any monotone path's maximum.
No claim is made for paths which temporarily move away from the target.

This does NOT establish the distance to unknown 2005 solutions. A 2006
sample reveals only the geometry of the known neutral class.
"""
import argparse,json,time
from pathlib import Path
from search import obtain,setup,evaluate

ROOT=Path(__file__).resolve().parent
PARENTS={
    'critical8':('neutral-critical8','neutral-certificate.json','neutral-verdict.json'),
    'mixed12':('neutral-mixed12','neutral-certificate.json','neutral-verdict.json'),
    'mixed16':('neutral-mixed16','neutral-certificate.json','neutral-verdict.json'),
    'mixed20':('neutral-mixed20','neutral-certificate.json','neutral-verdict.json'),
    'reversed5':('warm-backbone-5','neutral-certificate.json','best-verdict.json'),
    'reversed6':('warm-backbone-6','neutral-certificate.json','best-verdict.json'),
    'reversed7':('continuation-7','neutral-certificate.json','best-verdict.json'),
}

def load_parent(name,pos,dur):
    folder,cp,vp=PARENTS[name]
    prefix=ROOT/'results'/folder
    orders=json.loads((prefix/cp).read_text())['machines']
    verdict=json.loads((prefix/vp).read_text())
    assert verdict['valid'] and int(verdict['score'])==2006,(name,verdict)
    assert evaluate(orders,pos,dur)==2006,name
    return orders

def metrics(orders,base,core):
    pairs=0;adj=0;machines=0
    per_machine=[]
    for m,(a,b) in enumerate(zip(orders,base)):
        orig_index={j:i for i,j in enumerate(b)}
        perm=[orig_index[j] for j in a]
        inv=sum(perm[i]>perm[j] for i in range(30) for j in range(i+1,30))
        pos={job:i for i,job in enumerate(a)}
        adjm=sum(pos[b[i]]>pos[b[i+1]] for i in range(29))
        per_machine.append({'machine':m,'kendall_inversions':inv,'baseline_adjacent_reversed':adjm})
        pairs+=inv;adj+=adjm;machines+=(inv>0)
    core_rev=[c['index'] for c in core
              if orders[c['machine']].index(c['from_job']) >
                 orders[c['machine']].index(c['to_job'])]
    return {'changed_machine_orders':machines,'kendall_pair_inversions':pairs,
            'reversed_baseline_adjacent_pair_relations':adj,
            'reversed_certified_core_indices':core_rev,
            'core_reversal_count':len(core_rev),'per_machine':per_machine}

def directed_moves(orders,target):
    # Any adjacent inversion relative to target can be swapped to reduce
    # total Kendall distance by exactly one; all other machine orders unchanged.
    for m in range(20):
        targ={j:i for i,j in enumerate(target[m])}
        seq=orders[m]
        for k in range(29):
            if targ[seq[k]]>targ[seq[k+1]]:
                yield m,k

def key(orders):
    return tuple(j for m in orders for j in m)

def path_probe(initial,target,pos,dur,width):
    start=time.monotonic()
    total=metrics(initial,target,[])['kendall_pair_inversions']
    assert total>0
    cur=(initial,2006,2006,[])
    frontier=[cur]
    first_min=None;first_count=0;stage_sizes=[]
    best_scores={}
    for step in range(total):
        candidates={}
        for orders,barrier,score,path in frontier:
            for m,k in directed_moves(orders,target):
                newer=[x[:] for x in orders]
                newer[m][k],newer[m][k+1]=newer[m][k+1],newer[m][k]
                val=evaluate(newer,pos,dur)
                if step==0 and val is not None:
                    first_count+=1
                    first_min=val if first_min is None else min(first_min,val)
                if val is None:continue
                top=max(barrier,val)
                identity=key(newer)
                proposed=(newer,top,val,path+[(m,k,val)])
                old=candidates.get(identity)
                if old is None or (top,val)<(old[1],old[2]):
                    candidates[identity]=proposed
        assert candidates,('no valid monotone path found',step)
        frontier=sorted(candidates.values(),key=lambda x:(x[1],x[2]))[:width]
        stage_sizes.append(len(candidates))
        if step%10==0 or step==total-1:
            print('PATH',step+1,'/',total,'best peak',frontier[0][1],
                  'states',len(candidates),'seconds',round(time.monotonic()-start,2),flush=True)
    winner=frontier[0]
    assert winner[0]==target and winner[2]==2006
    reconstructed=[r[:] for r in initial]
    for m,k,_ in winner[3]:
        reconstructed[m][k:k+2]=reconstructed[m][k:k+2][::-1]
        assert evaluate(reconstructed,pos,dur) is not None
    assert reconstructed==target
    assert len(winner[3])==total
    assert first_min is not None
    assert winner[1]>=first_min
    return {
      'monotone_adjacent_swap_steps':total,
      'min_first_step_makespan_all_acyclic_target_directed_swaps':first_min,
      'first_step_feasible_count':first_count,
      'verified_path_maximum_makespan':winner[1],
      'path_peak_upper_bound_on_monotone_minimax_barrier':winner[1],
      'monotone_path_peak_lower_bound_from_first_move':first_min,
      'simultaneous_2006_endpoints_verified':True,
      'searched_beam_width':width,
      'last_step_frontier_states_examined':stage_sizes[-1],
      'elapsed_seconds':round(time.monotonic()-start,3),
      'verified_path_swaps':[{'machine':m,'position':k,'makespan_after':v} for m,k,v in winner[3]],
      'scope':'Feasible monotone single-adjacent-swap paths between TWO 2006 schedules only. First-step lower bound does not apply to nonmonotone routes.'
    }

def main(a):
    routes,rows,base=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    consensus=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    core=consensus['proven_unsat_core']
    assert consensus['status']=='INFEASIBLE' and len(core)==21
    families={}
    for name in PARENTS:
        orders=load_parent(name,pos,dur)
        families[name]=metrics(orders,base,core)
        print('METRIC',name,*(families[name][k] for k in (
            'changed_machine_orders','kendall_pair_inversions','core_reversal_count')),flush=True)
    result={'instance':'ta41','target':2005,'neutral_makespan':2006,
        'maximum_possible_machine_pair_inversions':20*435,
        'verified_2006_family_differences_from_baseline':families,
        'monotone_adjacent_swap_path_analysis':{},
        'interpretation':'A large number of changed machine permutations can coexist with a small pairwise Kendall distance. A neutral 2006 schedule alone cannot identify the unknown nearest 2005 schedule.',
        'source_core':'results/consensus-five-parents/consensus-analysis.json',
        'all_scores_checked_by_independent_dag_evaluator':True}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    for name in a.paths.split(','):
        if not name:continue
        target=load_parent(name,pos,dur)
        result['monotone_adjacent_swap_path_analysis'][name]=path_probe(base,target,pos,dur,a.beam)
        a.out.write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({
        'neutral_examples':{name:{k:v for k,v in x.items() if k!='per_machine'}
                            for name,x in families.items()},
        'paths':{name:{k:v for k,v in x.items() if k!='verified_path_swaps'}
                 for name,x in result['monotone_adjacent_swap_path_analysis'].items()}},flush=True))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=ROOT/'results'/'geometry-vs-coordination.json')
    p.add_argument('--beam',type=int,default=100)
    p.add_argument('--paths',type=str,default='critical8,reversed6')
    main(p.parse_args())
