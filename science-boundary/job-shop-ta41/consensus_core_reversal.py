#!/usr/bin/env python3
"""A complete 21-way disjunction covering EVERY ta41 schedule of <=2005.

The five verified 2006 parents have a shared precedence poset. Exact
CP-SAT proves that preserving a sufficient core of just 21 specific
shared same-machine job precedences is incompatible with Cmax<=2005.

Therefore ANY target schedule must REVERSE at least one of those 21
relationships, since NoOverlap forces one of two strict orientations.
Each branch here fixes one corresponding reversed precedence while
retaining the complete original instance (600 intervals, 20 NoOverlap
machines, and all job routes). This is a *complete disjunctive cover*
of the global target feasibility problem, not an incumbent-near search.

Stage A: a restricted global job-ejection reconstruction at deadline 2006,
to discover distant 2006 seeds breaking the shared backbone.
Stage B: unrestricted CP at deadline 2006 with one mandatory reversed arc.
Stage C: unrestricted CP at deadline 2005 with that same mandatory reverse.

Only stage-C INFEASIBLE is a global branch exclusion. UNKNOWN is not.
Any stage producing a makespan<=2005 schedule is independently DAG scored,
then externally Few Shots verified by the Action.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate


def build(orders,pos,duration,core_arc,horizon,free_cohort=None):
    model=cp_model.CpModel()
    s=[model.new_int_var(0,horizon,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,horizon,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],duration[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        if free_cohort is not None:
            non_ejected=[j for j in orders[m] if j not in free_cohort]
            for j,h in zip(non_ejected,non_ejected[1:]):
                model.add(s[h*20+pos[h][m]]>=e[j*20+pos[j][m]])
    m=core_arc['machine'];j=core_arc['from_job'];h=core_arc['to_job']
    # The original required j->h. The branch REVERSES it to h->j:
    model.add(s[j*20+pos[j][m]]>=e[h*20+pos[h][m]])
    return model,s


def solve_one(orders,pos,duration,arc,horizon,limit,seed,free_cohort=None):
    model,starts=build(orders,pos,duration,arc,horizon,free_cohort)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=limit
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    t=time.monotonic();status=solver.solve(model)
    info=dict(status=solver.status_name(status),
              seconds=round(time.monotonic()-t,3),
              conflicts=solver.num_conflicts,branches=solver.num_branches,
              restricted_reinsert_cohort=sorted(free_cohort) if free_cohort else None)
    candidate=None
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        candidate=[sorted(range(30),key=lambda j:solver.value(starts[j*20+pos[j][m]]))
                   for m in range(20)]
        val=evaluate(candidate,pos,duration)
        assert val is not None and val<=horizon,(val,horizon)
        info['independent_dag_score']=val
        m=arc['machine']
        assert candidate[m].index(arc['to_job'])<candidate[m].index(arc['from_job'])
    return info,candidate

def main(a):
    root=Path(__file__).parent
    source=json.loads((root/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert source['status']=='INFEASIBLE' and source['unsat_core_size']==21
    assert source['parents']==['baseline','critical8','mixed12','mixed16','mixed20']
    cores=source['proven_unsat_core']
    routes,ds,orders=obtain();pos,duration=setup(routes,ds)
    assert evaluate(orders,pos,duration)==2006
    # Choose release cohorts centered on jobs appearing in the core.
    frequency={j:0 for j in range(30)}
    for arc in cores:
        frequency[arc['from_job']]+=1;frequency[arc['to_job']]+=1
    priority=sorted(range(30),key=lambda j:(-frequency[j],j))
    assigned=[(i,arc) for i,arc in enumerate(cores) if i%a.shards==a.shard]
    a.out.mkdir(parents=True,exist_ok=True)
    report=dict(instance='ta41',baseline=2006,target=2005,
                core_source='consensus-five-parents/consensus-analysis.json',
                global_cover_branch_count=21,
                branch_semantics='At least one reversed shared pair is mandatory for any <=2005 schedule',
                shard=a.shard,shards=a.shards,
                assigned=len(assigned),checked=0,
                stage_c_global_infeasible=0,stage_c_unknown=0,feasible=0,
                neutral_2006_seeds=0,branches=[],complete=False)
    for i,arc in assigned:
        selected={arc['from_job'],arc['to_job']}
        selected.update(j for j in priority if len(selected)<16)
        rec=dict(branch_index=i,arc=arc,stage_a=None,stage_b=None,stage_c=None)
        A,neutral=solve_one(orders,pos,duration,arc,2006,a.stage_a_seconds,a.seed+i+1,selected)
        rec['stage_a']=A
        if neutral is None:
            B,neutral=solve_one(orders,pos,duration,arc,2006,a.stage_b_seconds,a.seed+i+251)
            rec['stage_b']=B
        if neutral is not None:
            makespan=evaluate(neutral,pos,duration)
            if makespan<=2005:
                (a.out/'certificate.json').write_text(json.dumps({'machines':neutral},separators=(',',':'))+'\n')
                rec['improved_score']=makespan;report['feasible']+=1
                report['branches'].append(rec)
                break
            (a.out/('neutral-core-%02d.json'%i)).write_text(
                json.dumps({'machines':neutral},separators=(',',':'))+'\n')
            report['neutral_2006_seeds']+=1
        if rec['stage_b'] is not None and rec['stage_b']['status']=='INFEASIBLE':
            rec['stage_c']={'status':'INFEASIBLE_IMPLIED_BY_UNRESTRICTED_2006'}
            report['stage_c_global_infeasible']+=1
        else:
            C,candidate=solve_one(orders,pos,duration,arc,2005,a.stage_c_seconds,a.seed+i+700)
            rec['stage_c']=C
            if candidate is not None:
                val=evaluate(candidate,pos,duration)
                assert val<=2005
                (a.out/'certificate.json').write_text(
                    json.dumps({'machines':candidate},separators=(',',':'))+'\n')
                rec['improved_score']=val;report['feasible']+=1
                report['branches'].append(rec);break
            if C['status']=='INFEASIBLE':report['stage_c_global_infeasible']+=1
            else:report['stage_c_unknown']+=1
        report['branches'].append(rec)
        print('BRANCH',i,'A',A['status'],'B',rec['stage_b']['status'] if rec['stage_b'] else '-',
              'C',rec['stage_c']['status'],
              'neutral_count',report['neutral_2006_seeds'],flush=True)
    report['checked']=len(report['branches'])
    report['complete']=report['checked']==len(assigned)
    (a.out/'forced-reversal.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='branches'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,default=7)
    p.add_argument('--stage-a-seconds',type=float,default=12)
    p.add_argument('--stage-b-seconds',type=float,default=16)
    p.add_argument('--stage-c-seconds',type=float,default=60)
    p.add_argument('--seed',type=int,default=1739)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
