#!/usr/bin/env python3
"""Time-geometry reformulation for ta41: synchronized temporal destroy/repair.

The earlier job-cohort experiments always kept every non-ejected job's
machine order. This different interface frees *operations* whose baseline
execution intersects a selected common time band, across ALL machines.
On each machine, only the relative order of operations fully outside
that band is retained. The solver may move released operations to ANY
new time, not just inside the original band.

This couples machine and job reorderings across a global temporal slice
without allowing resource overlap. Each fixed-band subspace is solved
exactly by CP-SAT at target 2005 (time-bounded: UNKNOWN is not proof).

No originality claim is made about temporal LNS in general. The tested
hypothesis is that the particular ta41 2006 resource-conflict barrier has
a lower-dimensional time-coherent interface than a job-set interface.
"""
import argparse
import json
import time
from collections import deque
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis
from multi_parent_cohort import verified_parent

ROOT=Path(__file__).resolve().parent
TARGET=2005

def selected_operations(parent,pos,durations,left,right):
    _,start,_,horizon=graph_analysis(parent,pos,durations)
    assert horizon==2006
    selected={i for i in range(600)
              if start[i]<right and start[i]+durations[i]>left}
    return selected,start

def fixed_precedence(parent,pos,selected):
    arcs=[]
    for m in range(20):
        kept=[j for j in parent[m] if j*20+pos[j][m] not in selected]
        for a,b in zip(kept,kept[1:]):
            arcs.append((a*20+pos[a][m],b*20+pos[b][m]))
    return arcs

def precursor_lb(durations,arcs):
    edges=[[] for _ in range(600)]
    indeg=[0]*600
    for j in range(30):
        for k in range(19):
            a=j*20+k;b=a+1
            edges[a].append(b);indeg[b]+=1
    for a,b in arcs:
        edges[a].append(b);indeg[b]+=1
    todo=deque(i for i in range(600) if indeg[i]==0)
    st=[0]*600;count=0;C=0
    while todo:
        a=todo.popleft();count+=1
        end=st[a]+durations[a];C=max(C,end)
        for b in edges[a]:
            if st[b]<end:st[b]=end
            indeg[b]-=1
            if indeg[b]==0:todo.append(b)
    assert count==600
    return C

def check_band(parent,pos,duration,arcs,seconds,seed):
    model=cp_model.CpModel()
    s=[model.new_int_var(0,TARGET,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,TARGET,'e%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(s[i],duration[i],e[i],'i%d'%i)
               for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    for a,b in arcs:
        model.add(s[b]>=e[a])
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=4
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.random_seed=seed
    before=time.monotonic()
    status=solver.solve(model)
    rec={'status':solver.status_name(status),
         'wall_seconds':round(time.monotonic()-before,3),
         'branches':solver.num_branches,'conflicts':solver.num_conflicts}
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        candidate=[sorted(range(30),
                  key=lambda j:solver.value(s[j*20+pos[j][m]]))
                  for m in range(20)]
        score=evaluate(candidate,pos,duration)
        assert score is not None and score<=TARGET,score
        rec['verified_dag_score']=score
        rec['changed_machine_permutations']=sum(parent[i]!=candidate[i] for i in range(20))
        return rec,candidate
    return rec,None

def run(args):
    routes,durations_by_job,baseline=obtain()
    pos,duration=setup(routes,durations_by_job)
    assert evaluate(baseline,pos,duration)==2006
    parent=verified_parent(args.parent,baseline,pos,duration)
    windows=[]
    for width in (300,600,900,1200):
        for center in (300,700,1100,1500,1900):
            left=max(0,center-width//2)
            right=min(2006,center+width//2)
            windows.append((left,right))
    assert len(windows)==20
    report=dict(instance='ta41',parent=args.parent,baseline=2006,target=TARGET,
        method='time-band full-operation synchronous ejection with unchanged outside relative order',
        searched_bands=len(windows),results=[],tested=0,
        dag_proved_infeasible=0,cp_proved_infeasible=0,
        unknown=0,improvements=0,complete=False)
    args.out.mkdir(parents=True,exist_ok=True)
    initial=time.monotonic()
    def save():
        report['tested']=len(report['results'])
        report['complete']=report['tested']==len(windows)
        report['wall_seconds']=round(time.monotonic()-initial,3)
        (args.out/'temporal-band-analysis.json').write_text(json.dumps(report,indent=2)+'\n')

    for index,(left,right) in enumerate(windows):
        if time.monotonic()-initial>args.total_seconds-4:break
        selected,starts=selected_operations(parent,pos,duration,left,right)
        arcs=fixed_precedence(parent,pos,selected)
        relaxation=precursor_lb(duration,arcs)
        rec=dict(index=index,window=[left,right],selected_operation_count=len(selected),
                 retained_machine_precedence_count=len(arcs),
                 precedence_only_lower_bound=relaxation)
        if relaxation>TARGET:
            rec['status']='INFEASIBLE_BY_DAG'
            rec['wall_seconds']=0.0
            report['dag_proved_infeasible']+=1
        else:
            budget=min(args.case_seconds,
                       max(1,args.total_seconds-(time.monotonic()-initial)-3))
            res,candidate=check_band(parent,pos,duration,arcs,budget,args.seed+index)
            rec.update(res)
            if res['status']=='INFEASIBLE':report['cp_proved_infeasible']+=1
            elif res['status'] in ('OPTIMAL','FEASIBLE'):
                report['improvements']+=1
                (args.out/'certificate.json').write_text(
                    json.dumps({'machines':candidate},separators=(',',':'))+'\n')
            else:report['unknown']+=1
        report['results'].append(rec)
        save()
        print('BAND',args.parent,index,[left,right],len(selected),
              rec['status'],'elapsed',report['wall_seconds'],flush=True)
        if report['improvements']:break
    save()
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=['baseline','critical8','mixed20'],required=True)
    p.add_argument('--total-seconds',type=int,default=320)
    p.add_argument('--case-seconds',type=int,default=18)
    p.add_argument('--seed',type=int,default=2608)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
