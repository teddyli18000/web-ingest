#!/usr/bin/env python3
"""Exact TSP refine for the 237-city minority subtour in an unpublished 100k 2-factor.

Representation pivot: before attempting complex 100k cross-tour repair, solve
the small island's OWN complete Euclidean TSP. If it can be shortened by
>=6 units, a formerly unprofitable +6 3-opt bridge could become a record.

The CP-SAT solver optimizes integer degree-two on kNN or all-pairs edges,
adding VALID x(delta(S))>=2 SEC cuts for every disconnected subtour; every
connected cycle is independently scored with exact original p010 distances.
Outputs a new disconnected 100k factor ONLY when the island was improved.
"""
import argparse,importlib.util,json,os,time
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model
N=100000
def E(u,v):return (min(u,v),max(u,v))
def main():
 p=argparse.ArgumentParser()
 for z in ('baseline','factor','report','factor-out'):p.add_argument('--'+z,required=True)
 p.add_argument('--k',type=int,default=16)
 p.add_argument('--seconds',type=float,default=180)
 p.add_argument('--workers',type=int,default=4)
 a=p.parse_args();started=time.monotonic()
 vpath=Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py'
 spec=importlib.util.spec_from_file_location('official',vpath)
 v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 xs,ys=v.coordinates()
 def d(u,w):return v.euc_2d(xs[u]-xs[w],ys[u]-ys[w])
 baseline=json.loads(Path(a.baseline).read_text())['tour']
 assert len(baseline)==N and v.tour_length(baseline)==5757191
 base={E(baseline[i]-1,baseline[(i+1)%N]-1) for i in range(N)}
 factor_info=json.loads(Path(a.factor).read_text())
 assert factor_info['cycles']==2
 rem={tuple(e) for e in factor_info['removed_baseline_edges']}
 add={tuple(e) for e in factor_info['added_nonbaseline_edges']}
 current=(base-rem)|add
 assert len(current)==N
 assert 5757191-sum(d(*e) for e in rem)+sum(d(*e) for e in add)==factor_info['factor_score']
 original_labels=np.asarray(factor_info['component_labels'],dtype=np.int32)
 counts=np.bincount(original_labels,minlength=2)
 minority=int(counts.argmin());vertices=sorted(np.flatnonzero(original_labels==minority).tolist())
 m=len(vertices);assert m<=500 and m>=4
 idx={u:i for i,u in enumerate(vertices)}
 current_small={e for e in current if original_labels[e[0]]==minority}
 assert len(current_small)==m and all(original_labels[e[1]]==minority for e in current_small)
 original_cost=sum(d(*e) for e in current_small)
 candidates=set(current_small)
 for i,u in enumerate(vertices):
    order=sorted((w for w in vertices if w!=u),
       key=lambda w:(d(u,w),w))
    for w in order[:a.k if a.k>0 else m-1]:candidates.add(E(u,w))
 assert current_small<=candidates
 model=cp_model.CpModel();xsvars={};incident=[[] for _ in vertices]
 for u,w in sorted(candidates):
    q=model.NewBoolVar(f'e{u}_{w}');xsvars[(u,w)]=q
    incident[idx[u]].append(q);incident[idx[w]].append(q)
    model.AddHint(q,1 if (u,w) in current_small else 0)
 for inc in incident:model.Add(sum(inc)==2)
 model.Minimize(sum(d(*e)*q for e,q in xsvars.items()))
 solver=cp_model.CpSolver()
 solver.parameters.num_search_workers=a.workers
 solver.parameters.random_seed=20261029
 knowncuts=set();events=[];good=None;last='NOT_SOLVED';proof=False
 while time.monotonic()-started<a.seconds-.1 and len(events)<100:
    remain=a.seconds-(time.monotonic()-started)
    solver.parameters.max_time_in_seconds=max(.05,min(12,remain))
    status=solver.Solve(model);last=solver.StatusName(status)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
       if status==cp_model.INFEASIBLE:raise AssertionError('old small cycle in graph yet infeasible')
       continue
    chosen={e for e,q in xsvars.items() if solver.Value(q)}
    assert len(chosen)==m
    ds=list(range(m))
    def root(i):
        while ds[i]!=i:
            ds[i]=ds[ds[i]];i=ds[i]
        return i
    for u,w in chosen:ds[root(idx[u])]=root(idx[w])
    comps={}
    for j,u in enumerate(vertices):comps.setdefault(root(j),set()).add(u)
    score=sum(d(*e) for e in chosen)
    assert int(round(solver.ObjectiveValue()))==score
    ev={'iteration':len(events)+1,'cycle_count':len(comps),'small_TSP_cost':score,
        'delta_vs_original':score-original_cost,'solver_status':last,
        'objective_bound':solver.BestObjectiveBound()}
    events.append(ev)
    print(json.dumps({'stage':'small_SEC',**ev}),flush=True)
    if len(comps)==1:
        if good is None or score<good[0]:good=(score,chosen)
        if status==cp_model.OPTIMAL:proof=True;break
        continue
    extra=0
    for comp in comps.values():
        if len(comp)>=m:continue
        mask=frozenset(comp)
        if mask in knowncuts:continue
        knowncuts.add(mask)
        out=[q for (u,w),q in xsvars.items() if (u in comp)!=(w in comp)]
        assert out,'original cycle implies cross-cut edges'
        model.Add(sum(out)>=2);extra+=1
    if not extra:break
 report={'source_factor_length':factor_info['factor_score'],
   'source_factor_cycles':2,'minority_size':m,'minority_original_cost':original_cost,
   'candidate_mode':('complete' if a.k<=0 else f'{a.k}NN+factor'),
   'candidate_edges':len(candidates),'n_certified':0,
   'solver_status':last,'proved_optimal_in_small_candidate_graph':proof,
   'iterations':len(events),'cuts':len(knowncuts),
   'events':events,'elapsed_seconds':round(time.monotonic()-started,4)}
 if good:
    score,chosen=good
    improvement=original_cost-score
    report.update({'best_small_cycle_cost':score,'small_cycle_improvement':improvement,
       'improved_factor_score':factor_info['factor_score']-improvement})
    if improvement>0:
        repaired=(current-current_small)|chosen
        assert len(repaired)==N
        added=repaired-base;removed=base-repaired
        newscore=5757191+sum(d(*e) for e in added)-sum(d(*e) for e in removed)
        assert newscore==factor_info['factor_score']-improvement
        snapshot={'source':'exact_connected_237city_subtour_refinement',
          'factor_score':newscore,'cycles':2,'cycle_sizes':counts.tolist(),
          'component_labels':original_labels.tolist(),
          'added_nonbaseline_edges':[list(e) for e in sorted(added)],
          'removed_baseline_edges':[list(e) for e in sorted(removed)],
          'small_cycle_improvement':improvement,
          'small_cycle_verified_connected':True,
          'small_cycle_optimality_proved_in_candidate_graph':proof}
        o=Path(a.factor_out);o.parent.mkdir(parents=True,exist_ok=True)
        o.write_text(json.dumps(snapshot,separators=(',',':'))+'\n')
 print(json.dumps({'stage':'small_final',**{k:v for k,v in report.items() if k!='events'}}),flush=True)
 out=Path(a.report);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
