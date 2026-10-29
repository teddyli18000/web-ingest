#!/usr/bin/env python3
"""DCPRR phase II: growing, path-replacement-informed CP joint repair.

Unlike previous experiments which fixed a job set/machine set/time band,
the released operation identities are selected DURING the run from
successive newly exposed critical-path machine arcs after tentative
bounded N7-inspired insertion moves.

Same total release count, exact DAG evaluation budget, CP cap and seed are
used by four controls; only release-set selection differs:
dynamic=newly generated critical arcs; static=baseline near-critical arcs;
core=21 proven consensus no-2005 precedence arcs; random=uniform.
All CP submodels retain hard NoOverlap and job precedence; only survivor
relative machine orders remain fixed to the verified 2006 parent.

A model's INFEASIBLE rules out ONLY its particular release set, not
all possible dynamic repair procedures. UNKNOWN is not a negative proof.
"""
import argparse,json,random,time
from collections import Counter
from pathlib import Path
from search import obtain,setup,evaluate
from dynamic_critical_replacement import state,scan,insert
from temporal_band_repair import fixed_precedence,precursor_lb,check_band

ROOT=Path(__file__).resolve().parent

def arc_ops(arcs,pos):
    for m,a,b in arcs:
        yield a*20+pos[a][m]
        yield b*20+pos[b][m]

def coordinate_neighborhood(ops,parent,pos):
    """Machine adjacency + job-chain adjacency; all are useful release candidates."""
    slot=[None]*600
    for m,seq in enumerate(parent):
        for k,j in enumerate(seq):slot[j*20+pos[j][m]]=(m,k)
    expanded=Counter()
    for op in ops:
        expanded[op]+=4
        m,k=slot[op]
        for offset in (-2,-1,1,2):
            p=k+offset
            if 0<=p<30:
                j=parent[m][p]
                expanded[j*20+pos[j][m]]+=1
        for offset in (-1,1):
            nxt=op+offset
            if op//20==nxt//20:expanded[nxt]+=2
    return expanded

