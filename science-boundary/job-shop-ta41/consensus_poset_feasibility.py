#!/usr/bin/env python3
"""Recombine several verified 2006 job-shop schedules by their common poset.

Given K independently verified makespan-2006 parents, retain only those
pairwise same-machine job precedences on which ALL K parents agree. This
intersection partial order (a permutation poset) is strictly more general
than machine-wise A/B crossover: new schedules may interleave jobs in
ways neither parent ever did.

All 20 NoOverlap machines and all 600 exact operations are still hard.
We solve the <=2005 full-resource feasibility problem. If infeasible,
extract a sufficient UNSAT core of *consensus precedence covers*, exposing
a small shared interface that must be broken to beat every parent.
No UNKNOWN is ever claimed as a certificate.
"""
import argparse,json,time
from collections import deque
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate

def get_parents(names,baseline,pos,dur):
    result=[]
    root=Path(__file__).parent/'results'
    for name in names:
        if name=='baseline':
            orders=baseline
        else:
            d=root/('neutral-'+name)
            orders=json.loads((d/'neutral-certificate.json').read_text())['machines']
            v=json.loads((d/'neutral-verdict.json').read_text())
            assert v['valid'] and int(v['score'])==2006,(name,v)
        assert evaluate(orders,pos,dur)==2006
        result.append(orders)
    return result

def poset_arcs(parents):
    arcs=[];machine_info=[]
    for m in range(20):
        ranks=[{job:idx for idx,job in enumerate(parent[m])} for parent in parents]
        comparable={(a,b) for a in range(30) for b in range(30) if a!=b
                    and all(p[a]<p[b] for p in ranks)}
        covers=[]
        for a,b in sorted(comparable):
            # Covers: there is no w strictly between a and b in
            # every parent ordering.
            if not any((a,w) in comparable and (w,b) in comparable
                       for w in range(30)):
                covers.append((a,b))
        graph=[[] for _ in range(30)]
        for a,b in covers:graph[a].append(b)
        # Exhaustively certify that the cover edges preserve EXACTLY
        # the parent-intersection poset (no omitted or extra comparisons).
        derived=set()
        for j in range(30):
            seen=set();stack=[j]
            while stack:
                u=stack.pop()
                for v in graph[u]:
                    if v not in seen:seen.add(v);stack.append(v)
            for v in seen:derived.add((j,v))
        assert derived==comparable,(m,len(derived),len(comparable))
        arcs.extend([(m,a,b) for a,b in covers])
        discordant=435-len(comparable)
        machine_info.append(dict(machine=m,cover_arcs=len(covers),
                                 agreed_pairwise_orders=len(comparable),
                                 free_pairwise_orders=discordant))
    return arcs,machine_info

def run(a):
    routes,ds,baseline=obtain()
    pos,duration=setup(routes,ds)
    parents=get_parents(a.parents,baseline,pos,duration)
    edges,details=poset_arcs(parents)
    T=2005;model=cp_model.CpModel()
    s=[model.new_int_var(0,T,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,T,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],duration[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    bits=[];id_to_core={}
    for idx,(m,j,h) in enumerate(edges):
        keep=model.new_bool_var('keep_%d_%d_%d'%(m,j,h))
        model.add(s[h*20+pos[h][m]]>=e[j*20+pos[j][m]]).only_enforce_if(keep)
        bits.append(keep);id_to_core[keep.index]=idx
    model.add_assumptions(bits)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=1  # exact assumption-core support
    solver.parameters.random_seed=a.seed
    start=time.monotonic()
    status=solver.solve(model)
    report=dict(
        instance='ta41',target=2005,parents=a.parents,
        all_parents_independently_verified_2006=True,
        fixed_consensus_poset_cover_arcs=len(edges),
        total_agreed_pairwise_machine_orders=sum(x['agreed_pairwise_orders'] for x in details),
        total_discordant_pairwise_machine_orders=sum(x['free_pairwise_orders'] for x in details),
        per_machine=details,
        full_NoOverlap_and_job_precedences=True,
        status=solver.status_name(status),
        seconds=round(time.monotonic()-start,3),
        conflicts=solver.num_conflicts,
        branches=solver.num_branches,
        proven_unsat_core=[],
        proof_scope='INFEASIBLE means no <=2005 schedule can preserve all pairwise order relations shared by every parent; UNKNOWN proves nothing. A sufficient core of cover arcs pinpoints what all candidate schedules must violate.'
    )
    a.out.mkdir(parents=True,exist_ok=True)
    if status==cp_model.INFEASIBLE:
        core=[id_to_core[x] for x in solver.sufficient_assumptions_for_infeasibility()]
        assert core and all(0<=j<len(edges) for j in core)
        report['proven_unsat_core']=[dict(machine=edges[j][0],from_job=edges[j][1],
                                        to_job=edges[j][2],index=j) for j in core]
        report['unsat_core_size']=len(core)
        report['unsat_core_distinct_machines']=len(set(edges[j][0] for j in core))
    elif status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        orders=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
                for m in range(20)]
        score=evaluate(orders,pos,duration)
        assert score is not None and score<=T,score
        report['independent_dag_score']=score
        (a.out/'certificate.json').write_text(json.dumps({'machines':orders},separators=(',',':'))+'\n')
    (a.out/'consensus-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items()
                               if k not in ('per_machine','proven_unsat_core')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parents',nargs='+',required=True)
    p.add_argument('--seconds',type=float,default=220)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
