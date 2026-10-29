#!/usr/bin/env python3
"""Exact global insertion of a 5- or 8-city disconnected microcycle.

The source is a cheap *2-factor* constructed by one/two profitable exchanges.
Instead of repairing with only two-edge swaps, enumerate every possible
Hamiltonian path through each isolated microcycle (up to 8! permutations)
and insert that path at ANY eligible external tour edge.

All 100,000 original edges plus 51-switch neutral edges are eligible as
attachment cuts; bridges and internal paths use the COMPLETE Euclidean graph,
not Cook et al.'s planar sparse graph. Every length uses exact TSPLIB EUC_2D.
The dynamic choices of disjoint insertion locations and compatible switch
states are optimized jointly.
"""
import argparse,importlib.util,itertools,json,os,time
from pathlib import Path

def E(a,b):return (a,b) if a<b else (b,a)

def components(n,edges):
    adj=[[] for _ in range(n+1)]
    for a,b in edges:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[u])==2 for u in range(1,n+1))
    seen=bytearray(n+1);cycles=[]
    for start in range(1,n+1):
        if seen[start]:continue
        now=start;prev=0;cycle=[]
        while not seen[now]:
            seen[now]=1;cycle.append(now)
            u,v=adj[now];nxt=u if u!=prev else v
            prev,now=now,nxt
        assert now==start
        cycles.append(cycle)
    return sorted(cycles,key=len)

