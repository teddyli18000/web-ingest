#!/usr/bin/env python3
"""Joint cross-cycle & interior edge reoptimization around a Mona Lisa 2-factor.

Unlike 11 sequential 2-opt merges, EVERY original factor edge incident to
candidate new ports becomes a variable (not necessarily deleted). Frozen
degree-two paths are contracted. Dynamic exact subtour cuts link components
until one Hamiltonian tour exists. End-to-end official EUC_2D scoring/verification.

A factor of 12 cycles and length 5,757,188 is NOT a tour; the only valid
breakthrough is a connected tour scoring <=5,757,190. Fixed-neighborhood
INFEASIBLE excludes ONLY this graph, not the general 100K instance.
"""
import argparse,importlib.util,json,os,sys,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from ortools.sat.python import cp_model
N=100000
def E(a,b):
    a=int(a);b=int(b)
    return (a,b) if a<b else (b,a)
def connected_components(n, links):
    root=list(range(n));rank=[0]*n
    def find(i):
        while root[i]!=i:
            root[i]=root[root[i]];i=root[i]
        return i
    def union(i,j):
        i=find(i);j=find(j)
        if i==j:return
        if rank[i]<rank[j]:i,j=j,i
        root[j]=i
        rank[i]+=rank[i]==rank[j]
    for u,w in links:union(u,w)
    comps={}
    for i in range(n):comps.setdefault(find(i),[]).append(i)
    return list(comps.values())
