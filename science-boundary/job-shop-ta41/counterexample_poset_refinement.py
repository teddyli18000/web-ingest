#!/usr/bin/env python3
"""Counterexample-guided refinement of ta41 2006 neutral *orientation basins*.

Run an active constraint-generation loop:
(1) a 2005 conditional CP model proves that a shared machine partial
    order among existing verified 2006 parents is insufficient.
(2) Independently rebuild the hard-core NoOverlap model, and extract a
    necessary disjunction: at least one common machine order must reverse.
(3) In a globally complete soft orientation model (no frozen survivor
    machine orders), enforce all nine prior certified no-2005 conflict
    cuts plus newly learned necessary disjunctions, objective makespan
    first, closeness to current incumbent second, and produce an actual
    2006-or-better counterexample schedule.
(4) Add the new 2006 schedule as a parent and RECOMPUTE the intersection
    poset. Repeat only while new valid neutral parents and cores appear.

This representation can change all 8700 machine pair orientations jointly,
unlike earlier fixed-survivor release neighborhoods. UNKNOWN is never UNSAT.
An official <=2005 certificate is required for breakthrough publication.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis
from cross_basin_poset import load,model_from_covers
from consensus_poset_feasibility import poset_arcs
from all_core_orientation_repair import source_cuts

ROOT=Path(__file__).resolve().parent

def all_prior_cuts(pos):
    prior,consensus=source_cuts()
    prior.append(('consensus21',[(z['from_job']*20+pos[z['from_job']][z['machine']],
                              z['to_job']*20+pos[z['to_job']][z['machine']])
                              for z in consensus]))
    assert len(prior)==9
    return [(label,list(ordered)) for label,ordered in prior]

def ops_from_machine_core(core,pos):
    return [(j*20+pos[j][m],k*20+pos[k][m]) for m,j,k in core]

def guided_full_schedule(pos,dur,baseline,parent,cuts,seconds,seed):
    cp=cp_model.CpModel()
    start=[cp.new_int_var(0,2006,f's{i}') for i in range(600)]
    end=[cp.new_int_var(0,2006,f'e{i}') for i in range(600)]
    iv=[cp.new_interval_var(start[i],dur[i],end[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            cp.add(start[j*20+k+1]>=end[j*20+k])
    for m in range(20):
        cp.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    machine_of=[-1]*600
    for j in range(30):
        for m in range(20):machine_of[j*20+pos[j][m]]=m
    pairs={}
    def before(u,v):
        assert u!=v and machine_of[u]==machine_of[v] and u//20!=v//20
        m=machine_of[u];a,b=sorted((u//20,v//20))
        key=(m,a,b)
        if key not in pairs:
            bit=cp.new_bool_var('before_%d_%d_%d'%key)
            x=a*20+pos[a][m];y=b*20+pos[b][m]
            cp.add(start[y]>=end[x]).only_enforce_if(bit)
            cp.add(start[x]>=end[y]).only_enforce_if(bit.Not())
            pairs[key]=bit
        return pairs[key] if u//20==a else pairs[key].Not()
    for label,arcs in cuts:
        assert arcs,label
        cp.add(sum(before(u,v).Not() for u,v in arcs)>=1)
    # Require the certified >=15 changed machine orders condition.
    switched=[]
    for m in range(20):
        seq=baseline[m]
        changes=[before(j*20+pos[j][m],k*20+pos[k][m]).Not()
                 for j,k in zip(seq,seq[1:])]
        active=cp.new_bool_var('changed_machine_%d'%m)
        cp.add_max_equality(active,changes)
        switched.append(active)
    cp.add(sum(switched)>=15)
    # Build an objective around a fully verified neutral parent; no pair is fixed.
    # All new cuts are necessary for <=2005. The 2006 neutral may need to
    # violate each cut as a deliberate way of crossing into a new basin.
    proximity=[]
    for m in range(20):
        for a,b in zip(parent[m],parent[m][1:]):
            proximity.append(before(a*20+pos[a][m],b*20+pos[b][m]).Not())
    C=cp.new_int_var(0,2006,'Cmax')
    cp.add_max_equality(C,end)
    cp.minimize(100000*C+sum(proximity))
    _,times,_,score=graph_analysis(parent,pos,dur)
    assert score==2006
    for i in range(600):
        cp.add_hint(start[i],times[i])
        cp.add_hint(end[i],times[i]+dur[i])
    cp.add_hint(C,2006)
    for (m,j,k),bit in pairs.items():
        ranks={x:i for i,x in enumerate(parent[m])}
        cp.add_hint(bit,int(ranks[j]<ranks[k]))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=4
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.random_seed=seed
    t=time.monotonic()
    status=solver.solve(cp)
    report=dict(status=solver.status_name(status),
       elapsed_seconds=round(time.monotonic()-t,3),
       objective_bound=solver.best_objective_bound,
       conflicts=solver.num_conflicts,branches=solver.num_branches,
       exact_resource_constraints=True,
       number_of_necessary_cuts=len(cuts),
       no_hard_survivor_order_freezing=True)
    candidate=None
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        candidate=[sorted(range(30),key=lambda j:solver.value(start[j*20+pos[j][m]]))
                   for m in range(20)]
        val=evaluate(candidate,pos,dur)
        assert val is not None and val<=2006,val
        report['independent_DAG_score']=val
        for label,arc in cuts:
            assert any(candidate[machine_of[u]].index(u//20)>
                       candidate[machine_of[u]].index(v//20) for u,v in arc),label
        report['verified_all_necessary_cuts']=True
        report['changed_machines_vs_original']=sum(candidate[m]!=baseline[m] for m in range(20))
        assert report['changed_machines_vs_original']>=15
        report['new_machine_order_distance_from_reference_parent']=sum(candidate[m]!=parent[m] for m in range(20))
    return report,candidate

def main(a):
    routes,rows,base=obtain();pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    sources=load(pos,dur,base)
    parents=[sources[name] for name in sources]
    source_labels=list(sources)
    cuts=all_prior_cuts(pos)
    a.out.mkdir(parents=True,exist_ok=True)
    # Seed new 2005 necessary disjunction from independently verified
    # 12-parent core which is currently preserved by ALL 12 schedules.
    prior=json.loads((ROOT/'results'/'cross-poset-all12'/'intersection-analysis.json').read_text())
    assert prior['certified_new_disjunction'] and prior['independent_hard_core_revalidation']['status']=='INFEASIBLE'
    new=[(z['machine'],z['from_job'],z['to_job']) for z in prior['new_sufficient_unsat_core']]
    cuts.append(('intersection12',ops_from_machine_core(new,pos)))
    current=sources['ninecore']
    report=dict(instance='ta41',baseline=2006,target=2005,
       method='counterexample-guided refinement of consensus posets with all-pair soft orientations',
       starting_verified_parent_names=source_labels,
       initial_nine_prior_core_cuts=9,
       initial_new_intersection_core_size=len(new),
       first_cut_hard_2005_independently_verified=True,
       cycles=[],witness_count=0,
       final_score=2006,
       note='NoOverlaps and job routes are hard. Only genuine solver-INFEASIBLE hard-verified poset cores become new necessary cuts. UNKNOWN never denotes exclusion.')
    def save():
        report['witness_count']=sum(int(c.get('new_valid_parent',False)) for c in report['cycles'])
        (a.out/'iteration.json').write_text(json.dumps(report,indent=2)+'\n')
    for roundno in range(1,a.rounds+1):
        step={'round':roundno,'current_parents':len(parents),
              'total_required_core_disjunctions':len(cuts)}
        info,newparent=guided_full_schedule(pos,dur,base,current,cuts,a.solve_seconds,a.seed+roundno*11)
        step['globally_complete_oriented_CP']=info
        if newparent is None:
            step['new_valid_parent']=False
            report['cycles'].append(step);save()
            break
        value=info['independent_DAG_score']
        dirname=a.out/('neutral-%02d'%roundno)
        dirname.mkdir(parents=True,exist_ok=True)
        (dirname/'certificate.json').write_text(json.dumps({'machines':newparent},separators=(',',':'))+'\n')
        if value<=2005:
            report['final_score']=value
            (a.out/'certificate.json').write_text(json.dumps({'machines':newparent},separators=(',',':'))+'\n')
            step['found_improvement']=True
            report['cycles'].append(step);save()
            break
        assert newparent not in parents
        parents.append(newparent)
        step['new_valid_parent']=True
        step['new_parent_score']=2006
        covers,per=poset_arcs(parents)
        step['post_refinement_common_pairwise_orders']=sum(x['agreed_pairwise_orders'] for x in per)
        step['post_refinement_shared_cover_arcs']=len(covers)
        target=model_from_covers(covers,pos,dur,2005,True,a.core_seconds,a.seed+roundno*79)
        step['next_consensus_2005_oracle']={k:v for k,v in target.items()
              if k not in ('machine_orders','core_indices')}
        if 'machine_orders' in target:
            possible=target['machine_orders']
            assert evaluate(possible,pos,dur)<=2005
            (a.out/'certificate.json').write_text(json.dumps({'machines':possible},separators=(',',':'))+'\n')
            report['final_score']=evaluate(possible,pos,dur)
            step['found_improvement_in_poset']=True
            report['cycles'].append(step);save()
            break
        if target['status']=='INFEASIBLE':
            members=[covers[i] for i in target['core_indices']]
            verify=model_from_covers(members,pos,dur,2005,False,a.recheck_seconds,a.seed+roundno*13)
            step['next_consensus_independent_core_check']={k:v for k,v in verify.items()
              if k!='machine_orders'}
            step['next_consensus_core_size']=len(members)
            if verify['status']=='INFEASIBLE':
                label='new_intersection_%d'%roundno
                cuts.append((label,ops_from_machine_core(members,pos)))
                step['new_independently_certified_necessary_cut']=label
            else:
                step['next_core_not_independently_certified']=True
        report['cycles'].append(step)
        save()
        current=newparent
        print('ITERATION',roundno, 'neutral new 2006','consensus',target['status'],
              'certified cuts',len(cuts),flush=True)
        if target['status']!='INFEASIBLE':break
    save()
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='cycles'}),
          flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--rounds',type=int,default=2)
    p.add_argument('--solve-seconds',type=float,default=150)
    p.add_argument('--core-seconds',type=float,default=55)
    p.add_argument('--recheck-seconds',type=float,default=35)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
