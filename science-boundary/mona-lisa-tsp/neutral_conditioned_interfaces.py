#!/usr/bin/env python3
"""Exact full-metric global path-interface reoptimization around frustrated chords.

Cut k widely separated edges from the incumbent Hamiltonian tour. All other
100,000-k edges remain mandatory. Contract each intact path into a fixed edge,
and solve the complete-metric Hamiltonian cycle on 2k endpoints by CP-SAT
AddCircuit. Every found gain is rescored by the official p010 verifier.

Seed edges come from locally profitable but disconnected exact 2-edge
exchanges found symbolically on the 51-dimensional neutral plateau. The
remaining cut edges are sampled from spatially and topologically nonlocal
endpoint frontiers. Exact solver infeasibility applies only to a chosen
finite set of deleted incumbent edges. This is NOT a proof of global k-opt
optimality or a claim of method novelty.
"""
import argparse,importlib.util,json,os,random,time
from pathlib import Path
from scipy.spatial import cKDTree
from ortools.sat.python import cp_model

def key(a,b):return (a,b) if a<b else (b,a)

def main():
 p=argparse.ArgumentParser()
 for name in ('baseline','motifs','report','certificate'):p.add_argument('--'+name,required=True)
 p.add_argument('--neutral-moves',required=True)
 p.add_argument('--neutral-state',choices=['baseline','all','euclidean','random'],default='baseline')
 p.add_argument('--k',type=int,default=12)
 p.add_argument('--start-seed',type=int,default=0)
 p.add_argument('--seeds',type=int,default=40)
 p.add_argument('--trials',type=int,default=4)
 p.add_argument('--time-per-model',type=float,default=2.0)
 p.add_argument('--neighbor-k',type=int,default=64)
 p.add_argument('--workers',type=int,default=2)
 p.add_argument('--random-seed',type=int,default=1298)
 a=p.parse_args();started=time.monotonic()
 original=json.loads(Path(a.baseline).read_text())['tour']
 assert len(original)==100000 and len(set(original))==100000
 n=len(original)
 original_base={key(original[i],original[(i+1)%n]) for i in range(n)}
 source_moves=json.loads(Path(a.neutral_moves).read_text())
 chosen_moves=[source_moves['moves'][i] for i in source_moves['selected_indices']]
 assert len(chosen_moves)==51
 if a.neutral_state=='all':neutral_mask=(1<<51)-1
 elif a.neutral_state=='euclidean':neutral_mask=sum(1<<i for i,m in enumerate(chosen_moves) if m['continuous_delta']<0)
 elif a.neutral_state=='random':neutral_mask=random.Random(a.random_seed).getrandbits(51)
 else:neutral_mask=0
 if neutral_mask:
    modified=set(original_base)
    for i,m in enumerate(chosen_moves):
       if (neutral_mask>>i)&1:modified.difference_update(key(*e) for e in m['removed'])
    for i,m in enumerate(chosen_moves):
       if (neutral_mask>>i)&1:modified.update(key(*e) for e in m['added'])
    assert len(modified)==n
    adj=[[] for _ in range(n+1)]
    for u,v in modified:adj[u].append(v);adj[v].append(u)
    assert all(len(adj[u])==2 for u in range(1,n+1))
    rebuild=[];u=1;prev=0;seen=bytearray(n+1)
    while not seen[u]:
       seen[u]=1;rebuild.append(u)
       x,y=adj[u];nxt=x if x!=prev else y
       prev,u=u,nxt
    assert u==1 and len(rebuild)==n
    original=rebuild
 spec=importlib.util.spec_from_file_location('p010',Path(os.environ['FEWSHOTS_ROOT'])/
     'problems/p010-mona-lisa-tsp/verify/verify.py')
 verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
 xs,ys=verify.coordinates()
 coords=list(zip(xs,ys))
 tree=cKDTree(coords)
 def dist(u,v):return verify.euc_2d(xs[u-1]-xs[v-1],ys[u-1]-ys[v-1])
 assert verify.tour_length(original)==5757191
 pos={city:i for i,city in enumerate(original)}
 oldpos={key(original[i],original[(i+1)%n]):i for i in range(n)}
 motifs=json.loads(Path(a.motifs).read_text())['positive_repair_motifs']
 usable=[(j,m) for j,m in enumerate(motifs)
         if all(key(*q) in oldpos for q in m['old'])
         and all(key(*q) not in oldpos for q in m['added'])]
 assert usable
 rng=random.Random(a.random_seed)
 def enough(q,choices):
    return all(min((q-p)%n,(p-q)%n)>1 for p in choices)
 def choose_cuts(seed,trial):
    chosen=[oldpos[key(*e)] for e in seed['old'] if key(*e) in oldpos]
    chosen=list(dict.fromkeys(chosen))
    if len(chosen)!=2 or not enough(chosen[0],[chosen[1]]):
        return None
    # Split-seed edges are mandatory. Remaining interfaces sample
    # positions near endpoints of prior cuts, plus occasional nonlocal
    # candidates from the 100K-city geometric field.
    while len(chosen)<a.k:
        if trial%4==0:
            focus=rng.choice(chosen)
            anchor=rng.choice((original[focus],original[(focus+1)%n]))
            _,near=tree.query((xs[anchor-1],ys[anchor-1]),k=a.neighbor_k)
            candidates=[]
            for v0 in near:
                p=pos[int(v0)+1]
                candidates.extend((p,(p-1)%n))
            rng.shuffle(candidates)
        elif trial%4==1:
            # Include another high-frustration motif's baseline endpoint.
            another=motifs[rng.randrange(min(500,len(motifs)))]
            candidates=[oldpos[key(*edge)] for edge in another['old'] if key(*edge) in oldpos]
            rng.shuffle(candidates)
        elif trial%4==2:
            focus=rng.choice(chosen)
            delta=rng.choice((-200,-100,-30,30,100,200,800,-800))
            candidates=[(focus+delta)%n,(focus+delta+1)%n]
        else:
            candidates=[rng.randrange(n) for _ in range(20)]
        got=False
        for q in candidates:
            if enough(q,chosen):
                chosen.append(q);got=True;break
        if not got:
            for _ in range(1000):
                q=rng.randrange(n)
                if enough(q,chosen):
                    chosen.append(q);got=True;break
        assert got
    return sorted(chosen)
 def exact(cuts,budget):
    # Removing k cycle edges leaves k vertex-disjoint immutable paths.
    # Endpoints are 2k distinct vertices because cuts are nonadjacent.
    endpoints=[]
    fixed=[]
    for i,q in enumerate(cuts):
        next_cut=cuts[(i+1)%len(cuts)]
        start_city=original[(q+1)%n]
        end_city=original[next_cut]
        assert start_city!=end_city
        endpoints.extend((start_city,end_city))
        fixed.append((start_city,end_city))
    assert len(set(endpoints))==2*len(cuts)
    idx={v:i for i,v in enumerate(endpoints)}
    m=cp_model.CpModel();arcs=[];edge_vars={};terms=[]
    for u,v in fixed:
        f=m.NewBoolVar(f'f{u}_{v}');r=m.NewBoolVar(f'r{u}_{v}')
        m.Add(f+r==1)
        arcs.extend(((idx[u],idx[v],f),(idx[v],idx[u],r)))
    for i,u in enumerate(endpoints):
        for j in range(i+1,len(endpoints)):
            v=endpoints[j]
            if i//2==j//2:continue
            e=key(u,v)
            if e in edge_vars:continue
            x=m.NewBoolVar(f'e{u}_{v}')
            f=m.NewBoolVar(f'F{u}_{v}');r=m.NewBoolVar(f'R{u}_{v}')
            m.Add(f+r==x)
            edge_vars[e]=x
            arcs.extend(((idx[u],idx[v],f),(idx[v],idx[u],r)))
            terms.append(dist(u,v)*x)
    m.AddCircuit(arcs)
    old_cost=sum(dist(original[q],original[(q+1)%n]) for q in cuts)
    new_cost=sum(terms)
    m.Add(new_cost<=old_cost-1)
    m.Minimize(new_cost)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=budget
    solver.parameters.num_search_workers=a.workers
    solver.parameters.random_seed=a.random_seed
    result=solver.Solve(m)
    status=solver.StatusName(result)
    if result not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return {'status':status,'bound':solver.BestObjectiveBound()-old_cost,
                'branches':solver.NumBranches(),'conflicts':solver.NumConflicts()},None
    candidate_edges={key(original[i],original[(i+1)%n]) for i in range(n)}
    for q in cuts:candidate_edges.remove(key(original[q],original[(q+1)%n]))
    added=[e for e,x in edge_vars.items() if solver.Value(x)]
    candidate_edges.update(added)
    assert len(candidate_edges)==n and len(added)==len(cuts)
    adj=[[] for _ in range(n+1)]
    for u,v in candidate_edges:adj[u].append(v);adj[v].append(u)
    assert all(len(adj[u])==2 for u in range(1,n+1))
    route=[];seen=bytearray(n+1);u=1;prev=0
    while not seen[u]:
        seen[u]=1;route.append(u)
        z,w=adj[u];nxt=z if z!=prev else w
        prev,u=u,nxt
    assert u==1 and len(route)==n
    score=verify.tour_length(route)
    assert score==5757191+sum(dist(*e) for e in added)-old_cost
    return {'status':status,'score':score,'gain':5757191-score,
            'bound':solver.BestObjectiveBound()-old_cost,
            'branches':solver.NumBranches()},route
 stats={'OPTIMAL':0,'INFEASIBLE':0,'UNKNOWN':0,'FEASIBLE':0,'MODEL_INVALID':0}
 best=5757191;records=[]
 target=Path(a.certificate)
 for i in range(a.start_seed,min(a.start_seed+a.seeds,len(usable))):
    original_motif_index,seed=usable[i]
    for trial in range(a.trials):
        cuts=choose_cuts(seed,trial)
        if cuts is None:continue
        result,route=exact(cuts,a.time_per_model)
        stats[result['status']]=stats.get(result['status'],0)+1
        rec={'seed_rank':i,'source_motif':original_motif_index,'trial':trial,'cut_positions':cuts,**result}
        records.append(rec)
        if route and result['score']<best:
            best=result['score']
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(json.dumps({'tour':route},separators=(',',':')))
            print(json.dumps({'stage':'breakthrough_candidate','score':best,
                'seed_rank':i,'source_motif':original_motif_index,'trial':trial}),flush=True)
        if len(records)%40==0:
            print(json.dumps({'stage':'progress','models':len(records),
                'best_score':best,'statuses':stats}),flush=True)
 report={'source':'Few Shots p010 baseline and symbolic positive motifs',
         'metric':'complete TSPLIB integer EUC_2D (not just planar sparse graph)',
         'k':a.k,'neutral_state':a.neutral_state,
         'neutral_mask':str(neutral_mask),'usable_seed_motifs':len(usable),
         'seed_range':[a.start_seed,a.start_seed+a.seeds],
         'trials_per_seed':a.trials,'models':len(records),'statuses':stats,
         'best_verified_score':best,'wall_seconds':round(time.monotonic()-started,2),
         'records':records}
 output=Path(a.report);output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k!='records'}),flush=True)

if __name__=='__main__':main()
