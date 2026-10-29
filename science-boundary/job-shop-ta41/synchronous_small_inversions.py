#!/usr/bin/env python3
"""Atomic multi-machine adjacent swaps: a complete small-Kendall neighborhood.

On each machine, select up to r disjoint adjacent transpositions of the
original order, simultaneously. Preserve all pairs originally separated
by >=2 positions. The final order differs by exactly the selected swaps,
so its Kendall distance is exactly their count. CP-SAT finds a final
feasible schedule directly, without making intermediate moves feasible.
UNKNOWN is never interpreted as an exclusion.
"""
import argparse,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate
ROOT=Path(__file__).resolve().parent

def distance(new,base):
    changed=0;distance=0
    for m in range(20):
        idx={j:i for i,j in enumerate(base[m])}
        p=[idx[j] for j in new[m]]
        d=sum(p[i]>p[j] for i in range(30) for j in range(i+1,30))
        changed+=(d>0);distance+=d
    return distance,changed

def main(a):
    routes,durs,base=obtain();pos,dur=setup(routes,durs)
    original=base
    if a.parent != 'baseline':
        folder=ROOT/'results'/('gateway-'+a.parent)
        verdict=json.loads((folder/'upstream-verdict.json').read_text())
        assert verdict['valid'] and int(verdict['score'])==2006
        base=json.loads((folder/'certificate.json').read_text())['machines']
    assert evaluate(base,pos,dur)==2006
    assert evaluate(original,pos,dur)==2006
    mod=cp_model.CpModel()
    s=[mod.new_int_var(0,a.target,f's{i}') for i in range(600)]
    e=[mod.new_int_var(0,a.target,f'e{i}') for i in range(600)]
    iv=[mod.new_interval_var(s[i],dur[i],e[i],f'iv{i}') for i in range(600)]
    for j in range(30):
        for k in range(19):mod.add(s[j*20+k+1]>=e[j*20+k])
    flips=[];changed=[]
    for m in range(20):
        seq=[j*20+pos[j][m] for j in base[m]]
        mod.add_no_overlap([iv[i] for i in seq])
        bs=[mod.new_bool_var(f'flip_{m}_{k}') for k in range(29)]
        flips.extend(bs)
        mod.add(sum(bs)<=a.per_machine)
        for k in range(28):mod.add(bs[k]+bs[k+1]<=1)
        for k in range(29):
            mod.add(s[seq[k+1]]>=e[seq[k]]).only_enforce_if(bs[k].Not())
            mod.add(s[seq[k]]>=e[seq[k+1]]).only_enforce_if(bs[k])
        for i in range(30):
            for j in range(i+2,30):
                mod.add(s[seq[j]]>=e[seq[i]])
        active=mod.new_bool_var(f'changed_{m}')
        mod.add_max_equality(active,bs)
        changed.append(active)
    mod.add(sum(flips)>=a.min_swaps)
    mod.add(sum(flips)<=a.max_swaps)
    mod.add(sum(changed)>=a.min_machines)
    slv=cp_model.CpSolver()
    slv.parameters.max_time_in_seconds=a.seconds
    slv.parameters.num_search_workers=4
    slv.parameters.random_seed=9241
    begin=time.monotonic();status=slv.solve(mod)
    out={'instance':'ta41','target_makespan':a.target,'baseline_makespan':2006,'source_parent':a.parent,
         'representation':'simultaneous disjoint adjacent swaps; no intermediate schedule required',
         'per_machine_max_swaps':a.per_machine,'min_swaps':a.min_swaps,
         'max_swaps':a.max_swaps,'min_changed_machine_orders':a.min_machines,
         'status':slv.status_name(status),'seconds':round(time.monotonic()-begin,3),
         'conflicts':slv.num_conflicts,'branches':slv.num_branches,
         'ortools_version':__import__('ortools').__version__,
         'scope':'Only disjoint adjacent swaps at each machine; no global distance theorem if INFEASIBLE.'}
    a.out.mkdir(parents=True,exist_ok=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        orders=[sorted(range(30),key=lambda j:slv.value(s[j*20+pos[j][m]]))
                for m in range(20)]
        score=evaluate(orders,pos,dur)
        dist,nchanged=distance(orders,base)
        chosen=sum(slv.value(v) for v in flips)
        assert score is not None and score<=a.target
        assert dist==chosen and a.min_swaps<=dist<=a.max_swaps,(dist,chosen)
        assert nchanged>=a.min_machines
        out.update(verified_makespan=score,exact_kendall_distance=dist,
                   changed_machine_orders=nchanged)
        (a.out/'certificate.json').write_text(json.dumps({'machines':orders})+'\n')
    (a.out/'decision.json').write_text(json.dumps(out,indent=2)+'\n')
    print('RESULT',json.dumps(out),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--parent',type=str,choices=('baseline','120','124','127'),default='baseline')
    p.add_argument('--target',type=int,required=True)
    p.add_argument('--per-machine',type=int,required=True)
    p.add_argument('--min-swaps',type=int,default=15)
    p.add_argument('--max-swaps',type=int,required=True)
    p.add_argument('--min-machines',type=int,default=15)
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--out',type=Path,required=True)
    main(p.parse_args())
