#!/usr/bin/env python3
"""Fully soft precedence-orientation repair after dynamic critical path release.

Critical distinction: previous 240-op CP LNS retained 340 hard survivor
machine-precedence arcs, and was UNSAT almost instantly at 2005.
Here NO survivor precedence arc is hard-pinned. Every original survivor
adjacency gets a reified keep/REVERSE binary variable. All 20 machine
NoOverlap constraints and all 570 job arcs are hard. Hence every legal
ta41 schedule is representable; this is a *complete* global model with a
bias over different but fully legal schedule orientations.

We use a previously *independently* verified sufficient UNSAT core to
require at least one reversal in that core (a necessary condition for
2005, but not sufficient). Different arms assign cheap orientation flip
weights to:
 dynamic: boundary of recently released dynamic path operations,
 static: original near-critical machine precedence neighborhoods,
 core: CP independent sufficient-UNSAT core itself,
 random: equally many random survivors.
The exact solver minimizes Cmax (dominant coefficient) and secondarily
weighted flips, with incumbent hints. It may prove OPTIMAL for the
*global* ta41 problem only if CP-SAT says OPTIMAL; otherwise not.
This is NOT Liu-Li-Gao's specific parameterization formula.
"""
import argparse,json,random,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis
from temporal_band_repair import fixed_precedence
from dynamic_critical_replacement import state

ROOT=Path(__file__).resolve().parent

def load(a):
    routes,ds,base=obtain()
    pos,dur=setup(routes,ds)
    assert evaluate(base,pos,dur)==2006
    parent=base
    if a.parent!='baseline':
        f=ROOT/'results'/('gateway-'+a.parent)
        vr=json.loads((f/'upstream-verdict.json').read_text())
        assert vr['valid'] and int(vr['score'])==2006
        parent=json.loads((f/'certificate.json').read_text())['machines']
    initial=json.loads((ROOT/'results'/f'dcprcp-{a.parent}-dynamic-4107'/'dynamic-repair.json').read_text())
    release=set(u for rec in initial['release_sets'] for u in rec['released_this_round'])
    assert len(release)==240
    audit=json.loads((ROOT/'results'/'dcprcp-independent-core-audit.json').read_text())
    record=next(x for x in audit['records'] if x['parent']==a.parent and x['policy']=='dynamic')
    assert record['status']=='INFEASIBLE' and len(record['core_precedences'])>0
    core={tuple(x) for x in record['core_precedences']}
    fixed=fixed_precedence(parent,pos,release)
    assert core.issubset(set(fixed)),(len(core-set(fixed)))
    return parent,pos,dur,initial,core,fixed,release

def cheap_arcs(a,parent,pos,initial,core,fixed):
    k=70
    rng=random.Random(a.seed)
    positions=[{j*20+pos[j][m]:i for i,j in enumerate(parent[m])} for m in range(20)]
    if a.policy=='random':
        return set(rng.sample(fixed,k))
    if a.policy=='core':
        return set(sorted(core,key=lambda arc:(arc[0],arc[1]))[:k])
    _,crit,near=state(parent,pos, __DURATION__) # replaced by required runtime binding
    if a.policy=='static':
        focus_ops=set()
        for m,j,h in near:
            focus_ops.add(j*20+pos[j][m])
            focus_ops.add(h*20+pos[h][m])
    else:
        # Dynamic-path source: last three release rounds were chosen after
        # repeated accepted critical-path replacement observations.
        focus_ops=set(u for rec in initial['release_sets'][-3:]
                        for u in rec['released_this_round'])
    scored=[]
    for u,v in fixed:
        m=next(m for m in range(20) if u in positions[m])
        i,j=positions[m][u],positions[m][v]
        pressure=0
        if a.policy=='static':
            pressure=int(u in focus_ops)+int(v in focus_ops)
            # Near-critical neighbors on same machine receive a smaller
            # discount; different strategies have fixed 70 favored arcs.
            pressure+=sum(abs(positions[m].get(x,100)-i)<=2 for x in focus_ops)
        else:
            pressure=sum(
                int(x in positions[m] and abs(positions[m][x]-i)<=3)
                for x in focus_ops)
        scored.append((pressure, rng.random(), (u,v)))
    scored.sort(reverse=True)
    return {x[2] for x in scored[:k]}

