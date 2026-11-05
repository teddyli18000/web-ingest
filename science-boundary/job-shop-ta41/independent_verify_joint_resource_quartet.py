#!/usr/bin/env python3
"""Independent verifier and dynamic-UNSAT-core trace for a *real improving* ta43.

Read a 20-second genuine N7 elite independently scored 1888 and a new,
fully specified 1887 machine order found by global joint CP repair.

(1) Independently rebuild all 600 job-chain + 580 machine-adjacent arcs
    and recompute both makespans via a fresh Kahn DAG evaluator.
(2) For ALL 16 subsets of four reversed incumbent adjacent arcs, use a
    fresh hard NoOverlap model and CP assumptions on retained arcs. An
    INFEASIBLE core is a certified precompletion disjunction.
(3) For each strict subset, independently rebuild the CP model using ONLY
    its extracted core arcs to check sufficiency: this audits the core
    as a real resource obstruction, not merely a solver diagnostic.
(4) Check each core intersects the known (but withheld from original
    search) still-unreleased improvement arcs, using the witness only
    in this post-hoc explanation study.

Important: restricting all OTHER 576 incumbent adjacent arcs is essential
to the four-arc minimality claim. The 2018 IEBO and classical CP edge
finding are prior art. No universal ta41 breakthrough is claimed.
"""
from pathlib import Path
import argparse,json,time
from collections import deque,Counter
from itertools import combinations
from ortools.sat.python import cp_model

ROOT=Path(__file__).resolve().parent

def read_example():
    vals=list(map(int,(ROOT/'positive-n7-elite-data'/'ta43js-n7elite1711'/'start.txt').read_text().split()))
    assert vals[:2]==[30,20] and len(vals)==1802
    rr=vals[2:1202]
    routes=[[rr[2*(j*20+k)] for k in range(20)] for j in range(30)]
    rows=[[rr[2*(j*20+k)+1] for k in range(20)] for j in range(30)]
    pos=[[0]*20 for j in range(30)]
    dur=[0]*600
    for j in range(30):
        assert sorted(routes[j])==list(range(20))
        for k,m in enumerate(routes[j]):
            pos[j][m]=k
            dur[j*20+k]=rows[j][k]
    sequence=vals[1202:]
    before=[sequence[m*30:(m+1)*30] for m in range(20)]
    after=json.loads((ROOT/'results'/'joint-global-ta43js-n7elite1711-static'/'certificate.json').read_text())['machines']
    assert len(after)==20 and all(sorted(x)==list(range(30)) for x in after)
    return before,after,pos,dur

def independent_score(orders,pos,dur):
    succ=[[] for _ in range(600)]
    deg=[0]*600
    for j in range(30):
        for k in range(19):
            u=j*20+k;v=u+1
            succ[u].append(v);deg[v]+=1
    for m,row in enumerate(orders):
        assert sorted(row)==list(range(30))
        for a,b in zip(row,row[1:]):
            u=a*20+pos[a][m];v=b*20+pos[b][m]
            succ[u].append(v);deg[v]+=1
    ready=deque(u for u in range(600) if deg[u]==0)
    earliest=[0]*600
    consumed=0;maximum=0
    while ready:
        u=ready.popleft()
        consumed+=1
        finish=earliest[u]+dur[u]
        if finish>maximum:maximum=finish
        for v in succ[u]:
            earliest[v]=max(earliest[v],finish)
            deg[v]-=1
            if deg[v]==0:ready.append(v)
    return maximum if consumed==600 else None

def oriented_pairs(before,after):
    arr=[]
    for m in range(20):
        p={j:i for i,j in enumerate(after[m])}
        for k,(a,b) in enumerate(zip(before[m],before[m][1:])):
            if p[a]>p[b]:arr.append(m*29+k)
    return arr

