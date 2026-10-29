#!/usr/bin/env python3
"""Exact Kendall-ball feasibility around the ta41 2006 incumbent.

Unlike whole-machine changed count or selective adjacent swap families,
every one of the 435 job pairs on each machine is explicitly oriented.
A reversal costs exactly one unit of Kendall distance. The sum gives
EXACT machine-permutation Kendall distance from the verified incumbent.

The optional window W only allows reversed pairs whose *incumbent*
positions differ <=W; W=29 covers ALL 8700 machine-job pairs. W<29 is
a restricted family, and no infeasibility claim may generalize to W=29.

A hard Cmax<=2005 NoOverlap+job route constraint is required. No old
learned cores are imported. UNKNOWN says nothing about a radius.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate

def kendall(new,base):
    total=0
    for m in range(20):
        rank={j:i for i,j in enumerate(base[m])}
        seq=[rank[j] for j in new[m]]
        total+=sum(seq[i]>seq[j] for i in range(30) for j in range(i+1,30))
    return total

def main(a):
    r,d,baseline=obtain()
    pos,dur=setup(r,d)
    assert evaluate(baseline,pos,dur)==2006
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2005,f's_{i}') for i in range(600)]
    e=[model.new_int_var(0,2005,f'e_{i}') for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],f'iv_{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):
            model.add(s[j*20+k+1]>=e[j*20+k])
    reversed_pairs=[]
    fixed_pairs=0
    for m in range(20):
        ops=[j*20+pos[j][m] for j in baseline[m]]
        model.add_no_overlap([iv[u] for u in ops])
        for i in range(30):
            for j in range(i+1,30):
                u=ops[i];v=ops[j]
                if j-i>a.window:
                    model.add(s[v]>=e[u])
                    fixed_pairs+=1
                else:
                    flipped=model.new_bool_var(f'reverse_{m}_{i}_{j}')
                    model.add(s[v]>=e[u]).only_enforce_if(flipped.Not())
                    model.add(s[u]>=e[v]).only_enforce_if(flipped)
                    reversed_pairs.append(flipped)
    model.add(sum(reversed_pairs)<=a.radius)
    slv=cp_model.CpSolver()
    slv.parameters.max_time_in_seconds=a.seconds
    slv.parameters.num_search_workers=a.workers
    slv.parameters.random_seed=a.seed
    t=time.monotonic();status=slv.solve(model)
    report={'instance':'ta41','target':2005,'baseline':2006,
       'exact_kendall_radius':a.radius,'baseline_order_position_window':a.window,
       'unrestricted_machine_pair_distance':a.window==29,
       'orientation_variables':len(reversed_pairs),'fixed_machine_pair_relations':fixed_pairs,
       'status':slv.status_name(status),'elapsed_seconds':round(time.monotonic()-t,3),
       'branches':slv.num_branches,'conflicts':slv.num_conflicts,
       'ortools_version':__import__('ortools').__version__,
       'valid_claim_if_INFEASIBLE':('All ta41 schedules with Cmax<=2005 have Kendall distance >%d from the given 2006 baseline.'%a.radius if a.window==29 else 'No target schedule inside the <=%d Kendall ball AND incumbent-pair position window <=%d.'%(a.radius,a.window)),
       'note':'Each reversal of a baseline machine job pair counts 1, not just adjacent swaps. No core clauses are imported.'}
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        machines=[sorted(range(30),key=lambda j:slv.value(s[j*20+pos[j][m]]))
                  for m in range(20)]
        score=evaluate(machines,pos,dur)
        dist=kendall(machines,baseline)
        assert score is not None and score<=2005 and dist<=a.radius,(score,dist)
        assert dist==sum(slv.value(x) for x in reversed_pairs),dist
        report['verified_score']=score
        report['verified_exact_kendall_distance']=dist
        (a.out/'certificate.json').write_text(json.dumps({'machines':machines},separators=(',',':'))+'\n')
    (a.out/'decision.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--window',type=int,required=True)
    p.add_argument('--radius',type=int,required=True)
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=20261029)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();assert 1<=a.window<=29 and a.radius>=0
    main(a)
