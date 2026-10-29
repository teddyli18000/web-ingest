#!/usr/bin/env python3
"""Jointly satisfy ALL independently proved 2005 necessary disjunctions.

No original survivor precedence is frozen. Every machine's full
NoOverlap and every job chain remain unconditional hard constraints.
The exact 2005 feasibility subspace is tightened only by conditions
INDEPENDENTLY CERTIFIED NECESSARY for a <=2005 solution:
 (1) at least 15/20 machine permutations differ from the official 2006
     baseline (independent full CP-SAT <=14 model INFEASIBLE),
 (2) reverse at least one directed machine pair from each of eight
     independently hard-NoOverlap-audited assumption UNSAT cores after
     dynamic 240-operation release (sources: both parents x four policies),
 (3) reverse at least one from the 21-arc consensus UNSAT core.

Each orientation variable is a genuine machine-job pair Boolean, not
a placeholder for merely relaxing a precedence. Thus a candidate can
reorient ANY machine pair, including outside the 9 learned cores.

The 2006 feasibility horizon is deliberately retained with a dominating
Cmax term and small orientation penalty. This permits warmstarts and
strictly checks any found makespan<=2005. A FEASIBLE 2006 outcome is NOT
an infeasibility certificate. Solver CP bound alone is not a record.
"""
import argparse,json,time,random
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis
from dynamic_critical_replacement import state

ROOT=Path(__file__).resolve().parent

def source_cuts():
    audit=json.loads((ROOT/'results'/'dcprcp-independent-core-audit.json').read_text())
    assert len(audit['records'])==8
    cuts=[]
    for r in audit['records']:
        assert r['status']=='INFEASIBLE'
        cut=[tuple(x) for x in r['core_precedences']]
        assert cut
        cuts.append((f"{r['parent']}-{r['policy']}",cut))
    consensus=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    assert consensus['status']=='INFEASIBLE' and len(consensus['proven_unsat_core'])==21
    # Consensus uses m + job identities; conversion to operation IDs
    # occurs after the fixed-route instance is loaded.
    return cuts,consensus['proven_unsat_core']