def main():
    p=argparse.ArgumentParser()
    for x in ('baseline','moves','motifs','report','certificate'):
        p.add_argument('--'+x,required=True)
    p.add_argument('--seed-indices',default='52')
    p.add_argument('--include-neutral',action='store_true')
    args=p.parse_args();clock=time.monotonic()
    tour=json.loads(Path(args.baseline).read_text())['tour'];n=len(tour)
    base={E(tour[i],tour[(i+1)%n]) for i in range(n)}
    assert len(base)==n
    moves=json.loads(Path(args.moves).read_text())
    mods=[moves['moves'][i] for i in moves['selected_indices']]
    motifdata=json.loads(Path(args.motifs).read_text())['positive_repair_motifs']
    seeds=[motifdata[i] for i in map(int,args.seed_indices.split(','))]
    old_seed=set();new_seed=set()
    for m in seeds:
        for q in m['old']:
            e=E(*q);assert e in base and e not in old_seed
            old_seed.add(e)
        for q in m['added']:
            e=E(*q);assert e not in base and e not in new_seed
            new_seed.add(e)
    seed_edges=(base-old_seed)|new_seed
    source=components(n,seed_edges)
    small=[x for x in source if len(x)<=20]
    assert len(small)==len(seeds) and len(source)==1+len(small)
    assert len(source[-1])==n-sum(map(len,small))
    inside=set().union(*(set(x) for x in small))
    assert all(5<=len(x)<=8 for x in small)
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
       'problems/p010-mona-lisa-tsp/verify/verify.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    xs,ys=v.coordinates()
    def d(a,b):return verifier.euc_2d(xs[a-1]-xs[b-1],ys[a-1]-ys[b-1])
    assert verifier.tour_length(tour)==5757191
    seed_score=5757191-sum(m['gain'] for m in seeds)
    old_owner={};new_owner={};blocked=set()
    for i,m in enumerate(mods):
        changed={city for pair in m['removed']+m['added'] for city in pair}
        if changed&inside:blocked.add(i)
        for q in m['removed']:
            e=E(*q);assert e not in old_owner;old_owner[e]=i
        for q in m['added']:
            e=E(*q);assert e not in new_owner;new_owner[e]=i
    # Candidate external cut edges in the baseline tour, seed's new external
    # edges, and neutral switches' new edges. Each carries a required bit.
    candidates={}
    for e in base:
        if e not in old_seed and e[0] not in inside and e[1] not in inside:
            candidates[e]=(old_owner[e],0) if e in old_owner else None
    for e in new_seed:
        if e[0] not in inside and e[1] not in inside:
            assert e not in candidates
            candidates[e]=None
    if args.include_neutral:
        for e,i in new_owner.items():
            if e[0] not in inside and e[1] not in inside and i not in blocked:
                if e not in candidates:candidates[e]=(i,1)
    # For each microcycle: exact minimum Hamiltonian path between endpoints.
    # This includes paths using edges outside the published reduction.
    path_dp=[]
    base_island_cost=[]
    for S in small:
        oldcost=sum(d(a,b) for a,b in seed_edges if a in S and b in S)
        assert oldcost>0
        base_island_cost.append(oldcost)
        opt={}
        for ordering in itertools.permutations(S):
            start,end=ordering[0],ordering[-1]
            cost=sum(d(ordering[i],ordering[i+1]) for i in range(len(S)-1))
            if (start,end) not in opt or cost<opt[(start,end)][0]:
                opt[(start,end)]=(cost,ordering)
        assert len(opt)==len(S)*(len(S)-1)
        path_dp.append(opt)
    options=[]
    for Sidx,opt in enumerate(path_dp):
        rows=[]
        oldcost=base_island_cost[Sidx]
        endpoints=sorted({u for edge in candidates for u in edge})
        near={u:[d(u,s) for s in small[Sidx]] for u in endpoints}
        S=small[Sidx]
        pathopts=[(S.index(start),S.index(end),info[0],info[1])
                  for (start,end),info in opt.items()]
        for (u,v),req in candidates.items():
            du=near[u];dv=near[v]
            low=None
            for i,j,pc,perm in pathopts:
                extra=du[i]+pc+dv[j]
                if low is None or extra<low[0]:low=(extra,perm)
            penalty=low[0]-d(u,v)-oldcost
            rows.append((penalty,(u,v),req,low[1]))
        rows.sort(key=lambda item:item[0])
        options.append(rows)
        print(json.dumps({'stage':'island_options','size':len(S),
            'eligible_external_edges':len(rows),
            'best_insertion_penalty':rows[0][0],
            'top_five_penalties':[r[0] for r in rows[:5]]}),flush=True)
    # Exact compatible joint minimum: skip pairs that use same outside edge,
    # demand opposing states of same switch, or contradict blocked switch.
    def compatible(A,B):
        if A[1]==B[1]:return False
        rules=[r[2] for r in (A,B) if r[2] is not None]
        if any(i in blocked and state==1 for i,state in rules):return False
        return not(len(rules)>1 and rules[0][0]==rules[1][0] and rules[0][1]!=rules[1][1])
    if len(options)==1:
        winner=(options[0][0],)
    else:
        winner=None;bestcost=float('inf')
        for a in options[0]:
            if a[0]+options[1][0][0]>=bestcost:break
            for b in options[1]:
                cost=a[0]+b[0]
                if cost>=bestcost:break
                if compatible(a,b):
                    bestcost=cost;winner=(a,b)
                    break
        assert winner
    penalty=sum(rec[0] for rec in winner)
    estimated=seed_score+penalty
    assert estimated>=0
    report={'baseline_score':5757191,'source_2factor_score':seed_score,
       'source_components':[len(x) for x in source],
       'islands':[len(x) for x in small],
       'seed_indices':list(map(int,args.seed_indices.split(','))),
       'allow_51_neutral_edges':args.include_neutral,
       'eligible_external_edges':len(candidates),
       'exact_best_penalty':penalty,
       'best_possible_tour_score_in_this_insertion_family':estimated,
       'winning_attachment_edges':[list(x[1]) for x in winner],
       'winning_paths':[list(x[3]) for x in winner],
       'elapsed_seconds':round(time.monotonic()-clock,2)}
    # Reconstruct a compatible 51-bit neutral state.
    mask=0
    for penalty_i,cut,req,path in winner:
        if req and req[1]==1:mask|=1<<req[0]
    assert all((mask>>i)&1==0 for i in blocked)
    eds=set(base)
    for i,m in enumerate(mods):
        if (mask>>i)&1:
            eds.difference_update(E(*q) for q in m['removed'])
            eds.update(E(*q) for q in m['added'])
    assert old_seed<=eds and not(new_seed&eds)
    eds.difference_update(old_seed);eds.update(new_seed)
    assert len(components(n,eds))==len(source)
    for S,rec in zip(small,winner):
        _,(u,v),req,path=rec
        cut=E(u,v)
        assert cut in eds
        eds.remove(cut)
        eds.difference_update(e for e in list(eds) if e[0] in S and e[1] in S)
        for i in range(len(path)-1):eds.add(E(path[i],path[i+1]))
        eds.add(E(u,path[0]));eds.add(E(path[-1],v))
    assert len(eds)==n
    candidate_cycles=components(n,eds)
    assert len(candidate_cycles)==1
    full=candidate_cycles[0]
    actual=verifier.tour_length(full)
    assert actual==estimated,(actual,estimated)
    report['verified_score']=actual
    report['winning_mask']=str(mask)
    report['official_hash']=verifier.canonical_hash({'tour':verifier.canonical_tour(full)})
    if actual<5757191:
        out=Path(args.certificate);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps({'tour':full},separators=(',',':')))
        report['breakthrough']=True
    else:report['breakthrough']=False
    output=Path(args.report);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result',**report}),flush=True)
if __name__=='__main__':main()
