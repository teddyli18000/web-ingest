#!/usr/bin/env python3
"""Independent cheap precedence relaxation of globally ejected job groups.

For each of 30 singles, 435 pairs, and 4060 triples, ignore machine
conflicts involving any ejected job, but retain hard job routes and
original relative machine sequence of all *non-ejected* jobs. The
resulting partial-order longest path is a valid lower bound for
the full job ejection NoOverlap subspace.

This guides which larger globally-coupled job cohorts to attempt.
A lower bound <=2005 is necessary, absolutely not sufficient.
"""
import argparse,itertools,json
from collections import deque
from pathlib import Path
from search import obtain,setup,evaluate

def lower_bound(orders,pos,dur,ejected):
    succ=[[] for _ in range(600)]
    indeg=[0]*600
    for j in range(30):
        for k in range(19):
            u=j*20+k;v=u+1
            succ[u].append(v);indeg[v]+=1
    for m in range(20):
        kept=[j for j in orders[m] if j not in ejected]
        for j,h in zip(kept,kept[1:]):
            u=j*20+pos[j][m];v=h*20+pos[h][m]
            succ[u].append(v);indeg[v]+=1
    q=deque(u for u in range(600) if not indeg[u])
    start=[0]*600;count=0;C=0
    while q:
        u=q.popleft();count+=1;end=start[u]+dur[u]
        if end>C:C=end
        for v in succ[u]:
            if start[v]<end:start[v]=end
            indeg[v]-=1
            if not indeg[v]:q.append(v)
    if count!=600:raise AssertionError('ejection partial DAG somehow cyclic')
    return C

def main(a):
    routes,ds,orders=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    report={'instance':'ta41','baseline':2006,'deadline':2005,
            'method':'job cohort machine-arc relaxed longest path',
            'levels':[],
            'semantics':'LB is a necessary condition only, because ejected jobs must still compete for machines in actual schedules.'}
    for k in (1,2,3):
        scores=[]
        for cohort in itertools.combinations(range(30),k):
            val=lower_bound(orders,pos,dur,set(cohort))
            scores.append((val,cohort))
        passing=[(v,cohort) for v,cohort in scores if v<=2005]
        scores.sort()
        report['levels'].append({
            'job_ejection_cardinality':k,
            'examined':len(scores),
            'min_relaxed_longest_path':scores[0][0],
            'cohorts_with_lower_bound_le_2005':len(passing),
            'max_relaxed_longest_path':scores[-1][0],
            'best_ten_cohorts':[{'jobs':list(c),'lower_bound':v} for v,c in scores[:10]],
        })
        print('LEVEL',k,'checked',len(scores),'LB<=2005',len(passing),
              'best',scores[0][0],flush=True)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'job-cohort-precedence-relaxation.json')
    main(p.parse_args())
