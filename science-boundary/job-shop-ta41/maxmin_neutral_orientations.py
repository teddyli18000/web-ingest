#!/usr/bin/env python3
"""Max-min orientation diversity over ta41's verified score-2006 level set.

Why: two 150s globally soft CP rounds with a *distance MINIMIZING*
secondary objective crossed additional necessary cores but yielded only
four new pairwise disagreements among 14 parents. That design explicitly
discouraged structural exploration. Continuing it would be uninformative.

This model uses Cmax<=2006, full NoOverlap and all job arcs, and permits
ALL machine precedences to change. Optimize MAXIMUM MINIMUM Hamming
distance of the 580 original consecutive machine-pair orientations
from a set of 12 independently verified 2006 parents. Optionally require
10 sound 2005 necessary conflict disjunctions as target-directed guidance.
A candidate <=2005 is independently DAG rescored and officially graded.
A 2006 candidate is useful only if it actually broadens orientation
diversity, measured by all 8700 pairwise Kendall coordinates afterwards.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis
from cross_basin_poset import load
from all_core_orientation_repair import source_cuts

ROOT=Path(__file__).resolve().parent

def kendall(a,b):
    total=0
    for m in range(20):
        rank={j:i for i,j in enumerate(b[m])}
        order=[rank[j] for j in a[m]]
        total+=sum(order[i]>order[k] for i in range(30) for k in range(i+1,30))
    return total

def prior_cuts(pos):
    src,cons=source_cuts()
    src.append(('consensus21',[(c['from_job']*20+pos[c['from_job']][c['machine']],
         c['to_job']*20+pos[c['to_job']][c['machine']]) for c in cons]))
    x=json.loads((ROOT/'results'/'cross-poset-all12'/'intersection-analysis.json').read_text())
    assert x['certified_new_disjunction'] and x['independent_hard_core_revalidation']['status']=='INFEASIBLE'
    pairs=[(c['from_job']*20+pos[c['from_job']][c['machine']],
            c['to_job']*20+pos[c['to_job']][c['machine']]) for c in x['new_sufficient_unsat_core']]
    src.append(('cross12',pairs))
    assert len(src)==10
    return src

def run(a):
    routes,ds,base=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(base,pos,dur)==2006
    parents=load(pos,dur,base)
    seed_parent=parents['ninecore']
    assert len(parents)==12
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2006,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,2006,'e%d'%i) for i in range(600)]
    intervals=[model.new_interval_var(s[i],dur[i],e[i],'i%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([intervals[j*20+pos[j][m]] for j in range(30)])
    pairvars={}
    def before(m,a,b):
        assert a!=b
        x,y=sorted((a,b));key=(m,x,y)
        if key not in pairvars:
            bit=model.new_bool_var('ord_%d_%d_%d'%key)
            u=x*20+pos[x][m];v=y*20+pos[y][m]
            model.add(s[v]>=e[u]).only_enforce_if(bit)
            model.add(s[u]>=e[v]).only_enforce_if(bit.Not())
            pairvars[key]=bit
        return pairvars[key] if a==x else pairvars[key].Not()
    dimensions=[]
    for m in range(20):
        for ja,jb in zip(base[m],base[m][1:]):
            dimensions.append((m,ja,jb,before(m,ja,jb)))
    assert len(dimensions)==580
    parent_dists=[]
    for name,order in parents.items():
        directions=[{j:i for i,j in enumerate(order[m])} for m in range(20)]
        disagreements=[]
        for m,j,k,lit in dimensions:
            disagreements.append(lit if directions[m][j]>directions[m][k]
                                     else lit.Not())
        d=model.new_int_var(0,580,'distance_%s'%name)
        model.add(d==sum(disagreements))
        parent_dists.append((name,d))
    minimum=model.new_int_var(0,580,'min_hamming')
    for name,d in parent_dists:model.add(minimum<=d)
    if a.guided:
        mapping=[-1]*600
        for j in range(30):
            for m in range(20):mapping[j*20+pos[j][m]]=m
        for label,pairs in prior_cuts(pos):
            model.add(sum(before(mapping[u],u//20,v//20).Not()
                          for u,v in pairs)>=1)
    model.maximize(minimum)
    _,hint,_,score=graph_analysis(seed_parent,pos,dur)
    assert score==2006
    for i in range(600):
        model.add_hint(s[i],hint[i])
        model.add_hint(e[i],hint[i]+dur[i])
    for (m,j,k),bit in pairvars.items():
        rank={u:i for i,u in enumerate(seed_parent[m])}
        model.add_hint(bit,int(rank[j]<rank[k]))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=a.seed
    t=time.monotonic();status=solver.solve(model)
    report=dict(instance='ta41',best_known_verified_score=2006,
      target=2005,model='full NoOverlap/job chains, max-min 580 baseline adjacent orientations',
      all_machine_orders_free=True,parent_count=len(parents),seed=a.seed,
      require_ten_certified_2005_necessary_core_cuts=a.guided,
      no_survivor_hard_freezing=True,status=solver.status_name(status),
      elapsed_seconds=round(time.monotonic()-t,3),
      conflicts=solver.num_conflicts,branches=solver.num_branches,
      max_min_hamming_solver_bound=solver.best_objective_bound)
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        orders=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
                for m in range(20)]
        score=evaluate(orders,pos,dur)
        assert score is not None and score<=2006,score
        base_kendall=kendall(orders,base)
        parent_kendall={name:kendall(orders,perm) for name,perm in parents.items()}
        parent_adj={}
        for name,perm in parents.items():
            positions=[{j:i for i,j in enumerate(orders[m])} for m in range(20)]
            parent_adj[name]=sum(positions[m][j]>positions[m][k] for m in range(20)
                   for j,k in zip(perm[m],perm[m][1:]))
        report.update(verified_makespan=score,
              minimum_adjacent_orientation_hamming_to_12_parents=round(solver.objective_value),
              minimum_true_kendall_to_12_parents=min(parent_kendall.values()),
              kendall_from_original_baseline=base_kendall,
              changed_machine_orders_from_original=sum(orders[m]!=base[m] for m in range(20)),
              true_kendall_distance_per_parent=parent_kendall,
              new_neutral_orientation_geometry='far' if min(parent_kendall.values())>=80 else 'near')
        folder=a.out/'witness'
        folder.mkdir(parents=True,exist_ok=True)
        (folder/'certificate.json').write_text(json.dumps({'machines':orders},separators=(',',':'))+'\n')
        if score<=2005:
            (a.out/'certificate.json').write_text(json.dumps({'machines':orders},separators=(',',':'))+'\n')
    (a.out/'diversity.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--guided',action='store_true')
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--seconds',type=float,default=180)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
