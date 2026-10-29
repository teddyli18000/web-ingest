#!/usr/bin/env python3
"""Exact pairwise-coordination lower bounds inside certified ta41 conflict cores.

A sufficient Cmax<=2005 UNSAT core means 'at least 1 of these machine
precedences must reverse'. This experiment tests a STRONGER claim:
must a target schedule reverse >=2, >=3, ... of these pairs TOGETHER?

Let f_i be the actual disjunctive orientation of machine pair i.
Build full hard job precedence and NoOverlap, put no restriction on any
other machine pairs, impose sum(f_i)<=k, and test Cmax<=2005.
INFEASIBLE => any <=2005 schedule must reverse >=k+1 pairs in that
specific certified core. UNKNOWN is not evidence either way.

For 'refined14', rebuild the new consensus core from all twelve
verified 2006 parents plus two new official neutral certificates, and
independently recheck its hard feasibility BEFORE using it.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from cross_basin_poset import load,model_from_covers
from consensus_poset_feasibility import poset_arcs

ROOT=Path(__file__).resolve().parent

def source_core(name,pos,dur,baseline,seed):
    if name=='old21':
        report=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
        assert report['status']=='INFEASIBLE' and len(report['proven_unsat_core'])==21
        return [(c['machine'],c['from_job'],c['to_job']) for c in report['proven_unsat_core']],dict(source='old five-parent consensus original 21',hard_recheck='previous certified')
    if name=='all12':
        report=json.loads((ROOT/'results'/'cross-poset-all12'/'intersection-analysis.json').read_text())
        assert report['certified_new_disjunction'] and report['independent_hard_core_revalidation']['status']=='INFEASIBLE'
        return [(c['machine'],c['from_job'],c['to_job']) for c in report['new_sufficient_unsat_core']],dict(source='all12 reconstructed and independently verified',hard_recheck='INFEASIBLE')
    if name=='refined14':
        parents=load(pos,dur,baseline)
        pool=list(parents.values())
        for index in (1,2):
            folder=ROOT/'results'/'iterative-poset-refinement'/('neutral-%02d'%index)
            verdict=json.loads((folder/'upstream-verdict.json').read_text())
            assert verdict['valid'] and int(verdict['score'])==2006
            orders=json.loads((folder/'certificate.json').read_text())['machines']
            assert evaluate(orders,pos,dur)==2006
            pool.append(orders)
        covers,_=poset_arcs(pool)
        query=model_from_covers(covers,pos,dur,2005,True,15,seed)
        assert query['status']=='INFEASIBLE',query
        core=[covers[i] for i in query['core_indices']]
        hard=model_from_covers(core,pos,dur,2005,False,20,seed+11)
        assert hard['status']=='INFEASIBLE',hard
        return core,dict(source='14 parent consensus replay',shared_cover_count=len(covers),
                         hard_recheck=hard['status'])
    raise ValueError(name)

def run(a):
    routes,rows,baseline=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(baseline,pos,dur)==2006
    core,provenance=source_core(a.core,pos,dur,baseline,a.seed)
    for m,j,k in core:
        assert baseline[m].index(j)<baseline[m].index(k),(m,j,k)
    cp=cp_model.CpModel()
    s=[cp.new_int_var(0,2005,'start_%d'%i) for i in range(600)]
    e=[cp.new_int_var(0,2005,'end_%d'%i) for i in range(600)]
    iv=[cp.new_interval_var(s[i],dur[i],e[i],'op_%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):cp.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        cp.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    flips=[]
    for idx,(m,j,k) in enumerate(core):
        u=j*20+pos[j][m];v=k*20+pos[k][m]
        bit=cp.new_bool_var('core_pair_flipped_%d'%idx)
        cp.add(s[v]>=e[u]).only_enforce_if(bit.Not())
        cp.add(s[u]>=e[v]).only_enforce_if(bit)
        flips.append(bit)
    cp.add(sum(flips)<=a.max_flips)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=a.seed
    t=time.monotonic();status=solver.solve(cp)
    report=dict(instance='ta41',baseline=2006,target=2005,
       chosen_core=a.core,core_provenance=provenance,
       core_arcs=[dict(machine=m,from_job=j,to_job=k) for m,j,k in core],
       core_size=len(core),max_core_pair_reversals=a.max_flips,
       status=solver.status_name(status),
       elapsed_seconds=round(time.monotonic()-t,3),
       conflicts=solver.num_conflicts,branches=solver.num_branches,
       independent_full_NoOverlap=True,
       all_other_machine_precedences_unrestricted=True,
       conditional_theorem=('If INFEASIBLE, any Cmax<=2005 schedule must reverse at least %d of these exact core pairwise machine relations.'%(a.max_flips+1)),
       no_unqualified_claim_if_unknown=True)
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        orders=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]])) for m in range(20)]
        score=evaluate(orders,pos,dur)
        assert score is not None and score<=2005
        actually_flipped=sum(orders[m].index(j)>orders[m].index(k) for m,j,k in core)
        assert actually_flipped==sum(solver.value(x) for x in flips)<=a.max_flips
        report['verified_score']=score
        report['verified_core_reversals']=actually_flipped
        (a.out/'certificate.json').write_text(json.dumps({'machines':orders},separators=(',',':'))+'\n')
    (a.out/'cardinality-core-decision.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='core_arcs'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--core',choices=['old21','all12','refined14'],required=True)
    p.add_argument('--max-flips',type=int,required=True)
    p.add_argument('--seconds',type=float,default=130)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
