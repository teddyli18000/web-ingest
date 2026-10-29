#!/usr/bin/env python3
"""Find connected 'alternative wiring' components in 8 official Mona Lisa tours.

Fixed edges: intersection of Nagata plus seven published historical tours.
Uncertain edges: union minus intersection. Their connected components form
contested wiring regions in the public tour population. A component's
projected edge patterns are alternative *local wirings*, not independently
swappable Hamiltonian tours; connectivity across fixed-edge ports matters.
For every region cross-tab LP fractional nodes from three published LPs.
"""
import argparse,importlib.util,json,os
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import historical_lp_disagreement as h

N=100000
def main():
 p=argparse.ArgumentParser()
 for arg in ('baseline','tours','lps','report','regions'):p.add_argument('--'+arg,required=True)
 a=p.parse_args()
 spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
    'problems/p010-mona-lisa-tsp/verify/verify.py')
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 xs,ys=v.coordinates()
 xs=np.asarray(xs);ys=np.asarray(ys)
 t=np.asarray(json.loads(Path(a.baseline).read_text())['tour'],dtype=np.int32)-1
 assert len(t)==N and v.tour_length((t+1).tolist())==5757191
 position=np.empty(N,dtype=np.int32);position[t]=np.arange(N,dtype=np.int32)
 tours={'Nagata':t}
 for name,path in json.loads(Path(a.tours).read_text()).items():
    route=h.parse_tour(path)
    assert v.tour_length((route+1).tolist())==int(name.split('_')[-1])
    tours[name]=route
 edges={name:set(map(int,h.tour_edges(route))) for name,route in tours.items()}
 stable=set.intersection(*(x for x in edges.values()))
 union=set.union(*(x for x in edges.values()))
 variable=union-stable
 assert len(stable)==94228 and len(union)>=103857, (len(stable),len(union))
 parent=np.arange(N,dtype=np.int32)
 size=np.ones(N,dtype=np.int32)
 def root(u):
    while parent[u]!=u:
        parent[u]=parent[parent[u]]
        u=int(parent[u])
    return u
 def merge(u,w):
    i=root(u);j=root(w)
    if i==j:return
    if size[i]<size[j]:i,j=j,i
    parent[j]=i;size[i]+=size[j]
 for e in variable:merge(e//N,e%N)
 members=defaultdict(list)
 for e in variable:
    for city in (e//N,e%N):
        members[root(city)].append(city)
 members={r:sorted(set(nodes)) for r,nodes in members.items()}
 keys=sorted(members,key=lambda r:(-len(members[r]),r))
 origin={r:i for i,r in enumerate(keys)}
 citycomp=np.full(N,-1,dtype=np.int32)
 for i,r in enumerate(keys):citycomp[members[r]]=i
 edgecomp=defaultdict(list)
 for e in variable:
    u,w=e//N,e%N
    assert citycomp[u]==citycomp[w]
    edgecomp[int(citycomp[u])].append(e)
 lpdata={name:h.lp_read(path) for name,path in json.loads(Path(a.lps).read_text()).items()}
 primary=lpdata['2012-04-18']
 stable_degree=np.zeros(N,dtype=np.int16)
 boundary=Counter()
 stable_lp=Counter()
 px=dict(zip(map(int,primary['edge_ids']),map(float,primary['x'])))
 for e in stable:
    u,w=e//N,e%N
    stable_degree[u]+=1;stable_degree[w]+=1
    i,j=citycomp[u],citycomp[w]
    if i>=0 and j!=i:boundary[i]+=1
    if j>=0 and i!=j:boundary[j]+=1
    x=px.get(e,0.)
    if x>=.99999:stable_lp['x1']+=1
    elif x<=.00001:stable_lp['x0']+=1
    else:stable_lp['fraction']+=1
 assert len(stable)==sum(stable_lp.values())
 base_neigh=h.tour_neigh(t)
 different=np.zeros(N,dtype=np.int16)
 for name,route in tours.items():
    if name=='Nagata':continue
    aa,bb=h.tour_neigh(route)
    different+=(aa!=base_neigh[0])|(bb!=base_neigh[1])
 result=[]
 for cid,r in enumerate(keys):
    ids=np.asarray(members[r],dtype=np.int32)
    eids=set(edgecomp[cid])
    cfg={}
    for name,es in edges.items():
        cfg[name]=frozenset(es&eids)
    variants={v:[] for v in cfg.values()}
    for name,pattern in cfg.items():variants[pattern].append(name)
    frac={name:int(lp['node_frac'][ids].sum()) for name,lp in lpdata.items()}
    persistent=np.ones(len(ids),dtype=bool)
    for lp in lpdata.values():persistent&=lp['node_frac'][ids]
    d2=(different[ids]>=2)
    overlap=int(np.sum(d2&primary['node_frac'][ids]))
    new_alt=sum(e not in edges['Nagata'] for e in eids)
    bbox=[int(np.min(xs[ids])),int(np.max(xs[ids])),int(np.min(ys[ids])),int(np.max(ys[ids]))]
    entry={'id':cid,'cities':len(ids),'uncertain_edges':len(eids),
       'new_alternative_edges':new_alt,
       'LP_fraction_nodes':frac,'persistent_fraction_nodes':int(persistent.sum()),
       'disagreement_2plus_nodes':int(d2.sum()),'joint_nodes':overlap,
       'fraction_given_disagreement':round(float(overlap/max(1,int(d2.sum()))),4),
       'competitor_wirings':len(variants),'wiring_source_groups':[g for g in variants.values()],
       'stable_boundary_edges':boundary[cid],
       'Nagata_position_range':[int(position[ids].min()),int(position[ids].max())],
       'bbox_xy':bbox,'mean_xy':[round(float(np.mean(xs[ids])),2),round(float(np.mean(ys[ids])),2)],
       'sample_city_ids_1based':[int(x)+1 for x in ids[:30]],
       'members_0based':ids.tolist()}
    # High joint count and multiple distinct alternative wirings are
    # separate evidence dimensions; scoring is a PRIORITY heuristic only.
    entry['priority_score']=int(overlap)*max(1,len(variants)-1)
    result.append(entry)
 candidates=sorted(result,key=lambda x:(-x['priority_score'],-x['joint_nodes'],-x['competitor_wirings']))
 summary={'reference':'Nagata and 7 published historical tours; original Concorde LP x from 2011/2012',
   'n':N,'tour_count':len(tours),'common_edges_all_8':len(stable),
   'union_edges_all_8':len(union),'uncertain_edges':len(variable),
   'variable_components':len(result),'total_variable_component_vertices':sum(x['cities'] for x in result),
   'stable_edges_vs_2012_lp':dict(stable_lp),
   'regions_at_least_3_wirings':sum(x['competitor_wirings']>=3 for x in result),
   'regions_at_least_4_wirings':sum(x['competitor_wirings']>=4 for x in result),
   'regions_with_joint_2plus_fraction':sum(x['joint_nodes']>0 for x in result),
   'largest_regions':[{k:v for k,v in row.items() if k!='members_0based'}
                      for row in sorted(result,key=lambda x:-x['cities'])[:12]],
   'top_priority_regions':[{k:v for k,v in row.items() if k!='members_0based'} for row in candidates[:50]],
   'key_caveat':'These components are of variable edges across observed tours, not necessarily independent feasible tour patches; 7 historic routes are correlated and LP values do not encode optimality probabilities.'}
 Path(a.report).parent.mkdir(parents=True,exist_ok=True)
 Path(a.report).write_text(json.dumps(summary,indent=2)+'\n')
 Path(a.regions).write_text(json.dumps({'components':result},separators=(',',':'))+'\n')
 print(json.dumps({'stage':'components',**{k:v for k,v in summary.items() if k not in ('largest_regions','top_priority_regions','key_caveat')}}),flush=True)
if __name__=='__main__':main()