def main():
    p=argparse.ArgumentParser()
    for arg in ('factor','baseline','report','certificate'):p.add_argument('--'+arg,required=True)
    p.add_argument('--budget',type=int,default=350)
    p.add_argument('--neighbors',type=int,default=48)
    p.add_argument('--within-budget',type=int,default=1000)
    p.add_argument('--within-neighbors',type=int,default=32)
    p.add_argument('--feasibility-only',action='store_true')
    p.add_argument('--factor-snapshot',required=True)
    p.add_argument('--limit',type=float,default=200)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=20261029)
    p.add_argument('--threshold',type=int,default=5757190)
    args=p.parse_args();tic=time.monotonic()
    vpath=Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py'
    spec=importlib.util.spec_from_file_location('v',vpath)
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    xs,ys=verifier.coordinates()
    xy=np.column_stack((xs,ys))
    def d(u,w):return verifier.euc_2d(xs[u]-xs[w],ys[u]-ys[w])
    orig=json.loads(Path(args.baseline).read_text())['tour']
    assert len(orig)==N and verifier.tour_length(orig)==5757191
    tour=[int(x)-1 for x in orig]
    base={E(tour[i],tour[(i+1)%N]) for i in range(N)}
    data=json.loads(Path(args.factor).read_text())
    label=np.asarray(data['component_labels'],dtype=np.int32)
    ncomp=int(data['cycles'])
    assert len(label)==N and ncomp>=2
    removed={tuple(e) for e in data['removed_baseline_edges']}
    inserted={tuple(e) for e in data['added_nonbaseline_edges']}
    assert removed<=base and not (inserted&base)
    factor=(base-removed)|inserted
    assert len(factor)==N
    factor_score=int(data['factor_score'])
    assert factor_score==5757191-sum(d(*e) for e in removed)+sum(d(*e) for e in inserted)
    adj=[[] for _ in range(N)]
    for u,w in factor:
        assert label[u]==label[w]
        adj[u].append(w);adj[w].append(u)
    assert all(len(x)==2 for x in adj)
    size=np.bincount(label,minlength=ncomp)
    giant=int(size.argmax())
    ports=np.flatnonzero(label!=giant)
    tree=cKDTree(xy)
    _,nn=tree.query(xy[ports],k=args.neighbors+1,workers=args.workers)
    cross={}
    for j,xx in enumerate(ports):
        u=int(xx);g=int(label[u])
        for yy in nn[j,1:]:
            w=int(yy);h=int(label[w])
            if g==h:continue
            e=E(u,w)
            # Estimate a 2-opt repair's net objective impact rather than
            # ranking short chord length; all factor incident edges are
            # independently reoptimized by final exact circuit model.
            old1=max(d(u,q) for q in adj[u])
            old2=max(d(w,q) for q in adj[w])
            estimate=2*d(u,w)-old1-old2
            cross[e]=min(cross.get(e,10**9),estimate)
    allcand=sorted(cross,key=lambda e:(cross[e],d(*e),e))
    assert len(allcand)>=args.budget
    # Minimum 6 incident new candidate chords per non-giant 2-factor cycle.
    # This avoids silently selecting no path out of a smaller component.
    chosen=set();cover=[0]*ncomp
    for cc in range(ncomp):
        if cc==giant:continue
        for e in allcand:
            if cc not in (int(label[e[0]]),int(label[e[1]])):continue
            if e not in chosen:
                chosen.add(e)
                for x in e:cover[int(label[x])]+=1
            if cover[cc]>=6:break
    if len(chosen)>args.budget:raise ValueError("budget insufficient for cycle coverage")
    for e in allcand:
        if len(chosen)==args.budget:break
        chosen.add(e)
    assert len(chosen)==args.budget and all(cover[c]>=6 for c in range(ncomp) if c!=giant)
    # New hypothesis: cheap global patching needs *negative local excitation*
    # inside the original subtours, not just cross-cycle chords.
    within=set()
    if args.within_budget:
        sites=set(x for e in chosen for x in e)
        sites.update(map(int,ports))
        sites=sorted(sites)
        _,same_nn=tree.query(xy[sites],k=args.within_neighbors+1,workers=args.workers)
        proposals={}
        for ii,origin in enumerate(sites):
            for candidate in same_nn[ii,1:]:
                w=int(candidate)
                if w==origin or label[origin]!=label[w]:continue
                e=E(origin,w)
                if e in factor:continue
                # Candidate edge cost relative to the removable incident
                # factor edges; selected exchange pairs jointly downstream.
                difference=2*d(origin,w)-max(d(origin,z) for z in adj[origin])-max(d(w,z) for z in adj[w])
                proposals[e]=min(difference,proposals.get(e,10**9))
        ranked=sorted(proposals,key=lambda e:(proposals[e],d(*e),e))
        if len(ranked)<args.within_budget:raise ValueError(('within pool undersized',len(ranked),args.within_budget))
        within=set(ranked[:args.within_budget])
    print(json.dumps({'stage':'candidate_pools','cross_chords':len(chosen),
          'within_chords':len(within),'within_probe_sites':len(sites) if args.within_budget else 0}),flush=True)
    # The known connected Nagata tour MUST be representable in the joint
    # neighborhood. This destroys the prior artificial choice: start from
    # disconnected factor OR preserve baseline, but never both.
    restore=base-factor
    assert len(restore)>0
    # Reoptimize factor incident edges at every novel port AND every
    # vertex where the factor disagrees with Nagata.
    breakable=set()
    for u,w in chosen|within|restore:
        for t in (u,w):
            for z in adj[t]:breakable.add(E(t,z))
    frozen=factor-breakable
    active=set(x for e in breakable for x in e)
    active.update(x for e in chosen|within|restore for x in e)
    frozen_adj={}
    for u,w in frozen:
        frozen_adj.setdefault(u,[]).append(w)
        frozen_adj.setdefault(w,[]).append(u)
    assert all(len(frozen_adj.get(z,[]))<=1 for z in active)
    mandatory=[];seen_frozen=set()
    for origin in sorted(active):
        for zz in frozen_adj.get(origin,[]):
            e=E(origin,zz)
            if e in seen_frozen:continue
            seen_frozen.add(e);prev=origin;cur=zz
            while cur not in active:
                neighbors=frozen_adj.get(cur,[])
                assert len(neighbors)==2
                following=neighbors[0] if neighbors[0]!=prev else neighbors[1]
                e=E(cur,following)
                assert e not in seen_frozen
                seen_frozen.add(e)
                prev,cur=cur,following
            assert origin!=cur
            mandatory.append(E(origin,cur))
    assert len(seen_frozen)==len(frozen),(len(seen_frozen),len(frozen)
    assert frozen<=base,('Baseline contains no frozen factor-only edge',len(frozen-base)))
    verts=sorted(active);index={u:i for i,u in enumerate(verts)}
    factor_breakcost=sum(d(*e) for e in breakable)
    variable_edges=sorted(breakable|chosen|within|restore)
    costs={e:d(*e) for e in variable_edges}
    model=cp_model.CpModel();bools={}
    inc={u:[] for u in verts};mandatory_inc={u:0 for u in verts}
    for u,w in mandatory:
        mandatory_inc[u]+=1;mandatory_inc[w]+=1
    for u,w in variable_edges:
        var=model.NewBoolVar(f'e{u}_{w}')
        bools[(u,w)]=var
        inc[u].append(var);inc[w].append(var)
        model.AddHint(var,1 if (u,w) in base else 0)
    for u in verts:
        model.Add(sum(inc[u])+mandatory_inc[u]==2)
    delta_expr=sum(costs[e]*x for e,x in bools.items())-factor_breakcost
    threshold_delta=args.threshold-factor_score
    model.Add(delta_expr<=threshold_delta)
    if not args.feasibility_only:model.Minimize(delta_expr)
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=args.seed
    events=[];cuts=0;cycles=0;status='NOT_SOLVED';last_factor=None;success=False
    index_edges=[(index[u],index[w],x) for (u,w),x in bools.items()]
    fixed_pairs=[(index[u],index[w]) for u,w in mandatory]
    while time.monotonic()-tic<args.limit-0.1 and cycles<80:
        seconds=args.limit-(time.monotonic()-tic)
        solver.parameters.max_time_in_seconds=min(20,max(.05,seconds))
        status_code=solver.Solve(model);status=solver.StatusName(status_code)
        cycles+=1
        if status_code not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
            if status_code==cp_model.INFEASIBLE:break
            continue
        selected={e for e,x in bools.items() if solver.Value(x)}
        score=factor_score-factor_breakcost+sum(costs[e] for e in selected)
        assert score<=args.threshold
        links=fixed_pairs+[(u,w) for u,w,x in index_edges if solver.Value(x)]
        groups=connected_components(len(verts),links)
        event={'round':cycles,'score':score,'component_count':len(groups),
            'cuts_so_far':cuts,'solver_status':status,'solver_bound':solver.BestObjectiveBound()}
        events.append(event)
        last_factor=(score,len(groups))
        print(json.dumps({'stage':'separation',**event}),flush=True)
        if len(groups)>1 and score<5757191:
            # Critical reformulation: previously selected cross ports were
            # scored for ORIGINAL cycles. Internal exchanges create NEW
            # bottleneck cycles, so regenerate their ports from scratch.
            complete=frozen|selected
            assert len(complete)==N
            whole_adj=[[] for _ in range(N)]
            for u,w in complete:whole_adj[u].append(w);whole_adj[w].append(u)
            assert all(len(aa)==2 for aa in whole_adj)
            current_labels=[-1]*N;cycle_sizes=[]
            for start in range(N):
                if current_labels[start]>=0:continue
                cid=len(cycle_sizes);node=start;prior=-1;number=0
                while current_labels[node]<0:
                    current_labels[node]=cid;number+=1
                    aa,bb=whole_adj[node]
                    following=aa if aa!=prior else bb
                    prior,node=node,following
                assert node==start
                cycle_sizes.append(number)
            assert len(cycle_sizes)==len(groups)
            snapshot={'source':'dynamic SEC degree2 cycle feedback',
                'factor_score':score,'cycles':len(cycle_sizes),
                'cycle_sizes':cycle_sizes,'component_labels':current_labels,
                'added_nonbaseline_edges':[list(e) for e in sorted(complete-base)],
                'removed_baseline_edges':[list(e) for e in sorted(base-complete)],
                'source_factor_score':factor_score,
                'search_candidate_chords':len(chosen),'search_within_chords':len(within)}
            out=Path(args.factor_snapshot);out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(snapshot,separators=(',',':'))+'\n')
            print(json.dumps({'stage':'new_factor','cycles':len(cycle_sizes),
                'score':score,'snapshot':str(out)}),flush=True)
        if len(groups)==1:
            # Full N-city permutation and authoritative scorer.
            edges=frozen|selected
            assert len(edges)==N
            all_adj=[[] for _ in range(N)]
            for u,w in edges:all_adj[u].append(w);all_adj[w].append(u)
            assert all(len(z)==2 for z in all_adj)
            cycle=[1];seen=bytearray(N);cur=0;prev=-1
            while not seen[cur]:
                seen[cur]=1
                x,y=all_adj[cur];nextcity=x if x!=prev else y
                cycle.append(nextcity+1);prev,cur=cur,nextcity
            assert cur==0 and len(cycle)==N+1
            cycle=cycle[:-1]
            assert verifier.tour_length(cycle)==score
            blob=json.dumps({'tour':cycle},separators=(',',':')).encode()
            verdict=verifier.verify_bytes(blob,verifier.load_config())
            assert verdict['valid'] and int(verdict['score'])==score
            fp=Path(args.certificate);fp.parent.mkdir(parents=True,exist_ok=True)
            fp.write_bytes(blob)
            success=True
            break
        # Add valid subtour cut inequalities for every proper component;
        # mandatory frozen paths never cross this partition.
        for group in groups:
            if len(group)>len(verts)//2:continue
            S=set(group)
            outward=[x for u,w,x in index_edges if (u in S)!=(w in S)]
            assert outward,'original factor spans all cycles but pool excludes an incumbent?'
            model.Add(sum(outward)>=2);cuts+=1
        if not any(len(g)<=len(verts)//2 for g in groups):
            raise AssertionError('no valid SEC component selected')
    result={'status':status,'original_factor_cycles':ncomp,'original_factor_cost':factor_score,
        'record_score':5757191,'threshold':args.threshold,
        'new_cross_cycle_edge_pool':len(cross),
        'candidate_chords':len(chosen),'within_cycle_chords':len(within),
        'baseline_edges_restored_as_optional':len(restore),
        'feasibility_only':args.feasibility_only,'factor_edges_reoptimized':len(breakable),
        'frozen_edges':len(frozen),'mandatory_paths':len(mandatory),
        'contracted_vertices':len(verts),'variable_edges':len(variable_edges),
        'selected_coverage_counts':cover,
        'iterations':cycles,'cuts_added':cuts,'events':events[-30:],
        'last_good_degree_two':last_factor,
        'elapsed_seconds':round(time.monotonic()-tic,3),
        'verified_record_breakthrough':success}
    dest=Path(args.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'stage':'result',**{k:v for k,v in result.items() if k!='events'}}),flush=True)
if __name__=='__main__':main()
