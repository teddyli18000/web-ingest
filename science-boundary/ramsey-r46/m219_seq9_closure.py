#!/usr/bin/env python3
"""Close the m=219 degree sequence 11^12 12^6 13^18.

This is a compact verifier for the structural argument.  It consumes two
previous exact results in results/:
  * m219-r3-fixedAB.json: both A26 x B116-ordinal4 branches are UNSAT;
  * m219-seq9-mu3-relaxation.json: B116-ordinal1 cannot realize a mu=3
    low-low nonedge for h=1,2,3, even in a Ramsey-free degree/r relaxation.

Everything else is recomputed combinatorially here.
"""
from __future__ import annotations
import argparse, itertools, json
from collections import Counter
from pathlib import Path
import networkx as nx

A26=("JiQC@{}N`{?","JqPA@{}N`{?")
B116=(
"W?jIhu?OG_cD`ZIfAnQTiyJIp[UhiJdsQU_seQobWKbkYLE",
"WkGjGVA_SdqKItLBGiIoSFPNoRsxd@eoOEsZQXWoXQjkF~?",
"WoCJ?j?@XDBBmGr@shMaHUgKrRiMU`[cuh{PbnIBb{CIvg_",
"WoCJ?j?GgJBBmGsPx_dIbUgKrIh[UqMfIM{Wi^Obb{AIvc_",
"WoCOZBSmLKXOLQUPDWAM@oE]_fgLlGgysWetAeuhBqigLtT",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZfDMmg|?jYwF\\SAfYaKnSA",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SAfYaKnSA",
"Wt@IXqOg?W`SCYGTGQqHQjH]YZnDMeg|?jYqF\\SQfY_KnS@",
"Wv?IXZ?gGT?kAU@dE@a_FiZZIVUIfdLXgtZOTjg`teoJNcC")

def c2(n): return n*(n-1)//2

def min_c2(total,bins):
    q,r=divmod(total,bins)
    return (bins-r)*c2(q)+r*c2(q+1)

def independent_sets(G,k):
    return [set(S) for S in itertools.combinations(G.nodes(),k)
            if all(not G.has_edge(u,v) for u,v in itertools.combinations(S,2))]

def hitting_number_i5(G):
    I=independent_sets(G,5)
    for k in range(G.number_of_nodes()+1):
        n=sum(all(set(S)&J for J in I) for S in itertools.combinations(G.nodes(),k))
        if n:return k,n
    raise AssertionError

