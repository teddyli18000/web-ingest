#!/usr/bin/env python3
"""Constructive large-neighborhood search from verified 102-gate AES AND shear.

Rather than solving a 3000-edge whole-circuit CP-SAT model from scratch,
keep most of a *valid complete 102-gate witness* fixed, releasing a dependent
cone and a second nonlocal cluster. Newly synthesized XOR/XNOR helpers and
alternate 102-parent factorizations may serve both clusters simultaneously.

Every returned circuit is re-evaluated over all 256 AES inputs. A strict
improvement with a genuinely different AND truth-function set becomes a
reproducible 101/100 certificate. This script makes no UNSAT claims about the
whole problem, and distinguishes UNKNOWN from a verified 102 seed.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib, random, time
from ortools.sat.python import cp_model
import released_and_skeleton as ras
import semantic_shear_fixed_and as sf
import semantic_helper_closure as hc
import make_and_shear_102 as shear

INPUTS=sf.INPUTS
OPS=sf.OPS

def prepared_graph(archive,parents,helpers,include_and,args_source):
    baseline=ras.load_circuit('fs-101')
    _,_,pool=sf.collect(archive,parents,baseline,102)
    seed=baseline if args_source=='fs101' else shear.build()[1]
    vals,ands,es=sf.describe(seed)
    pool.append({'path':'active-verified-seed','c':seed,'v':vals,'ands':ands,'edges':es})
    other=shear.build()[1] if args_source=='fs101' else baseline
    v2,a2,e2=sf.describe(other)
    pool.append({'path':'alternate-nonlinear-parent','c':other,'v':v2,'ands':a2,'edges':e2})
    edges,incoming,nodes=sf.union_graph(pool)
    if helpers:
        edges,incoming,nodes,helper_info=hc.expand_semantic_gate_space(
            edges,nodes,helpers,include_and)
    else: helper_info={'original_nodes':len(nodes),'original_edges':len(edges),
                      'expanded_nodes':len(nodes),'expanded_edges':len(edges),
                      'selected_novel_helpers':0}
    output_vals=[vals[w] for w in seed['outputs']]
    required_and=sf.describe(seed)[1]
    ref_and=sf.describe(baseline)[1]
    return seed,edges,incoming,nodes,output_vals,required_and,ref_and,helper_info,len(pool)

def seed_info(seed):
    v=sf.trace(seed)
    keys=[];by_fun={}
    graph=collections.defaultdict(set)
    for idx,g in enumerate(seed['gates']):
        f=v[g['out']];a=v[g['a']];b=v[g['b']]
        key=(f,g['op'],*sorted((a,b)))
        keys.append(key);by_fun[f]=idx
    for idx,g in enumerate(seed['gates']):
        for w in (g['a'],g['b']):
            if w in v and v[w] in by_fun:
                graph[by_fun[v[w]]].add(idx)
    return keys,graph,v

def downstream(graph,index):
    seen={index};todo=[index]
    while todo:
        i=todo.pop()
        for j in graph[i]:
            if j not in seen:seen.add(j);todo.append(j)
    return seen

def neighborhood(rng,keys,graph,size,kind,pivot=None):
    N=len(keys)
    nonlinear=[i for i,x in enumerate(keys) if x[1]=='AND']
    all_indices=list(range(N))
    if kind=='cone':
        starts=[rng.choice(all_indices)]
        if rng.random()<0.65:starts.append(rng.choice(all_indices))
        free=set().union(*(downstream(graph,i) for i in starts))
        if len(free)>size:
            # Switch to a later root whose dependency closure fits in size.
            ranks=[i for i in all_indices if 4<=len(downstream(graph,i))<=size]
            if ranks:
                free=downstream(graph,rng.choice(ranks))
        if len(free)<size:
            # Add a second separated neighborhood, permitting nonlocal sharing.
            center=rng.choice(all_indices)
            radius=max(1,(size-len(free))//2)
            free.update(range(max(0,center-radius),min(N,center+radius+1)))
    elif kind=='two-windows':
        p=rng.choice(nonlinear) if rng.random()<0.35 else rng.randrange(N)
        q=rng.randrange(N)
        width=max(2,size//4)
        free=set(range(max(0,p-width),min(N,p+width+1)))
        free.update(range(max(0,q-width),min(N,q+width+1)))
    elif kind=='late':
        p=rng.randrange(max(0,N-size),N)
        free=set(range(p,N))
        q=rng.randrange(N)
        free.update(range(max(0,q-size//5),min(N,q+size//5+1)))
    else:
        free=set(rng.sample(all_indices,min(N,size)))
    if pivot is not None and rng.random()<0.45:
        free.update(range(max(0,pivot-3),min(N,pivot+4)))
    if len(free)>size:
        # Keeping a dependency cone intact matters more than arbitrary pruning.
        # Prefer only the originally chosen subset if within size, otherwise
        # preserve a contiguous sample around a central index.
        free=set(sorted(free)[rng.randrange(len(free)-size+1):][:size])
    return free

def solve_neighbor(seed,edges,nodes,outputs,required_and,
                   free,upper_bound,seconds,workers,rng,
                   force_change=False,allow_and_change=False,calibrate=False):
    seed_edges,graph,v=seed_info(seed)
    edge_pos={e:k for k,e in enumerate(edges)}
    for x in seed_edges:
        if x not in edge_pos:raise AssertionError(('seed edge missing in graph',x))
    model=cp_model.CpModel()
    inputs=set(INPUTS.values())
    active={f:model.NewBoolVar('n'+str(i)) for i,f in enumerate(sorted(nodes-inputs))}
    max_depth=150
    level={f:model.NewIntVar(1,max_depth,'d'+str(i)) for i,f in enumerate(sorted(nodes-inputs))}
    chosen=[model.NewBoolVar('e'+str(i)) for i in range(len(edges))]
    by_target=collections.defaultdict(list)
    and_target=collections.defaultdict(list)
    for i,(f,op,a,b) in enumerate(edges):
        by_target[f].append(i)
        if op=='AND':and_target[f].append(i)
        for p in (a,b):
            if p not in inputs:
                model.AddImplication(chosen[i],active[p])
                model.Add(level[f]>level[p]).OnlyEnforceIf(chosen[i])
    for f,var in active.items():
        model.Add(sum(chosen[i] for i in by_target[f])==var)
    for f in outputs:model.Add(active[f]==1)
    if allow_and_change:
        model.Add(sum(chosen[i] for i,e in enumerate(edges) if e[1]=='AND')<=34)
    else:
        for f in required_and:
            model.Add(sum(chosen[i] for i in and_target[f])==1)
        for i,(f,op,a,b) in enumerate(edges):
            if op=='AND' and f not in required_and:model.Add(chosen[i]==0)
    for j,e in enumerate(seed_edges):
        if j not in free:model.Add(chosen[edge_pos[e]]==1)
    if force_change:
        changed=[edge_pos[seed_edges[j]] for j in free]
        model.Add(sum(chosen[i] for i in changed)<=len(changed)-1)
    model.Add(sum(active.values())<=upper_bound)
    model.Minimize(sum(active.values()))
    # Baseline hints do not assert facts; they just provide a good 102 solution.
    active_set={e[0] for e in seed_edges}
    for f,z in active.items():model.AddHint(z,int(f in active_set))
    for i,e in enumerate(edges):model.AddHint(chosen[i],int(e in seed_edges))
    depths={f:0 for f in inputs}
    for f,op,a,b in seed_edges:
        depths[f]=max(depths[a],depths[b])+1
    for f,z in level.items():
        if f in depths:model.AddHint(z,depths[f])
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=rng
    status=solver.Solve(model)
    report={'status':solver.StatusName(status),'conflicts':solver.NumConflicts(),
            'branches':solver.NumBranches(),'bound':solver.BestObjectiveBound(),
            'free':len(free),'cap':upper_bound}
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return None,report
    chosen_defs={edges[i][0]:edges[i] for i in range(len(edges)) if solver.Value(chosen[i])}
    produced={tv:wire for wire,tv in INPUTS.items()};gates=[]
    def make(f):
        if f in produced:return produced[f]
        _,op,a,b=chosen_defs[f]
        wa,wb=make(a),make(b)
        assert wa!=wb
        name='g'+str(len(gates))
        gates.append({'op':op,'a':wa,'b':wb,'out':name})
        produced[f]=name
        return name
    outs=[make(x) for x in outputs]
    candidate=ras.prune({'gates':gates,'outputs':outs})
    assert ras.independent_check(candidate)[0],('incorrect CP-SAT reconstruction',report)
    # Forced AND atoms may be disconnected by the solver and vanish during
    # reachability pruning. That is still a valid constructive circuit, but
    # it must not be misreported as the original 33-AND basis.
    actual_and=sf.describe(candidate)[1]
    report.update(objective=solver.ObjectiveValue(),gates=len(candidate['gates']),
                  retained_AND_atoms=len(actual_and&required_and),
                  verified_AND_atoms=len(actual_and),independent_all_256=True)
    return candidate,report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive-dir',required=True)
    ap.add_argument('--parents',type=int,default=70)
    ap.add_argument('--source',choices=['fs101','shear102'],default='fs101')
    ap.add_argument('--allow-and-change',action='store_true')
    ap.add_argument('--helpers',type=int,default=80)
    ap.add_argument('--include-and',action='store_true')
    ap.add_argument('--seed',type=int,default=1)
    ap.add_argument('--seconds',type=int,default=400)
    ap.add_argument('--per-neighbor',type=float,default=4.0)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--free-widths',type=int,nargs='+',default=[16,26,40,60])
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rng=random.Random(args.seed)
    seed,edges,incoming,nodes,outputs,required_and,old_and,helpers,parents=prepared_graph(
        args.archive_dir,args.parents,args.helpers,args.include_and,args.source)
    assert len(seed['gates']) in (101,102) and len(required_and)==33
    seed_edges,graph,_=seed_info(seed)
    pivot=next((i for i,e in enumerate(seed_edges) if e[1]=='AND' and e[0] not in old_and),None)
    # Positive model-calibration control. Fix the whole seed; must give 102.
    control,rep=solve_neighbor(seed,edges,nodes,outputs,required_and,set(),len(seed['gates']),
                               min(args.per_neighbor,5.0),args.workers,args.seed,
                               allow_and_change=args.allow_and_change)
    assert control is not None and len(control['gates'])==len(seed['gates']),('known-seed control failed',rep)
    best=seed;pool=[seed];known={sf.ident(seed)};witnesses=[]
    results=collections.Counter();results['control_verified']=1
    start=time.monotonic();iteration=0
    while time.monotonic()-start<args.seconds and len(best['gates'])>100:
        iteration+=1
        parent=rng.choice(pool) if rng.random()<0.7 else seed
        pk,pgraph,_=seed_info(parent)
        # The parent edge set may not be in the graph only if a prior
        # result was invalid; solve_neighbor asserts that cannot happen.
        width=rng.choice(args.free_widths)
        kind=rng.choice(('cone','cone','two-windows','two-windows','late','random'))
        region=neighborhood(rng,pk,pgraph,width,kind,pivot if parent is seed else None)
        cap=len(seed['gates'])-1 if iteration%4!=0 else len(seed['gates'])
        changed=cap==len(seed['gates'])
        candidate,r=solve_neighbor(parent,edges,nodes,outputs,required_and,region,cap,
                                   args.per_neighbor,args.workers,args.seed+iteration,
                                   force_change=changed,allow_and_change=args.allow_and_change)
        results['attempts']+=1
        results['status_'+r['status']]+=1
        if candidate is None:continue
        n=len(candidate['gates'])
        results['feasible']+=1
        h=sf.ident(candidate)
        if h not in known:
            known.add(h);results['new_valid_topologies']+=1
            if n<=len(seed['gates']) and len(pool)<32:pool.append(candidate)
            elif n<=len(seed['gates']) and rng.random()<0.4:pool[rng.randrange(len(pool))]=candidate
            if n<len(best['gates']):
                best=candidate
                witness={'iteration':iteration,'gates':n,'kind':kind,'width':width,'solver':r}
                witnesses.append(witness)
                (out/'best.json').write_text(json.dumps(best,indent=2)+'\n')
                print(json.dumps({'event':'new_best',**witness}),flush=True)
                if n<=101:(out/'new-basis-101.json').write_text(json.dumps(best,indent=2)+'\n')
        if iteration%25==0:
            print(json.dumps({'event':'checkpoint','iterations':iteration,'best':len(best['gates']),
                              'known':len(known),'pool':len(pool),'elapsed':round(time.monotonic()-start,1)}),flush=True)
    if not (out/'best.json').exists():(out/'best.json').write_text(json.dumps(best,indent=2)+'\n')
    summary={'baseline_gates':len(seed['gates']),'best_gates':len(best['gates']),
             'source':args.source,'allow_AND_changes':args.allow_and_change,
             'AND_truth_set_delta_from_101':len(sf.describe(best)[1]^old_and),
             'full_256_verified':ras.independent_check(best)[0],
             'model_control':rep,'solver_stats':dict(results),
             'iterations':iteration,'known_topologies':len(known),
             'pool':len(pool),'seconds':round(time.monotonic()-start,2),
             'parents':parents,'semantic_nodes':len(nodes),'semantic_edges':len(edges),
             'helper_extension':helpers,'witnesses':witnesses,
             'scope':'constructive CP-SAT LNS with either fixed or freely joint-reoptimized AND architecture'}
    (out/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    if len(best['gates'])<=100:(out/'candidate.json').write_text(json.dumps(best,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__':main()
