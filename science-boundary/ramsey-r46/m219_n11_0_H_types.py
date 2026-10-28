#!/usr/bin/env python3
"""Enumerate the tiny induced high-vertex graph cover for m=219,n11=0.

There are two surviving aggregate degree sequences after m219_structure.py:
  S0 = 12^30 13^6
  S1 = 12^31 13^4 14.

The complete lucky-d12 exclusion implies every degree-12 vertex has S<=146.
With no degree-11 vertices this means its total excess weight
sum_{high neighbour h}(deg(h)-12) is at most 2.

For S0 this bounds M--H edges by 60.  The six degree-13 vertices have total
degree 78, so e(H)>=9.  K4-freeness gives e(H)<=12.  Exhausting all 2^15
labelled 6-vertex graphs and quotienting by isomorphism leaves 25 H types.

For S1, write h for neighbours of the unique degree-14 vertex inside H and x
for edges among the four degree-13 vertices.  The weighted degree-12 capacity
plus K4-freeness leaves exactly four colored H isomorphism types.  This script
recomputes both finite covers and writes adjacency representatives for the
fixed-H SAT campaign.
"""
from __future__ import annotations

import argparse,itertools,json
from collections import Counter
from pathlib import Path
import networkx as nx


def k4_free(g:nx.Graph)->bool:
    return not any(g.subgraph(s).number_of_edges()==6 for s in itertools.combinations(g.nodes,4))

def add_unlabeled(bucket:list[nx.Graph],g:nx.Graph,node_match=None)->bool:
    for h in bucket:
        if nx.is_isomorphic(g,h,node_match=node_match):return False
    bucket.append(g.copy());return True

def adj_rows(g:nx.Graph,n:int):
    return [''.join('1' if i!=j and g.has_edge(i,j) else '0' for j in range(n)) for i in range(n)]

def seq0_types():
    n=6;pairs=list(itertools.combinations(range(n),2));groups={};out=[]
    for mask in range(1<<len(pairs)):
        e=mask.bit_count()
        if not 9<=e<=12:continue
        g=nx.Graph();g.add_nodes_from(range(n));g.add_edges_from(pairs[i] for i in range(len(pairs)) if (mask>>i)&1)
        if not k4_free(g):continue
        key=(e,tuple(sorted(dict(g.degree()).values())),nx.weisfeiler_lehman_graph_hash(g))
        b=groups.setdefault(key,[])
        if add_unlabeled(b,g):out.append(g.copy())
    out.sort(key=lambda g:(g.number_of_edges(),sorted(dict(g.degree()).values()),nx.to_graph6_bytes(g,header=False).strip()))
    assert len(out)==25,len(out)
    return [{'sequence':0,'index':i,'edges':g.number_of_edges(),'degree_sequence':sorted(dict(g.degree()).values()),'adjacency':adj_rows(g,6)} for i,g in enumerate(out)]

def seq1_types():
    n=5;pairs=list(itertools.combinations(range(n),2));nm=nx.algorithms.isomorphism.categorical_node_match('kind',None)
    groups={};out=[]
    for mask in range(1<<len(pairs)):
        g=nx.Graph();g.add_nodes_from(range(n));g.add_edges_from(pairs[i] for i in range(len(pairs)) if (mask>>i)&1)
        nx.set_node_attributes(g,{i:('14' if i==4 else '13') for i in range(n)},'kind')
        if not k4_free(g):continue
        h=g.degree(4);x=g.subgraph(range(4)).number_of_edges()
        # M neighbours of degree-14 =14-h; they spend their full excess budget
        # on that weight-2 edge and cannot meet a degree-13 vertex.  The other
        # M vertices can meet at most two degree-13 vertices.
        q=14-h
        md13=52-2*x-h
        if q<0 or q>31 or md13>2*(31-q):continue
        key=(h,x,tuple(sorted(g.degree(i) for i in range(4))))
        b=groups.setdefault(key,[])
        if add_unlabeled(b,g,nm):out.append(g.copy())
    out.sort(key=lambda g:(g.degree(4),g.subgraph(range(4)).number_of_edges(),sorted(g.degree(i) for i in range(4)),nx.to_graph6_bytes(g,header=False).strip()))
    assert len(out)==4,len(out)
    rows=[]
    for i,g in enumerate(out):
        rows.append({'sequence':1,'index':i,'edges':g.number_of_edges(),'h14_to_13':g.degree(4),
                     'edges_among_13':g.subgraph(range(4)).number_of_edges(),
                     'degree13_H_degrees':sorted(g.degree(j) for j in range(4)),'adjacency':adj_rows(g,5)})
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    s0=seq0_types();s1=seq1_types();out={'sequence0':s0,'sequence1':s1,'counts':{'sequence0':len(s0),'sequence1':len(s1),'total':len(s0)+len(s1)}}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'counts':out['counts'],'s0_edges':dict(Counter(x['edges'] for x in s0)),
                      's1_hx':[(x['h14_to_13'],x['edges_among_13']) for x in s1]},sort_keys=True))
if __name__=='__main__':main()
