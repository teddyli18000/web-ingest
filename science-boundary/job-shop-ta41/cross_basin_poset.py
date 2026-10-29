#!/usr/bin/env python3
"""Multi-parent consensus posets to discover new NECESSARY ta41 2005 orientations.

Unlike previous static release neighborhoods, these parent intersections
are constructed from independently verified, *distant and core-crossing*
score-2006 schedules. Retain ONLY machine-pair precedences common to every
parent. Exact full job and NoOverlap constraints remain hard.

At target 2005:
  INFEASIBLE => at least one retained consensus cover arc must reverse.
  Extract a sufficient assumption UNSAT core and INDEPENDENTLY verify it
  with a separate hard-precedence interval model before accepting the cut.
  UNKNOWN => no exclusion proved. FEASIBLE => independently score and
  preserve a machine-order certificate for the Few Shots official grader.

This is a new layer of constraints after crossing nine previously
certified cuts; it is not a global makespan lower bound.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from consensus_poset_feasibility import poset_arcs

ROOT=Path(__file__).resolve().parent

SOURCES={
 'baseline':None,
 'critical8':('neutral-critical8','neutral-certificate.json','neutral-verdict.json'),
 'mixed12':('neutral-mixed12','neutral-certificate.json','neutral-verdict.json'),
 'mixed16':('neutral-mixed16','neutral-certificate.json','neutral-verdict.json'),
 'mixed20':('neutral-mixed20','neutral-certificate.json','neutral-verdict.json'),
 'gate120':('gateway-120','certificate.json','upstream-verdict.json'),
 'gate124':('gateway-124','certificate.json','upstream-verdict.json'),
 'gate127':('gateway-127','certificate.json','upstream-verdict.json'),
 'rev5':('warm-backbone-5','neutral-certificate.json','best-verdict.json'),
 'rev6':('warm-backbone-6','neutral-certificate.json','best-verdict.json'),
 'rev7':('continuation-7','neutral-certificate.json','best-verdict.json'),
 'ninecore':('ninecore-neutral-baseline','neutral-certificate.json','neutral-verdict.json'),
}
OLD=['baseline','critical8','mixed12','mixed16','mixed20']
SETS={
 'oldplusnine':OLD+['ninecore'],
 'gateways':['baseline','gate120','gate124','gate127','ninecore'],
 'oldnew':OLD+['gate120','gate124','gate127','ninecore'],
 'all12':list(SOURCES),
 'diverse7':None,
}

def load(pos,dur,baseline):
    result={}
    for name,ref in SOURCES.items():
        if ref is None:
            orders=baseline
        else:
            folder,certificate,verdict=ref
            d=ROOT/'results'/folder
            proof=json.loads((d/verdict).read_text())
            assert proof['valid'] and int(proof['score'])==2006,(name,proof)
            orders=json.loads((d/certificate).read_text())['machines']
        assert evaluate(orders,pos,dur)==2006,name
        assert len(orders)==20 and all(sorted(z)==list(range(30)) for z in orders)
        result[name]=orders
    return result

def reversed_orientations(orders,base):
    mask=set()
    for m in range(20):
        prior={j:i for i,j in enumerate(base[m])}
        for a in range(30):
            for b in range(a+1,30):
                if (prior[a]<prior[b])!=(orders[m].index(a)<orders[m].index(b)):
                    mask.add((m,a,b))
    return mask

def select(names,parents):
    if names!='diverse7':return SETS[names]
    original=parents['baseline']
    reversed_sets={name:reversed_orientations(orders,original)
                   for name,orders in parents.items()}
    chosen=['baseline'];covered=set()
    while len(chosen)<7:
        candidates=[name for name in SOURCES if name not in chosen]
        name=max(candidates,key=lambda n:(len(reversed_sets[n]-covered),n))
        chosen.append(name);covered.update(reversed_sets[name])
    return chosen

def model_from_covers(covers,pos,dur,T,assumptions,seconds,seed):
    cp=cp_model.CpModel()
    starts=[cp.new_int_var(0,T,'s%d'%i) for i in range(600)]
    ends=[cp.new_int_var(0,T,'e%d'%i) for i in range(600)]
    intervals=[cp.new_interval_var(starts[i],dur[i],ends[i],'i%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):cp.add(starts[j*20+k+1]>=ends[j*20+k])
    for m in range(20):
        cp.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    mapping={}
    for index,(m,a,b) in enumerate(covers):
        u=a*20+pos[a][m];v=b*20+pos[b][m]
        if assumptions:
            bit=cp.new_bool_var('keep%d'%index)
            cp.add(starts[v]>=ends[u]).only_enforce_if(bit)
            cp.add_assumption(bit)
            mapping[bit.index]=index
        else:
            cp.add(starts[v]>=ends[u])
    solver=cp_model.CpSolver()
    solver.parameters.random_seed=seed
    solver.parameters.num_search_workers=1 if assumptions else 4
    solver.parameters.max_time_in_seconds=seconds
    t=time.monotonic();status=solver.solve(cp)
    data=dict(status=solver.status_name(status),
              elapsed_seconds=round(time.monotonic()-t,3),
              conflicts=solver.num_conflicts,branches=solver.num_branches,
              intervals=600,full_no_overlap=True,hard_consensus_arcs=len(covers))
    if status==cp_model.INFEASIBLE and assumptions:
        ids=solver.sufficient_assumptions_for_infeasibility()
        assert ids and all(x in mapping for x in ids),ids
        data['core_indices']=[mapping[x] for x in ids]
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        orders=[sorted(range(30),key=lambda j:solver.value(starts[j*20+pos[j][m]]))
                for m in range(20)]
        score=evaluate(orders,pos,dur)
        assert score is not None and score<=T,score
        data['independently_verified_DAG_score']=score
        data['machine_orders']=orders
    return data

def run(a):
    routes,rows,base=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    parents=load(pos,dur,base)
    chosen=select(a.cohort,parents)
    covers,details=poset_arcs([parents[name] for name in chosen])
    old=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    oldcore={(z['machine'],z['from_job'],z['to_job']) for z in old['proven_unsat_core']}
    consensus_set=set(covers)
    report=dict(instance='ta41',baseline_score=2006,target=2005,
        cohort=a.cohort,parents=chosen,total_known_parent_count=len(parents),
        retained_cover_precedences=len(covers),
        retained_consensus_pairwise_precedences=sum(x['agreed_pairwise_orders'] for x in details),
        released_disagreements=sum(x['free_pairwise_orders'] for x in details),
        existing_21_core_edges_still_fixed=sum(e in consensus_set for e in oldcore),
        per_machine_poset=details,
        independent_hard_core_revalidation=None,
        inference='A fresh unsat consensus-core proves at least one retained arc must reverse for any <=2005 schedule. It is a necessary disjunction, not a construction.')
    a.out.mkdir(parents=True,exist_ok=True)
    search=model_from_covers(covers,pos,dur,2005,True,a.seconds,a.seed)
    orders=search.pop('machine_orders',None)
    ids=search.pop('core_indices',[])
    report['initial_oracle']=search
    if ids:
        newcore=[covers[i] for i in ids]
        report['new_sufficient_unsat_core']=[dict(machine=m,from_job=j,to_job=k)
                                            for m,j,k in newcore]
        report['new_core_size']=len(newcore)
        report['new_core_overlap_with_prior21']=len(oldcore.intersection(newcore))
        # Independent model: no assumption literals, rebuild hard precedence
        hard=model_from_covers(newcore,pos,dur,2005,False,a.recheck_seconds,a.seed+17)
        if 'machine_orders' in hard:
            report['unexpected_verification_candidate']=hard.pop('machine_orders')
        report['independent_hard_core_revalidation']=hard
        report['certified_new_disjunction']=(hard['status']=='INFEASIBLE')
    if orders:
        (a.out/'certificate.json').write_text(
            json.dumps({'machines':orders},separators=(',',':'))+'\n')
        report['found_candidate']=True
    else:report['found_candidate']=False
    (a.out/'intersection-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items()
                               if k not in ('per_machine_poset','new_sufficient_unsat_core')}),
          flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cohort',choices=sorted(SETS),required=True)
    p.add_argument('--seconds',type=float,default=190)
    p.add_argument('--recheck-seconds',type=float,default=70)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
