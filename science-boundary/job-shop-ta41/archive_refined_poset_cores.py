#!/usr/bin/env python3
"""Replay and independently audit fresh ta41 consensus conflict cores.

Original refinement Action stored only 48/41 sizes, not the exact arc
lists. This repair explicitly preserves *every* necessary precedence
triple for the 13 and 14 independently verified neutral parents.
OR-Tools assumption core discovery and a separate hard-NoOverlap rebuild
are both archived, plus resource-independent longest-path lower bound.

Recomputation can return a different sufficient core; do NOT claim
byte-for-byte identity with the original 48/41 (which were not retained).
"""
import argparse,json
from collections import deque
from pathlib import Path
from search import obtain,setup,evaluate
from cross_basin_poset import load,model_from_covers
from consensus_poset_feasibility import poset_arcs

ROOT=Path(__file__).resolve().parent

def longest_path(pos,dur,core):
    edges=[[] for _ in range(600)]
    degree=[0]*600
    def edge(a,b):
        edges[a].append(b);degree[b]+=1
    for j in range(30):
        for k in range(19):edge(j*20+k,j*20+k+1)
    for m,j,k in core:edge(j*20+pos[j][m],k*20+pos[k][m])
    q=deque(i for i in range(600) if degree[i]==0)
    start=[0]*600;seen=0;peak=0
    while q:
        u=q.popleft();seen+=1
        j=u//20;k=u%20;end=start[u]+dur[u]
        peak=max(peak,end)
        for v in edges[u]:
            start[v]=max(start[v],end)
            degree[v]-=1
            if degree[v]==0:q.append(v)
    assert seen==600
    return peak

def run(a):
    routes,rows,base=obtain();pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    parents=load(pos,dur,base)
    chosen=list(parents.values())
    names=list(parents)
    for i in range(1,a.nneutral+1):
        folder=ROOT/'results'/'iterative-poset-refinement'/('neutral-%02d'%i)
        proof=json.loads((folder/'upstream-verdict.json').read_text())
        assert proof['valid'] and int(proof['score'])==2006
        sol=json.loads((folder/'certificate.json').read_text())['machines']
        assert evaluate(sol,pos,dur)==2006
        chosen.append(sol);names.append('refinement-neutral-%d'%i)
    covers,info=poset_arcs(chosen)
    first=model_from_covers(covers,pos,dur,2005,True,15,4107)
    assert first['status']=='INFEASIBLE',first
    core=[covers[i] for i in first['core_indices']]
    hard=model_from_covers(core,pos,dur,2005,False,20,4154)
    assert hard['status']=='INFEASIBLE',hard
    output=dict(instance='ta41',target=2005,verified_2006_parent_names=names,
         parent_count=len(chosen),total_agreed_pairs=sum(x['agreed_pairwise_orders'] for x in info),
         total_cover_arcs=len(covers),core_count=len(core),
         independently_rebuilt_hard_2005_core_status=hard['status'],
         independent_precedence_only_longest_path=longest_path(pos,dur,core),
         no_overlap_essential_to_current_core_proof=True,
         full_machine_precedence_triples=[dict(machine=m,from_job=j,to_job=k) for m,j,k in core],
         source_seed=4107,
         scope='A newly extracted and independently hard-certified sufficient UNSAT core. A different sufficient core from the original run is possible; core minimality not proved.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(output,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in output.items()
                                if k!='full_machine_precedence_triples'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--nneutral',type=int,choices=[1,2],required=True)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
