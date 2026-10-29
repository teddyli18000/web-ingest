#!/usr/bin/env python3
"""Independently replay and quantify a verified 2006 nine-core-crossing ta41 schedule.

Compute exact pairwise Kendall distances and full critical machine-edge
replacement sets against baseline, gateway124 and the 15-swap neutral.
Independently reconstruct all eight separate assumption-core reversal
counts plus 21 consensus pairs and validate their positive hit counts.
No claim that any 2005 schedule has been reached.
"""
import json
from pathlib import Path
from search import obtain,setup,evaluate
from dynamic_critical_replacement import state

ROOT=Path(__file__).resolve().parent

def read(name):
    p=ROOT/'results'/name
    v=json.loads((p/'neutral-verdict.json').read_text()) if name=='ninecore-neutral-baseline' else None
    if v is not None: assert v['valid'] and int(v['score'])==2006
    return json.loads((p/('neutral-certificate.json' if v is not None else 'certificate.json')).read_text())['machines']

def kendall(a,b):
    total=0;machines=0;adj=0
    for ma,mb in zip(a,b):
        ref={job:i for i,job in enumerate(mb)}
        perm=[ref[x] for x in ma]
        d=sum(perm[i]>perm[j] for i in range(30) for j in range(i+1,30))
        total+=d;machines+=int(d>0)
        ranks={job:i for i,job in enumerate(ma)}
        adj+=sum(ranks[mb[i]]>ranks[mb[i+1]] for i in range(29))
    return dict(kendall_pair_distance=total,changed_machine_orders=machines,
                reversed_original_adjacent_pairs=adj)

def main():
    routes,rows,base=obtain()
    pos,dur=setup(routes,rows)
    assert evaluate(base,pos,dur)==2006
    n=read('ninecore-neutral-baseline')
    g=json.loads((ROOT/'results'/'gateway-124'/'certificate.json').read_text())['machines']
    swap=json.loads((ROOT/'results'/'synchronous-single-2006'/'certificate.json').read_text())['machines']
    assert evaluate(n,pos,dur)==evaluate(g,pos,dur)==evaluate(swap,pos,dur)==2006
    audit=json.loads((ROOT/'results'/'dcprcp-independent-core-audit.json').read_text())['records']
    core=json.loads((ROOT/'results'/'consensus-five-parents'/'consensus-analysis.json').read_text())['proven_unsat_core']
    op_machine={j*20+pos[j][m]:m for j in range(30) for m in range(20)}
    rank=[{j:i for i,j in enumerate(seq)} for seq in n]
    hit={}
    for entry in audit:
        assert entry['status']=='INFEASIBLE'
        key=entry['parent']+'-'+entry['policy']
        hit[key]=sum(rank[op_machine[u]][u//20]>rank[op_machine[u]][v//20]
                     for u,v in entry['core_precedences'])
    hit['consensus-21']=sum(rank[c['machine']][c['from_job']]>
                            rank[c['machine']][c['to_job']] for c in core)
    assert len(hit)==9 and all(x>=1 for x in hit.values())
    crit={}
    for name,orders in [('baseline',base),('gateway-124',g),('neutral-swap15',swap),('ninecore-neutral',n)]:
        score,edges,_=state(orders,pos,dur)
        assert score==2006
        crit[name]=edges
    report=dict(
        instance='ta41',objective='Cmax',certified_score=2006,
        official_fewshots_verdict=json.loads((ROOT/'results'/'ninecore-neutral-baseline'/'neutral-verdict.json').read_text()),
        from_original_baseline=kendall(n,base),
        from_gateway_124=kendall(n,g),
        from_neutral_15_swaps=kendall(n,swap),
        core_reversals=hit,
        all_nine_independently_verified_core_cuts_violated_at_least_once=True,
        critical_edge_counts={name:len(edges) for name,edges in crit.items()},
        new_critical_edges_vs_baseline=sorted([list(x) for x in crit['ninecore-neutral']-crit['baseline']]),
        disappeared_critical_edges_vs_baseline=sorted([list(x) for x in crit['baseline']-crit['ninecore-neutral']]),
        new_critical_edges_vs_gateway_124=sorted([list(x) for x in crit['ninecore-neutral']-crit['gateway-124']]),
        lost_critical_edges_vs_gateway_124=sorted([list(x) for x in crit['gateway-124']-crit['ninecore-neutral']]),
        scope='Existing 2006 record is unchanged. This independently reconstructs quantitative novelty of a verified multi-core-crossing 2006 schedule, not evidence that target 2005 is reachable nearby.'
    )
    assert report['from_original_baseline']['changed_machine_orders']==15
    ROOT.joinpath('results/ninecore-neutral-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print('RESULT',json.dumps({k:(len(v) if k.startswith(('new_critical','lost_critical','disappeared_critical')) else v) for k,v in report.items() if k!='scope'}),flush=True)

if __name__=='__main__':main()
