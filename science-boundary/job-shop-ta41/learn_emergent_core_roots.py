#!/usr/bin/env python3
"""Source-only *emergent-core* predictor of hidden resource conflicts.

Given a 30x20 incumbent and target <=Cmax-1, build its partial-order CSP:
all job arcs, full 20 NoOverlap constraints, and 580 incumbent adjacent
machine relations as assumptions. Extract initial sufficient UNSAT core C0.

For EACH original core relation c, hypothetically release just c, and
extract the new sufficient core C_c. The empirical emergence count
E(r)=|{c in C0 : r in C_c\C0}| ranks resource relations which are
*invisible* in the initial conflict but are frequently exposed by
many independent first-step relaxations.

E is hypothesis-guided evidence of replacement bottlenecks, NOT a
necessary or sufficient condition for improvement. It needs strong
held-out benchmarks, and may depend on the CP solver explanation heuristic.
The scoring reads ZERO archived better solutions. A separately run
post-hoc audit may compare ranks with valid complete witnesses.
"""
import argparse,json,time,random
from pathlib import Path
from collections import Counter
from partial_resource_pair_repair import parse_case
from counterfactual_core_replacement import build,query
from structural_cut import disjunctive_dag

ROOT=Path(__file__).resolve().parent
def run(a):
    orders,pos,dur,incumbent=parse_case(a.start)
    L=incumbent-1
    model,bits=build(orders,pos,dur,L)
    begin=time.monotonic()
    initial=query(model,bits,set(),a.query_seconds,a.seed)
    result=dict(case=('ta41' if a.start=='ta41' else Path(a.start).parent.name),
       incumbent=incumbent,target=L,seed=a.seed,
       source_only=True,
       initial_core_status=initial['status'],
       initial_core=initial.get('core',[]),probe_results=[],
       ranking=[],
       method='Initial sufficient UNSAT core; one-candidate release per core item; rank new relations by their frequency in successor cores; no oracle.')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    if initial['status']!='INFEASIBLE':
        result['status']='INITIAL_'+initial['status']
        a.out.write_text(json.dumps(result,indent=2)+'\n')
        return
    C0=set(initial['core'])
    assert 0<len(C0)<=580
    emergent=Counter()
    replacement=Counter()
    tried=0
    for c in sorted(C0):
        rec=query(model,bits,{c},a.query_seconds,a.seed)
        entry=dict(removed_initial_core_arc=c,status=rec['status'],
                   seconds=rec['wall_seconds'])
        if rec['status']=='INFEASIBLE':
            new=set(rec['core'])
            emergence=new-C0
            for x in emergence:emergent[x]+=1
            for x in new:replacement[x]+=1
            entry.update(successor_core_size=len(new),
                         new_core_arc_count=len(emergence),
                         new_core_arc_ids=sorted(emergence))
        result['probe_results'].append(entry)
        tried+=1
    _,arcs,_,head,tail,C=disjunctive_dag(orders,pos,dur,set())
    assert C==incumbent and len(arcs)==580
    slack=[C-(head[u]+dur[u]+tail[v]) for m,k,u,v in arcs]
    out=[]
    for i in range(580):
        if i in C0:continue
        neighbors=sum((i+offset) in C0 and (i+offset)//29==i//29
                      for offset in (-2,-1,1,2))
        out.append(dict(resource_arc_id=i,machine=i//29,
                source_core_emergence_frequency=emergent[i],
                source_core_neighbor_density=neighbors,
                original_critical_slack=slack[i]))
    out.sort(key=lambda x:(-x['source_core_emergence_frequency'],
        -x['source_core_neighbor_density'],
        x['original_critical_slack'],x['resource_arc_id']))
    result.update(status='COMPLETE',num_core_probes=tried,
        num_infeasible_followups=sum(x['status']=='INFEASIBLE' for x in result['probe_results']),
        num_unknown_followups=sum(x['status']=='UNKNOWN' for x in result['probe_results']),
        emerged_distinct_resource_arcs=sum(bool(x) for x in emergent.values()),
        top_ranked_outside_initial_core=out[:a.keep],
        top_ranked_all_relations_by_static_slack=sorted(
            range(580),key=lambda i:(slack[i],i))[:a.keep],
        full_ranked_arc_ids=[x['resource_arc_id'] for x in out],
        wall_seconds=round(time.monotonic()-begin,3))
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print('RESULT',result['case'],'initial core',len(C0),
       'followup UNSAT',result['num_infeasible_followups'],
       'emergent',len(emergent),'top',[(x['resource_arc_id'],
            x['source_core_emergence_frequency']) for x in out[:10]],
       flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--start',required=True)
    p.add_argument('--query-seconds',type=float,default=0.55)
    p.add_argument('--seed',type=int,default=403)
    p.add_argument('--keep',type=int,default=40)
    p.add_argument('--out',type=Path,required=True)
    run(p.parse_args())
