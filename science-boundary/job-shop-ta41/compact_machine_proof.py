#!/usr/bin/env python3
"""Portable compact >=8 machine-order escape certificate for ta41.

Find a small subset of empirically learned fixed-machine UNSAT cores such
that EVERY choice of at most seven changed machine orders leaves at least
one of these cores entirely fixed. Exhaustively check all 137,980 such
20-bit choices, then *independently* reconstruct each selected core's
hard-constraint CP-SAT model and prove infeasibility at makespan 2005.

Compared with the original core collector, verification never relies on
assumption literals or the collector's own model state.
"""
import argparse,itertools,json,time
from pathlib import Path
from ortools.sat.python import cp_model
from search import obtain,setup,evaluate

def select(cores):
    candidates=[x for x in range(1<<20) if x.bit_count()<=7]
    n=len(candidates)
    bitsets=[]
    for core in cores:
        mask=sum(1<<m for m in core)
        bits=bytearray((n+7)//8)
        for i,v in enumerate(candidates):
            if not (v & mask):bits[i>>3]|=1<<(i&7)
        bitsets.append(int.from_bytes(bits,'little'))
    uncovered=(1<<n)-1
    selected=[]
    while uncovered:
        hits=[(uncovered&bits).bit_count() if i not in selected else 0
              for i,bits in enumerate(bitsets)]
        ix=max(range(len(hits)),key=lambda x:hits[x])
        if not hits[ix]:
            raise AssertionError('the existing core collection does not prove >=8 changes')
        selected.append(ix)
        uncovered&=~bitsets[ix]
    chosen=[sum(1<<m for m in cores[ix]) for ix in selected]
    assert all(any((v & mask)==0 for mask in chosen) for v in candidates)
    return selected,len(candidates)


def hard_status(core,pos,duration,target,seconds):
    model=cp_model.CpModel()
    s=[model.new_int_var(0,target,'s%d'%i) for i in range(600)]
    e=[model.new_int_var(0,target,'e%d'%i) for i in range(600)]
    iv=[model.new_interval_var(s[i],duration[i],e[i],'iv%d'%i) for i in range(600)]
    for j in range(30):
        for k in range(19):model.add(s[j*20+k+1]>=e[j*20+k])
    routes, ds, orders = INSTANCE
    for m in range(20):
        model.add_no_overlap([iv[j*20+pos[j][m]] for j in range(30)])
        if m in core:
            for a,b in zip(orders[m],orders[m][1:]):
                model.add(s[b*20+pos[b][m]]>=e[a*20+pos[a][m]])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=41
    t=time.monotonic();result=solver.solve(model)
    return solver.status_name(result),round(time.monotonic()-t,3)

INSTANCE=None

def main(a):
    global INSTANCE
    dat=json.loads(a.cores.read_text())
    raw=[list(c) for c in dat['cores']]
    assert dat['target']==2005 and dat['baseline']==2006 and len(raw)>=100
    for c in raw:assert c and len(set(c))==len(c) and all(0<=m<20 for m in c)
    idx,n=select(raw)
    routes,ds,orders=obtain(); INSTANCE=(routes,ds,orders)
    pos,dur=setup(routes,ds)
    assert evaluate(orders,pos,dur)==2006
    cases=[]
    for i in idx:
        status,sec=hard_status(set(raw[i]),pos,dur,2005,a.seconds)
        cases.append({'source_core_index':i,'fixed_machines':raw[i],
                      'independent_hard_cp_status':status,'seconds':sec})
        print('CORE',len(cases),'of',len(idx),i,raw[i],status,flush=True)
        if status!='INFEASIBLE':break
    complete=len(cases)==len(idx) and all(c['independent_hard_cp_status']=='INFEASIBLE' for c in cases)
    report={
      'instance':'ta41','target':2005,'baseline':2006,
      'source_machine_core_count':len(raw),
      'selected_machine_core_count':len(idx),
      'all_changed_machine_subsets_size_at_most_seven_enumerated':n,
      'finite_hypergraph_cover_verified':True,
      'independent_core_infeasibility_checks_complete':complete,
      'conclusion':('ANY <=2005 schedule must differ from incumbent on >=8 machines'
                    if complete else 'No independent lower bound claimed (incomplete core revalidation)'),
      'selected_hard_core_verdicts':cases,
      'proof_logic':'If <=7 machines change, some selected core lies fully in unchanged machine orders; its infeasibility at 2005 is then a contradiction.',
      'solver_version':__import__('ortools').__version__,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:v for k,v in report.items() if k!='selected_hard_core_verdicts'}),flush=True)
    if not complete:raise RuntimeError('Independent core verification incomplete')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cores',type=Path,default=Path(__file__).parent/'results'/'machine-cores'/'machine-core-analysis.json')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'machine-core-compact-proof.json')
    p.add_argument('--seconds',type=float,default=12)
    main(p.parse_args())