def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--output',type=Path)
    a=p.parse_args(); ws=a.workspace
    # Catalogue facts, recomputed from the authenticated graph6 representatives.
    ah=[]
    for s in A26:
        G=nx.from_graph6_bytes(s.encode()); assert G.number_of_edges()==26
        assert not any(len(c)==3 for c in nx.enumerate_all_cliques(G) if len(c)>=3)
        h,n=hitting_number_i5(G); assert h==2; ah.append({'degree_histogram':dict(sorted(Counter(dict(G.degree()).values()).items())),'i5_hitting_number':h,'minimum_hitting_sets':n})
    bh=[]
    for s in B116:
        G=nx.from_graph6_bytes(s.encode()); assert G.number_of_edges()==116
        bh.append(dict(sorted(Counter(dict(G.degree()).values()).items())))
    assert bh[1]=={8:1,9:7,10:15,11:1}
    assert bh[4]=={8:8,10:8,11:8}
    assert all(min(d)>=9 for i,d in enumerate(bh) if i not in (1,4))
    # Existing exact B4 exclusion.
    old=json.loads((ws/'results/m219-r3-fixedAB.json').read_text())
    b4={(r.get('a_ordinal'),r.get('b_ordinal')):r.get('status') for r in old['rows'] if r.get('b_ordinal')==4}
    assert b4=={(0,4):'UNSAT',(1,4):'UNSAT'},b4
    # New weaker-than-Ramsey mu3 relaxation exclusion for h=1,2,3.
    mu=json.loads((ws/'results/m219-seq9-mu3-relaxation.json').read_text())
    assert mu['all_infeasible'] and {(r['a_type'],r['h']) for r in mu['cases']}=={(i,h) for i in (0,1) for h in (1,2,3)}
    # Zero-deficit identity: all local S upper bounds must be tight.
    sum_d2=12*11**2+6*12**2+18*13**2
    upper=12*129+6*146+18*163
    assert sum_d2==upper==5358
    # Therefore every low vertex has S=129 and r=132-S=3.  If t=d_L(v),
    # then h=#13-neighbours=t-3 and m=#12-neighbours=14-2t.  Since globally
    # there are only six degree-12 vertices, h>=1 and t is in {4,5,6,7}.
    # A26 hitting number 2 and B116 minimum internal degree 8 give mu in {2,3}
    # on every low-low nonedge.  B4 is excluded; B1 has one degree-8 slot, so
    # mu=3 nonedges form a matching.  The new relaxation excludes a B1 mu=3
    # endpoint for h=1,2,3, hence only t=7 vertices can be endpoints.
    survivors=[]; rejected={'common_neighbor_bound':0,'forced_adjacency':0}
    for n4 in range(13):
      for n5 in range(13-n4):
       for n6 in range(13-n4-n5):
        n7=12-n4-n5-n6
        degsum=4*n4+5*n5+6*n6+7*n7
        if degsum%2: continue
        x=degsum//2
        # If two t=7 vertices were nonadjacent, they already have >=4 common
        # neighbours inside L, impossible since total mu<=3.  Thus t=7 is a
        # clique, so n7<=3 by K4-freeness.  A nonedge of types 7/6 has at least
        # three L-common neighbours, hence would be mu=3, but t=6 endpoints are
        # excluded.  So every 7 is also adjacent to every 6.
        if n7>3 or (n7 and n6+n7-1>7):
            rejected['forced_adjacency']+=1; continue
        y=168-4*x; z=2*x-36
        if y<0 or z<0: continue
        Lpart=n4*c2(4)+n5*c2(5)+n6*c2(6)+n7*c2(7)
        lower=Lpart+min_c2(y,6)+min_c2(z,18)
        qcap=n7//2
        upperP=3*x+132+qcap
        if lower>upperP:
            rejected['common_neighbor_bound']+=1; continue
        survivors.append({'n4':n4,'n5':n5,'n6':n6,'n7':n7,'edges_L':x,'LM':y,'LH':z,'P_lower':lower,'P_upper':upperP,'mu3_cap':qcap})
    assert survivors==[{'n4':0,'n5':0,'n6':12,'n7':0,'edges_L':36,'LM':24,'LH':36,'P_lower':234,'P_upper':240,'mu3_cap':0}],survivors
    # Final contradiction.  L is 6-regular.  With no t=7 vertices q=0, every
    # nonedge has total mu=2.  Two nonadjacent degree-6 vertices of L already
    # have at least 6+6-10=2 common L-neighbours, so they have exactly two.
    # H=complement(L) is therefore 5-regular, and for every H-edge uv,
    # c_L(u,v)=2+c_H(u,v)=2, so H is triangle-free.  But N_H(v) has five
    # vertices and is independent in H, hence is a K5 in L, contradicting K4-free.
    out={'campaign':'m219-seq9-structural-closure','degree_sequence':{'11':12,'12':6,'13':18},
         'sum_degree_squares':sum_d2,'sum_local_S_upper_bounds':upper,'all_low_r3':True,
         'A26':ah,'B116_degree_histograms':bh,'b4_fixedAB_unsat':True,
         'mu3_endpoint_excluded_h':[1,2,3],'mu3_endpoint_only_L_degree':7,
         'aggregate_survivors':survivors,'closed':True,
         'contradiction':'L is forced 6-regular; complement(L) is forced 5-regular triangle-free, whose 5-vertex neighborhood is independent there and hence a K5 in L.'}
    text=json.dumps(out,indent=2,sort_keys=True)+'\n';print(text,end='')
    if a.output:a.output.write_text(text)
if __name__=='__main__':main()
