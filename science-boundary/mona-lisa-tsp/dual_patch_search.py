#!/usr/bin/env python3
"""Exact face-patch TSP search in the public planar Mona Lisa reduction.

Uses CP-SAT for local face spins, exact degree-two constraints, iteratively
separated global connectivity cuts, and the authoritative Few Shots scorer.
Search results are conditional on the published sparse edge set.
"""
import argparse, gzip, importlib.util, json, os, time
from collections import defaultdict, deque
from pathlib import Path
import networkx as nx
from ortools.sat.python import cp_model

def key(u,v):
    return (u,v) if u<v else (v,u)

def load(edges_path,tour):
    n=len(tour)
    with gzip.open(edges_path,'rt') as inp:
        header=list(map(int,inp.readline().split()))
        raw=[tuple(map(int,line.split())) for line in inp if line.strip()]
    assert header==[n,len(raw)]
    offset=0 if min(min(u,v) for u,v,w in raw)==0 else 1
    weights={key(u-offset,v-offset):w for u,v,w in raw}
    assert len(weights)==len(raw)
    graph=nx.Graph()
    graph.add_nodes_from(range(n))
    graph.add_edges_from(weights.keys())
    planar,embedding=nx.check_planarity(graph)
    assert planar
    baseline={key(tour[i],tour[(i+1)%n]) for i in range(n)}
    assert len(baseline)==n and baseline<=weights.keys()
    half={}
    faces=[]
    positive=[]
    for a,b in graph.edges():
        for u,v in ((a,b),(b,a)):
            if (u,v) in half:continue
            vs=embedding.traverse_face(u,v)
            f=len(faces)
            faces.append(vs)
            for i,x in enumerate(vs):
                half[(x,vs[(i+1)%len(vs)])]=f
            if len(vs)==4 and len(set(vs))==4:
                edges=[key(vs[i],vs[(i+1)%4]) for i in range(4)]
                marks=[e in baseline for e in edges]
                if all(marks[i]!=marks[(i+1)%4] for i in range(4)):
                    gain=sum((1 if m else -1)*weights[e] for e,m in zip(edges,marks))
                    if gain>0: positive.append((gain,f))
    dual=[set() for _ in faces]
    sides={}
    for e in weights:
        a,b=e
        f,g=half[(a,b)],half[(b,a)]
        sides[e]=(f,g)
        if f!=g:
            dual[f].add(g)
            dual[g].add(f)
    assert len(faces)==len(weights)-n+2
    return weights,baseline,faces,dual,sides,sorted(positive,reverse=True)

def patch(seed,radius,dual,cap):
    selected={seed}
    queue=deque([(seed,0)])
    while queue:
        f,d=queue.popleft()
        if d>=radius:continue
        for other in dual[f]:
            if other not in selected:
                if len(selected)>=cap:return None
                selected.add(other)
                queue.append((other,d+1))
    return selected

def reconstruct(n,base,flips):
    adj=[[] for _ in range(n)]
    for a,b in base:
        adj[a].append(b);adj[b].append(a)
    for a,b in flips:
        if (a,b) in base:
            adj[a].remove(b);adj[b].remove(a)
        else:
            adj[a].append(b);adj[b].append(a)
    assert all(len(x)==2 for x in adj)
    seen=bytearray(n)
    cycles=[]
    for start in range(n):
        if seen[start]:continue
        cycle=[]
        u=start;previous=-1
        while not seen[u]:
            seen[u]=1
            cycle.append(u)
            x,y=adj[u]
            nxt=x if x!=previous else y
            previous,u=u,nxt
        assert u==start
        cycles.append(cycle)
    return cycles

