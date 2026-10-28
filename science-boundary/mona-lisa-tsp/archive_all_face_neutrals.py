#!/usr/bin/env python3
"""Independently reconstruct all public equal-score four-face split/merge edits.

Read only simple numeric, non-executable data from completed own GitHub Actions
artifacts. Independent authoritative p010 scorer verifies every unique tour.
Determine maximum vertex-disjoint family with an exact CP-SAT graph model.
"""
import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
from ortools.sat.python import cp_model

def edge(a,b):return (a,b) if a<b else (b,a)
def canonical_edges(t):return {edge(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def recover(n,base,removed,added):
    g=[[] for _ in range(n+1)]
    for a,b in base:
        if (a,b) not in removed:
            g[a].append(b);g[b].append(a)
    for a,b in added:
        g[a].append(b);g[b].append(a)
    assert all(len(g[i])==2 for i in range(1,n+1))
    seen=bytearray(n+1);route=[]
    now=1;previous=0
    while not seen[now]:
        seen[now]=1;route.append(now)
        u,v=g[now]
        nxt=u if u!=previous else v
        previous,now=now,nxt
    assert now==1 and len(route)==n and len(set(route))==n
    return route

def main():
    ap=argparse.ArgumentParser()
    for name in ('baseline','input-dir','output'):
        ap.add_argument('--'+name,required=True)
    args=ap.parse_args()
    spec=importlib.util.spec_from_file_location('verify',Path(os.environ['FEWSHOTS_ROOT'])/
             'problems/p010-mona-lisa-tsp/verify/verify.py')
    verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
    tour=json.loads(Path(args.baseline).read_text())['tour']
    assert len(tour)==100000
    baseline=canonical_edges(tour)
    assert verify.tour_length(tour)==5757191
    xs,ys=verify.coordinates()
    uniq={}
    groups=[]
    for start in range(0,14400,1200):
        folder=Path(args.input_dir)/f'monalisa-all-faces-{start}'
        src=folder/'neutrals.tsv'
        assert src.is_file(),str(src)
        count=0
        for line in src.read_text().splitlines():
            z=list(map(int,line.split()))
            rank,gain,k=z[:3]
            assert len(z)==3+4*k and k>=2 and k<=4
            removed=tuple(sorted(edge(z[3+2*i]+1,z[4+2*i]+1) for i in range(k)))
            added=tuple(sorted(edge(z[3+2*k+2*i]+1,z[4+2*k+2*i]+1)
                               for i in range(k)))
            assert set(removed)<=baseline and not(set(added)&baseline)
            key=(removed,added)
            count+=1
            if key in uniq:uniq[key]['source_ranks'].append(rank);continue
            candidate=recover(100000,baseline,set(removed),set(added))
            score=verify.tour_length(candidate)
            assert score==5757191, (rank,score)
            eu=lambda e:math.hypot(xs[e[0]-1]-xs[e[1]-1],ys[e[0]-1]-ys[e[1]-1])
            cont=math.fsum(eu(e) for e in added)-math.fsum(eu(e) for e in removed)
            digest=verify.canonical_hash({'tour':verify.canonical_tour(candidate)})
            uniq[key]={'source_ranks':[rank],'face_gain':gain,
                       'removed':[list(x) for x in removed],
                       'added':[list(x) for x in added],
                       'continuous_delta':round(cont,12),
                       'canonical_hash':digest,'score':score}
        groups.append({'start':start,'raw_neutral_rows':count})
        if start%3600==0:print(json.dumps({'stage':'verify','start':start,'unique_so_far':len(uniq)}),flush=True)
    moves=sorted(uniq.values(),key=lambda m:(min(m['source_ranks']),m['canonical_hash']))
    assert len({m['canonical_hash'] for m in moves})==len(moves)
    support=[set(x for pair in m['removed']+m['added'] for x in pair) for m in moves]
    conflicts=[(i,j) for i in range(len(moves)) for j in range(i+1,len(moves)) if support[i]&support[j]]
    model=cp_model.CpModel()
    on=[model.NewBoolVar(f'select_{i}') for i in range(len(moves))]
    for i,j in conflicts:model.Add(on[i]+on[j]<=1)
    model.Maximize(sum(on))
    sol=cp_model.CpSolver()
    sol.parameters.max_time_in_seconds=120
    sol.parameters.num_search_workers=4
    result=sol.Solve(model)
    assert result==cp_model.OPTIMAL,('MIS not solved',sol.StatusName(result))
    best_size=round(sol.ObjectiveValue())
    # Among exact max-cardinality families, maximize unrounded Euclidean saving.
    model.Add(sum(on)==best_size)
    model.Minimize(sum(round(1000000*m['continuous_delta'])*on[i] for i,m in enumerate(moves)))
    second=cp_model.CpSolver()
    second.parameters.max_time_in_seconds=120
    second.parameters.num_search_workers=4
    result2=second.Solve(model)
    assert result2 in (cp_model.OPTIMAL,cp_model.FEASIBLE)
    choice=[i for i in range(len(moves)) if second.Value(on[i])]
    assert len(choice)==best_size and not any(i in choice and j in choice for i,j in conflicts)
    data={'baseline':5757191,'source_run':40696640556,
          'face_catalogue_count':12281,
          'raw_neutrals':sum(g['raw_neutral_rows'] for g in groups),
          'unique_neutral_moves':len(moves),'source_groups':groups,
          'independent_family_size':best_size,
          'selected_indices':choice,
          'selected_continuous_delta':sum(moves[i]['continuous_delta'] for i in choice),
          'max_independent_optimality':'CP-SAT OPTIMAL for vertex-disjoint support only',
          'second_objective_status':second.StatusName(result2),
          'conflict_pairs':len(conflicts),'moves':moves}
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k not in ('moves','source_groups')}),flush=True)
if __name__=='__main__':main()