def cp_check(before,pos,dur,L,released=None,only=None,seconds=2.0):
    # Fresh, explicit NoOverlap and resource precedences; no call to
    # any production search/repair model.
    model=cp_model.CpModel()
    s=[model.new_int_var(0,L,f'st{i}') for i in range(600)]
    e=[model.new_int_var(0,L,f'en{i}') for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    active=[]
    for m,seq in enumerate(before):
        for k,(a,b) in enumerate(zip(seq,seq[1:])):
            i=m*29+k
            if only is not None and i not in only:continue
            if released is not None and i in released:continue
            u=a*20+pos[a][m]
            v=b*20+pos[b][m]
            if only is not None:
                model.add(s[v]>=e[u])
            else:
                bit=model.new_bool_var(f'pin_{i}')
                model.add(s[v]>=e[u]).only_enforce_if(bit)
                model.add_assumption(bit)
                active.append((bit.index,i))
    t=time.monotonic()
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.max_time_in_seconds=seconds
    status=solver.solve(model)
    report=dict(status=solver.status_name(status),seconds=round(time.monotonic()-t,3))
    if status==cp_model.INFEASIBLE and only is None:
        mp=dict(active)
        literals=solver.sufficient_assumptions_for_infeasibility()
        assert literals and all(i in mp for i in literals)
        report['core_arcs']=sorted(mp[x] for x in literals)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        orders=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
                for m in range(20)]
        report['independent_score']=independent_score(orders,pos,dur)
        assert report['independent_score'] is not None and report['independent_score']<=L
    return report

def run(a):
    before,after,pos,dur=read_example()
    incumbent=independent_score(before,pos,dur)
    improvement=independent_score(after,pos,dur)
    assert incumbent==1888 and improvement==1887
    actual=oriented_pairs(before,after)
    assert len(actual)==4
    checks=[]
    for size in range(5):
        for subset in combinations(actual,size):
            remaining=set(actual)-set(subset)
            result=cp_check(before,pos,dur,1887,set(subset),seconds=a.seconds)
            record=dict(released=list(subset),retained_target_change_arcs=sorted(remaining),
                        status=result['status'],seconds=result['seconds'])
            if size<4:
                assert result['status']=='INFEASIBLE',record
                core=result['core_arcs']
                assert set(core).intersection(remaining),(subset,core,remaining)
                # INDEPENDENT hard model must show this exact extracted
                # core alone is sufficient to make target infeasible.
                verifier=cp_check(before,pos,dur,1887,only=set(core),seconds=a.seconds)
                assert verifier['status']=='INFEASIBLE',verifier
                record.update(core_size=len(core),
                    core_intersects_remaining_corrective_arcs=sorted(set(core)&remaining),
                    independent_core_recheck_status=verifier['status'],
                    verified_core=True)
            else:
                assert result['status'] in ('FEASIBLE','OPTIMAL')
                record['reconstructed_makespan']=result['independent_score']
            checks.append(record)
            print('INDEPENDENT',subset,record['status'],
                  record.get('core_intersects_remaining_corrective_arcs'),flush=True)
    assert len(checks)==16
    summary={
        'instance':'ta43js',
        'published_reference_blind_to_search':True,
        'new_complete_score':improvement,'real_original_elite_score':incumbent,
        'changed_baseline_adjacent_resource_relations':actual,
        'tested_all_16_subsets':len(checks),
        'all_15_proper_subsets_independently_proved_infeasible':True,
        'full_set_independently_reconstructs_improvement':True,
        'every_new_core_independently_rechecked_with_only_those_resource_arcs':True,
        'every_core_identifies_at_least_one_unreleased_corrective_arc':True,
        'explanation_core_sizes':[x.get('core_size') for x in checks if 'core_size' in x],
        'scope':'Exactly the four specified adjacency arcs can be removed, while all 576 other original incumbent adjacencies remain hard fixed; globally different improvements are NOT ruled out.',
        'records':checks
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(summary,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in summary.items() if k!='records'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seconds',type=float,default=2.0)
    p.add_argument('--out',type=Path,default=ROOT/'results'/'ta43-joint-4-arc-independent-audit.json')
    run(p.parse_args())
