#!/usr/bin/env python3
"""5-second constructive job-release radius ladder for blinded strong JSSP starts.

This benchmark calls a single JOINT CP model at successive release budgets
K=2,4,5,7,10 (per-case/time configuration). A source-only Boolean free[j]
simultaneously controls all incumbent resource-adjacency precedences
touching job j; machine NoOverlap, all job arcs, hard deadline
Cmax(current_best)-1 are always enforced.

At each radius, CP chooses its OWN released job set jointly with ALL
machine orders. If feasible, independently score a complete permutation,
replace best incumbent, and tighten deadline before next radius. If
INFEASIBLE it excludes only that radius's restricted subspace. If UNKNOWN,
simply continue with larger K. Strictly no archived answer or oracle loaded.

Benchmark paired against published real source-native N7 5-second continuation
from the EXACT same 12 independent 20-second N7 elite starts, seeds 4107,4113.
This tests whether switching the *joint decision interface* improves
constructive rate or runtime. Baseline exact N7 scores are judged separately.
"""
import argparse,json,time,statistics
from pathlib import Path
from ortools.sat.python import cp_model
from partial_resource_pair_repair import parse_case
from structural_cut import disjunctive_dag
from search import evaluate

ROOT=Path(__file__).resolve().parent
def solve(orders,pos,dur,best,K,seconds,seed,head):
    L=best-1
    model=cp_model.CpModel()
    st=[model.new_int_var(0,L-dur[i],f's_{i}') for i in range(600)]
    en=[model.new_int_var(dur[i],L,f'e_{i}') for i in range(600)]
    iv=[model.new_interval_var(st[i],dur[i],en[i],f'i{i}') for i in range(600)]
    free=[model.new_bool_var(f'free_{j}') for j in range(30)]
    model.add(sum(free)<=K)
    for j in range(30):
        for t in range(19):
            model.add(st[j*20+t+1]>=en[j*20+t])
    for m,row in enumerate(orders):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        for a,b in zip(row,row[1:]):
            u=a*20+pos[a][m];v=b*20+pos[b][m]
            model.add(st[v]>=en[u]).only_enforce_if([free[a].Not(),free[b].Not()])
    for i in range(600):
        guess=min(head[i],L-dur[i])
        model.add_hint(st[i],guess)
        model.add_hint(en[i],guess+dur[i])
    for j in range(30):model.add_hint(free[j],0)
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=seed
    solver.parameters.max_time_in_seconds=seconds
    stat=solver.solve(model)
    record=dict(radius_jobs=K,target=L,
        status=solver.status_name(stat),
        solver_seconds=round(solver.wall_time,4),
        conflicts=solver.num_conflicts,
        branches=solver.num_branches)
    if stat in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        out=[sorted(range(30),key=lambda j:solver.value(st[j*20+pos[j][m]]))
             for m in range(20)]
        score=evaluate(out,pos,dur)
        assert score is not None and score<=L,(score,L)
        selected={j for j in range(30) if solver.value(free[j])}
        changed=[]
        for m,row in enumerate(orders):
            rr={j:i for i,j in enumerate(out[m])}
            for t,(a,b) in enumerate(zip(row,row[1:])):
                if rr[a]>rr[b]:
                    assert a in selected or b in selected
                    changed.append(m*29+t)
        record.update(independent_score=score,
            free_jobs=sorted(selected),
            changed_adjacencies=len(changed))
        return record,out
    return record,None

def benchmark(a):
    if len(a.radii)!=len(a.time_caps):raise ValueError('radius vs caps mismatch')
    if any(x<0 or x>30 for x in a.radii):raise ValueError('bad radius')
    if any(x<=0 for x in a.time_caps):raise ValueError('bad wall budget')
    cases=sorted(a.cases.glob('ta*js-n7elite*/start.txt'))
    if a.only:cases=[p for p in cases if p.parent.name in a.only]
    if a.ta41:cases.append('ta41')
    assert cases
    a.out.mkdir(parents=True,exist_ok=True)
    records=[]
    for entry in cases:
        start_source=str(entry)
        orders,pos,dur,initial=parse_case(start_source)
        _,_,_,head,tail,baseline=disjunctive_dag(orders,pos,dur,set())
        assert baseline==initial
        for seed in a.seeds:
            tick=time.monotonic()
            best=initial
            best_orders=orders
            stages=[]
            for i,(K,seconds) in enumerate(zip(a.radii,a.time_caps)):
                rec,candidate=solve(orders,pos,dur,best,K,seconds,seed*17+i,head)
                if candidate is not None:
                    best=rec['independent_score']
                    best_orders=candidate
                stages.append(rec)
            independently=evaluate(best_orders,pos,dur)
            assert independently==best and best<=initial
            ident=('ta41' if start_source=='ta41' else Path(start_source).parent.name)
            record=dict(case=ident,seed=seed,initial=initial,
                best_score=best,improvement=initial-best,
                solver_seconds_total=sum(x['solver_seconds'] for x in stages),
                full_wall_seconds=round(time.monotonic()-tick,3),
                strictly_improved=best<initial,
                verified_complete_machine_permutations=True,
                stages=stages)
            records.append(record)
            if best<initial:
                (a.out/f'{ident}-seed{seed}-certificate.json').write_text(
                    json.dumps({'machines':best_orders},separators=(',',':'))+'\n')
            (a.out/'checkpoint.json').write_text(
                json.dumps(dict(complete=False,trials=records),indent=2)+'\n')
            print('TRIAL',ident,seed,initial,best,
                  'stages',[(x['radius_jobs'],x['status'],x.get('independent_score')) for x in stages],
                  flush=True)
    report=dict(experiment='Oracle-blind 30x20 full CP joint job release radius ladder',
        source='20s native-N7 independent elite starts, unless case=ta41',
        solver='OR-Tools 9.14.6206',
        radii=a.radii,time_caps=a.time_caps,
        time_caps_total_seconds=sum(a.time_caps),
        hidden_lookahead_used=False,
        trials=len(records),
        improved_trials=sum(x['strictly_improved'] for x in records),
        mean_improvement=statistics.mean(x['improvement'] for x in records),
        sample=records,complete=True)
    (a.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='sample'}),
          flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cases',type=Path,default=ROOT/'positive-n7-elite-data')
    p.add_argument('--only',nargs='*',default=[])
    p.add_argument('--ta41',action='store_true')
    p.add_argument('--seeds',nargs='+',type=int,default=[4107,4113])
    p.add_argument('--radii',nargs='+',type=int,default=[2,4,5,7,10])
    p.add_argument('--time-caps',nargs='+',type=float,default=[0.8,1.0,1.0,1.1,1.1])
    p.add_argument('--out',type=Path,required=True)
    benchmark(p.parse_args())
