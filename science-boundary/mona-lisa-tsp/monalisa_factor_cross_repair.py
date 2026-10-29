#!/usr/bin/env python3
"""Counterexample-driven *complete-metric* two-edge repairs of a Mona Lisa 2-factor.

The input is a disconnected 100,000-city integer 2-factor from LP/history
SEC separation, NOT a tour and NOT a record. Enumerate short cross-cycle
2-opt repairs involving the full Euclidean nearest neighbors, preserving
the *pair* of new edges needed to merge cycles. A beam search composes
compatible component merges until exactly ONE Hamiltonian tour remains.

All edges/weights/validity are recomputed with the official Few Shots
EUC_2D scorer. A valid score below 5,757,191 is mandatory for a certificate.
The only novelty claim, if justified, would be the resulting new certificate.
"""
import argparse,importlib.util,json,os,time,heapq
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

N=100000
def ek(u,v):return (u,v) if u<v else (v,u)
def make_tour(edges):
    assert len(edges)==N
    adj=[[] for _ in range(N)]
    for u,v in edges:adj[u].append(v);adj[v].append(u)
    assert all(len(z)==2 for z in adj),'degree-two violation'
    path=[1];seen=bytearray(N);cur=0;prev=-1
    while not seen[cur]:
        seen[cur]=1
        x,y=adj[cur];nxt=x if x!=prev else y
        path.append(nxt+1);prev,cur=cur,nxt
    assert cur==0 and len(path)==N+1,'disconnected factor'
    return path[:-1]

