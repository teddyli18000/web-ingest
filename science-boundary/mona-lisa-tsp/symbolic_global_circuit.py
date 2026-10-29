#!/usr/bin/env python3
"""Exact simultaneous 51-neutral-switch + improving 2-edge repair SAT search.

Every possible positive-gain local 2-edge pairing using the public sparse
graph is exported by symbolic_hypercube_2opt.py. Instead of enumerating
2**51 neutral states, choose one such repair AND all 51 neutral switches
together in one contracted Hamiltonian-circuit CP-SAT model.

The exact model includes all variable tour edges, optional restored baseline
edges, and mandatory contracted fixed paths. AddCircuit enforces a single
100,000-city cycle, not merely degree two. All integer gains are rechecked
against the authoritative p010 distance function.
"""
import argparse,importlib.util,json,os,time
from collections import defaultdict
from pathlib import Path
from ortools.sat.python import cp_model

def edge(a,b):return (a,b) if a<b else (b,a)
def tedges(t):return {edge(t[i],t[(i+1)%len(t)]) for i in range(len(t))}

def main():
 p=argparse.ArgumentParser()
 for name in ('baseline','moves','motifs','report','certificate'):p.add_argument('--'+name,required=True)
 p.add_argument('--minimum-gain',type=int,default=1)
 p.add_argument('--seconds',type=int,default=150)
 p.add_argument('--workers',type=int,default=4)
 p.add_argument('--mode',choices=['improve','baseline','two-factor'],default='improve')
 p.add_argument('--repairs',type=int,default=1)
 p.add_argument('--max-motifs',type=int,default=0)
 p.add_argument('--bridge-motifs',default=None)
 p.add_argument('--max-bridges',type=int,default=0)
 args=p.parse_args();start=time.monotonic()
 tour=json.loads(Path(args.baseline).read_text())['tour']
 n=len(tour);assert n==100000 and len(set(tour))==n
 base=tedges(tour);assert len(base)==n
 source=json.loads(Path(args.moves).read_text())
 assert len(source['selected_indices'])==51
 mods=[source['moves'][i] for i in source['selected_indices']]
 oldsets=[{tuple(q) for q in move['removed']} for move in mods]
 newsets=[{tuple(q) for q in move['added']} for move in mods]
 motifs=json.loads(Path(args.motifs).read_text())['positive_repair_motifs']
 motifs=[x for x in motifs if x['gain']>=args.minimum_gain]
 motifs.sort(key=lambda x:-x['gain'])
 if args.max_motifs:motifs=motifs[:args.max_motifs]
 positive_count=len(motifs)
 if args.bridge_motifs:
    bridges=json.loads(Path(args.bridge_motifs).read_text())['bridge_motifs']
    if args.max_bridges:bridges=bridges[:args.max_bridges]
    motifs+=bridges
 assert len(motifs)>=args.repairs>=1
 spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
    'problems/p010-mona-lisa-tsp/verify/verify.py')
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 xs,ys=v.coordinates()
 def cost(q):
    a,b=q
    return v.euc_2d(xs[a-1]-xs[b-1],ys[a-1]-ys[b-1])
 assert v.tour_length(tour)==5757191
 for m in motifs:
    assert len(m['old'])==len(m['added'])==2
    assert sum(cost(q) for q in m['old'])-sum(cost(q) for q in m['added'])==m['gain']
 variable_edges=set()
 old_owner={}
 new_owner={}
 for i,(old,new) in enumerate(zip(oldsets,newsets)):
    for ed in old:
        assert ed in base and ed not in old_owner
        old_owner[ed]=i
    for ed in new:
        assert ed not in base and ed not in new_owner
        new_owner[ed]=i
    variable_edges.update(old);variable_edges.update(new)
 impact=defaultdict(list)
 for j,m in enumerate(motifs):
    old={tuple(q) for q in m['old']}
    new={tuple(q) for q in m['added']}
    assert len(old)==len(new)==2 and not(old&new)
    for e in old:impact[e].append((j,-1))
    for e in new:impact[e].append((j,1))
    variable_edges.update(old);variable_edges.update(new)
 assert all(1<=a<b<=n for a,b in variable_edges)
 flexible_vertices={u for e in variable_edges for u in e}
 ordered=[u for u in tour if u in flexible_vertices]
 positions={u:i for i,u in enumerate(tour)}
 index={u:i for i,u in enumerate(ordered)}
 assert len(index)==len(ordered)
 macros=[]
 for i,u in enumerate(ordered):
    nxt=ordered[(i+1)%len(ordered)]
    if positions[nxt]==(positions[u]+1)%n and edge(u,nxt) in variable_edges:continue
    macros.append((u,nxt))
 model=cp_model.CpModel()
 switches=[model.NewBoolVar(f'switch_{i}') for i in range(len(mods))]
 choices=[model.NewBoolVar(f'repair_{j}') for j in range(len(motifs))]
 if args.mode=='baseline':model.Add(sum(choices)==0)
 else:model.Add(sum(choices)==args.repairs)
 if args.bridge_motifs and args.mode!='baseline':
    model.Add(sum(choices[:positive_count])==args.repairs-1)
    model.Add(sum(choices[positive_count:])==1)
    model.Add(sum(m['gain']*choices[j] for j,m in enumerate(motifs))>=1)
 arcs=[]
 degree=defaultdict(list)
 selectable={}
 for a,b in sorted(variable_edges):
    ed=(a,b)
    selected=model.NewBoolVar(f'sel_{a}_{b}')
    selectable[ed]=selected
    degree[a].append(selected);degree[b].append(selected)
    if ed in old_owner:
        expr=1-switches[old_owner[ed]]
    elif ed in new_owner:
        expr=switches[new_owner[ed]]
    else:
        expr=int(ed in base)
    plus=[choices[j] for j,sign in impact[ed] if sign>0]
    minus=[choices[j] for j,sign in impact[ed] if sign<0]
    model.Add(selected==expr+sum(plus)-sum(minus))
    f=model.NewBoolVar(f'F_{a}_{b}')
    r=model.NewBoolVar(f'R_{a}_{b}')
    model.Add(f+r==selected)
    arcs.extend(((index[a],index[b],f),(index[b],index[a],r)))
 for a,b in macros:
    f=model.NewBoolVar(f'MF_{a}_{b}')
    r=model.NewBoolVar(f'MR_{a}_{b}')
    model.Add(f+r==1)
    degree[a].append(1);degree[b].append(1)
    arcs.extend(((index[a],index[b],f),(index[b],index[a],r)))
 if args.mode=='two-factor':
    for city in ordered:model.Add(sum(degree[city])==2)
 else:model.AddCircuit(arcs)
 model.Maximize(sum(m['gain']*choices[j] for j,m in enumerate(motifs)))
 report={'baseline':5757191,'switches':51,'total_motifs':len(motifs),
       'minimum_gain':args.minimum_gain,'mode':args.mode,'repairs':args.repairs,
       'positive_motifs':positive_count,'bridge_motifs':len(motifs)-positive_count,
       'variable_edges':len(variable_edges),
       'contracted_vertices':len(ordered),'mandatory_macro_paths':len(macros),
       'maximum_gain_in_candidates':max(m['gain'] for m in motifs),
       'time_limit_seconds':args.seconds}
 print(json.dumps({'stage':'model',**report}),flush=True)
 solver=cp_model.CpSolver()
 solver.parameters.max_time_in_seconds=args.seconds
 solver.parameters.num_search_workers=args.workers
 solver.parameters.random_seed=17
 status=solver.Solve(model)
 report.update({'status':solver.StatusName(status),
     'elapsed_seconds':round(time.monotonic()-start,2),
     'branches':solver.NumBranches(),'conflicts':solver.NumConflicts()})
 if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
    js=[i for i,y in enumerate(choices) if solver.Value(y)]
    assert len(js)==(0 if args.mode=='baseline' else args.repairs)
    mask=sum(1<<i for i,x in enumerate(switches) if solver.Value(x))
    selected=set(base)
    for i in range(len(switches)):
        if (mask>>i)&1:selected.difference_update(oldsets[i])
    for i in range(len(switches)):
        if (mask>>i)&1:selected.update(newsets[i])
    motif_list=[motifs[j] for j in js]
    changes=defaultdict(int)
    for motif in motif_list:
        for q in motif['old']:changes[tuple(q)]-=1
        for q in motif['added']:changes[tuple(q)]+=1
    for ed,difference in changes.items():
        current=int(ed in selected)
        next_state=current+difference
        assert next_state in (0,1),(ed,current,difference)
        if next_state:selected.add(ed)
        else:selected.discard(ed)
    assert len(selected)==n
    adj=[[] for _ in range(n+1)]
    for a,b in selected:adj[a].append(b);adj[b].append(a)
    assert all(len(adj[u])==2 for u in range(1,n+1))
    if args.mode=='two-factor':
        seen=bytearray(n+1)
        sizes=[]
        for start_vertex in range(1,n+1):
            if seen[start_vertex]:continue
            u=start_vertex;prev=0;size=0
            while not seen[u]:
                seen[u]=1;size+=1
                aa,bb=adj[u];nxt=aa if aa!=prev else bb
                prev,u=u,nxt
            assert u==start_vertex
            sizes.append(size)
        total_gain=sum(m['gain'] for m in motif_list)
        expected=5757191-total_gain
        actual=sum(cost(e) for e in selected)
        assert actual==expected
        report.update({'degree_two_factor_total':actual,'components':len(sizes),
                       'component_sizes':sorted(sizes),'winning_gain':total_gain,
                       'winning_motifs':js,'neutral_mask':str(mask)})
        dest=Path(args.report);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'stage':'result',**report}),flush=True)
        return
    visited=bytearray(n+1);route=[];u=1;prev=0
    while not visited[u]:
        visited[u]=1;route.append(u)
        aa,bb=adj[u];nxt=aa if aa!=prev else bb
        prev,u=u,nxt
    assert u==1 and len(route)==n
    cert={'tour':route}
    payload=json.dumps(cert,separators=(',',':')).encode()
    verdict=v.verify_bytes(payload,v.load_config())
    total_gain=sum(m['gain'] for m in motif_list)
    expected=5757191-total_gain
    assert verdict['valid'] and int(verdict['score'])==expected
    output=Path(args.certificate)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(payload)
    report.update({'verified_score':int(verdict['score']),
       'canonical_hash':verdict['canonical_hash'],
       'winning_motifs':js,'winning_motif_gain':total_gain,
       'neutral_mask':str(mask)})
 else:
    report['best_objective_bound']=solver.BestObjectiveBound()
 dest=Path(args.report);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'stage':'result',**report}),flush=True)

if __name__=='__main__':main()
