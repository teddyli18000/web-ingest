#!/usr/bin/env python3
"""Exact optimistic multiblock re-insertion bounds for isolated microcycles.

Split a 5- or 8-city disconnected cycle into k disjoint Hamiltonian paths
and insert each path into any other tour edge, using COMPLETE EUC_2D weights.
Relaxation allows insertion cuts to overlap or demand incompatible 51-switch
states, so its minimum is a valid LOWER BOUND for actual k-block insertion.
If this lower bound is >= 5,757,191, *all* such improvements are excluded.
"""
import argparse,gzip,importlib.util,itertools,json,os,time
from pathlib import Path

def ed(a,b):return (a,b) if a<b else (b,a)
def findcycles(n,edges):
    adj=[[] for _ in range(n+1)]
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[i])==2 for i in range(1,n+1))
    seen=bytearray(n+1);out=[]
    for start in range(1,n+1):
        if seen[start]:continue
        cyc=[];v=start;prev=0
        while not seen[v]:
            seen[v]=1;cyc.append(v)
            a,b=adj[v];nxt=a if a!=prev else b
            prev,v=v,nxt
        assert v==start
        out.append(cyc)
    return sorted(out,key=len)

def exact_subset_path_cost(S,D):
    k=len(S)
    path={}
    for count in range(1,k+1):
        for cities in itertools.combinations(range(k),count):
            mask=sum(1<<i for i in cities)
            for order in itertools.permutations(cities):
                cost=sum(D[order[i]][order[i+1]] for i in range(count-1))
                key=(mask,order[0],order[-1])
                if key not in path or cost<path[key][0]:path[key]=(cost,order)
    return path

def main():
    p=argparse.ArgumentParser()
    for name in ('baseline','moves','motifs','report'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--seed-indices',default='52')
    p.add_argument('--include-neutral',action='store_true')
    p.add_argument('--max-blocks',type=int,default=4)
    args=p.parse_args();t0=time.monotonic()
    t=json.loads(Path(args.baseline).read_text())['tour'];n=len(t)
    base={ed(t[i],t[(i+1)%n]) for i in range(n)}
    data=json.loads(Path(args.moves).read_text())
    mods=[data['moves'][i] for i in data['selected_indices']]
    motifs=json.loads(Path(args.motifs).read_text())['positive_repair_motifs']
    seed_idxs=list(map(int,args.seed_indices.split(',')))
    old=set();new=set()
    for j in seed_idxs:
        for q in motifs[j]['old']:
            e=ed(*q);assert e in base and e not in old;old.add(e)
        for q in motifs[j]['added']:
            e=ed(*q);assert e not in base and e not in new;new.add(e)
    seed=(base-old)|new
    cycles=findcycles(n,seed)
    islands=[x for x in cycles if len(x)<=20]
    assert len(islands)==len(seed_idxs)
    island_vertices=set().union(*(set(x) for x in islands))
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
    xs,ys=verify.coordinates()
    def d(a,b):return verify.euc_2d(xs[a-1]-xs[b-1],ys[a-1]-ys[b-1])
    assert verify.tour_length(t)==5757191
    candidates=set(e for e in seed if e[0] not in island_vertices and e[1] not in island_vertices)
    if args.include_neutral:
        for i,m in enumerate(mods):
            touched={v for q in m['removed']+m['added'] for v in q}
            if touched&island_vertices:continue
            for q in m['added']:
                e=ed(*q)
                if e[0] not in island_vertices and e[1] not in island_vertices:
                    candidates.add(e)
    assert candidates
    seedcost=5757191-sum(motifs[i]['gain'] for i in seed_idxs)
    info=[];bounds_by_island=[]
    for S in islands:
        k=len(S);K=(1<<k)-1
        cyclecost=sum(d(a,b) for a,b in seed if a in S and b in S)
        internal=[[d(u,v) for v in S] for u in S]
        pathcost=exact_subset_path_cost(S,internal)
        bridge=[[float('inf')]*k for _ in range(k)]
        bridgeedge=[[None]*k for _ in range(k)]
        for u,v in candidates:
            oldcost=d(u,v)
            left=[d(u,x) for x in S]
            right=[d(v,x) for x in S]
            for a in range(k):
                for b in range(k):
                    value=left[a]+right[b]-oldcost
                    if value<bridge[a][b]:
                        bridge[a][b]=value;bridgeedge[a][b]=(u,v)
        # Cheapest insertion path through each nonempty subset.
        single={};by_subset={}
        for (mask,i,j),(pathlen,order) in pathcost.items():
            val=pathlen+bridge[i][j]
            if mask not in single or val<single[mask][0]:
                single[mask]=(val,tuple(S[q] for q in order),bridgeedge[i][j])
        by_subset[1]={m:rec for m,rec in single.items()}
        optimistic={1:(single[K][0],(K,))}
        for blocks in range(2,min(args.max_blocks,k)+1):
            last=by_subset[blocks-1]
            cur={}
            for mask in range(1,K+1):
                best=None
                sub=(mask-1)&mask
                while sub:
                    rest=mask^sub
                    if rest in last:
                        cost=last[rest][0]+single[sub][0]
                        if best is None or cost<best[0]:
                            best=(cost,last[rest][1]+(sub,))
                    sub=(sub-1)&mask
                if best:cur[mask]=best
            by_subset[blocks]=cur
            if K in cur:optimistic[blocks]=cur[K]
        data_out={}
        for blocks,(value,partition) in optimistic.items():
            data_out[str(blocks)]={'block_count':blocks,'relaxed_insertion_cost':value,
              'cycle_cost_removed':cyclecost,'net_insertion_penalty':value-cyclecost,
              'partition_sizes':[int(mask).bit_count() for mask in partition],
              'selected_paths':[list(single[mask][1]) for mask in partition],
              'selected_attachment_edges':[list(single[mask][2]) for mask in partition],
              'is_relaxed_bound':True}
        info.append({'island_size':k,'old_cycle_cost':cyclecost,'paths':len(pathcost),
           'outside_edge_candidates':len(candidates),'optimistic_by_blocks':data_out})
        bounds_by_island.append({b:val[0]-cyclecost for b,val in optimistic.items()})
        print(json.dumps({'stage':'island','size':k,'bounds':bounds_by_island[-1]}),flush=True)
    # Joint bounds simply add individual minima; independent optimal
    # cut/neutral-state constraints are relaxed, so this is safe.
    combos=[]
    for block_counts in itertools.product(*(list(x) for x in bounds_by_island)):
        score=seedcost+sum(bounds_by_island[i][blocks] for i,blocks in enumerate(block_counts))
        combos.append({'blocks_per_island':list(block_counts),
                       'optimistic_lower_bound_on_tour_score':score})
    result={'baseline':5757191,'seed_score':seedcost,
        'seed_indices':seed_idxs,'source_components':[len(x) for x in cycles],
        'neutral_candidate_edges':args.include_neutral,
        'outside_edge_candidates':len(candidates),'islands':info,
        'joint_relaxed_lower_bounds':sorted(combos,key=lambda x:x['optimistic_lower_bound_on_tour_score']),
        'elapsed_seconds':round(time.monotonic()-t0,2)}
    dest=Path(args.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'stage':'result','best_relaxed_score':result['joint_relaxed_lower_bounds'][0],
                       'time_seconds':result['elapsed_seconds']}),flush=True)

if __name__=='__main__':main()
