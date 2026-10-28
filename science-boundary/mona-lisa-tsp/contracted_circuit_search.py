#!/usr/bin/env python3
"""Exact contracted-TSP search over globally distributed sparse-graph chords.

A set of candidate non-tour edges is selected from profitable / neutral
alternating planar faces (or from saved neutral mutations). Both baseline edges
incident to every candidate-chord endpoint become flexible. Every other
baseline edge is immutable. Contract every maximal immutable baseline path.
The result is a small *exact* Hamiltonian-cycle problem solved by CP-SAT
AddCircuit, with no subtour separation and no possibility of a disconnected
2-factor passing as a tour.

This is a conditional search, NOT a globally optimality claim.
"""
import argparse
import gzip
import importlib.util
import json
import os
import time
from pathlib import Path

import networkx as nx
from ortools.sat.python import cp_model

def ek(a,b):
    return (a,b) if a<b else (b,a)

def source_graph(path,n):
    with gzip.open(path,'rt') as inp:
        head=list(map(int,inp.readline().split()))
        raw=[tuple(map(int,line.split())) for line in inp if line.strip()]
    assert head==[n,len(raw)]
    off=0 if min(min(a,b) for a,b,w in raw)==0 else 1
    w={ek(a-off,b-off):cost for a,b,cost in raw}
    assert len(w)==len(raw)
    return w

def profitable_face_chords(graph,base,weights):
    isplanar,embedding=nx.check_planarity(graph)
    assert isplanar
    visited=set()
    ranked=[]
    for a,b in graph.edges():
        for u,v in ((a,b),(b,a)):
            if (u,v) in visited:continue
            face=embedding.traverse_face(u,v)
            L=len(face)
            visited.update((face[i],face[(i+1)%L]) for i in range(L))
            if L!=4 or len(set(face))!=4:continue
            edges=[ek(face[i],face[(i+1)%L]) for i in range(L)]
            marks=[edge in base for edge in edges]
            if any(marks[i]==marks[(i+1)%L] for i in range(L)):continue
            gain=sum(weights[edge]*(1 if present else -1)
                     for edge,present in zip(edges,marks))
            new=tuple(edge for edge in edges if edge not in base)
            assert len(new)==2
            ranked.append((gain,new))
    ranked.sort(key=lambda x:-x[0])
    return ranked

def build_active(tour,base,nonbase):
    n=len(tour)
    active=set(nonbase)
    incident_baseline={}
    for i,v in enumerate(tour):
        incident_baseline[v]=(ek(tour[(i-1)%n],v),ek(v,tour[(i+1)%n]))
    for u,v in nonbase:
        active.update(incident_baseline[u])
        active.update(incident_baseline[v])
    assert active>=nonbase
    U={v for edge in active for v in edge}
    ordered=[v for v in tour if v in U]
    # Every fixed tour path between consecutive flexible vertices is mandatory.
    pos={v:i for i,v in enumerate(tour)}
    macros=[]
    for i,v in enumerate(ordered):
        nxt=ordered[(i+1)%len(ordered)]
        if (pos[nxt]-pos[v])%n==1 and ek(v,nxt) in active:
            continue
        macros.append((v,nxt))
    assert len(ordered)>3
    return active,ordered,macros

def reconstruct(tour,base,active,selected):
    n=len(tour)
    adj=[[] for _ in range(n)]
    for u,v in base:
        if (u,v) in active and (u,v) not in selected:continue
        adj[u].append(v);adj[v].append(u)
    for u,v in selected:
        if (u,v) not in base:
            adj[u].append(v);adj[v].append(u)
    assert all(len(x)==2 for x in adj), 'degree-two violated'
    visited=bytearray(n)
    route=[]
    cur=0;prev=-1
    while not visited[cur]:
        visited[cur]=1
        route.append(cur+1)
        a,b=adj[cur]
        nxt=a if a!=prev else b
        prev,cur=cur,nxt
    assert cur==0 and len(route)==n, 'not a Hamiltonian cycle'
    return route

