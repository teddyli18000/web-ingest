#!/usr/bin/env python3
"""Core-replacement experiment after dynamic critical-path operation release.

Eight independently UNSAT-revalidated CP neighborhoods (240 ejected
operations each) have sufficient assumption cores of 59..95 pinned
machine precedences. Solve the EXACT set-cover over operation endpoints
with universe consisting of the eight SUFFICIENT (not minimal) cores.

A selected operation hits a core if it is an endpoint of any precedence in
that core. Releasing it invalidates *that one proof witness*, NOT the
underlying scheduling contradiction. Rebuild a fresh CP-SAT model with
every machine resource still NoOverlap and test whether a new sufficient
core appears.

Compare min-cover endpoint release with the SAME number of randomly chosen
nonreleased operations in every individual source subspace. This measures
obstruction *replacement* not makespan progress.

All claimed infeasibility core statuses are checked with hard, independent
NoOverlap submodels. UNKNOWN is not counted as infeasible.
"""
import argparse,json,random,time
from pathlib import Path
from collections import Counter
from search import obtain,setup,evaluate
from audit_dynamic_repair_cores import core_probe
from temporal_band_repair import fixed_precedence,check_band
ROOT=Path(__file__).resolve().parent
POLICIES=('dynamic','static','core','random')
PARENTS=('baseline','124')

def read_inputs():
    audit=json.loads((ROOT/'results'/'dcprcp-independent-core-audit.json').read_text())
    records=audit['records']
    assert len(records)==8 and all(x['status']=='INFEASIBLE' for x in records)
    assert [(x['parent'],x['policy']) for x in records]==[(p,m) for p in PARENTS for m in POLICIES]
    return records

def minimum_core_hitting_set(records):
    signatures={}
    for i,record in enumerate(records):
        for u,v in record['core_precedences']:
            signatures[u]=signatures.get(u,0)|(1<<i)
            signatures[v]=signatures.get(v,0)|(1<<i)
    assert len(signatures)>50
    states=1<<len(records)
    dp=[None]*states
    dp[0]=()
    for op,cover in sorted(signatures.items()):
        # DP over set union. Each operation is used at most once.
        previous=dp[:]
        for mask,selected in enumerate(previous):
            if selected is None:continue
            target=mask|cover
            proposed=selected+(op,)
            if dp[target] is None or len(proposed)<len(dp[target]) or (
              len(proposed)==len(dp[target]) and proposed<dp[target]):
                dp[target]=proposed
    chosen=dp[-1]
    assert chosen is not None and all(any(u in chosen or v in chosen for u,v in x['core_precedences']) for x in records)
    assert all(not any(u==op or v==op for u,v in records[i]['core_precedences'])
                   for i in range(len(records)) if not any(signatures[u]&(1<<i) for u in chosen))
    return chosen,signatures

