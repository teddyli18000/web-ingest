#!/usr/bin/env python3
"""Explain incumbent ta41 by exact critical-path enumeration and minimum cuts.

This script does NOT solve the job-shop problem. It establishes combinatorial
necessary conditions for any strict improvement over a particular incumbent.

Each source-to-sink critical path is a certificate of the incumbent's 2006
makespan. To achieve 2005, at least one baseline machine precedence arc
on every 2006-length path must be violated. Minimum s-t cut computes the
exact minimum number of such *baseline adjacent machine arcs* needed.
Job arcs have effectively infinite capacity, because they cannot be changed.

An iterated cut provides a constrained-LNS relaxation blueprint, not proof
that a feasible lower-makespan schedule exists.
"""
import argparse
import json
import random
from collections import deque
from pathlib import Path
from search import obtain, setup, evaluate


def disjunctive_dag(orders, pos, duration, removed):
    edges = [[] for _ in range(600)]
    indeg = [0]*600
    machine_arcs = []
    for j in range(30):
        for k in range(19):
            u, v = j*20+k, j*20+k+1
            edges[u].append((v, None))
            indeg[v] += 1
    for m, jobs in enumerate(orders):
        for k, (j, h) in enumerate(zip(jobs, jobs[1:])):
            u, v = j*20+pos[j][m], h*20+pos[h][m]
            index = len(machine_arcs)
            machine_arcs.append((m,k,u,v))
            if index not in removed:
                edges[u].append((v,index))
                indeg[v] += 1
    q=deque(i for i in range(600) if indeg[i]==0)
    topo=[]; head=[0]*600
    while q:
        u=q.popleft();topo.append(u)
        for v,_ in edges[u]:
            head[v]=max(head[v],head[u]+duration[u])
            indeg[v]-=1
            if indeg[v]==0:q.append(v)
    assert len(topo)==600
    tail=duration[:]
    for u in reversed(topo):
        if edges[u]:
            tail[u]=duration[u]+max(tail[v] for v,_ in edges[u])
    makespan=max(head[i]+duration[i] for i in range(600))
    return edges,machine_arcs,topo,head,tail,makespan


class Dinic:
    def __init__(self,n):
        self.g=[[] for _ in range(n)]
    def add(self,u,v,c):
        a=[v,c,None]; b=[u,0,a];a[2]=b
        self.g[u].append(a);self.g[v].append(b)
    def mincut(self,s,t):
        result=0
        while True:
            level=[-1]*len(self.g);level[s]=0
            q=deque([s])
            while q:
                u=q.popleft()
                for v,c,_ in self.g[u]:
                    if c>0 and level[v]<0: level[v]=level[u]+1;q.append(v)
            if level[t]<0:break
            it=[0]*len(self.g)
            def dfs(u,flow):
                if u==t:return flow
                while it[u]<len(self.g[u]):
                    e=self.g[u][it[u]]
                    v,c,_=e
                    if c>0 and level[v]==level[u]+1:
                        val=dfs(v,min(flow,c))
                        if val:
                            e[1]-=val;e[2][1]+=val
                            return val
                    it[u]+=1
                return 0
            while True:
                p=dfs(s,10**9)
                if not p:break
                result+=p
        visited={s};q=deque([s])
        while q:
            u=q.popleft()
            for v,c,_ in self.g[u]:
                if c>0 and v not in visited:
                    visited.add(v);q.append(v)
        return result,visited


def cut_analysis(orders,pos,duration,removed,rng,weighted=False):
    edges,arcs,topo,head,tail,C=disjunctive_dag(orders,pos,duration,removed)
    source,sink=600,601
    graph=Dinic(602)
    critical=[head[i]+tail[i]==C for i in range(600)]
    critical_m=set()
    path_count=[0]*600
    for u in topo:
        if critical[u] and head[u]==0:
            graph.add(source,u,10000000)
            path_count[u]+=1
        for v,i in edges[u]:
            if not critical[u] or not critical[v]:continue
            if head[u]+duration[u]+tail[v]!=C:continue
            if i is None:
                graph.add(u,v,10000000)
            else:
                critical_m.add(i)
                graph.add(u,v,rng.randrange(1,5) if weighted else 1)
            path_count[v]+=path_count[u]
        if critical[u] and head[u]+duration[u]==C:
            graph.add(u,sink,10000000)
    total_paths=sum(path_count[i] for i in range(600)
                    if critical[i] and head[i]+duration[i]==C)
    cost,side=graph.mincut(source,sink)
    if cost>=10000000:
        raise ValueError("immutable job arcs alone contain a critical path")
    cut=[i for i in critical_m if arcs[i][2] in side and arcs[i][3] not in side]
    assert cut
    if not weighted:assert len(cut)==cost,(len(cut),cost)
    return dict(makespan=C,critical_nodes=sum(critical),
                critical_machine_arcs=len(critical_m),
                critical_path_count=str(total_paths),
                mincut_machine_arcs=len(cut),cut_arcs=sorted(cut),
                cut_machines=sorted(set(arcs[i][0] for i in cut)),
                arc_tuples=[list(arcs[i]) for i in cut])


def main(seconds_unused,seed,out):
    routes,durs,orders=obtain()
    pos,duration=setup(routes,durs)
    assert evaluate(orders,pos,duration)==2006
    rng=random.Random(seed)
    report={"instance":"ta41","baseline_makespan":2006,
            "mathematics":"minimum machine-arc edge cut in incumbent critical DAG",
            "interpretation":"Necessary broken-adjacency bound for baseline only; not global optimum",
            "seed":seed,"targets":{}}
    for target in (2005,2000,1990,1975,1950,1915):
        removed=set()
        steps=[]
        for it in range(580):
            d=cut_analysis(orders,pos,duration,removed,rng,weighted=(it%3==1))
            if d["makespan"]<=target:break
            to_add=set(d["cut_arcs"])
            assert not removed.intersection(to_add)
            removed.update(to_add)
            steps.append(d)
        else:raise RuntimeError("unable to break incumbent to target "+str(target))
        _,_,_,_,_,lower_bound=disjunctive_dag(orders,pos,duration,removed)
        assert lower_bound<=target
        report["targets"][str(target)]={
            "removed_machine_arcs":len(removed),
            "residual_fixed_arc_lower_bound":lower_bound,
            "steps":len(steps),
            "first_cut":steps[0] if steps else None,
            "removed_arc_indices":sorted(removed),
            "relaxation_only_no_feasible_schedule_claimed":True}
        print(json.dumps({"target":target,
                          "released":len(removed),"residual_LB":lower_bound,
                          "iterations":len(steps)},separators=(",",":")),flush=True)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n")
    print("RESULT diagnostic-only verified baseline=2006",flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,default=41)
    p.add_argument("--out",type=Path,default=Path(__file__).resolve().parent/"results"/"critical-cut.json")
    a=p.parse_args()
    main(None,a.seed,a.out)
