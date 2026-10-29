#!/usr/bin/env python3
"""Novel equal-score GPX2 offspring: compare against 58 known face-neutral moves.

The 5,757,195 3-opt tour, crossed with Nagata, produced a legal 5,757,191
offspring differing by 36 edges from the incumbent. Test whether its 36 added
edges all lie in the known old 58 neutral-move union (and whether this
introduces a genuinely new 0-score neutral basin).

If genuinely new, attempt exact connected-tour improvement from the union
of all 58 moves, this GPX child, and optionally its 5757195 parent.
Never call equality a record.
"""
import argparse,importlib.util,json,os,sys,time
from pathlib import Path
from ortools.sat.python import cp_model
sys.path.insert(0,str(Path(__file__).resolve().parent))
from contracted_circuit_search import build_active,reconstruct
N=100000
def E(u,v):return (min(u,v),max(u,v))
def edges(t):return {E(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def main():
    p=argparse.ArgumentParser()
    for k in ('baseline','offspring','neutrals','report','candidate'):p.add_argument('--'+k,required=True)
    p.add_argument('--include-3opt',action='store_true')
    p.add_argument('--three-opt',default=None)
    p.add_argument('--seconds',type=float,default=100)
    p.add_argument('--workers',type=int,default=4)
    a=p.parse_args();t0=time.monotonic()
    spec=importlib.util.spec_from_file_location('official',Path(os.environ['FEWSHOTS_ROOT'])/
        'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    base1=json.loads(Path(a.baseline).read_text())['tour']
    child1=json.loads(Path(a.offspring).read_text())['tour']
    assert len(base1)==len(child1)==N
    assert v.tour_length(base1)==v.tour_length(child1)==5757191
    base=edges([x-1 for x in base1]);child=edges([x-1 for x in child1])
    novel=child-base;deleted=base-child
    assert len(novel)==len(deleted)==36
    source=json.loads(Path(a.neutrals).read_text())
    old_add=set();all_new=set()
    for item in source['moves']:
        for u,w in item['added']:old_add.add(E(u-1,w-1))
        for u,w in item['removed']:
            assert E(u-1,w-1) in base
    additional=novel-old_add
    e3=set()
    if a.include_3opt:
        assert a.three_opt
        t3=json.loads(Path(a.three_opt).read_text())['tour']
        assert len(t3)==N and v.tour_length(t3)==5757195
        e3=edges([x-1 for x in t3])-base
    union=old_add|novel|e3
    report={'source_neutral_moves':len(source['moves']),
      'source_known_new_edges':len(old_add),'gpx_added_edges':len(novel),
      'gpx_added_edges_already_known':len(novel&old_add),
      'gpx_novel_equal-score_edges':len(additional),
      'new_gpx_neutral_not_in_known_58_move_edge_pool':bool(additional),
      'include_5757195_parent':a.include_3opt,
      'added_edges_from_3opt_parent':len(e3),
      'total_edges_beyond_baseline':len(union),
      'target_score_max':5757190}
    if not additional and not e3:
        report['status']='SKIPPED_PREVIOUSLY_PROVEN_UNION_SUBSET'
    else:
        src=[x-1 for x in base1]
        active,ordered,macros=build_active(src,base,union)
        index={u:i for i,u in enumerate(ordered)}
        model=cp_model.CpModel();arcs=[];x={};cost=0;obj=[]
        xs,ys=v.coordinates()
        def d(i,j):return v.euc_2d(xs[i]-xs[j],ys[i]-ys[j])
        for u,w in sorted(active):
            present=model.NewBoolVar(f'e{u}_{w}')
            f=model.NewBoolVar(f'f{u}_{w}');r=model.NewBoolVar(f'r{u}_{w}')
            model.Add(f+r==present)
            arcs.extend(((index[u],index[w],f),(index[w],index[u],r)))
            x[(u,w)]=present
            obj.append(d(u,w)*present)
            if (u,w) in base:cost+=d(u,w)
        for u,w in macros:
            f=model.NewBoolVar(f'fM{u}_{w}');r=model.NewBoolVar(f'rM{u}_{w}')
            model.Add(f+r==1)
            arcs.extend(((index[u],index[w],f),(index[w],index[u],r)))
        model.AddCircuit(arcs)
        delta=sum(obj)-cost
        model.Add(delta<=-1)
        model.Minimize(delta)
        solver=cp_model.CpSolver()
        solver.parameters.num_search_workers=a.workers
        solver.parameters.max_time_in_seconds=a.seconds
        solver.parameters.random_seed=20261029
        print(json.dumps({'stage':'model','active':len(active),'contracted_vertices':len(ordered),
                          'macros':len(macros),'novel_edges':len(additional),
                          'include_3opt':a.include_3opt}),flush=True)
        status=solver.Solve(model)
        report.update({'status':solver.StatusName(status),
                       'active_edges':len(active),'contracted_vertices':len(ordered),
                       'objective_bound':solver.BestObjectiveBound()})
        if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
            chosen={e for e,z in x.items() if solver.Value(z)}
            result=reconstruct(src,base,active,chosen)
            score=v.tour_length(result)
            assert score<=5757190
            b=json.dumps({'tour':result},separators=(',',':')).encode()
            verdict=v.verify_bytes(b,v.load_config())
            assert verdict['valid'] and int(verdict['score'])==score
            Path(a.candidate).parent.mkdir(parents=True,exist_ok=True)
            Path(a.candidate).write_bytes(b)
            report.update({'strict_record_breakthrough':True,'score':score,'official_hash':verdict['canonical_hash']})
    report['seconds']=round(time.monotonic()-t0,3)
    Path(a.report).parent.mkdir(parents=True,exist_ok=True)
    Path(a.report).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result',**report}),flush=True)
if __name__=='__main__':main()
