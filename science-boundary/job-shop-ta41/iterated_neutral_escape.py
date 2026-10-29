#!/usr/bin/env python3
"""Iterated neutral-manifold search on ta41, preserving exact resource physics.

Each transition reconstructs 600 operations and maximizes machine-order
diversity at <=2006 from the CURRENT (not original) 2006 incumbent.
Repeated transitions can cross many machines, unlike 1/2 swaps or isolated
job ejection from a single immutable incumbent. Candidate schedules are
re-scored on the ORIGINAL instance after every transition.

A second stage probes full NoOverlap feasibility at <=2005 with
job-centered 3/4/6/8/12-job ejection cohorts selected from current
critical-path jobs and randomized diversification. UNKNOWN is recorded
as such, and each verified candidate is archived before any claim.
"""
import argparse,hashlib,itertools,json,random,time
from pathlib import Path
from search import obtain,setup,evaluate
from job_ejection_search import counterfactual
from neutral_plateau_escape import diversify
from job_ejection_dag import lower_bound

def pair_distance(a,b):
    d=0
    for m in range(20):
        loc={j:k for k,j in enumerate(b[m])}
        seq=[loc[j] for j in a[m]]
        for i in range(30):
            d+=sum(seq[i]>seq[k] for k in range(i+1,30))
    return d

def pool_cohort(current,pos,dur,rng,n):
    _,critical=evaluate(current,pos,dur,True)
    # CP's critical path is one among potentially many. Combine critical
    # jobs with random support rather than freezing one bottleneck.
    cj=sorted(set(i//20 for i in critical))
    q=min(len(cj), max(1,n//2))
    selected=set(rng.sample(cj,q))
    selected.update(rng.sample([i for i in range(30) if i not in selected],n-len(selected)))
    assert len(selected)==n
    return selected

def escape_phase(current,pos,dur,rng,seed,budget,output):
    st=time.monotonic();tested=[];unknown=0;proven=0;attempts=0
    _,path=evaluate(current,pos,dur,True)
    critical_jobs=sorted(set(i//20 for i in path))
    for n in (3,4,6,8,12):
        if time.monotonic()-st>budget-0.6:break
        candidates=[]
        for i in range(8):
            chosen=set(rng.sample(critical_jobs,min(len(critical_jobs),max(1,n//2))))
            rest=[j for j in range(30) if j not in chosen]
            chosen.update(rng.sample(rest,n-len(chosen)))
            lb=lower_bound(current,pos,dur,chosen)
            candidates.append((lb,tuple(sorted(chosen))))
        candidates=sorted(set(candidates))
        for bound,chosen in candidates[:4]:
            if time.monotonic()-st>budget-0.5:break
            if bound>2005:
                proven+=1
                continue
            score,certificate=counterfactual(current,pos,dur,set(chosen),2005,
                min(1.0,max(.3,budget-(time.monotonic()-st)-.2)),seed+attempts)
            attempts+=1
            if score['status']=='INFEASIBLE':proven+=1
            elif score['status']=='UNKNOWN':unknown+=1
            else:
                assert score['status'] in ('FEASIBLE','OPTIMAL')
                v=evaluate(certificate,pos,dur)
                assert v is not None and v<=2005
                (output/'certificate.json').write_text(json.dumps({'machines':certificate},separators=(',',':'))+'\n')
                tested.append(dict(jobs=list(chosen),score=v,status=score['status']))
                return dict(proven_infeasible=proven,unknown=unknown,
                            tried=attempts,found_improvement=True,
                            improvement_score=v),True
    return dict(proven_infeasible=proven,unknown=unknown,
                tried=attempts,found_improvement=False),False

def run(a):
    routes,ds,baseline=obtain();pos,dur=setup(routes,ds)
    assert evaluate(baseline,pos,dur)==2006
    rng=random.Random(a.seed);out=a.out;out.mkdir(parents=True,exist_ok=True)
    current=[r[:] for r in baseline]
    bestdiv=0; bestneutral=None
    visited=set();elite=[];log=[]
    start=time.monotonic()
    improvements=0
    for step in range(a.rounds):
        if time.monotonic()-start>a.seconds-10:break
        if elite and step%7==6:
            current=[row[:] for row in rng.choice(elite)[1]]
        n=rng.choice([6,8,10,12,14,16,20])
        group=pool_cohort(current,pos,dur,rng,n)
        remaining=max(2,a.seconds-(time.monotonic()-start)-8)
        info,proposal=diversify(current,pos,dur,group,min(a.step_seconds,remaining),a.seed+step)
        record={'step':step,'size_jobs':n,'cohort':sorted(group),
                'neutral_solver_status':info['status'],
                'neutral_score':info.get('score'),
                'relative_changed_machines':info.get('changed_machine_orders'),
                'solver_seconds':info['seconds']}
        if proposal is not None:
            score=evaluate(proposal,pos,dur)
            assert score is not None and score<=2006
            if score<=2005:
                (out/'certificate.json').write_text(json.dumps({'machines':proposal},separators=(',',':'))+'\n')
                record['improved_score']=score;improvements+=1
                log.append(record);break
            fingerprint=hashlib.sha256(json.dumps(proposal,separators=(',',':')).encode()).hexdigest()
            record['novel']=fingerprint not in visited
            visited.add(fingerprint)
            d=pair_distance(proposal,baseline)
            changed=sum(x!=y for x,y in zip(proposal,baseline))
            record.update(pair_inversions_from_original=d,
                          changed_machines_from_original=changed)
            if changed*10000+d>bestdiv:
                bestdiv=changed*10000+d
                bestneutral=[r[:] for r in proposal]
                (out/'neutral-certificate.json').write_text(
                    json.dumps({'machines':bestneutral},separators=(',',':'))+'\n')
            if fingerprint not in {x[0] for x in elite}:
                elite.append((fingerprint,[r[:] for r in proposal],changed*10000+d))
                elite.sort(key=lambda x:x[2],reverse=True)
                elite=elite[:12]
            current=proposal
            if step%2==0:
                escape_result,found=escape_phase(current,pos,dur,rng,a.seed+20000+step*100,
                    min(a.escape_seconds,max(0,a.seconds-(time.monotonic()-start)-6)),out)
                record['escape']=escape_result
                if found:
                    improvements+=1
                    log.append(record);break
        log.append(record)
        if step%5==0:
            print('PROGRESS',step,'neutral_distinct',len(visited),'best_machine_changes',
                  bestdiv//10000,'elapsed',round(time.monotonic()-start,1),flush=True)
    result={
        'instance':'Taillard ta41','baseline':2006,'target':2005,
        'algorithm':'iterated cross-machine neutral schedule reconstruction plus multi-job global escape',
        'seed':a.seed,'requested_rounds':a.rounds,'rounds_executed':len(log),
        'unique_2006_neutral_schedules':len(visited),
        'best_changed_machine_orders_from_original':bestdiv//10000,
        'best_pairwise_order_inversions_from_original':bestdiv%10000,
        'found_improvement':improvements>0,
        'score_claim':None if not improvements else '<=2005 (requires independent upstream verifier)',
        'records':log,
        'elapsed_seconds':round(time.monotonic()-start,3),
    }
    (out/'neutral-walk.json').write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in result.items() if k!='records'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--rounds',type=int,default=35)
    p.add_argument('--seconds',type=float,default=390)
    p.add_argument('--step-seconds',type=float,default=8)
    p.add_argument('--escape-seconds',type=float,default=11)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
