#!/usr/bin/env python3
"""Exact tour merging of independently verified equal-score Mona Lisa tours.

Unlike the 51-switch hypercube, the full 58 neutral parents overlap in
seven sites, and arbitrary edge recombination need not factor into switches.
Keep the union of parent edges; contract unchanged incumbent paths;
solve minimum Hamiltonian circuit in this complete *union graph* with CP-SAT.
This is an exact, connectivity-preserving instance of Cook-Seymour tour
merging / GPX-style recombination, not a purported new technique.
"""
import argparse,importlib.util,json,os,sys,time
from pathlib import Path
from ortools.sat.python import cp_model
sys.path.insert(0,str(Path(__file__).resolve().parent))
from contracted_circuit_search import build_active, reconstruct

def ek(a,b):return (a,b) if a<b else (b,a)

def main():
    p=argparse.ArgumentParser()
    for k in ('baseline','neutral-moves','report','candidate'):p.add_argument('--'+k,required=True)
    p.add_argument('--family',choices=['independent51','all58'],default='all58')
    p.add_argument('--motifs',required=True)
    p.add_argument('--price-report',default=None)
    p.add_argument('--augmentation-count',type=int,default=64)
    p.add_argument('--selector',choices=['gain','repair','random'],default='gain')
    p.add_argument('--target-improvement',type=int,default=1)
    p.add_argument('--seconds',type=int,default=180)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=131)
    a=p.parse_args();t0=time.monotonic()
    source=json.loads(Path(a.baseline).read_text())['tour']
    assert len(source)==100000 and len(set(source))==100000
    t=[i-1 for i in source];n=len(t)
    base={ek(t[i],t[(i+1)%n]) for i in range(n)}
    data=json.loads(Path(a.neutral_moves).read_text())
    assert len(data['moves'])==58
    if a.family=='independent51':
        chosen=[data['moves'][i] for i in data['selected_indices']]
        assert len(chosen)==51
    else:chosen=data['moves']
    extra=set()
    changed_sites=set()
    for m in chosen:
        removed={ek(x-1,y-1) for x,y in m['removed']}
        added={ek(x-1,y-1) for x,y in m['added']}
        assert removed <= base and not(added&base)
        assert len(removed)==len(added)>0
        extra.update(added)
        changed_sites.update(v for e in removed|added for v in e)
    motifs=json.loads(Path(a.motifs).read_text())['positive_repair_motifs']
    assert motifs and a.augmentation_count>0
    if a.selector=='repair':
        assert a.price_report
        pricing=json.loads(Path(a.price_report).read_text())
        order=pricing['source_ranking']
        # Metric bridge score ranks edge choices; it is NOT a LP dual certificate.
    elif a.selector=='random':
        import random
        order=list(range(len(motifs)))
        random.Random(a.seed).shuffle(order)
    else:order=sorted(range(len(motifs)),key=lambda i:-motifs[i]['gain'])
    selected_indices=order[:a.augmentation_count]
    before=len(extra)
    for i in selected_indices:
        for u,v in motifs[i]['added']:
            e=ek(u-1,v-1)
            if e not in base:extra.add(e)
    added_chords=len(extra)-before
    active,ordered,macros=build_active(t,base,extra)
    assert len(ordered)>4 and len(extra)>0
    spec=importlib.util.spec_from_file_location('v',Path(os.environ['FEWSHOTS_ROOT'])/
           'problems/p010-mona-lisa-tsp/verify/verify.py')
    verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
    xs,ys=verify.coordinates()
    def d(u,v):return verify.euc_2d(xs[u]-xs[v],ys[u]-ys[v])
    assert verify.tour_length(source)==5757191
    for m in chosen:
        delta=sum(d(u-1,v-1) for u,v in m['added'])-sum(d(u-1,v-1) for u,v in m['removed'])
        assert delta==0
    idx={v:i for i,v in enumerate(ordered)}
    model=cp_model.CpModel()
    arcs=[]
    variables={}
    weighted=[]
    previous=0
    for a0,b0 in sorted(active):
        selected=model.NewBoolVar(f'e{a0}_{b0}')
        forward=model.NewBoolVar(f'f{a0}_{b0}')
        reverse=model.NewBoolVar(f'r{a0}_{b0}')
        model.Add(forward+reverse==selected)
        arcs.extend(((idx[a0],idx[b0],forward),(idx[b0],idx[a0],reverse)))
        variables[(a0,b0)]=selected
        weighted.append(d(a0,b0)*selected)
        if (a0,b0) in base:previous+=d(a0,b0)
    for a0,b0 in macros:
        forward=model.NewBoolVar(f'MF{a0}_{b0}')
        reverse=model.NewBoolVar(f'MR{a0}_{b0}')
        model.Add(forward+reverse==1)
        arcs.extend(((idx[a0],idx[b0],forward),(idx[b0],idx[a0],reverse)))
    model.AddCircuit(arcs)
    difference=sum(weighted)-previous
    model.Add(difference<=-a.target_improvement)
    model.Minimize(difference)
    solver=cp_model.CpSolver()
    solver.parameters.random_seed=a.seed
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=a.workers
    report={'family':a.family,'parents':len(chosen),
            'base_score':5757191,'target_gain':a.target_improvement,
            'selector':a.selector,'augmentation_count':len(selected_indices),
            'augmented_chords':added_chords,
            'chosen_motif_indices':selected_indices,
            'nonbase_union_edges':len(extra),'parent_changed_cities':len(changed_sites),
            'active_edges':len(active),'contracted_vertices':len(ordered),
            'fixed_paths':len(macros),'seconds_budget':a.seconds}
    print(json.dumps({'stage':'model',**report}),flush=True)
    status=solver.Solve(model)
    report.update({'status':solver.StatusName(status),
                   'seconds':round(time.monotonic()-t0,3),
                   'conflicts':solver.NumConflicts(),
                   'branches':solver.NumBranches(),
                   'objective_bound':solver.BestObjectiveBound()})
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        selected={e for e,x in variables.items() if solver.Value(x)}
        candidate=reconstruct(t,base,active,selected)
        score=verify.tour_length(candidate)
        assert score==5757191+sum(d(*e) for e in selected)-previous
        assert score<=5757191-a.target_improvement
        blob=json.dumps({'tour':candidate},separators=(',',':')).encode()
        verdict=verify.verify_bytes(blob,verify.load_config())
        assert verdict['valid'] and int(verdict['score'])==score
        output=Path(a.candidate);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(blob)
        report.update({'score':score,'gain':5757191-score,
                       'canonical_hash':verdict['canonical_hash']})
    dest=Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result',**report}),flush=True)

if __name__=='__main__':main()
