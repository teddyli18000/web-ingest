#!/usr/bin/env python3
"""Quantify Concorde fractional edges that CROSS competing-wiring components.

In contrast to local LP edges (typically already seen in historic routes),
cross-block fractional edges connect otherwise separate historical alternative
wiring regions. These edges may offer missing global repair interfaces.
This script only inventories them; it makes no optimality assertion.
"""
import argparse,json
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import historical_lp_disagreement as h
N=100000
def main():
 p=argparse.ArgumentParser()
 for a in ('regions','lps','baseline','report','edges'):p.add_argument('--'+a,required=True)
 args=p.parse_args()
 components=json.loads(Path(args.regions).read_text())['components']
 place=np.full(N,-1,dtype=np.int32)
 for c in components:
    vs=np.asarray(c['members_0based'],dtype=np.int32)
    place[vs]=int(c['id'])
 counts=Counter()
 source=json.loads(Path(args.lps).read_text())
 lpdata={key:h.lp_read(path) for key,path in source.items()}
 prim=lpdata['2012-04-18']
 base=np.asarray(json.loads(Path(args.baseline).read_text())['tour'],dtype=np.int32)-1
 basekeys=set(map(int,h.tour_edges(base)))
 x_by_e=defaultdict(list)
 for name,lp in lpdata.items():
    for e,x,isfrac in zip(lp['edge_ids'],lp['x'],lp['frac']):
        if isfrac:x_by_e[int(e)].append((name,float(x)))
 order=sorted(components,key=lambda c:(-c['priority_score'],-c['joint_nodes']))
 top_sets={str(n):set(int(c['id']) for c in order[:n]) for n in (1,3,8,20,50)}
 records=[]
 for e,x in zip(prim['edge_ids'],prim['x']):
    if not 1e-5<x<1-1e-5:continue
    ek=int(e);u,w=ek//N,ek%N
    cu,cw=int(place[u]),int(place[w])
    if cu==cw:continue
    counts['all_fractional_cross_component']+=1
    if ek in basekeys:counts['cross_component_baseline']+=1;continue
    records.append({'edge_id':ek,'u':u,'v':w,'lp_x':round(float(x),8),
       'persistence':len(x_by_e[ek]),
       'groups':[cu,cw],'ambiguity':round(float(x*(1-x)),8)})
 records.sort(key=lambda r:(-r['persistence'],-r['ambiguity'],r['edge_id']))
 summary={'all_fractional_cross_component':counts['all_fractional_cross_component'],
          'cross_component_baseline':counts['cross_component_baseline'],
          'nonbaseline_cross_component':len(records),'per_top_group':{}}
 for k,S in top_sets.items():
    selected=[r for r in records if r['groups'][0] in S or r['groups'][1] in S]
    both=[r for r in selected if r['groups'][0] in S and r['groups'][1] in S]
    summary['per_top_group'][k]={
       'cross_lp_edges_touching':len(selected),'cross_lp_edges_both_in_top':len(both),
       'persist_all_three':sum(r['persistence']==3 for r in selected),
       'cross_to_undisputed_vertices':sum(-1 in r['groups'] for r in selected)}
 out=Path(args.report);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(summary,indent=2)+'\n')
 src=Path(args.edges);src.parent.mkdir(parents=True,exist_ok=True)
 src.write_text(json.dumps({'source':'original three Concorde LP primal snapshots',
                          'records':records},separators=(',',':'))+'\n')
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