def run(a):
    routes,rows,baseline=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(baseline,pos,dur)==2006
    parent=[seq[:] for seq in baseline]
    if a.parent!='baseline':
        root=ROOT/'results'/('gateway-'+a.parent)
        vr=json.loads((root/'upstream-verdict.json').read_text())
        assert vr['valid'] and int(vr['score'])==2006
        parent=json.loads((root/'certificate.json').read_text())['machines']
    assert evaluate(parent,pos,dur)==2006
    core=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert core['status']=='INFEASIBLE'
    core_arcs={(c['machine'],c['from_job'],c['to_job']) for c in core['proven_unsat_core']}
    rng=random.Random(a.seed)
    orders=[x[:] for x in parent]
    now,initial_crit,static_near=state(orders,pos,dur)
    last_critical=initial_crit.copy()
    dynamic_frontier=initial_crit.copy()
    seen_critical_edges=set()
    evidence=Counter()
    released=set()
    total_dag_evals=0
    accepted=0
    replacement_events=0
    dag_reject=0
    report=dict(instance='ta41',target=2005,parent=a.parent,policy=a.policy,seed=a.seed,
        initial_score=2006,release_per_round=a.growth,round_budget=a.rounds,
        dag_evals_per_round=a.dag_evals,cp_seconds_per_round=a.cp_seconds,
        rounds_completed=0,CP_INFEASIBLE=0,CP_UNKNOWN=0,CP_FEASIBLE=0,
        DAG_exclusions=0,critical_replacements_seen=0,received_candidate_scores=0,
        total_exact_DAG_evaluations=0,release_sets=[],complete=False,
        note='All fixed-survivor NoOverlap subproblems preserve full resources; identities released dynamically, not fixed a priori. Controls share same growth/solver limits.')
    a.out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    def save():
        report['critical_replacements_seen']=replacement_events
        report['total_exact_DAG_evaluations']=total_dag_evals
        report['received_candidate_scores']=accepted
        report['elapsed_seconds']=round(time.monotonic()-started,3)
        (a.out/'dynamic-repair.json').write_text(json.dumps(report,indent=2)+'\n')
    for step in range(a.rounds):
        # Advance exploratory schedules and observe a new critical path after
        # every accepted insertion: the operation set is not predetermined.
        for inner in range(a.dag_evals//a.batch):
            if a.policy=='dynamic':
                focus=dynamic_frontier|last_critical
            elif a.policy=='static':
                focus=static_near
            elif a.policy=='core':
                focus=core_arcs
            else:
                focus=set()
            options,invalid,used=scan(orders,pos,dur,focus,rng,a.batch)
            total_dag_evals+=used;dag_reject+=invalid
            fit=[(v,m) for v,m in options if v<=2006+a.max_uphill]
            if not fit:continue
            fit.sort(key=lambda p:(p[0],rng.random()))
            new_score,move=fit[0] if rng.random()<0.85 else rng.choice(fit[:min(len(fit),5)])
            insert(orders,move)
            assert evaluate(orders,pos,dur)==new_score
            now=new_score;accepted+=1
            _,current_critical,_=state(orders,pos,dur)
            newly=current_critical-last_critical
            if newly:replacement_events+=1
            if a.policy=='dynamic':
                dynamic_frontier=newly if newly else current_critical
                for u in arc_ops(newly,pos):evidence[u]+=8
                for u in arc_ops(current_critical,pos):evidence[u]+=2
            last_critical=current_critical
        if a.policy=='static':
            for u in arc_ops(static_near,pos):evidence[u]+=3
        elif a.policy=='core':
            for u in arc_ops(core_arcs,pos):evidence[u]+=3
        elif a.policy=='random':
            for u in rng.sample(range(600),a.growth):evidence[u]+=3
        # Expand high-weight non-fixed operations to permit coupled
        # machine/job predecessors; consume only a fixed growth budget.
        expanded=coordinate_neighborhood(evidence.keys(),parent,pos)
        candidates=sorted(range(600),
              key=lambda op:(-(evidence[op]*8+expanded[op]),rng.random()))
        selected=[op for op in candidates if op not in released][:a.growth]
        assert len(selected)==a.growth
        released.update(selected)
        fixed_arcs=fixed_precedence(parent,pos,released)
        lower=precursor_lb(dur,fixed_arcs)
        record=dict(round=step+1,released_operations=len(released),
             retained_survivor_machine_arcs=len(fixed_arcs),
             precedence_only_lower_bound=lower,
             proposal_current_makespan=now,
             critical_replacement_events_so_far=replacement_events,
             released_this_round=selected)
        if lower>2005:
            record.update(status='INFEASIBLE_BY_DAG',seconds=0.0)
            report['DAG_exclusions']+=1
        else:
            outcome,cert=check_band(parent,pos,dur,fixed_arcs,a.cp_seconds,
                                    a.seed*101+step)
            record.update(status=outcome['status'],seconds=outcome['wall_seconds'],
                          branches=outcome['branches'],conflicts=outcome['conflicts'])
            if outcome['status']=='INFEASIBLE':report['CP_INFEASIBLE']+=1
            elif outcome['status'] in ('FEASIBLE','OPTIMAL'):
                report['CP_FEASIBLE']+=1
                score=evaluate(cert,pos,dur)
                assert score is not None and score<=2005
                record['independent_DAG_score']=score
                (a.out/'certificate.json').write_text(json.dumps({'machines':cert},separators=(',',':'))+'\n')
            else:report['CP_UNKNOWN']+=1
        report['release_sets'].append(record)
        report['rounds_completed']=len(report['release_sets'])
        save()
        print('ROUND',a.policy,a.parent,step+1,'released',len(released),
              record['status'],'critical replacements',replacement_events,flush=True)
        if record['status'] in ('FEASIBLE','OPTIMAL'):break
    report['complete']=report['rounds_completed']==a.rounds
    save()
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='release_sets'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--policy',choices=['dynamic','static','core','random'],required=True)
    p.add_argument('--parent',choices=['baseline','124'],default='baseline')
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--growth',type=int,default=30)
    p.add_argument('--rounds',type=int,default=8)
    p.add_argument('--dag-evals',type=int,default=240)
    p.add_argument('--batch',type=int,default=24)
    p.add_argument('--cp-seconds',type=float,default=6.0)
    p.add_argument('--max-uphill',type=int,default=55)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();assert a.growth*a.rounds<=600
    run(a)
