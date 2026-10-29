#!/usr/bin/env python3
"""Counterexample-guided subtour elimination on a full 8-NN candidate pool.

Same 18-second single-core budget and public only as AddCircuit benchmark.
At each step, cheapest degree-2 integer solution is a counterexample if
disconnected. Separate VALID x(delta(S))>=2 cuts, then reoptimize. Do not
confuse a cheap disconnected 2-factor with an improving Hamiltonian tour.

This follows classical TSP branch-and-cut principles and 2026 ML-SEC work;
the experimental change is the interface/representation, not a novelty claim.
"""
import argparse,json,time
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model
from tsplib_counterfactual_bench import E, edge_set,score

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--public',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--seconds',type=float,default=18)
    p.add_argument('--seed',type=int,default=1701)
    a=p.parse_args();t0=time.perf_counter()
    d=json.loads(Path(a.public).read_text())
    D=np.asarray(d['distance'],dtype=np.int32);n=len(D)
    ref=d['reference'];base=edge_set(ref)
    assert score(ref,D)==d['reference_score']
    parents=set().union(base,*(edge_set(t) for t in d['parents']))
    knn=set()
    for u in range(n):
        for v in np.argsort(D[u],kind='stable')[:9]:
            v=int(v)
            if u!=v:knn.add(E(u,v))
    pool=parents|knn
    vars={};inc=[[] for _ in range(n)]
    m=cp_model.CpModel()
    for u,v in sorted(pool):
        q=m.NewBoolVar(f'e{u}_{v}')
        vars[(u,v)]=q
        inc[u].append(q);inc[v].append(q)
        m.AddHint(q,int((u,v) in base))
    for u in range(n):m.Add(sum(inc[u])==2)
    m.Minimize(sum(int(D[u,v])*x for (u,v),x in vars.items()))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=a.seed
    rounds=[];cuts=0;knowncuts=set();best=d['reference_score'];tour=list(ref);last='NOT_SOLVED'
    final_certified=False
    while time.perf_counter()-t0<a.seconds-.1 and len(rounds)<75:
        remaining=a.seconds-(time.perf_counter()-t0)
        solver.parameters.max_time_in_seconds=max(.05,min(3.0,remaining))
        outcome=solver.Solve(m)
        last=solver.StatusName(outcome)
        if outcome not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            if outcome==cp_model.INFEASIBLE:raise AssertionError('incumbent must remain feasible')
            if remaining<.2:break
            continue
        edges={e for e,x in vars.items() if solver.Value(x)}
        assert len(edges)==n
        parent=list(range(n))
        def root(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]]
                i=parent[i]
            return i
        for u,v in edges:parent[root(u)]=root(v)
        groups={}
        for u in range(n):groups.setdefault(root(u),set()).add(u)
        objective=int(round(solver.ObjectiveValue()))
        assert objective==sum(int(D[e]) for e in edges)
        row={'round':len(rounds)+1,'degree2_score':objective,
             'components':len(groups),'solver_status':last,
             'best_bound':solver.BestObjectiveBound()}
        rounds.append(row)
        if len(groups)==1:
            adj=[[] for _ in range(n)]
            for u,v in edges:adj[u].append(v);adj[v].append(u)
            assert all(len(x)==2 for x in adj)
            path=[0];prev=-1;cur=0;seen={0}
            while True:
                x,y=adj[cur];nxt=x if x!=prev else y
                if nxt==0:break
                assert nxt not in seen
                seen.add(nxt);path.append(nxt);prev,cur=cur,nxt
            assert len(path)==n and score(path,D)==objective
            if objective<best:tour=path;best=objective
            if outcome==cp_model.OPTIMAL:final_certified=True;break
            continue
        changed=0
        for S in groups.values():
            if len(S)==n:continue
            cut=frozenset(S)
            if cut in knowncuts:continue
            knowncuts.add(cut)
            crossing=[q for (u,v),q in vars.items() if (u in S)!=(v in S)]
            if not crossing:
                # No improving connected tour possible in such an edge pool,
                # but incumbent already exists, so this case is impossible.
                raise AssertionError('empty cut in incumbent-connected edge pool')
            m.Add(sum(crossing)>=2);cuts+=1;changed+=1
        row['new_SEC_cuts']=changed
        print(json.dumps({'stage':'SEC_cut_round','instance':d['instance'],**row}),flush=True)
        if not changed:break
    result={'instance':d['instance'],'strategy':'knn8_dynamic_SEC',
        'reference_score':d['reference_score'],'score':best,
        'gain':d['reference_score']-best,
        'budget':'full eight-nearest-neighbor plus original parents',
        'novel_pool_edges':len(knn-parents),'status':'OPTIMAL' if final_certified else last,
        'proof_of_restricted_optimality':final_certified,
        'candidate_model_size':len(pool),'separated_cuts':cuts,
        'round_history':rounds,'elapsed_seconds':round(time.perf_counter()-t0,4),
        'tour':tour}
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tour','round_history')}),flush=True)
if __name__=='__main__':main()
