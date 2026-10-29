#!/usr/bin/env python3
"""Counterfactual proposal-coverage ablation: preserve or truncate candidate edges.

Public-only inputs: TSPLIB reference, allowed parent tours, independently
computed LP primal-support edges and integer geometry. No hidden tours or
optimal values. Optimize a *single connected circuit*, never a 2-factor.
At fixed 18-second single-thread budgets, compare all LP-positive edges,
all 8NN geometric edges, or their union, versus previously tested 12-edge
bottleneck. This is a post-hoc representation diagnostic on old heldouts.
"""
import argparse,json,time
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model
from tsplib_counterfactual_bench import E,edge_set,score

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--public',required=True)
    p.add_argument('--selector',choices=['lp_full','knn8_full','lp_knn_union'],required=True)
    p.add_argument('--seconds',type=float,default=18)
    p.add_argument('--output',required=True)
    a=p.parse_args();start=time.perf_counter()
    d=json.loads(Path(a.public).read_text())
    D=np.asarray(d['distance'],dtype=np.int32);n=D.shape[0]
    ref=d['reference'];parent_edges=set().union(edge_set(ref),*(edge_set(t) for t in d['parents']))
    assert score(ref,D)==d['reference_score']
    lp={E(r['u'],r['v']) for r in d['lp_positive']}
    knn=set()
    for u in range(n):
        for v in np.argsort(D[u],kind='stable')[:9]:
            v=int(v)
            if u!=v:knn.add(E(u,v))
    if a.selector=='lp_full':candidates=lp-parent_edges
    elif a.selector=='knn8_full':candidates=knn-parent_edges
    else:candidates=(lp|knn)-parent_edges
    m=cp_model.CpModel();arcs=[];vars={}
    incumbent_oriented={(ref[i],ref[(i+1)%n]) for i in range(n)}
    incumbent_set=edge_set(ref)
    for u,v in sorted(parent_edges|candidates):
        q=m.NewBoolVar(f'e{u}_{v}');f=m.NewBoolVar(f'f{u}_{v}');r=m.NewBoolVar(f'r{u}_{v}')
        m.Add(f+r==q)
        arcs.extend(((u,v,f),(v,u,r)))
        vars[(u,v)]=q
        # Warm-start the exact incumbent in the much larger candidate graph;
        # previous version returned worse feasible tours under short time caps.
        m.AddHint(q,1 if (u,v) in incumbent_set else 0)
        m.AddHint(f,1 if (u,v) in incumbent_oriented else 0)
        m.AddHint(r,1 if (v,u) in incumbent_oriented else 0)
    m.AddCircuit(arcs)
    m.Minimize(sum(int(D[u,v])*q for (u,v),q in vars.items()))
    solver=cp_model.CpSolver()
    solver.parameters.random_seed=1701
    solver.parameters.num_search_workers=1
    solver.parameters.max_time_in_seconds=max(.1,a.seconds-(time.perf_counter()-start))
    status=solver.Solve(m)
    result={'instance':d['instance'],'strategy':a.selector,
       'reference_score':d['reference_score'],
       'LP_all_supported_edges':len(lp),'geometric_8NN_edges':len(knn),
       'parent_edges':len(parent_edges),
       'added_candidate_edges':len(candidates),
       'status':solver.StatusName(status),'elapsed_seconds':round(time.perf_counter()-start,4),
       'selected_chords':[list(e) for e in sorted(candidates)],
       'solver_bound':solver.BestObjectiveBound(),
       'incumbent_warm_start':True}
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        selected={e for e,q in vars.items() if solver.Value(q)}
        assert len(selected)==n
        adj=[[] for _ in range(n)]
        for u,v in selected:adj[u].append(v);adj[v].append(u)
        assert all(len(z)==2 for z in adj)
        route=[0];prev=-1;cur=0;seen={0}
        while True:
            x,y=adj[cur];nxt=x if x!=prev else y
            if nxt==0:break
            assert nxt not in seen
            seen.add(nxt);route.append(nxt);prev,cur=cur,nxt
        assert len(route)==n
        actual=score(route,D);assert actual==int(round(solver.ObjectiveValue()))
        result.update({'score':actual,'gain':d['reference_score']-actual,
            'selected_edges_used':len(selected&candidates),'tour':route})
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tour','selected_chords')}),flush=True)
if __name__=='__main__':main()
