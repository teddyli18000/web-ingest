#!/usr/bin/env python3
"""Original-factor 3-opt, 2-subtour merge over exact complete Euclidean metric.

The previous 2-opt patch requires +7 from 5,757,190, leaving 5,757,197.
Here test ALL admissible 3-edge reconnection patterns when cutting either
(2 edges of giant cycle + 1 of small) or (2 small + 1 giant). Both preserve
all original internal factor paths except the three explicitly removed edges.
The 3 replacement edges MUST connect the three fixed paths into one cycle.

This is a classical 3-opt PATCH FAMILY, not a novel algorithm; our scientific
test is whether higher-order coupling can overcome the observed topological
gap while satisfying exact official Few Shots p010 verification.
"""
import argparse,importlib.util,json,math,os,time
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
N=100000
def E(u,v):
    u=int(u);v=int(v)
    return (u,v) if u<v else (v,u)
def patterns():
    # Perfect matchings on six terminals. Frozen paths connect (0,1),
    # (2,3), (4,5); add three edges such that all six terminals are
    # connected in a single six-vertex cycle.
    def allpair(z):
        if not z:yield ()
        else:
            a=z[0]
            for i in range(1,len(z)):
                b=z[i]
                for rem in allpair(z[1:i]+z[i+1:]):
                    yield ((a,b),)+rem
    good=[]
    for edges in allpair(list(range(6))):
        p=list(range(6))
        def root(i):
            while p[i]!=i:
                p[i]=p[p[i]];i=p[i]
            return i
        for u,v in ((0,1),(2,3),(4,5))+edges:
            p[root(u)]=root(v)
        if len(set(root(i) for i in range(6)))==1:good.append(edges)
    assert len(good)==8,(len(good),good)
    return good
def order_cycle(seed,adj):
    route=[seed];prev=-1;cur=seed
    while True:
        a,b=adj[cur]
        nxt=a if a!=prev else b
        if nxt==seed:break
        assert nxt not in route
        route.append(nxt)
        prev,cur=cur,nxt
    return route
