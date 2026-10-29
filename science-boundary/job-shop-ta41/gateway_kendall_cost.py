#!/usr/bin/env python3
"""Find the minimal coordinated Kendall cost to reverse one proven necessary arc.

The 21-arc certified consensus UNSAT core implies that every score<=2005
solution must reverse AT LEAST ONE of these specific baseline machine
precedences. For selected gateway arcs, force the reversal but optimize
the exact 8700-pair Kendall distance of a score<=2006 schedule.

Uses a verified 2006 neutral parent already reversing the arc as an
initial feasible hint, then the full CP-SAT model may discover nearer
solutions. The numeric objective lower bound is solver-certified only
if status proves it; a feasible 2006 incumbent gives an UPPER bound,
not an exact minimum unless status OPTIMAL.

Note: minimizing gateway reversal cost at Cmax<=2006 does not directly
bound the cost of a Cmax<=2005 schedule.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
from core_guided_lns import graph_analysis

ROOT=Path(__file__).resolve().parent
PARENTS={
  124:'warm-backbone-5',
  120:'warm-backbone-6',
  127:'continuation-7',
}

def kendall(a,b):
    count=0
    for m in range(20):
        p={j:i for i,j in enumerate(b[m])}
        q=[p[x] for x in a[m]]
        count+=sum(q[i]>q[j] for i in range(30) for j in range(i+1,30))
    return count

def main(a):
    routes,rows,base=obtain();pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    coredata=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())
    edge=next(c for c in coredata['proven_unsat_core'] if c['index']==a.arc)
    folder=ROOT/'results'/PARENTS[a.arc]
    parent=json.loads((folder/'neutral-certificate.json').read_text())['machines']
    vr=json.loads((folder/'best-verdict.json').read_text())
    assert vr['valid'] and int(vr['score'])==2006 and evaluate(parent,pos,dur)==2006
    assert parent[edge['machine']].index(edge['from_job'])>parent[edge['machine']].index(edge['to_job'])
    _,start_hint,_,crit=graph_analysis(parent,pos,dur)
    assert crit==2006
    model=cp_model.CpModel()
    s=[model.new_int_var(0,2006,f's{i}') for i in range(600)]
    e=[model.new_int_var(0,2006,f'e{i}') for i in range(600)]
    iv=[model.new_interval_var(s[i],dur[i],e[i],f'iv{i}') for i in range(600)]
    for i in range(600):
        model.add_hint(s[i],start_hint[i])
        model.add_hint(e[i],start_hint[i]+dur[i])
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    inverted=[]
    for m in range(20):
        base_ops=[j*20+pos[j][m] for j in base[m]]
        model.add_no_overlap([iv[u] for u in base_ops])
        ranks={j:i for i,j in enumerate(parent[m])}
        for i in range(30):
            for j in range(i+1,30):
                x=base_ops[i];y=base_ops[j]
                b=model.new_bool_var(f'flip_{m}_{i}_{j}')
                model.add(s[y]>=e[x]).only_enforce_if(b.Not())
                model.add(s[x]>=e[y]).only_enforce_if(b)
                model.add_hint(b, int(ranks[base[m][i]]>ranks[base[m][j]]))
                inverted.append(b)
    u=edge['from_job']*20+pos[edge['from_job']][edge['machine']]
    v=edge['to_job']*20+pos[edge['to_job']][edge['machine']]
    model.add(s[u]>=e[v])
    model.minimize(sum(inverted))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=4
    solver.parameters.random_seed=a.seed
    st=time.monotonic();status=solver.solve(model)
    report={'instance':'ta41','target_upper_bound':2006,
        'required_gateway_arc':edge,
        'objective':'minimum Kendall distance over all 8700 baseline machine job pairs',
        'known_verified_parent_kendall_distance':kendall(parent,base),
        'status':solver.status_name(status),
        'seconds':round(time.monotonic()-st,3),
        'solver_objective_lower_bound':solver.best_objective_bound,
        'branches':solver.num_branches,'conflicts':solver.num_conflicts,
        'interpretation':'Feasible candidate gives an upper bound on gateway cost; OPTIMAL alone proves exact minimum. This 2006 gateway cost is not automatically a 2005 bound.'}
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        solution=[sorted(range(30),key=lambda j:solver.value(s[j*20+pos[j][m]]))
                  for m in range(20)]
        score=evaluate(solution,pos,dur);dist=kendall(solution,base)
        assert score is not None and score<=2006
        assert dist==round(solver.objective_value),(dist,solver.objective_value)
        assert solution[edge['machine']].index(edge['from_job'])>solution[edge['machine']].index(edge['to_job'])
        report.update(verified_makespan=score,found_kendall_distance=dist)
        (a.out/'certificate.json').write_text(json.dumps({'machines':solution},separators=(',',':'))+'\n')
    (a.out/'gateway-cost.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--arc',type=int,choices=tuple(PARENTS),required=True)
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--seed',type=int,default=202614)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
