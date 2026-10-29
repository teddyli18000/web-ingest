#!/usr/bin/env python3
"""Check whether MAX-MIN neutral 2006 schedules break the old frozen poset.

The two new schedules were *officially* verified as valid Cmax=2006 and
have minimum Kendall distances 147 and 141 from the prior 12-member
solution ensemble. Recompute the EXACT 8700 pairwise consensus after
admitting them; then independently test whether Cmax<=2005 is possible
while keeping the remaining common partial order.

INFEASIBLE => new sufficient resource-conflict core, independently
rechecked as a separate hard-NoOverlap interval model.
UNKNOWN => no exclusion; FEASIBLE => official Few Shots verifier required.
This tests whether the new representation truly changes the obstruction.
"""
import argparse,json
from pathlib import Path
from search import obtain,setup,evaluate
from consensus_poset_feasibility import poset_arcs
from cross_basin_poset import load,model_from_covers

ROOT=Path(__file__).resolve().parent

def far_parent(mode,pos,dur):
    folder=ROOT/'results'/('orientation-maxmin-'+mode)
    v=json.loads((folder/'witness'/'upstream-verdict.json').read_text())
    assert v['valid'] and int(v['score'])==2006,v
    p=json.loads((folder/'witness'/'certificate.json').read_text())['machines']
    assert evaluate(p,pos,dur)==2006
    return p

def run(a):
    routes,rows,base=obtain();pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    parents=load(pos,dur,base)
    keys=list(parents)
    ensemble=list(parents.values())
    if a.family in ('farA','both','all16'):
        ensemble.append(far_parent('false',pos,dur));keys.append('farA')
    if a.family in ('farB','both','all16'):
        ensemble.append(far_parent('true',pos,dur));keys.append('farB')
    if a.family=='all16':
        for i in (1,2):
            folder=ROOT/'results'/'iterative-poset-refinement'/('neutral-%02d'%i)
            proof=json.loads((folder/'upstream-verdict.json').read_text())
            assert proof['valid'] and int(proof['score'])==2006
            orders=json.loads((folder/'certificate.json').read_text())['machines']
            assert evaluate(orders,pos,dur)==2006
            ensemble.append(orders);keys.append('near%d'%i)
    covers,details=poset_arcs(ensemble)
    old=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    oldcore=old['proven_unsat_core']
    rank=[{m:{j:i for i,j in enumerate(p[m])} for m in range(20)} for p in ensemble]
    old_still_common=sum(all(s[c['machine']][c['from_job']]<s[c['machine']][c['to_job']]
                             for s in rank) for c in oldcore)
    data=dict(instance='ta41',baseline_score=2006,target=2005,
        family=a.family,verified_parents=keys,
        all_parent_schedules_officially_verified_2006=True,
        shared_pairwise_machine_precedences=sum(z['agreed_pairwise_orders'] for z in details),
        now_discordant_pairs=sum(z['free_pairwise_orders'] for z in details),
        poset_cover_arcs=len(covers),
        previously_certified_21_core_relations_still_common=old_still_common,
        source='Two new max-min orientation diverse schedule certificates at Cmax 2006.')
    a.out.mkdir(parents=True,exist_ok=True)
    res=model_from_covers(covers,pos,dur,2005,True,a.seconds,a.seed)
    candidate=res.pop('machine_orders',None)
    ids=res.pop('core_indices',[])
    data['target_2005_consensus_oracle']=res
    if ids:
        core=[covers[i] for i in ids]
        data['sufficient_core_pairs']=[dict(machine=m,from_job=j,to_job=k) for m,j,k in core]
        data['sufficient_core_size']=len(core)
        proof=model_from_covers(core,pos,dur,2005,False,a.hard_seconds,a.seed+121)
        assert 'machine_orders' not in proof or proof['status']!='INFEASIBLE'
        data['independent_hard_no_overlap_core_verification']={k:v for k,v in proof.items() if k!='machine_orders'}
        data['new_necessary_cut_certified']=(proof['status']=='INFEASIBLE')
    if candidate:
        assert evaluate(candidate,pos,dur)<=2005
        (a.out/'certificate.json').write_text(json.dumps({'machines':candidate},separators=(',',':'))+'\n')
        data['found_possible_record']=True
    else:data['found_possible_record']=False
    (a.out/'diverse-poset.json').write_text(json.dumps(data,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in data.items() if k!='sufficient_core_pairs'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--family',choices=['farA','farB','both','all16'],required=True)
    p.add_argument('--seconds',type=float,default=135)
    p.add_argument('--hard-seconds',type=float,default=40)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