def run(a):
    parent,pos,dur,initial,core,fixed,release=load(a)
    global __DURATION__
    __DURATION__=dur
    favored=cheap_arcs(a,parent,pos,initial,core,fixed)
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2006,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,2006,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    bits={}
    for idx,(u,v) in enumerate(fixed):
        rev=model.new_bool_var('reorient_%d'%idx)
        model.add(s[v]>=e[u]).only_enforce_if(rev.Not())
        model.add(s[u]>=e[v]).only_enforce_if(rev)
        bits[(u,v)]=rev
    # At 2005 at least one originally fixed core precedence MUST reverse.
    # The core is a verified sufficient UNSAT core, but is not minimized.
    model.add(sum(bits[arc] for arc in core)>=1)
    cmax=model.new_int_var(0,2006,'Cmax')
    model.add_max_equality(cmax,e)
    objective_weight=10000
    secondary=sum((1 if arc in favored else 8)*bit
                  for arc,bit in bits.items())
    model.minimize(objective_weight*cmax+secondary)
    _,hint,_,val=graph_analysis(parent,pos,dur)
    assert val==2006
    for i in range(600):
        model.add_hint(s[i],hint[i])
        model.add_hint(e[i],hint[i]+dur[i])
    model.add_hint(cmax,2006)
    parent_pos=[{job:i for i,job in enumerate(seq)} for seq in parent]
    for arc,bit in bits.items():
        u,v=arc
        j=u//20;h=v//20
        m=next(m for m in range(20) if u==j*20+pos[j][m])
        model.add_hint(bit,int(parent_pos[m][j]>parent_pos[m][h]))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=a.seed
    start=time.monotonic()
    result=solver.solve(model)
    out=dict(instance='ta41',parent=a.parent,policy=a.policy,seed=a.seed,
        method='complete global JSSP with soft survivor-pair orientations; no frozen survivor order',
        full_resource_NoOverlap=True,
        incumbent_score=2006,target=2005,
        total_prior_hard_survivor_relations=len(fixed),
        now_soft_reorientation_variables=len(bits),favored_low_cost_arcs=len(favored),
        independently_verified_core_arcs=len(core),
        required_core_flips_at_least_one=True,
        status=solver.status_name(result),wall_seconds=round(time.monotonic()-start,3),
        branches=solver.num_branches,conflicts=solver.num_conflicts,
        objective_weight=objective_weight,
        best_objective_bound=solver.best_objective_bound,
        note='All 340 survivor arcs are now independently reversible; this is global, not a conditioned fixed-survivor subspace. FEASIBLE 2006 does not rule out 2005.')
    a.out.mkdir(parents=True,exist_ok=True)
    if result in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        cert=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
              for m in range(20)]
        actual=evaluate(cert,pos,dur)
        assert actual is not None and actual<=2006
        flipped=[(u,v) for (u,v),b in bits.items() if solver.value(b)]
        assert any(arc in flipped for arc in core)
        out.update(verified_dag_makespan=actual,changed_survivor_pair_orientations=len(flipped),
                   favored_flips=sum(x in favored for x in flipped),
                   objective_value=solver.objective_value)
        if actual<=2005:
            (a.out/'certificate.json').write_text(json.dumps({'machines':cert},separators=(',',':'))+'\n')
    (a.out/'soft-orientation.json').write_text(json.dumps(out,indent=2)+'\n')
    print('RESULT',json.dumps(out),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=['baseline','124'],required=True)
    p.add_argument('--policy',choices=['dynamic','static','core','random'],required=True)
    p.add_argument('--seed',type=int,default=4107)
    p.add_argument('--seconds',type=int,default=130)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