def run(a):
    routes,rows,base=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    proof=json.loads((ROOT/'results'/'machine-budget14'/'decision.json').read_text())
    assert proof['status']=='INFEASIBLE' and proof['maximum_changed_machine_orders']==14 and proof['target']==2005
    parent=base
    if a.parent!='baseline':
        folder=ROOT/'results'/'gateway-124'
        vr=json.loads((folder/'upstream-verdict.json').read_text())
        assert vr['valid'] and int(vr['score'])==2006
        parent=json.loads((folder/'certificate.json').read_text())['machines']
    assert evaluate(parent,pos,dur)==2006
    cuts,consensus=source_cuts()
    cuts.append(('consensus-21',[(x['from_job']*20+pos[x['from_job']][x['machine']],
                                  x['to_job']*20+pos[x['to_job']][x['machine']])
                                 for x in consensus]))
    # all 600 op IDs map to their one fixed machine.
    mach_of=[-1]*600
    for j in range(30):
        for m in range(20):mach_of[j*20+pos[j][m]]=m
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2006,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,2006,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
    # canonical bool orientation: true iff smaller job ID runs first.
    bits={}
    def orient(u,v):
        assert mach_of[u]==mach_of[v] and u//20!=v//20
        m=mach_of[u];a,b=sorted((u//20,v//20))
        key=(m,a,b)
        if key not in bits:
            var=model.new_bool_var('machine_pair_%d_%d_%d'%key)
            x=a*20+pos[a][m];y=b*20+pos[b][m]
            model.add(s[y]>=e[x]).only_enforce_if(var)
            model.add(s[x]>=e[y]).only_enforce_if(var.Not())
            bits[key]=var
        var=bits[key]
        return var if u//20==a else var.Not()
    cuts_metadata=[]
    for name,pairs in cuts:
        violations=[orient(u,v).Not() for u,v in pairs]
        model.add(sum(violations)>=1)
        cuts_metadata.append(dict(source=name,necessary_arc_count=len(pairs)))
    # All baseline-adjacent pair orientations, 580; one original
    # inversion is necessary whenever its machine permutation changes.
    machine_changed=[]
    baseline_reversals=[]
    baseline_reverse_keys=[]
    for m in range(20):
        revs=[]
        seq=base[m]
        for ja,jb in zip(seq,seq[1:]):
            u=ja*20+pos[ja][m];v=jb*20+pos[jb][m]
            lit=orient(u,v).Not()
            revs.append(lit);baseline_reversals.append(lit)
            baseline_reverse_keys.append((u,v,m))
        active=model.new_bool_var('changed_machine_%d'%m)
        model.add_max_equality(active,revs)
        machine_changed.append(active)
    model.add(sum(machine_changed)>=15)
    # Preference weights, not fixed precedences. All nine necessary
    # cuts and >=15 machines apply identically across policies.
    rng=random.Random(a.seed)
    focus_arcs=set(tuple(p) for _,pairs in cuts for p in pairs)
    _,critical,near=state(parent,pos,dur)
    crit_ops=set()
    for m,j,h in critical:
        crit_ops.add(j*20+pos[j][m]);crit_ops.add(h*20+pos[h][m])
    near_ops=set()
    for m,j,h in near:
        near_ops.add(j*20+pos[j][m]);near_ops.add(h*20+pos[h][m])
    released_dynamic={u for rec in json.loads((ROOT/'results'/f'dcprcp-{a.parent}-dynamic-4107'/'dynamic-repair.json').read_text())['release_sets'][-3:] for u in rec['released_this_round']}
    # discount 100 baseline-adjacent variables according to signal.
    scored=[]
    for k,(u,v,m) in enumerate(baseline_reverse_keys):
        if a.policy=='dynamic':weight=int(u in released_dynamic)+int(v in released_dynamic)+int(u in crit_ops)+int(v in crit_ops)
        elif a.policy=='static':weight=int(u in near_ops)+int(v in near_ops)
        elif a.policy=='core':weight=int((u,v) in focus_arcs)+int((v,u) in focus_arcs)
        else:weight=0
        scored.append((weight,rng.random(),k))
    if a.policy=='random':
        cheap=set(rng.sample(range(len(scored)),100))
    else:
        scored.sort(reverse=True)
        cheap={k for _,_,k in scored[:100]}
    obj_weight=100000
    score=model.new_int_var(0,2006,'Cmax')
    model.add_max_equality(score,e)
    model.minimize(obj_weight*score+sum((1 if k in cheap else 8)*v for k,v in enumerate(baseline_reversals)))
    _,hints,_,original=graph_analysis(parent,pos,dur)
    assert original==2006
    for op in range(600):
        model.add_hint(s[op],hints[op])
        model.add_hint(e[op],hints[op]+dur[op])
    model.add_hint(score,2006)
    # Machine pair hints represent the actual verified neutral parent.
    for (m,ja,jb),lit in bits.items():
        rnk={j:i for i,j in enumerate(parent[m])}
        model.add_hint(lit,int(rnk[ja]<rnk[jb]))
    cp=cp_model.CpSolver()
    cp.parameters.max_time_in_seconds=a.seconds
    cp.parameters.num_search_workers=4
    cp.parameters.random_seed=a.seed
    start=time.monotonic()
    status=cp.solve(model)
    report=dict(instance='ta41',target=2005,reference=2006,
        parent=a.parent,policy=a.policy,seed=a.seed,
        nine_independently_validated_necessary_orientation_cuts=cuts_metadata,
        required_changed_machine_orders=15,
        orientation_boolean_count=len(bits),
        baseline_adjacent_order_variables=580,
        all_pairs_unrestricted_except_true_job_resource_constraints=True,
        status=cp.status_name(status),
        objective_bound=cp.best_objective_bound,
        conflicts=cp.num_conflicts,branches=cp.num_branches,
        seconds=round(time.monotonic()-start,3),
        claimed_global_proof=False,
        note='All nine cuts are necessary for <=2005; optimization with horizon 2006 may return a neutral feasible solution. UNKNOWN/FEASIBLE do not prove target impossible.')
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        cert=[sorted(range(30),key=lambda j:cp.value(s[j*20+pos[j][m]]))
              for m in range(20)]
        makespan=evaluate(cert,pos,dur)
        assert makespan is not None and makespan<=2006
        n_changed=sum(cert[m]!=base[m] for m in range(20))
        assert n_changed>=15
        report.update(verified_score=makespan,changed_machine_orders=n_changed,
                      solver_objective=cp.objective_value,
                      reversed_baseline_adjacencies=sum(cp.value(x) for x in baseline_reversals),
                      cuts_checked={name:sum(cert[mach_of[u]].index(u//20)>cert[mach_of[u]].index(v//20)
                                  for u,v in pairs) for name,pairs in cuts})
        assert all(v>=1 for v in report['cuts_checked'].values())
        if makespan<=2005:
            (a.out/'certificate.json').write_text(json.dumps({'machines':cert},separators=(',',':'))+'\n')
        if makespan==2006:
            # Retain every machine permutation for an independently checked
            # neutral schedule satisfying all 9 necessary 2005 core cuts.
            (a.out/'neutral-certificate.json').write_text(
                json.dumps({'machines':cert},separators=(',',':'))+'\n')
    (a.out/'all-cores-reorientation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',choices=['baseline','124'],required=True)
    p.add_argument('--policy',choices=['dynamic','core','static','random'],required=True)
    p.add_argument('--seed',type=int,default=4113)
    p.add_argument('--seconds',type=float,default=150)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