def main():
    p=argparse.ArgumentParser()
    for f in ('edges','baseline','neutral-moves','report','output'):
        p.add_argument('--'+f,required=True)
    p.add_argument('--faces',type=int,default=279)
    p.add_argument('--extra-neutral',action='store_true')
    p.add_argument('--time-limit',type=int,default=90)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--random-seed',type=int,default=1)
    args=p.parse_args()
    started=time.monotonic()
    base_t=json.loads(Path(args.baseline).read_text())['tour']
    n=len(base_t)
    assert n==100000 and len(set(base_t))==n
    tour=[x-1 for x in base_t]
    base={ek(tour[i],tour[(i+1)%n]) for i in range(n)}
    weights=source_graph(args.edges,n)
    assert base<=weights.keys()
    graph=nx.Graph()
    graph.add_nodes_from(range(n))
    graph.add_edges_from(weights)
    ranked=profitable_face_chords(graph,base,weights)
    assert len(ranked)>=279 and ranked[0][0]==16
    chosen=ranked[:args.faces]
    chords={e for _,new in chosen for e in new}
    if args.extra_neutral:
        for move in json.loads(Path(args.neutral_moves).read_text())['neutral_moves']:
            chords.update(ek(a-1,b-1) for a,b in move['added'])
    assert all(e in weights and e not in base for e in chords)
    active,ordered,macros=build_active(tour,base,chords)
    spec=importlib.util.spec_from_file_location('p010_verifier',
        Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    for (a,b) in active:
        assert weights[(a,b)]==v.euc_2d(xs[a]-xs[b],ys[a]-ys[b])
    assert v.tour_length(base_t)==5757191

    nodes={u:i for i,u in enumerate(ordered)}
    model=cp_model.CpModel()
    arcs=[]
    variables={}
    weighted=[]
    constant=0
    for (a,b) in sorted(active):
        x=model.NewBoolVar(f'e{a}_{b}')
        f=model.NewBoolVar(f'f{a}_{b}')
        r=model.NewBoolVar(f'r{a}_{b}')
        model.Add(f+r==x)
        arcs.append((nodes[a],nodes[b],f))
        arcs.append((nodes[b],nodes[a],r))
        variables[(a,b)]=x
        weighted.append(weights[(a,b)]*x)
        if (a,b) in base:constant+=weights[(a,b)]
    for a,b in macros:
        f=model.NewBoolVar(f'F{a}_{b}')
        r=model.NewBoolVar(f'R{a}_{b}')
        model.Add(f+r==1)
        arcs.append((nodes[a],nodes[b],f))
        arcs.append((nodes[b],nodes[a],r))
    model.AddCircuit(arcs)
    delta=sum(weighted)-constant
    model.Add(delta<=-1)
    model.Minimize(delta)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.time_limit
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=args.random_seed
    solver.parameters.log_search_progress=False
    report={'status':'NOT_STARTED','selected_faces':args.faces,
        'min_face_gain':chosen[-1][0] if chosen else None,
        'chords':len(chords),'variable_edges':len(active),
        'flexible_vertices':len(ordered),'fixed_macro_paths':len(macros),
        'base':5757191,'include_neutral':args.extra_neutral,
        'candidate_graph_edges':len(weights),'time_limit':args.time_limit}
    print(json.dumps({'stage':'model','report':report}),flush=True)
    outcome=solver.Solve(model)
    report['status']=solver.StatusName(outcome)
    report['elapsed_seconds']=round(time.monotonic()-started,3)
    report['branches']=solver.NumBranches()
    report['conflicts']=solver.NumConflicts()
    if outcome in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        selected={e for e,x in variables.items() if solver.Value(x)}
        route=reconstruct(tour,base,active,selected)
        score=v.tour_length(route)
        predicted=5757191+sum(weights[e] for e in selected)-constant
        assert score==predicted and score<5757191
        cert=Path(args.output)
        cert.parent.mkdir(parents=True,exist_ok=True)
        cert.write_text(json.dumps({'tour':route},separators=(',',':')))
        report.update({'verified_score':score,'improvement':5757191-score,
                       'official_style_hash':v.canonical_hash({'tour':v.canonical_tour(route)}),
                       'candidate':str(cert)})
    else:
        report['best_objective_bound']=solver.BestObjectiveBound()
    path=Path(args.report)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result','report':report}),flush=True)

if __name__=='__main__':
    main()
