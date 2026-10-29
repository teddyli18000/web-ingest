#!/usr/bin/env python3
"""Matched-budget experiment: LP fractionality x tour disagreement as candidate selector.

Compare five deterministic selectors against identical Nagata baseline, exact
EUC_2D scorer and AddCircuit Hamiltonian constraint:
history / lp-fraction / intersection / spatial-joint / random.

The original 2012 Concorde LP x is a REAL LP solution, not a reconstructed
approximation. Fractionality identifies a relaxation's uncertainty, not the
likelihood that an edge belongs to the optimum. Every result is conditional
on its edge pool. A separate degree-2 model quantifies the connectivity gap.
"""
import argparse,importlib.util,json,math,os,random,sys,time
from collections import Counter
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model

sys.path.insert(0,str(Path(__file__).resolve().parent))
import historical_lp_disagreement as hist
from contracted_circuit_search import build_active,reconstruct

N=100000
def unpack(e):return int(e//N),int(e%N)

def main():
    p=argparse.ArgumentParser()
    for name in ('baseline','tours','lp','report','certificate'):p.add_argument('--'+name,required=True)
    p.add_argument('--selector',choices=['history','fraction','intersection','joint','random'],required=True)
    p.add_argument('--budget',type=int,default=256)
    p.add_argument('--seconds',type=int,default=80)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=20261029)
    a=p.parse_args();started=time.monotonic()
    tbase=np.asarray(json.loads(Path(a.baseline).read_text())['tour'],dtype=np.int32)-1
    assert len(tbase)==N and len(np.unique(tbase))==N
    base={hist.encode(np.asarray([tbase[i]]),np.asarray([tbase[(i+1)%N]])).item() for i in range(N)}
    verify_path=Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py'
    spec=importlib.util.spec_from_file_location('verify',verify_path)
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    assert v.tour_length((tbase+1).tolist())==5757191
    a0,b0=hist.tour_neigh(tbase)
    tours=json.loads(Path(a.tours).read_text())
    contested=np.zeros(N,dtype=np.int8)
    votes=Counter()
    for name,path in tours.items():
        t=hist.parse_tour(path)
        assert len(t)==N and len(np.unique(t))==N
        ta,tb=hist.tour_neigh(t)
        contested+=((a0!=ta)|(b0!=tb)).astype(np.int8)
        votes.update(hist.tour_edges(t).tolist())
    lp=hist.lp_read(a.lp)
    fract={int(e):float(x) for e,x,isfrac in
           zip(lp['edge_ids'],lp['x'],lp['frac']) if isfrac and int(e) not in base}
    historical={int(e):count for e,count in votes.items() if int(e) not in base}
    pool=set(fract)|set(historical)
    assert len(pool)>a.budget
    def score(e):
        u,w=unpack(e)
        f=fract.get(e)
        fv=(f*(1-f) if f is not None else 0)
        d=contested[u]+contested[w]
        d2=int(contested[u]>=2)+int(contested[w]>=2)
        x=historical.get(e,0)
        if a.selector=='history':return (x,d2,d,fv)
        if a.selector=='fraction':return (fv,d2,x,d)
        if a.selector=='intersection':return (int(x>0 and f is not None),x*fv,d2,x,d)
        if a.selector=='joint':return (d2,int(f is not None),int(x>0),d*fv,d,x)
        raise ValueError(a.selector)
    if a.selector=='random':
        ordered=sorted(pool);random.Random(a.seed).shuffle(ordered)
    else:ordered=sorted(pool,key=lambda e:(score(e),-e),reverse=True)
    chosen=ordered[:a.budget]
    novel={unpack(e) for e in chosen}
    assert len(novel)==a.budget and all(0<=x<y<N for x,y in novel)
    base_edges={unpack(e) for e in base}
    active,ordered_vertices,macro=build_active(tbase.tolist(),base_edges,novel)
    nodes={city:i for i,city in enumerate(ordered_vertices)}
    def cost(u,w):return v.euc_2d(xs[u]-xs[w],ys[u]-ys[w])
    m=cp_model.CpModel()
    binary={};arcs=[];degree={node:[] for node in nodes}
    weighted=[];constant=0
    for u,w in sorted(active):
        xx=m.NewBoolVar(f'x{u}_{w}')
        binary[(u,w)]=xx
        f=m.NewBoolVar(f'F{u}_{w}');r=m.NewBoolVar(f'R{u}_{w}')
        m.Add(f+r==xx)
        arcs.extend(((nodes[u],nodes[w],f),(nodes[w],nodes[u],r)))
        degree[u].append(xx);degree[w].append(xx)
        weighted.append(cost(u,w)*xx)
        if (u,w) in base_edges:constant+=cost(u,w)
    for u,w in macro:
        f=m.NewBoolVar(f'MF{u}_{w}');r=m.NewBoolVar(f'MR{u}_{w}')
        m.Add(f+r==1)
        arcs.extend(((nodes[u],nodes[w],f),(nodes[w],nodes[u],r)))
        degree[u].append(1);degree[w].append(1)
    m.AddCircuit(arcs)
    delta=sum(weighted)-constant
    m.Add(delta<=-1)
    m.Minimize(delta)
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=a.seconds
    solver.parameters.num_search_workers=a.workers
    solver.parameters.random_seed=a.seed
    report={'selector':a.selector,'budget':a.budget,
       'comparison_parent_count':len(tours),'pool_historical_chords':len(historical),
       'pool_lp_fractional_chords':len(fract),'pool_all_chords':len(pool),
       'selected_historical_chords':sum(e in historical for e in chosen),
       'selected_lp_fractional_chords':sum(e in fract for e in chosen),
       'selected_chords_both':sum(e in fract and e in historical for e in chosen),
       'selected_touch_disagreement_2plus':sum(any(contested[x]>=2 for x in unpack(e)) for e in chosen),
       'selected_touch_both_fraction_and_disagreement':sum(any(contested[x]>=2 and lp['node_frac'][x] for x in unpack(e)) for e in chosen),
       'selected_chord_ids':list(map(int,chosen)),
       'contracted_vertices':len(ordered_vertices),'active_edges':len(active),
       'macro_paths':len(macro),'seconds_limit':a.seconds}
    print(json.dumps({'stage':'constructed',**{k:v for k,v in report.items() if k!='selected_chord_ids'}}),flush=True)
    result=solver.Solve(m)
    report.update({'status':solver.StatusName(result),
       'objective_bound':solver.BestObjectiveBound(),
       'branches':solver.NumBranches(),'conflicts':solver.NumConflicts(),
       'wall_seconds':round(time.monotonic()-started,3)})
    if result in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        selected={e for e,x in binary.items() if solver.Value(x)}
        tour=reconstruct(tbase.tolist(),base_edges,active,selected)
        score=v.tour_length(tour)
        assert score<5757191
        verdict=v.verify_bytes(json.dumps({'tour':tour},separators=(',',':')).encode(),v.load_config())
        assert verdict['valid'] and int(verdict['score'])==score
        Path(a.certificate).write_text(json.dumps({'tour':tour},separators=(',',':')))
        report.update({'verified_score':score,'breakthrough':True,
                       'canonical_hash':verdict['canonical_hash']})
    else:report['breakthrough']=False
    # Solve a separate integer 2-factor relaxation of exactly the same pool.
    model2=cp_model.CpModel()
    x2={e:model2.NewBoolVar(f'e{e[0]}_{e[1]}') for e in sorted(active)}
    for u in ordered_vertices:
        incident=[x2[e] for e in x2 if u in e]
        constant_inc=sum(1 for aa,bb in macro if u in (aa,bb))
        model2.Add(sum(incident)+constant_inc==2)
    delta2=sum(cost(*e)*b for e,b in x2.items())-constant
    model2.Minimize(delta2)
    relax=cp_model.CpSolver()
    relax.parameters.max_time_in_seconds=min(a.seconds,45)
    relax.parameters.num_search_workers=a.workers
    relax.parameters.random_seed=a.seed
    stat=relax.Solve(model2)
    report['twofactor_status']=relax.StatusName(stat)
    if stat in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        report['twofactor_best_length']=5757191+round(relax.ObjectiveValue())
        report['twofactor_lower_bound']=5757191+math.ceil(relax.BestObjectiveBound())
    dest=Path(a.report);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result',**{k:v for k,v in report.items() if k!='selected_chord_ids'}}),flush=True)

if __name__=='__main__':main()
