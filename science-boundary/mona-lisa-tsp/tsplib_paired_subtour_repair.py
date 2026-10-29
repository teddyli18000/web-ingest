#!/usr/bin/env python3
"""Paired cross-subtour repairs, not independent "good-looking" edges.

A 2-factor of the old parent-tour graph is optimized first. A violation of
global connectivity is treated as a *counterexample*. For each pair of cycles,
enumerate 2-opt joining moves replacing (u,a),(v,b) by either {(u,v),(a,b)}
or {(u,b),(a,v)} and rank by EXACT integer total length increase. Introduce
both unseen chords together. This avoids the incoherent single-chord selection
failure of the previous repair heuristic.

No withheld tour, optimal score or LP x values may be read. Every candidate
is judged by exact AddCircuit over the same old-parent union.
"""
import argparse, json, time
from collections import defaultdict
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model
from tsplib_counterfactual_bench import E, edge_set, score

def factor(parent_edges,D,limit=3):
    n=D.shape[0]
    model=cp_model.CpModel()
    vars={e:model.NewBoolVar(f'F{e[0]}_{e[1]}') for e in parent_edges}
    incident=[[] for _ in range(n)]
    for (u,v),q in vars.items():incident[u].append(q);incident[v].append(q)
    for inc in incident:model.Add(sum(inc)==2)
    model.Minimize(sum(int(D[u,v])*q for (u,v),q in vars.items()))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.max_time_in_seconds=limit
    result=solver.Solve(model)
    if result not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return None,{'status':solver.StatusName(result)}
    chosen={e for e,q in vars.items() if solver.Value(q)}
    adj=[[] for _ in range(n)]
    for u,v in chosen:adj[u].append(v);adj[v].append(u)
    assert len(chosen)==n and all(len(z)==2 for z in adj)
    cid=[-1]*n;components=[]
    for start in range(n):
        if cid[start]>=0:continue
        j=len(components);stack=[start];members=[]
        while stack:
            u=stack.pop()
            if cid[u]>=0:continue
            cid[u]=j;members.append(u);stack.extend(adj[u])
        components.append(members)
    return (chosen,cid,components),{
        'status':solver.StatusName(result),'degree2_score':int(round(solver.ObjectiveValue())),
        'component_count':len(components),'component_sizes':sorted(map(len,components))}

def selected_pairs(f,D,parents,budget):
    n=len(D);edges,cid,groups=f
    candidate=[]
    Efac=sorted(edges)
    for i,(u,a) in enumerate(Efac):
        for v,b in Efac[i+1:]:
            if cid[u]==cid[v]:continue
            old=int(D[u,a])+int(D[v,b])
            for x,y in (((u,v),(a,b)),((u,b),(a,v))):
                left,right=E(*x),E(*y)
                if left==right or left in edges or right in edges:continue
                new={left,right}-parents
                if not new:continue
                delta=int(D[left])+int(D[right])-old
                candidate.append((delta,len(new),left,right,cid[u],cid[v]))
    candidate.sort(key=lambda z:(z[0],z[1],z[2],z[3]))
    selected=set();paired=[];gparent=list(range(len(groups)))
    def root(i):
        while gparent[i]!=i:
            gparent[i]=gparent[gparent[i]];i=gparent[i]
        return i
    def add(entry):
        _,_,a,b,cu,cv=entry
        new={a,b}-parents-selected
        if not new or len(selected)+len(new)>budget:return False
        selected.update(new)
        paired.append((a,b,cu,cv,entry[0]))
        return True
    # First, greedily spanning as many disconnected components as possible.
    for e in candidate:
        if root(e[4])==root(e[5]):continue
        if add(e):gparent[root(e[4])]=root(e[5])
        if len(selected)==budget:break
    # Then include other low-cost coherent patches, still adding both chords.
    for e in candidate:
        if len(selected)==budget:break
        add(e)
    return selected,paired,candidate

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--public',required=True);p.add_argument('--output',required=True)
    p.add_argument('--budget',type=int,default=12);p.add_argument('--seconds',type=float,default=18)
    args=p.parse_args();start=time.monotonic()
    pub=json.loads(Path(args.public).read_text())
    D=np.asarray(pub['distance'],dtype=np.int32);n=len(D)
    ref=pub['reference'];base=edge_set(ref)
    assert score(ref,D)==pub['reference_score']
    parents=set().union(base,*(edge_set(t) for t in pub['parents']))
    f,meta=factor(parents,D,limit=min(3,args.seconds/5))
    proposed=set();pairs=[];proposal_count=0
    if f is not None and meta['component_count']>1:
        proposed,pairs,candidates=selected_pairs(f,D,parents,args.budget)
        proposal_count=len(candidates)
    # On degenerate cases, fill with shortest unused geometric chords, but
    # report the exact number of such fallbacks so success isn't attributed
    # to a subtour signal that was not present.
    n_paired=len(proposed)
    if len(proposed)<args.budget:
        additional=sorted(((u,v) for u in range(n) for v in range(u+1,n)
                            if (u,v) not in parents and (u,v) not in proposed),
                            key=lambda e:(int(D[e]),e))
        proposed.update(additional[:args.budget-len(proposed)])
    assert len(proposed)==args.budget and not(proposed&parents)
    model=cp_model.CpModel();arcs=[];vars={}
    for u,v in sorted(parents|proposed):
        q=model.NewBoolVar(f'e{u}_{v}')
        fw=model.NewBoolVar(f'fw{u}_{v}');rv=model.NewBoolVar(f'rv{u}_{v}')
        model.Add(fw+rv==q);arcs.extend(((u,v,fw),(v,u,rv)));vars[(u,v)]=q
    model.AddCircuit(arcs)
    model.Minimize(sum(int(D[u,v])*q for (u,v),q in vars.items()))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=1701
    solver.parameters.max_time_in_seconds=max(.1,args.seconds-(time.monotonic()-start))
    status=solver.Solve(model)
    result={'instance':pub['instance'],'strategy':'paired_subtour_repair',
        'reference_score':pub['reference_score'],'budget':args.budget,
        'status':solver.StatusName(status),'seconds':round(time.monotonic()-start,3),
        'selected_chords':[list(e) for e in sorted(proposed)],
        'method_meta':{'two_factor':meta,'pair_proposals':proposal_count,
            'coherent_patches_selected':len(pairs),'novel_chords_from_pairs':n_paired,
            'fallback_nearest_chords':args.budget-n_paired}}
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        chosen={e for e,q in vars.items() if solver.Value(q)}
        assert len(chosen)==n
        adj=[[] for _ in range(n)]
        for u,v in chosen:adj[u].append(v);adj[v].append(u)
        assert all(len(z)==2 for z in adj)
        route=[0];cur=0;prev=-1;visited={0}
        while True:
            a,b=adj[cur];nxt=a if a!=prev else b
            if nxt==0:break
            assert nxt not in visited
            visited.add(nxt);route.append(nxt);prev,cur=cur,nxt
        assert len(route)==n
        length=score(route,D);assert length==round(solver.ObjectiveValue())
        result.update({'tour':route,'score':length,'gain':pub['reference_score']-length,
                       'selected_edges_used':len(proposed&chosen)})
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('tour','selected_chords')}),flush=True)
if __name__=='__main__':main()
