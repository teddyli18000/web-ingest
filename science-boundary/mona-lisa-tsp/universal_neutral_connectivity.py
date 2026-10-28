#!/usr/bin/env python3
"""Universal connectivity SAT test for exponential family of zero-cost TSP edits.

The base tour is cut at each potentially removed edge, and its immutable
paths are contracted. Every switch preserves degree 2, but MAY disconnect
the cycle. A disconnected outcome exists iff the contracted graph admits
a nonconstant two-coloring that is constant across all selected edges.

Two independent solvers (CP-SAT and Z3) evaluate that existential question.
If SAT, produce a concrete full-tour disconnection witness and greedily prune
switches until the remaining switch family is certified universally connected.
"""
import argparse
import importlib.util
import json
import math
import time
from collections import Counter
from pathlib import Path
from ortools.sat.python import cp_model
import z3

def edge(a,b):return (a,b) if a<b else (b,a)

def dsu_components(n,base,optional):
    parent=list(range(n+1))
    size=[1]*(n+1)
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]
            a=parent[a]
        return a
    def merge(a,b):
        a,b=find(a),find(b)
        if a!=b:
            if size[a]<size[b]:a,b=b,a
            parent[b]=a;size[a]+=size[b]
    for a,b in base:
        if (a,b) not in optional:merge(a,b)
    seen={}
    out={}
    for a,b in optional:
        for v in (a,b):
            r=find(v)
            if r not in seen:seen[r]=len(seen)
            out[v]=seen[r]
    assert len(seen)==len(optional)
    return out,len(seen)

def real_cycle_count(n,base,oldsets,newsets,switchset):
    adj=[[] for _ in range(n+1)]
    edges=set(base)
    for i in switchset:edges.difference_update(oldsets[i])
    for i in switchset:edges.update(newsets[i])
    assert len(edges)==n
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[v])==2 for v in range(1,n+1))
    seen=bytearray(n+1); sizes=[]
    for v in range(1,n+1):
        if seen[v]:continue
        last=0;cur=v;size=0
        while not seen[cur]:
            seen[cur]=1;size+=1
            a,b=adj[cur]
            nxt=a if a!=last else b
            last,cur=cur,nxt
        assert cur==v
        sizes.append(size)
    return sizes

def cp_check(k,components,oldsets,newsets,allowed,limit=120):
    model=cp_model.CpModel()
    colors=[model.NewBoolVar(f'color_{j}') for j in range(k)]
    switches=[model.NewBoolVar(f'move_{i}') for i in range(len(oldsets))]
    model.Add(colors[0]==0)
    model.AddBoolOr(colors[1:])
    for i in range(len(switches)):
        if i not in allowed:model.Add(switches[i]==0)
        for a,b in oldsets[i]:
            model.Add(colors[components[a]]==colors[components[b]]).OnlyEnforceIf(switches[i].Not())
        for a,b in newsets[i]:
            model.Add(colors[components[a]]==colors[components[b]]).OnlyEnforceIf(switches[i])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=limit
    solver.parameters.num_search_workers=4
    status=solver.Solve(model)
    name=solver.StatusName(status)
    if status==cp_model.FEASIBLE or status==cp_model.OPTIMAL:
        selected={i for i in range(len(switches)) if solver.Value(switches[i])}
        return name,selected
    return name,None

def smt_check(k,components,oldsets,newsets,allowed,limit=120):
    s=z3.Solver()
    s.set(timeout=1000*limit)
    colors=[z3.Bool(f'c_{j}') for j in range(k)]
    switches=[z3.Bool(f's_{i}') for i in range(len(oldsets))]
    s.add(z3.Not(colors[0]))
    s.add(z3.Or(*colors[1:]))
    for i in range(len(switches)):
        if i not in allowed:s.add(z3.Not(switches[i]))
        for a,b in oldsets[i]:
            s.add(z3.Implies(z3.Not(switches[i]),
                             colors[components[a]]==colors[components[b]]))
        for a,b in newsets[i]:
            s.add(z3.Implies(switches[i],
                             colors[components[a]]==colors[components[b]]))
    ans=s.check()
    if ans==z3.sat:
        model=s.model()
        selected={i for i in range(len(switches)) if z3.is_true(model.eval(switches[i]))}
        return 'SAT',selected
    if ans==z3.unsat:return 'UNSAT',None
    return 'UNKNOWN',None