def main():
    p=argparse.ArgumentParser()
    for k in ('factor','baseline','report','certificate'):p.add_argument('--'+k,required=True)
    p.add_argument('--neighbors',type=int,default=128)
    p.add_argument('--per-edge',type=int,default=28)
    args=p.parse_args();start=time.monotonic()
    spec=importlib.util.spec_from_file_location('verify',
       Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py')
    verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
    xs,ys=verify.coordinates()
    def distance(u,v):return verify.euc_2d(xs[u]-xs[v],ys[u]-ys[v])
    t=json.loads(Path(args.baseline).read_text())['tour']
    assert len(t)==N and verify.tour_length(t)==5757191
    base={E(t[i]-1,t[(i+1)%N]-1) for i in range(N)}
    data=json.loads(Path(args.factor).read_text())
    assert int(data['cycles'])==2
    old={tuple(e) for e in data['removed_baseline_edges']}
    new={tuple(e) for e in data['added_nonbaseline_edges']}
    factor=(base-old)|new
    assert len(factor)==N
    assert 5757191-sum(distance(*e) for e in old)+sum(distance(*e) for e in new)==data['factor_score']
    adj=[[] for _ in range(N)]
    for u,v in factor:adj[u].append(v);adj[v].append(u)
    assert all(len(z)==2 for z in adj)
    labels=np.asarray(data['component_labels'])
    sizes=np.bincount(labels,minlength=2)
    big,small=int(sizes.argmax()),int(sizes.argmin())
    sg=np.flatnonzero(labels==small)
    bg=np.flatnonzero(labels==big)
    assert len(sg)+len(bg)==N
    smallroute=order_cycle(int(sg.min()),adj)
    bigroute=order_cycle(int(bg.min()),adj)
    assert len(smallroute)==len(sg) and len(bigroute)==len(bg)
    for route in (smallroute,bigroute):
        assert all(E(route[i],route[(i+1)%len(route)]) in factor for i in range(len(route)))
    # Edges retain orientation i->i+1 in each original cycle.
    small_e=[(smallroute[i],smallroute[(i+1)%len(smallroute)]) for i in range(len(smallroute))]
    big_e=[(bigroute[i],bigroute[(i+1)%len(bigroute)]) for i in range(len(bigroute))]
    small_pos={E(*e):i for i,e in enumerate(small_e)}
    big_pos={E(*e):i for i,e in enumerate(big_e)}
    tree=cKDTree(np.column_stack((xs,ys)))
    _,nn=tree.query(np.column_stack((np.asarray(xs)[sg],np.asarray(ys)[sg])),
                    k=args.neighbors+1,workers=4)
    # Index big factor edges touched by neighborhoods of small-cycle ports.
    neighbor_big=set()
    neighbor_giant_per_city={}
    bigcity_index={u:i for i,u in enumerate(bigroute)}
    for j,u0 in enumerate(sg):
        u=int(u0);local=set()
        for v0 in nn[j,1:]:
            v=int(v0)
            if labels[v]!=big:continue
            k=bigcity_index[v]
            local.add(k);local.add((k-1)%len(bigroute))
        neighbor_giant_per_city[u]=local
        neighbor_big.update(local)
    print(json.dumps({'stage':'ports','small_size':len(sg),'giant_size':len(bg),
         'nearby_giant_factor_edges':len(neighbor_big),'3opt_patterns':len(patterns())}),flush=True)
    good=patterns()
    best=(10**15,None,None,None)
    trials=[0,0]
    def check(terminals,removed,mode):
        nonlocal best
        assert len(set(terminals))==6
        removed_set={E(*e) for e in removed}
        oldcost=sum(distance(*e) for e in removed_set)
        for pattern in good:
            conn=tuple(E(terminals[i],terminals[j]) for i,j in pattern)
            if len(set(conn))!=3 or any(e in removed_set for e in conn):continue
            delta=sum(distance(*e) for e in conn)-oldcost
            if delta<best[0]:
                best=(delta,removed_set,set(conn),mode)
    # Two cuts on giant, one on small.
    for i,(u,v) in enumerate(small_e):
        options=neighbor_giant_per_city[u]|neighbor_giant_per_city[v]
        items=sorted(options,key=lambda j:(
            min(distance(u,big_e[j][0]),distance(u,big_e[j][1]),
                distance(v,big_e[j][0]),distance(v,big_e[j][1])),j))[:args.per_edge]
        for ix,p0 in enumerate(items):
            for q0 in items[ix+1:]:
                pi,qi=sorted((p0,q0))
                a,b=big_e[pi];c,d=big_e[qi]
                if len({u,v,a,b,c,d})<6:continue
                # Frozen path 1: small u..v. Giant fixed paths:
                # b..c, d..a (since p<q in giant cyclic order).
                check([u,v,b,c,d,a],[(u,v),(a,b),(c,d)],'2big_1small')
                trials[0]+=1
    # Two cuts on small and one on giant. The nearest small *edges*
    # to a giant factor edge supply 3-opt candidates.
    for j in sorted(neighbor_big):
        u,v=big_e[j]
        near=sorted(range(len(small_e)),key=lambda k:(
            min(distance(u,small_e[k][0]),distance(u,small_e[k][1]),
                distance(v,small_e[k][0]),distance(v,small_e[k][1])),k))[:args.per_edge]
        for ix,p0 in enumerate(near):
            for q0 in near[ix+1:]:
                pi,qi=sorted((p0,q0))
                a,b=small_e[pi];c,d=small_e[qi]
                if len({u,v,a,b,c,d})<6:continue
                check([u,v,b,c,d,a],[(u,v),(a,b),(c,d)],'1big_2small')
                trials[1]+=1
    assert best[1] is not None
    delta,removed,added,mode=best
    edges=(factor-removed)|added
    assert len(edges)==N
    adj2=[[] for _ in range(N)]
    for u,v in edges:adj2[u].append(v);adj2[v].append(u)
    assert all(len(zz)==2 for zz in adj2)
    seen=bytearray(N);tour=[];cur=0;prev=-1
    while not seen[cur]:
        seen[cur]=1;tour.append(cur+1)
        a,b=adj2[cur];following=a if a!=prev else b
        prev,cur=cur,following
    assert cur==0 and len(tour)==N
    actual=verify.tour_length(tour)
    assert actual==data['factor_score']+delta
    verdict=verify.verify_bytes(json.dumps({'tour':tour},separators=(',',':')).encode(),verify.load_config())
    assert verdict['valid'] and int(verdict['score'])==actual
    output={'factor_score':data['factor_score'],'two_cycle_sizes':sizes.tolist(),
        'mode':mode,'best_3opt_delta':delta,'best_connected_score':actual,
        'record_score':5757191,'record_improved':actual<5757191,
        'giant_cut_candidates':len(neighbor_big),'3opt_triples_tested':trials,
        'removed_edges':[list(e) for e in sorted(removed)],
        'added_edges':[list(e) for e in sorted(added)],
        'elapsed_seconds':round(time.monotonic()-start,3),
        'official_verified_hash':verdict['canonical_hash']}
    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,indent=2)+'\n')
    if actual<5757191:
        Path(args.certificate).write_text(json.dumps({'tour':tour},separators=(',',':')))
    print(json.dumps({'stage':'3opt_result',**output}),flush=True)
if __name__=='__main__':main()