def main():
    p=argparse.ArgumentParser()
    for k in ('factor','baseline','report','certificate'):p.add_argument('--'+k,required=True)
    p.add_argument('--neighbors',type=int,default=64)
    p.add_argument('--max-ports',type=int,default=25000)
    p.add_argument('--top-per-component-pair',type=int,default=80)
    p.add_argument('--beam',type=int,default=150)
    a=p.parse_args();start=time.monotonic()
    spec=importlib.util.spec_from_file_location('verifier',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    xs,ys=verifier.coordinates()
    xy=np.column_stack((xs,ys))
    def dist(u,w):return verifier.euc_2d(xs[u]-xs[w],ys[u]-ys[w])
    baseline=json.loads(Path(a.baseline).read_text())['tour']
    assert len(baseline)==N and verifier.tour_length(baseline)==5757191
    tour=[x-1 for x in baseline]
    base={ek(tour[i],tour[(i+1)%N]) for i in range(N)}
    data=json.loads(Path(a.factor).read_text())
    cycles=int(data['cycles']);labels=list(map(int,data['component_labels']))
    print(json.dumps({'stage':'loaded_factor','cycle_count':cycles,'sizes':data['cycle_sizes']}),flush=True)
    if cycles>15:raise RuntimeError(f'{cycles} factor cycles: needs different global repair formulation')
    old={tuple(x) for x in data['removed_baseline_edges']}
    new={tuple(x) for x in data['added_nonbaseline_edges']}
    assert len(old)==len(new) and old<=base and not (new&base)
    factor=(base-old)|new
    assert len(factor)==N
    assert len(labels)==N and set(labels)==set(range(cycles))
    adj=[[] for _ in range(N)]
    for u,w in factor:
        assert labels[u]==labels[w]
        adj[u].append(w);adj[w].append(u)
    assert all(len(z)==2 for z in adj)
    original_score=5757191+sum(dist(*e) for e in new)-sum(dist(*e) for e in old)
    assert original_score==data['factor_score']
    sizes=np.bincount(labels,minlength=cycles)
    assert sorted(map(int,sizes))==sorted(data['cycle_sizes'])
    dominant=int(np.argmax(sizes))
    scan=np.flatnonzero(np.asarray(labels)!=dominant)
    if len(scan)>a.max_ports:
        scan=scan[np.linspace(0,len(scan)-1,a.max_ports,dtype=int)]
    tree=cKDTree(xy)
    _,nearest=tree.query(xy[scan],k=min(a.neighbors+1,N),workers=4)
    heaps={}
    observed=0;available=0;scanned_cross=0
    for row,u0 in enumerate(scan):
        u=int(u0);ca=labels[u]
        for v0 in nearest[row,1:]:
            v=int(v0);cb=labels[v]
            if ca==cb:continue
            scanned_cross+=1
            ckey=(min(ca,cb),max(ca,cb))
            if ckey not in heaps:heaps[ckey]=[]
            for x in adj[u]:
                for y in adj[v]:
                    if len({u,x,v,y})!=4:continue
                    r1=ek(u,x);r2=ek(v,y)
                    basecost=dist(*r1)+dist(*r2)
                    for n1,n2 in ((ek(u,v),ek(x,y)),(ek(u,y),ek(x,v))):
                        if n1==n2:continue
                        dc=dist(*n1)+dist(*n2)-basecost
                        # Novelty is defined against THIS factor. Every
                        # new cross-component edge is necessarily absent.
                        observed+=1
                        rec=(int(dc),tuple(sorted((r1,r2))),tuple(sorted((n1,n2))),ckey)
                        heap=heaps[ckey]
                        item=(-rec[0],rec[1],rec[2],rec[3])
                        if len(heap)<a.top_per_component_pair:
                            heapq.heappush(heap,item)
                        elif item>heap[0]:
                            heapq.heapreplace(heap,item)
    candidates=set()
    for rows in heaps.values():
        for neg,rm,ad,cp in rows:
            candidates.add((-neg,rm,ad,cp))
    ordered=sorted(candidates,key=lambda z:(z[0],z[1],z[2],z[3]))
    assert ordered
    # State=(total cost, partition of ORIGINAL factor cycles,
    #        removed ORIGINAL factor edges, added new edges, chosen patches).
    states=[(0,tuple(range(cycles)),frozenset(),frozenset(),tuple())]
    beam_history=[]
    for depth in range(cycles-1):
        nxt=[]
        for current,partition,removed,added,history in states:
            for dc,rm,ad,cp in ordered:
                ca,cb=cp
                if partition[ca]==partition[cb]:continue
                if rm[0] in removed or rm[1] in removed:continue
                if ad[0] in added or ad[1] in added:continue
                lo=min(partition[ca],partition[cb]);hi=max(partition[ca],partition[cb])
                group=tuple(lo if q==hi else q for q in partition)
                nxt.append((current+dc,group,
                   removed|frozenset(rm),added|frozenset(ad),history+((dc,rm,ad,cp),)))
        if not nxt:break
        nxt.sort(key=lambda s:(s[0],s[1],tuple(sorted(s[2])),tuple(sorted(s[3]))))
        dedup=set();best=[]
        for entry in nxt:
            key=(entry[1],entry[2],entry[3])
            if key in dedup:continue
            dedup.add(key);best.append(entry)
            if len(best)>=a.beam:break
        states=best
        beam_history.append({'step':depth+1,'states':len(best),
                 'lowest_combined_repair_delta':best[0][0]})
        print(json.dumps({'stage':'beam','step':depth+1,
            'best_delta':best[0][0],'width':len(best)}),flush=True)
    complete=[s for s in states if len(set(s[1]))==1]
    report={'baseline_score':5757191,'factor_score':original_score,
       'factor_cycles':cycles,'cycle_sizes':list(map(int,sizes)),
       'scanned_port_vertices':len(scan),'near_cross_cycle_neighbors':scanned_cross,
       'examined_two_edge_repairs':observed,
       'retained_repair_proposals':len(ordered),
       'component_pair_coverage':[list(x) for x in sorted(heaps)],
       'beam_history':beam_history,'connected_beam_states':len(complete),
       'elapsed_seconds':round(time.monotonic()-start,3),
       'record_improved':False}
    if complete:
        winners=[]
        for delta,partition,removed,added,history in complete:
            edges=(factor-set(removed))|set(added)
            assert len(edges)==N
            # Any formally composed complete cycle must pass complete N-city
            # Hamiltonian reconstruction rather than relying only on the DSU.
            route=make_tour(edges)
            objective=verifier.tour_length(route)
            assert objective==original_score+delta
            winners.append((objective,route,history))
        winners.sort(key=lambda z:z[0])
        best,route,history=winners[0]
        report.update({'best_connected_score':best,
           'repair_cost_from_factor':best-original_score,
           'best_repair_moves':[{'delta':h[0],
                        'removed':[list(e) for e in h[1]],
                        'added':[list(e) for e in h[2]],
                        'component_pair':list(h[3])} for h in history],
           'record_improved':best<5757191})
        blob=json.dumps({'tour':route},separators=(',',':')).encode()
        verdict=verifier.verify_bytes(blob,verifier.load_config())
        assert verdict['valid'] and int(verdict['score'])==best
        report['official_hash']=verdict['canonical_hash']
        if best<5757191:
            cert=Path(a.certificate);cert.parent.mkdir(parents=True,exist_ok=True)
            cert.write_bytes(blob)
    target=Path(a.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result',**{k:z for k,z in report.items() if k not in ('best_repair_moves','beam_history')}}),flush=True)

if __name__=='__main__':main()
