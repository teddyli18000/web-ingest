#!/usr/bin/env python3
"""Exact minimum collateral precedence changes for reversing critical arcs.

For a baseline adjacent machine edge u->v, remove just that edge. All
remaining machine+job edges may already imply u->v. Reverse v->u would
then create a cycle. A min u-v edge cut, with infinite capacity on
immutable job edges, computes a certified lower bound on additional
baseline machine adjacencies that must be released.

No solution or globally optimal bound is claimed. This analyzes only
relative to the 2006 incumbent and its adjacency encoding.
"""
import argparse
import json
from collections import Counter, deque
from pathlib import Path
from search import obtain, setup, evaluate
from structural_cut import disjunctive_dag, Dinic

BIG=10000000

def min_cycle_repair(edges,arcs,u,v,skipped):
    graph=Dinic(600)
    for x in range(600):
        for y,index in edges[x]:
            graph.add(x,y,BIG if index is None else 1)
    cost,side=graph.mincut(u,v)
    if cost>=BIG:return dict(invertible=False,minimum_additional_relaxations=None,arc_indices=[])
    hits=[i for i,(_,_,a,b) in enumerate(arcs)
          if i!=skipped and a in side and b not in side]
    assert cost==len(hits),(cost,len(hits))
    return dict(invertible=True,minimum_additional_relaxations=cost,arc_indices=hits)

def bound_with_reverse(orders,pos,durations,deleted,u,v):
    edges,_,_,_,_,_=disjunctive_dag(orders,pos,durations,deleted)
    edges[v].append((u,None))
    indeg=[0]*600
    for x in range(600):
        for y,_ in edges[x]:indeg[y]+=1
    q=deque(i for i in range(600) if indeg[i]==0)
    head=[0]*600;done=0
    while q:
        x=q.popleft();done+=1
        for y,_ in edges[x]:
            head[y]=max(head[y],head[x]+durations[x])
            indeg[y]-=1
            if indeg[y]==0:q.append(y)
    if done<600:return None
    return max(head[x]+durations[x] for x in range(600))

def main(out):
    routes,durations_by_job,orders=obtain()
    pos,duration=setup(routes,durations_by_job)
    assert evaluate(orders,pos,duration)==2006
    edges,arcs,topo,head,tail,C=disjunctive_dag(orders,pos,duration,set())
    critical=[i for i,(_,_,u,v) in enumerate(arcs)
              if head[u]+duration[u]+tail[v]==C]
    assert len(critical)==53
    rows=[]
    for i in critical:
        m,k,u,v=arcs[i]
        remaining,_,_,_,_,_=disjunctive_dag(orders,pos,duration,{i})
        repair=min_cycle_repair(remaining,arcs,u,v,i)
        deleted={i,*repair["arc_indices"]}
        lb=bound_with_reverse(orders,pos,duration,deleted,u,v) if repair["invertible"] else None
        rows.append(dict(index=i,machine=m,machine_position=k,
                         from_job=u//20,to_job=v//20,
                         additional_cuts=repair["minimum_additional_relaxations"],
                         coupled_relaxed_arc_indices=sorted(deleted),
                         residual_lower_bound_with_hard_reverse=lb,
                         hard_reverse_acyclic=(lb is not None)))
    rows.sort(key=lambda x:(x["additional_cuts"] if x["additional_cuts"] is not None else BIG,
                            x["residual_lower_bound_with_hard_reverse"] or BIG))
    hist=dict(sorted(Counter(x["additional_cuts"] for x in rows).items()))
    main_edge=next(x for x in rows if x["index"]==471)
    report={
       "baseline":C,
       "critical_machine_arcs":len(critical),
       "semantics":"Exact minimal additional original machine arcs to break all alternative u->v paths, with immutable job arcs; NOT a feasible-schedule result.",
       "collateral_cut_histogram":{str(k):v for k,v in hist.items()},
       "distinguished_minimum_longest_path_cut_edge":main_edge,
       "smallest_coupled_repairs":rows[:12],
       "all_critical_edges":rows,
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k not in ("all_critical_edges","smallest_coupled_repairs")},indent=2))
    print("RESULT all 53 critical arc reverse dependencies analyzed",flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,default=Path(__file__).parent/"results"/"coupled-precedence.json")
    a=p.parse_args();main(a.out)
