#!/usr/bin/env python3
"""Multi-tour competing-wiring regions × persistent Concorde fractional LP edges.

A rigorous conditional exact test on selected variable-edge components.
Keep original Nagata tour edges everywhere. In ranked regions, admit ALL
historical parent edges plus a fixed budget of nonhistorical LP fractional
edges. Rank by persistence across THREE public LP primal snapshots and by
fractional ambiguity x*(1-x); matched random controls sample from the same
eligible region pool. Contract every frozen baseline path; enforce a single
Hamiltonian circuit with AddCircuit. Strict improvement verified by Few Shots.
"""
import argparse,importlib.util,json,math,os,random,sys,time
from pathlib import Path
from collections import Counter
from ortools.sat.python import cp_model

sys.path.insert(0,str(Path(__file__).resolve().parent))
import historical_lp_disagreement as h
from contracted_circuit_search import build_active,reconstruct

N=100000
def unpack(e):return int(e//N),int(e%N)
def main():
    p=argparse.ArgumentParser()
    for name in ('baseline','tours','lps','components','report','candidate'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--selector',choices=['persistent','ambiguous','random'],required=True)
    p.add_argument('--attachment',choices=['interior','cross','all'],default='interior')
    p.add_argument('--nregions',type=int,default=3)
    p.add_argument('--lp-budget',type=int,default=256)
    p.add_argument('--seconds',type=float,default=110)
    p.add_argument('--workers',type=int,default=4)
    args=p.parse_args();start=time.monotonic()
    spec=importlib.util.spec_from_file_location('verify',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    base_t=[x-1 for x in json.loads(Path(args.baseline).read_text())['tour']]
    assert len(base_t)==N and v.tour_length([x+1 for x in base_t])==5757191
    base_edges={h.encode([base_t[i]],[base_t[(i+1)%N]]).item() for i in range(N)}
    comps=json.loads(Path(args.components).read_text())['components']
    regions=sorted(comps,key=lambda c:(-c['priority_score'],-c['joint_nodes']))[:args.nregions]
    vertices={int(q) for c in regions for q in c['members_0based']}
    assert vertices
    comp_map=[-1]*N
    for c in comps:
        for u in c['members_0based']:comp_map[int(u)]=c['id']
    top_ids={c['id'] for c in regions}
    paths=json.loads(Path(args.tours).read_text())
    alt=Counter()
    for path in paths.values():
        t=h.parse_tour(path)
        assert len(t)==N and len(set(t.tolist()))==N
        for e in h.tour_edges(t):
            u,w=unpack(e)
            if u in vertices and w in vertices and int(e) not in base_edges:
                alt[int(e)]+=1
    lpdocs={key:h.lp_read(path) for key,path in json.loads(Path(args.lps).read_text()).items()}
    primary=lpdocs['2012-04-18']
    values={}
    for lp in lpdocs.values():
        for e,x,frac in zip(lp['edge_ids'],lp['x'],lp['frac']):
            if not frac:continue
            en=int(e)
            u,w=unpack(en)
            if args.attachment=='interior':
                allowed=(u in vertices and w in vertices)
            elif args.attachment=='cross':
                allowed=(comp_map[u]!=comp_map[w] and
                         (comp_map[u] in top_ids or comp_map[w] in top_ids))
            else:
                allowed=(comp_map[u] in top_ids or comp_map[w] in top_ids)
            if not allowed or en in base_edges or en in alt:continue
            values.setdefault(en,[]).append(float(x))
    pool=list(values)
    assert len(pool)>=args.lp_budget,(len(pool),args.lp_budget)
    if args.selector=='random':
        pool.sort();random.Random(90053).shuffle(pool)
    elif args.selector=='persistent':
        pool.sort(key=lambda e:(len(values[e]),min(x*(1-x) for x in values[e]),-e),reverse=True)
    else:pool.sort(key=lambda e:(next((x*(1-x) for x in values[e]),0),len(values[e]),-e),reverse=True)
    lp_selected=pool[:args.lp_budget]
    pool_edges=set(alt)|set(lp_selected)
    edges={unpack(e) for e in pool_edges}
    active,ordered,macros=build_active(base_t,{unpack(e) for e in base_edges},edges)
    idx={u:i for i,u in enumerate(ordered)}
    def cost(u,w):return v.euc_2d(xs[u]-xs[w],ys[u]-ys[w])
    model=cp_model.CpModel();arcs=[];vars={};weighted=[];basecost=0
    for u,w in sorted(active):
        x=model.NewBoolVar(f'e{u}_{w}')
        f=model.NewBoolVar(f'F{u}_{w}');r=model.NewBoolVar(f'R{u}_{w}')
        model.Add(f+r==x)
        arcs.extend(((idx[u],idx[w],f),(idx[w],idx[u],r)))
        vars[(u,w)]=x
        weighted.append(cost(u,w)*x)
        if h.encode([u],[w]).item() in base_edges:basecost+=cost(u,w)
    for u,w in macros:
        f=model.NewBoolVar(f'MF{u}_{w}');r=model.NewBoolVar(f'MR{u}_{w}')
        model.Add(f+r==1)
        arcs.extend(((idx[u],idx[w],f),(idx[w],idx[u],r)))
    model.AddCircuit(arcs)
    delta=sum(weighted)-basecost
    model.Add(delta<=-1);model.Minimize(delta)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=args.seconds
    solver.parameters.num_search_workers=args.workers
    solver.parameters.random_seed=20261029
    report={'selector':args.selector,'attachment':args.attachment,'regions':args.nregions,
      'region_ids':[c['id'] for c in regions],
      'region_cities':len(vertices),'historical_edges_added':len(alt),
      'LP_fractional_candidate_pool':len(pool),
      'LP_chords_added':len(lp_selected),
      'persistent_in_all_three_LPs':sum(len(values[e])==3 for e in lp_selected),
      'local_graph_edges':len(pool_edges),'active_edges':len(active),
      'contracted_vertices':len(ordered),'mandatory_macro_paths':len(macros),
      'LP_chords':[int(e) for e in lp_selected]}
    print(json.dumps({'stage':'model',**{k:x for k,x in report.items() if k!='LP_chords'}}),flush=True)
    status=solver.Solve(model)
    report.update({'status':solver.StatusName(status),'objective_bound':solver.BestObjectiveBound(),
       'branches':solver.NumBranches(),'conflicts':solver.NumConflicts(),
       'wall_seconds':round(time.monotonic()-start,3)})
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        selected={e for e,x in vars.items() if solver.Value(x)}
        t=reconstruct(base_t,{unpack(e) for e in base_edges},active,selected)
        assert v.tour_length(t)<=5757190
        blob=json.dumps({'tour':t},separators=(',',':')).encode()
        verification=v.verify_bytes(blob,v.load_config())
        assert verification['valid'] and int(verification['score'])<=5757190
        out=Path(args.candidate);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(blob)
        report.update({'improvement':5757191-int(verification['score']),
                       'new_score':int(verification['score']),'verified_hash':verification['canonical_hash']})
    dest=Path(args.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result',**{k:x for k,x in report.items() if k!='LP_chords'}}),flush=True)

if __name__=='__main__':main()
