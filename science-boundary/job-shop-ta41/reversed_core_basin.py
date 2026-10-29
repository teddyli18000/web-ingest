#!/usr/bin/env python3
"""Explore verified 2006 schedules that reverse a 21-arc shared UNSAT core.

All earlier baseline/neutral parent experiments preserved 21 common
machine precedence arcs. Three independently graded 2006 schedules now
REVERSE one of those arcs (5,6,7), leaving that prior fixed interface.

This experiment applies two controlled, exact (NoOverlap) neighborhoods
to these qualitatively different parents: globally ejected job cohorts
of size 6-15, and simultaneous 300-1200 time-band operation release.
All candidates are independently rescored; an improvement must also pass
the Few Shots official verification workflow. UNKNOWN never proves UNSAT.
"""
import argparse
import json
import time
from pathlib import Path
from search import obtain,setup,evaluate
from multi_parent_cohort import cohorts
from job_ejection_dag import lower_bound
from job_ejection_search import counterfactual
from temporal_band_repair import (
    selected_operations,fixed_precedence,precursor_lb,check_band)

ROOT=Path(__file__).resolve().parent

PARENTS={
 'rev5':('warm-backbone-5',5),
 'rev6':('warm-backbone-6',6),
 'rev7':('continuation-7',7),
}

def load_parent(name,baseline,pos,dur):
    folder,idx=PARENTS[name]
    data=ROOT/'results'/folder
    cert=json.loads((data/'neutral-certificate.json').read_text())['machines']
    verdict=json.loads((data/'best-verdict.json').read_text())
    assert verdict['valid'] and int(verdict['score'])==2006,verdict
    assert evaluate(cert,pos,dur)==2006
    core=json.loads((ROOT/'results'/'consensus-five-parents'/
                     'consensus-analysis.json').read_text())['proven_unsat_core']
    assert len(core)==21
    c=core[idx]
    assert cert[c['machine']].index(c['to_job'])<cert[c['machine']].index(c['from_job'])
    assert baseline[c['machine']].index(c['from_job'])<baseline[c['machine']].index(c['to_job'])
    return cert,c

def generate_windows():
    result=[]
    for width in (300,600,900,1200):
        for center in (300,700,1100,1500,1900):
            result.append([max(0,center-width//2),min(2006,center+width//2)])
    return result

def run(a):
    routes,ds,baseline=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(baseline,pos,dur)==2006
    parent,forced_arc=load_parent(a.parent,baseline,pos,dur)
    if a.mode=='cohorts':
        plan=cohorts(parent,baseline,a.seed)
    else:
        plan=[dict(window=w) for w in generate_windows()]
    report=dict(instance='ta41',target=2005,baseline=2006,
       parent=a.parent,mode=a.mode,verified_2006_parent=True,
       reversed_prior_shared_core_arc=forced_arc,
       exact_unconditional_NoOverlap=True,
       candidate_subspaces=len(plan),tested=0,unsat=0,unknown=0,
       dag_unsat=0,improvements=0,complete=False,
       results=[],
       interpretation='One prior shared-core arc was already reversed in the 2006 parent; therefore this explores a distinct parent basin, not a new makespan result.')
    a.out.mkdir(parents=True,exist_ok=True)
    began=time.monotonic()
    def store():
        report['tested']=len(report['results'])
        report['complete']=report['tested']==len(plan)
        report['elapsed_seconds']=round(time.monotonic()-began,3)
        (a.out/'reversed-basin-analysis.json').write_text(json.dumps(report,indent=2)+'\n')

    for i,entry in enumerate(plan):
        if time.monotonic()-began>a.seconds-4:break
        record=dict(entry,index=i)
        if a.mode=='cohorts':
            free=set(entry['jobs'])
            lb=lower_bound(parent,pos,dur,free)
            record['precedence_lower_bound']=lb
            if lb>2005:
                record['status']='INFEASIBLE_BY_DAG'
                report['dag_unsat']+=1
                candidate=None
            else:
                res,candidate=counterfactual(parent,pos,dur,free,2005,
                    min(a.case_seconds,max(1,a.seconds-(time.monotonic()-began)-3)),
                    a.seed+i*113)
                record.update(res)
        else:
            left,right=entry['window']
            ops,_=selected_operations(parent,pos,dur,left,right)
            arcs=fixed_precedence(parent,pos,ops)
            lb=precursor_lb(dur,arcs)
            record.update(free_operations=len(ops),
                          pinned_machine_arcs=len(arcs),
                          precedence_lower_bound=lb)
            if lb>2005:
                record['status']='INFEASIBLE_BY_DAG'
                report['dag_unsat']+=1
                candidate=None
            else:
                res,candidate=check_band(parent,pos,dur,arcs,
                    min(a.case_seconds,max(1,a.seconds-(time.monotonic()-began)-3)),
                    a.seed+i*113)
                record.update(res)
        if record['status']=='INFEASIBLE':
            report['unsat']+=1
        elif record['status'] in ('FEASIBLE','OPTIMAL'):
            assert candidate is not None
            score=evaluate(candidate,pos,dur)
            assert score is not None and score<=2005,score
            record['verified_dag_score']=score
            report['improvements']+=1
            (a.out/'certificate.json').write_text(
                json.dumps({'machines':candidate},separators=(',',':'))+'\n')
        elif record['status']=='UNKNOWN':
            report['unknown']+=1
        elif record['status']!='INFEASIBLE_BY_DAG':
            raise AssertionError(record)
        report['results'].append(record)
        store()
        print('SUBSPACE',a.parent,a.mode,i,record['status'],
              'elapsed',report['elapsed_seconds'],flush=True)
        if report['improvements']:break
    store()
    print('RESULT',json.dumps({k:v for k,v in report.items()
                              if k!='results'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=sorted(PARENTS),required=True)
    p.add_argument('--mode',choices=('cohorts','timebands'),required=True)
    p.add_argument('--seed',type=int,default=42021)
    p.add_argument('--seconds',type=int,default=320)
    p.add_argument('--case-seconds',type=float,default=18)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
