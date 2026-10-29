#!/usr/bin/env python3
"""Independent blinded *geometric* negative controls for public TSPLIB splits.

Inputs = public.json only: reference, independently permitted parents and
geometry. Never reads hidden local winner, official optima, or LP scores.

All controls add exactly 12 nonparent edges and use same CP-SAT AddCircuit,
objective, single thread and 18-second inclusive budget as existing split.
These are post-hoc controls on earlier 10 test cases; judge prospectively
on a new split before asserting method superiority.
"""
import argparse,json,random,time
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model
from tsplib_counterfactual_bench import E,edge_set,score

def candidate_edges(D,base,parents,strategy,k,seed):
    n=len(D)
    universe=[(i,j) for i in range(n) for j in range(i+1,n) if (i,j) not in parents]
    assert len(universe)>=k
    reference=base
    neighbors=[[] for _ in range(n)]
    for u,v in reference:neighbors[u].append(v);neighbors[v].append(u)
    assert all(len(z)==2 for z in neighbors)
    if strategy=='nearest':
        return sorted(universe,key=lambda e:(int(D[e]),e))[:k]
    if strategy=='local_delta':
        # Local candidate score excludes LP and candidate-tour edges entirely.
        # It penalizes replacing already short incumbent neighbor edges.
        def surplus(u,v):
            return 2*int(D[u,v])-min(int(D[u,w]) for w in neighbors[u])-min(int(D[v,w]) for w in neighbors[v])
        return sorted(universe,key=lambda e:(surplus(*e),int(D[e]),e))[:k]
    if strategy=='random_8nn':
        pool=[]
        for u,v in universe:
            count_u=int((D[u]<D[u,v]).sum()) # ties deliberately kept
            count_v=int((D[v]<D[v,u]).sum())
            if min(count_u,count_v)<=8:pool.append((u,v))
        pool.sort()
        rng=random.Random(seed);rng.shuffle(pool)
        if len(pool)<k:
            spare=list(set(universe)-set(pool));spare.sort();rng.shuffle(spare);pool+=spare
        return pool[:k]
    raise ValueError(strategy)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--public',required=True)
    p.add_argument('--strategy',choices=['nearest','local_delta','random_8nn'],required=True)
    p.add_argument('--budget',type=int,default=12)
    p.add_argument('--seconds',type=float,default=18)
    p.add_argument('--seed',type=int,default=20261029)
    p.add_argument('--out',required=True)
    args=p.parse_args()
    started=time.monotonic()
    pub=json.loads(Path(args.public).read_text())
    D=np.asarray(pub['distance'],dtype=np.int32)
    ref=pub['reference'];n=len(ref)
    assert len(set(ref))==n and score(ref,D)==pub['reference_score']
    parents=set().union(edge_set(ref),*(edge_set(t) for t in pub['parents']))
    chosen=candidate_edges(D,edge_set(ref),parents,args.strategy,args.budget,args.seed)
    assert len(chosen)==args.budget and not(set(chosen)&parents)
    model=cp_model.CpModel();arcs=[];variables={}
    for u,v in sorted(parents|set(chosen)):
        q=model.NewBoolVar(f'e{u}_{v}')
        f=model.NewBoolVar(f'F{u}_{v}');r=model.NewBoolVar(f'R{u}_{v}')
        model.Add(f+r==q)
        arcs.extend(((u,v,f),(v,u,r)))
        variables[(u,v)]=q
    model.AddCircuit(arcs)
    model.Minimize(sum(int(D[u,v])*q for (u,v),q in variables.items()))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=1701
    solver.parameters.max_time_in_seconds=max(.1,args.seconds-(time.monotonic()-started))
    status=solver.Solve(model)
    output={'instance':pub['instance'],'strategy':args.strategy,'budget':args.budget,
        'reference_score':pub['reference_score'],'status':solver.StatusName(status),
        'seconds':round(time.monotonic()-started,3),
        'selected_chords':chosen,'method_meta':{'uses_LP':False,'uses_hidden':False}}
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        es={e for e,q in variables.items() if solver.Value(q)}
        assert len(es)==n
        adj=[[] for _ in range(n)]
        for u,v in es:adj[u].append(v);adj[v].append(u)
        assert all(len(z)==2 for z in adj)
        cur=0;prev=-1;route=[0];seen={0}
        while True:
            a,b=adj[cur];w=a if a!=prev else b
            if w==0:break
            assert w not in seen
            seen.add(w);route.append(w);prev,cur=cur,w
        assert len(route)==n
        total=score(route,D)
        assert total==round(solver.ObjectiveValue())
        output.update({'score':total,'gain':pub['reference_score']-total,'tour':route,
                       'selected_edges_used':len(es&set(chosen))})
    path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('tour','selected_chords')}),flush=True)

if __name__=='__main__':main()