def run(args):
    routes,rows,base=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    records=read_inputs()
    hinge,signatures=minimum_core_hitting_set(records)
    assert len(hinge)==2,hinge
    rng=random.Random(args.seed)
    outcomes=[]
    start=time.monotonic()
    for source in records:
        parent_name=source['parent'];policy=source['policy']
        parent=[row[:] for row in base]
        if parent_name!='baseline':
            folder=ROOT/'results'/'gateway-124'
            verifier=json.loads((folder/'upstream-verdict.json').read_text())
            assert verifier['valid'] and int(verifier['score'])==2006
            parent=json.loads((folder/'certificate.json').read_text())['machines']
            assert evaluate(parent,pos,dur)==2006
        p=ROOT/'results'/f'dcprcp-{parent_name}-{policy}-4107'/'dynamic-repair.json'
        older=json.loads(p.read_text())
        assert older['complete'] and older['rounds_completed']==8
        released=set(u for row in older['release_sets'] for u in row['released_this_round'])
        assert len(released)==240
        old_arcs=set(map(tuple,source['core_precedences']))
        assert old_arcs.issubset(set(fixed_precedence(parent,pos,released)))
        free=[op for op in range(600) if op not in released]
        selected=[op for op in hinge if op not in released]
        # If the globally chosen hinge is already released in this case,
        # add another high-hit-count operation to retain matched new release size.
        ranked=sorted(free,key=lambda op:(-sum(
            u==op or v==op for u,v in source['core_precedences']),op))
        for u in ranked:
            if len(selected)>=len(hinge):break
            if u not in selected:selected.append(u)
        assert len(selected)==2
        controls={'hinge':selected,'random':rng.sample(free,2)}
        case={'parent':parent_name,'policy':policy,
              'original_240_operation_core_size':source['sufficient_core_size'],
              'original_core_machine_count':source['distinct_core_machine_count'],
              'core_endpoint_count':len(set(sum(([u,v] for u,v in old_arcs),[]))),
              'interventions':{}}
        for strategy,extra in controls.items():
            newfree=released|set(extra)
            assert len(newfree)==242
            arcs=set(fixed_precedence(parent,pos,newfree))
            removed_core=old_arcs-arcs
            assert (strategy!='hinge') or removed_core,(
                 'hinge must invalidate original sufficient core',parent_name,policy)
            diagnosis=core_probe(pos,dur,parent,newfree,args.core_seconds)
            newcore=set(map(tuple,diagnosis.get('core_precedences',[])))
            if diagnosis['status']=='INFEASIBLE':
                assert newcore.issubset(arcs)
            record={
               'newly_released_operations':sorted(extra),
               'original_core_arcs_no_longer_fixed':len(removed_core),
               'original_core_broken':len(removed_core)>0,
               'old_assumption_core_size':len(old_arcs),
               'remaining_fixed_machine_arcs':len(arcs),
               'new_status':diagnosis['status'],
               'new_sufficient_unsat_core_size':diagnosis.get('sufficient_core_size'),
               'new_core_overlap_old_core_arcs':len(old_arcs&newcore),
               'new_core_novel_arc_count':len(newcore-old_arcs),
               'new_core_machine_count':diagnosis.get('distinct_core_machine_count'),
               'solver_seconds':diagnosis['seconds'],
            }
            # If old proof evaporates, test a fresh hard model with a
            # little more budget, but do NOT treat UNKNOWN as a witness.
            if diagnosis['status']!='INFEASIBLE':
                hard,cert=check_band(parent,pos,dur,list(arcs),args.hard_seconds,
                                     args.seed+len(outcomes))
                record['hard_oracle_status']=hard['status']
                if cert is not None:
                    score=evaluate(cert,pos,dur)
                    assert score is not None and score<=2005
                    record['verified_score']=score
                    args.out.parent.mkdir(parents=True,exist_ok=True)
                    (args.out.parent/f'hinge-improved-{parent_name}-{policy}-{strategy}.json').write_text(
                       json.dumps({'machines':cert},separators=(',',':'))+'\n')
            case['interventions'][strategy]=record
        outcomes.append(case)
        print('CASE',parent_name,policy,'old',len(old_arcs),
           'hinge',case['interventions']['hinge']['new_status'],
           'random',case['interventions']['random']['new_status'],flush=True)
    report={
      'instance':'ta41','baseline':2006,'target':2005,
      'question':'Do minimal source-core-hitting releases expose replacement CP conflicts?',
      'source_independent_unsat_cores':len(records),
      'source_core_sizes':[x['sufficient_core_size'] for x in records],
      'unique_core_endpoint_operations':len(signatures),
      'exact_minimum_hitting_set_operations':list(hinge),
      'hitting_set_minimal_cardinality':len(hinge),
      'hitting_set_method':'Exact 2^8 subset DP over operation-to-core endpoint incidence',
      'control':'Two random nonreleased operations from each matched 240-op source subspace',
      'tests':outcomes,
      'elapsed_seconds':round(time.monotonic()-start,3),
      'limits':'Hitting a particular UNSAT witness only removes that witness, not every possible reason for infeasibility. Each new CP core is sufficient not minimal; UNKNOWN proves nothing. These are 8 different conditioned subspaces.',
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({
      'chosen':list(hinge),'cases':len(outcomes),
      'hinge_statuses':Counter(o['interventions']['hinge']['new_status'] for o in outcomes),
      'random_statuses':Counter(o['interventions']['random']['new_status'] for o in outcomes),
      'elapsed_seconds':report['elapsed_seconds']},default=dict),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=ROOT/'results'/'dynamic-core-hinge-replacement.json')
    p.add_argument('--seed',type=int,default=202629)
    p.add_argument('--core-seconds',type=float,default=4)
    p.add_argument('--hard-seconds',type=float,default=9)
    run(p.parse_args())