def solve(seed,radius,selected,weights,baseline,sides,tour,verifier,
          outdir,seconds,max_cuts):
    n=len(tour)
    m=cp_model.CpModel()
    vars={f:m.NewBoolVar('f%d'%f) for f in selected}
    toggles={}
    inc=defaultdict(list)
    delta=[]
    for edge,w in weights.items():
        f,g=sides[edge]
        a=vars.get(f);b=vars.get(g)
        if f==g or (a is None and b is None):continue
        if a is None or b is None:
            x=b if a is None else a
        else:
            x=m.NewBoolVar('x%d_%d'%edge)
            # x = a XOR b; ORTools XOr requires odd parity.
            m.AddBoolXOr([a,b,x.Not()])
        toggles[edge]=x
        sign=-1 if edge in baseline else 1
        delta.append(sign*w*x)
        u,v=edge
        inc[u].append(sign*x);inc[v].append(sign*x)
    for terms in inc.values():m.Add(sum(terms)==0)
    m.Add(sum(delta)<=-1)
    m.Minimize(sum(delta))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=11
    start=time.monotonic()
    cuts=rounds=0
    final_status='UNKNOWN'
    while time.monotonic()-start<seconds and cuts<=max_cuts:
        solver.parameters.max_time_in_seconds=max(.2,seconds-(time.monotonic()-start))
        result=solver.Solve(m)
        final_status=solver.StatusName(result)
        rounds+=1
        if result not in (cp_model.FEASIBLE,cp_model.OPTIMAL):break
        flipped={e for e,x in toggles.items() if solver.Value(x)}
        cycles=reconstruct(n,baseline,flipped)
        diff=sum(weights[e]*(-1 if e in baseline else 1) for e in flipped)
        assert diff==round(solver.ObjectiveValue()) and diff<0
        if len(cycles)==1:
            candidate=[x+1 for x in cycles[0]]
            score=verifier.tour_length(candidate)
            assert score==5757191+diff and score<5757191
            path=outdir/f'candidate-{seed}-{radius}.json'
            path.write_text(json.dumps({'tour':candidate},separators=(',',':')))
            return {'seed':seed,'radius':radius,'faces':len(selected),
                'active_edges':len(toggles),'status':'VERIFIED_IMPROVEMENT',
                'score':score,'delta':diff,'certificate':str(path),
                'rounds':rounds,'cuts':cuts,'seconds':round(time.monotonic()-start,2)}
        # Subtour elimination over *all* reduced graph crossing edges.
        # Non-active edges are fixed to baseline incidence.
        for cycle in sorted(cycles,key=len)[:-1]:
            inside=bytearray(n)
            for v in cycle:inside[v]=1
            base_cut=sum(inside[tour[i]]!=inside[tour[(i+1)%n]] for i in range(n))
            terms=[(-1 if e in baseline else 1)*x for e,x in toggles.items()
                   if inside[e[0]]!=inside[e[1]]]
            m.Add(base_cut+sum(terms)>=2)
            cuts+=1
            if cuts>max_cuts:break
    if cuts>max_cuts:final_status='CUT_BUDGET'
    return {'seed':seed,'radius':radius,'faces':len(selected),
        'active_edges':len(toggles),'status':final_status,
        'rounds':rounds,'cuts':cuts,'seconds':round(time.monotonic()-start,2)}

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--edges',required=True)
    a.add_argument('--baseline',required=True)
    a.add_argument('--report',required=True)
    a.add_argument('--outdir',required=True)
    a.add_argument('--seed-start',type=int,default=0)
    a.add_argument('--seeds',type=int,default=4)
    a.add_argument('--radii',default='2,3,4,5')
    a.add_argument('--max-faces',type=int,default=280)
    a.add_argument('--seconds',type=int,default=45)
    a.add_argument('--max-cuts',type=int,default=80)
    args=a.parse_args()
    start=time.monotonic()
    tour=[x-1 for x in json.loads(Path(args.baseline).read_text())['tour']]
    assert len(tour)==100000 and len(set(tour))==100000
    weights,base,faces,dual,sides,positive=load(args.edges,tour)
    print(json.dumps({'stage':'graph','edges':len(weights),
        'faces':len(faces),'positive_4faces':len(positive),
        'top_gains':positive[:10]}),flush=True)
    spec=importlib.util.spec_from_file_location('verify',
        Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py')
    verifier=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    assert verifier.tour_length([t+1 for t in tour])==5757191
    outdir=Path(args.outdir)
    outdir.mkdir(parents=True,exist_ok=True)
    records=[]
    for rank in range(args.seed_start,min(len(positive),args.seed_start+args.seeds)):
        gain,seed=positive[rank]
        for radius in map(int,args.radii.split(',')):
            selected=patch(seed,radius,dual,args.max_faces)
            if selected is None:
                rec={'rank':rank,'seed':seed,'radius':radius,
                     'status':'SKIPPED_TOO_MANY_FACES'}
            else:
                rec={'rank':rank,'seed_gain':gain,**solve(seed,radius,selected,
                    weights,base,sides,tour,verifier,outdir,args.seconds,args.max_cuts)}
            records.append(rec)
            print(json.dumps({'stage':'patch',**rec}),flush=True)
            Path(args.report).write_text(json.dumps({'records':records},
                indent=2)+'\n')
            if rec['status']=='VERIFIED_IMPROVEMENT':break
    Path(args.report).write_text(json.dumps({'records':records,
        'total_elapsed_seconds':round(time.monotonic()-start,2)},indent=2)+'\n')
if __name__=='__main__':
    main()