def main():
    p=argparse.ArgumentParser()
    for name in ('baseline','catalogue','report'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--seconds',type=int,default=120)
    args=p.parse_args()
    started=time.monotonic()
    baseline=json.loads(Path(args.baseline).read_text())['tour']
    n=len(baseline)
    assert n==100000
    source=json.loads(Path(args.catalogue).read_text())
    choices=source['selected_indices']
    moves=[source['moves'][i] for i in choices]
    oldsets=[{edge(*z) for z in move['removed']} for move in moves]
    newsets=[{edge(*z) for z in move['added']} for move in moves]
    base={edge(baseline[i],baseline[(i+1)%n]) for i in range(n)}
    optional=set().union(*oldsets)
    assert len(optional)==sum(map(len,oldsets))
    for i in range(len(moves)):
        assert oldsets[i]<=base and not(newsets[i]&base)
    comps,k=dsu_components(n,base,optional)
    print(json.dumps({'stage':'model','moves':len(moves),'contracted_segments':k}),flush=True)
    allowed=set(range(len(moves)))
    iterations=[]
    while True:
        status,witness=cp_check(k,comps,oldsets,newsets,allowed,args.seconds)
        iteration={'remaining':len(allowed),'status':status,
                   'removed_moves_so_far':len(moves)-len(allowed)}
        if status=='INFEASIBLE':
            smt,smt_witness=smt_check(k,comps,oldsets,newsets,allowed,args.seconds)
            iteration['z3_crosscheck']=smt
            assert smt=='UNSAT',(status,smt,smt_witness)
            iterations.append(iteration)
            break
        if status not in ('FEASIBLE','OPTIMAL'):
            iteration['warning']='Solver did not prove either side'
            iterations.append(iteration)
            break
        sizes=real_cycle_count(n,base,oldsets,newsets,witness)
        assert len(sizes)>1
        iteration['witness_moves']=sorted(witness)
        iteration['witness_cycles']=sizes
        # Shrink witness to a minimal disconnected set by exact graph checking.
        minimal=set(witness)
        for i in sorted(minimal):
            attempt=minimal-{i}
            if len(real_cycle_count(n,base,oldsets,newsets,attempt))>1:
                minimal=attempt
        assert len(minimal)>=2
        iteration['minimal_disconnected_moves']=sorted(minimal)
        # Keep the stronger negative continuous-euclidean switches when possible.
        drop=max(minimal,key=lambda i:(moves[i]['continuous_delta'],i))
        allowed.remove(drop)
        iteration['removed_move_index']=drop
        iterations.append(iteration)
        print(json.dumps({'stage':'counterexample',**iteration}),flush=True)
    guaranteed=(iterations[-1]['status']=='INFEASIBLE' and
                iterations[-1].get('z3_crosscheck')=='UNSAT')
    selected=sorted(allowed)
    if guaranteed:
        for mask in [0,(1<<len(selected))-1]:
            chosen={selected[i] for i in range(len(selected)) if (mask>>i)&1}
            assert len(real_cycle_count(n,base,oldsets,newsets,chosen))==1
    delta=sum(min(0,moves[i]['continuous_delta']) for i in selected)
    report={'source_harvest_run':40696640556,
        'total_neutral_moves':source['unique_neutral_moves'],
        'initial_disjoint_family_size':len(moves),
        'contracted_segments':k,
        'universal_connectivity_verified':guaranteed,
        'universally_connected_dimension':len(selected) if guaranteed else None,
        'selected_harvest_indices':[choices[i] for i in selected],
        'continuous_euclidean_best_delta_estimate':delta if guaranteed else None,
        'iterations':iterations,
        'elapsed_seconds':round(time.monotonic()-started,3)}
    out=Path(args.report)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({z:v for z,v in report.items() if z!='iterations'}),flush=True)
if __name__=='__main__':main()
