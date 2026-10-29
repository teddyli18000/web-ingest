#!/usr/bin/env python3
"""Cycle-graph minimum-spanning-tree lower bound for ORIGINAL-factor 2-opt patching.

For every pair of original disconnected 2-factor cycles, identify the least
cost 2-edge exchange among cross-component kNN port pairs. MST of these
pair costs is a lower bound on merging all ORIGINAL cycles using edge-disjoint
cross-cycle 2-opt operations chosen from THIS port pool. It does NOT bound
3-opt, new-edge rebreaking, internal rearrangements or unseen port pairs.

Cycles can be much cheaper than complete Hamiltonian tour; no record claim.
"""
import argparse,importlib.util,json,os,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
N=100000
def E(u,v):return (int(u),int(v)) if u<v else (int(v),int(u))
def main():
 p=argparse.ArgumentParser()
 for name in ('factor','baseline','report'):p.add_argument('--'+name,required=True)
 p.add_argument('--neighbors',type=int,default=32)
 p.add_argument('--max-ports',type=int,default=30000)
 a=p.parse_args();tic=time.monotonic()
 spec=importlib.util.spec_from_file_location('verifier',Path(os.environ['FEWSHOTS_ROOT'])/
     'problems/p010-mona-lisa-tsp/verify/verify.py')
 verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
 xs,ys=verifier.coordinates()
 def d(u,v):return verifier.euc_2d(xs[u]-xs[v],ys[u]-ys[v])
 tour=json.loads(Path(a.baseline).read_text())['tour']
 assert len(tour)==N and verifier.tour_length(tour)==5757191
 t=[x-1 for x in tour]
 base={E(t[i],t[(i+1)%N]) for i in range(N)}
 j=json.loads(Path(a.factor).read_text())
 removed={tuple(x) for x in j['removed_baseline_edges']}
 added={tuple(x) for x in j['added_nonbaseline_edges']}
 factor=(base-removed)|added
 assert len(factor)==N
 assert 5757191+sum(d(*e) for e in added)-sum(d(*e) for e in removed)==j['factor_score']
 label=np.asarray(j['component_labels'],dtype=np.int32)
 ncomp=int(j['cycles']);counts=np.bincount(label,minlength=ncomp)
 assert sorted(counts.tolist())==sorted(j['cycle_sizes'])
 giant=int(counts.argmax())
 adj=[[] for _ in range(N)]
 for u,v in factor:
   adj[u].append(v);adj[v].append(u)
 assert all(len(a)==2 for a in adj)
 sites=np.flatnonzero(label!=giant)
 if len(sites)>a.max_ports:
   sites=sites[np.linspace(0,len(sites)-1,a.max_ports,dtype=int)]
 tree=cKDTree(np.column_stack((xs,ys)))
 _,nn=tree.query(np.column_stack((np.asarray(xs)[sites],np.asarray(ys)[sites])),
                 k=a.neighbors+1,workers=4)
 pairs={};scanned=0
 for ii,z in enumerate(sites):
    u=int(z);gu=int(label[u])
    for p in nn[ii,1:]:
      v=int(p);gv=int(label[v])
      if gv==gu:continue
      scanned+=1
      ab=(min(gu,gv),max(gu,gv))
      for x in adj[u]:
        for y in adj[v]:
          c0=d(u,x)+d(v,y)
          candidate=min(d(u,v)+d(x,y)-c0,d(u,y)+d(x,v)-c0)
          if ab not in pairs or candidate<pairs[ab]:pairs[ab]=candidate
 parent=list(range(ncomp));rank=[0]*ncomp
 def root(i):
    while parent[i]!=i:
      parent[i]=parent[parent[i]];i=parent[i]
    return i
 total=0;chosen=[]
 for (u,v),cost in sorted(pairs.items(),key=lambda entry:(entry[1],entry[0])):
   a0=root(u);b0=root(v)
   if a0==b0:continue
   if rank[a0]<rank[b0]:a0,b0=b0,a0
   parent[b0]=a0;rank[a0]+=(rank[a0]==rank[b0])
   total+=cost;chosen.append((u,v,cost))
 edges_needed=ncomp-1
 exists=len(chosen)==edges_needed
 result={'factor_score':j['factor_score'],'factor_cycles':ncomp,'cycle_sizes':counts.tolist(),
    'giant_cycle':int(counts[giant]),'scanned_port_vertices':len(sites),
    'scanned_cross_cycle_neighbors':scanned,'component_pair_edges':len(pairs),
    'complete_spanning_tree':exists,'MST_pair_patch_delta':total if exists else None,
    'factor_plus_MST':j['factor_score']+total if exists else None,
    'record_score':5757191,'best_pair_patch_edges':[list(e) for e in chosen],
    'elapsed_seconds':round(time.monotonic()-tic,3),
    'scope':'Minimum sum of original-cycle pairwise 2-edge patch costs, over observed kNN cross links; NOT a bound for globally reoptimized tours, arbitrary multi-edge exchanges or unobserved candidate edges.'}
 out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'stage':'patchMST',**{k:v for k,v in result.items() if k not in ('cycle_sizes','best_pair_patch_edges')}}),flush=True)
if __name__=='__main__':main()
