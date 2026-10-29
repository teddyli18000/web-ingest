#!/usr/bin/env python3
"""Score disconnection-vs-repair *jointly*, for every baseline-valid split motif.

A positive 2-edge exchange may create a cheap disconnected 2-factor. A cut
has a *price*: the least extra integer cost of reconnecting its small cycle.
Here we estimate that cost via K nearest COMPLETE-GRAPH cross-cut bridges
for each island vertex. Crucially, the bridge replaces an edge in the
*modified* 2-factor, not necessarily an original tour edge.

If gain minus reconnect cost is positive, emit a full upstream-verified
Hamiltonian certificate. This is a deterministic no-training selector
baseline for cut-dual/learned neighborhood selection, not an exact global
lower bound unless all cross-cut pairs were searched.
"""
import argparse,gzip,importlib.util,json,os,random,time
from pathlib import Path
from functools import lru_cache
from collections import Counter
import numpy as np
from scipy.spatial import cKDTree

def E(a,b):return (a,b) if a<b else (b,a)

def main():
 p=argparse.ArgumentParser()
 for name in ('baseline','motifs','report','candidate'):p.add_argument('--'+name,required=True)
 p.add_argument('--cross-neighbors',type=int,default=64)
 p.add_argument('--maximum-island',type=int,default=80)
 p.add_argument('--seed-start',type=int,default=0)
 p.add_argument('--seed-count',type=int,default=3000)
 p.add_argument('--verify-positive',action='store_true')
 a=p.parse_args();t0=time.monotonic()
 tour=json.loads(Path(a.baseline).read_text())['tour']
 n=len(tour);assert n==100000
 positions={v:i for i,v in enumerate(tour)}
 base={E(tour[i],tour[(i+1)%n]) for i in range(n)}
 sources=json.loads(Path(a.motifs).read_text())['positive_repair_motifs']
 spec=importlib.util.spec_from_file_location('verify',Path(os.environ['FEWSHOTS_ROOT'])/
       'problems/p010-mona-lisa-tsp/verify/verify.py')
 verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
 xs,ys=verifier.coordinates()
 xy=np.column_stack((xs,ys))
 tree=cKDTree(xy)
 @lru_cache(maxsize=1000000)
 def dist(u,v):
    if u>v:u,v=v,u
    return verifier.euc_2d(xs[u-1]-xs[v-1],ys[u-1]-ys[v-1])
 assert verifier.tour_length(tour)==5757191
 report=[]
 best_gain=-10**9;best=None;skips=Counter()
 for j in range(a.seed_start,min(len(sources),a.seed_start+a.seed_count)):
    m=sources[j]
    old={E(*q) for q in m['old']}
    new={E(*q) for q in m['added']}
    if len(old)!=2 or len(new)!=2 or not old<=base or bool(new&base):
        skips['not_baseline_compatible']+=1;continue
    i,jj=sorted(positions[next(iter([u for u,v in old if E(u,tour[(positions[u]+1)%n]) in old])):])[:0] if False else (0,0)
    indices=sorted({next((p for p in (positions[u],positions[v]) if E(tour[p],tour[(p+1)%n])==edge),-1)
                 for edge in old for u,v in [edge]})
    if len(indices)!=2 or indices[0]<0:
        skips['unparseable_edge']+=1;continue
    i,jj=indices
    ends=(tour[(i+1)%n],tour[jj],tour[(jj+1)%n],tour[i])
    if new!={E(ends[0],ends[1]),E(ends[2],ends[3])}:
        skips['connected_or_other_exchange']+=1;continue
    left=jj-i
    right=n-left
    if min(left,right)>a.maximum_island:
        skips['too_large_island']+=1;continue
    small=tour[i+1:jj+1] if left<=right else tour[jj+1:]+tour[:i+1]
    S=set(small)
    assert len(S)==min(left,right)
    rew={}
    for u,v in old:
        rew.setdefault(u,[tour[(positions[u]-1)%n],tour[(positions[u]+1)%n]]).remove(v)
        rew.setdefault(v,[tour[(positions[v]-1)%n],tour[(positions[v]+1)%n]]).remove(u)
    for u,v in new:
        rew.setdefault(u,[tour[(positions[u]-1)%n],tour[(positions[u]+1)%n]]).append(v)
        rew.setdefault(v,[tour[(positions[v]-1)%n],tour[(positions[v]+1)%n]]).append(u)
    assert all(len(q)==2 for q in rew.values())
    def adjacent(city):
        return rew[city] if city in rew else (tour[(positions[city]-1)%n],tour[(positions[city]+1)%n])
    best_here=None
    for u in small:
        _,ids=tree.query(xy[u-1],k=min(n,p.cross_neighbors+len(small)+1) if False else min(n,a.cross_neighbors+len(small)+1))
        for v0 in np.atleast_1d(ids):
            v=int(v0)+1
            if v in S or v==u:continue
            for pu in adjacent(u):
                for pv in adjacent(v):
                    if len({u,v,pu,pv})<4:continue
                    repair_cost=dist(u,v)+dist(pu,pv)-dist(u,pu)-dist(v,pv)
                    net=m['gain']-repair_cost
                    if best_here is None or net>best_here[0]:
                        best_here=(net,repair_cost,(u,pu),(v,pv),(u,v),(pu,pv))
    if best_here is None:
        skips['no_candidate']+=1;continue
    gain,price,old1,old2,new1,new2=best_here
    result={'source_motif_index':j,'seed_gain':m['gain'],
           'island_size':len(small),'estimated_cut_repair_price':price,
           'net_gain':gain,'removed':[list(old1),list(old2)],
           'bridges':[list(new1),list(new2)]}
    report.append(result)
    if gain>best_gain:
        best_gain=gain;best=(j,old,new,old1,old2,new1,new2)
        if gain>0 and a.verify_positive:
            edges=(base-old)|new
            assert E(*old1) in edges and E(*old2) in edges
            edges.remove(E(*old1));edges.remove(E(*old2))
            edges.add(E(*new1));edges.add(E(*new2))
            assert len(edges)==n
            adj=[[] for _ in range(n+1)]
            for u,v in edges:adj[u].append(v);adj[v].append(u)
            assert all(len(adj[u])==2 for u in range(1,n+1))
            seen=bytearray(n+1);now=1;previous=0;candidate=[]
            while not seen[now]:
                seen[now]=1;candidate.append(now)
                x,y=adj[now];nxt=x if x!=previous else y
                previous,now=now,nxt
            assert now==1 and len(candidate)==n
            score=verifier.tour_length(candidate)
            assert score==5757191-gain
            cert=Path(a.candidate);cert.parent.mkdir(parents=True,exist_ok=True)
            cert.write_text(json.dumps({'tour':candidate},separators=(',',':')))
            print(json.dumps({'stage':'verified_candidate','score':score,
                 'gain':gain,'source_motif_index':j}),flush=True)
    if len(report)%100==0:
        print(json.dumps({'stage':'progress','examined':len(report),'best_net':best_gain}),flush=True)
 report.sort(key=lambda r:(-r['net_gain'],-r['seed_gain']))
 result={'method':'complete EUC_2D kNN cross-cut bridge prices after split',
         'cross_neighbors':a.cross_neighbors,'max_island':a.maximum_island,
         'candidate_motifs':len(sources),'evaluated_splits':len(report),
         'skips':dict(skips),'best_net_gain':best_gain,
         'best_approximate_repair_price':report[0]['estimated_cut_repair_price'] if report else None,
         'top_repair_aware':report[:100],
         'source_ranking':[r['source_motif_index'] for r in report],
         'secs':round(time.monotonic()-t0,2)}
 output=Path(a.report);output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('top_repair_aware','source_ranking')}),flush=True)
if __name__=='__main__':main()
