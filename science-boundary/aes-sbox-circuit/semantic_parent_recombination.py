#!/usr/bin/env python3
"""Constructive multi-parent AES circuit recombination by semantic hypergraph.

Inputs are verified complete AES circuits from a neutral/nonlinear-basis search.
Collapse equal 256-bit wire functions into one semantic node, pool *different*
AND/XOR/XNOR decompositions of each function across parents, and jointly select
one acyclic implementation of all eight AES outputs with minimum total gates.

This is a synthesis/selection procedure, not a lower-bound engine. Any CP-SAT
witness is reconstructed as an ordinary Few Shots certificate and independently
checked on every AES byte. The search can combine gates from multiple parents
at once instead of choosing a replacement for one local cone at a time.
"""
from __future__ import annotations
import argparse, collections, glob, hashlib, json, os, pathlib, time
from ortools.sat.python import cp_model
import released_and_skeleton as ras
import seed_family_census as census

OPS=('AND','XOR','XNOR')
INPUTS=census.input_tables(False)

def canonical(c):
    return ras.prune(c)

def trace(c):
    v=dict(INPUTS)
    for g in c['gates']:
        v[g['out']]=census.op_eval(g['op'],v[g['a']],v[g['b']])
    return v

def ident(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def describe(c):
    v=trace(c)
    ands={v[g['out']] for g in c['gates'] if g['op']=='AND'}
    edges=set()
    for g in c['gates']:
        a,b=sorted((v[g['a']],v[g['b']]))
        f=v[g['out']]
        if f in INPUTS.values() or f==a or f==b:continue
        edges.add((f,g['op'],a,b))
    return v,ands,edges

def collect(path,limit,baseline):
    files=sorted(set(glob.glob(os.path.join(path,'**','archive-*.json'),recursive=True)+
                     glob.glob(os.path.join(path,'**','best.json'),recursive=True)+
                     glob.glob(os.path.join(path,'**','candidate.json'),recursive=True)))
    archive=[];seen={ident(baseline)}
    for file in files:
        c=canonical(json.load(open(file)))
        if len(c['gates'])>len(baseline['gates']):continue
        h=ident(c)
        if h in seen:continue
        if not ras.independent_check(c)[0]:raise AssertionError(('invalid parent',file))
        seen.add(h)
        v,ands,edges=describe(c)
        archive.append({'path':file,'c':c,'v':v,'ands':ands,'edges':edges})
    rootv,rootands,rootedges=describe(baseline)
    chosen=[{'path':'built-in-fs-101','c':baseline,'v':rootv,'ands':rootands,'edges':rootedges}]
    unused=list(archive)
    all_edges=set(rootedges);all_ands=set(rootands)
    while unused and len(chosen)<limit:
        def score(p):
            nedge=len(p['edges']-all_edges)
            nands=len(p['ands']-all_ands)
            distance=min(len(p['ands']^q['ands']) for q in chosen)
            return (nedge + 8*nands + 3*distance,nedge,nands)
        j=max(range(len(unused)),key=lambda i:score(unused[i]))
        p=unused.pop(j)
        chosen.append(p);all_edges.update(p['edges']);all_ands.update(p['ands'])
    return files,archive,chosen

def union_graph(parents):
    raw=set()
    for p in parents:raw.update(p['edges'])
    edge_list=sorted(raw,key=lambda z:(z[0],z[1],z[2],z[3]))
    incoming=collections.defaultdict(list)
    allnodes=set(INPUTS.values())
    for k,(f,op,a,b) in enumerate(edge_list):
        incoming[f].append(k);allnodes.update((f,a,b))
    return edge_list,incoming,allnodes

def solve(edges,incoming,nodes,outputs,baseline,seconds,workers,rng):
    model=cp_model.CpModel()
    inp=set(INPUTS.values()); noninputs=sorted(nodes-inp)
    active={v:model.NewBoolVar('n'+str(i)) for i,v in enumerate(noninputs)}
    levels={v:model.NewIntVar(1,101,'d'+str(i)) for i,v in enumerate(noninputs)}
    choose=[model.NewBoolVar('e'+str(i)) for i in range(len(edges))]
    for v in noninputs:
        if v in incoming:
            model.Add(sum(choose[i] for i in incoming[v])==active[v])
        else:model.Add(active[v]==0)
    for oi,f in enumerate(outputs):
        if f not in active:raise AssertionError(('AES output not in graph',oi))
        model.Add(active[f]==1)
    for e,(f,op,a,b) in enumerate(edges):
        z=choose[e]
        for t in (a,b):
            if t not in inp:
                model.AddImplication(z,active[t])
                model.Add(levels[f]>levels[t]).OnlyEnforceIf(z)
            else:
                model.Add(levels[f]>=1).OnlyEnforceIf(z)
    model.Add(sum(active.values())<=len(baseline['gates']))
    model.Minimize(sum(active.values()))
    # Guide the solver with a validated, complete 101-gate witness.
    v=trace(baseline)
    baseedges=set()
    basedepth={x:0 for x in INPUTS.values()}
    for g in baseline['gates']:
        f=v[g['out']];a,b=sorted((v[g['a']],v[g['b']]))
        baseedges.add((f,g['op'],a,b))
        basedepth[f]=1+max(basedepth[a],basedepth[b])
    for f,x in active.items():
        model.AddHint(x,int(f in basedepth))
        if f in basedepth:model.AddHint(levels[f],basedepth[f])
    for k,key in enumerate(edges):model.AddHint(choose[k],int(key in baseedges))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=workers
    solver.parameters.random_seed=rng
    solver.parameters.log_search_progress=False
    tic=time.monotonic();status=solver.Solve(model);elapsed=time.monotonic()-tic
    report={'solver_status':solver.StatusName(status),'seconds':round(elapsed,2),
            'best_bound':solver.BestObjectiveBound(),'conflicts':solver.NumConflicts(),
            'branches':solver.NumBranches()}
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):return baseline,report
    picked={f:edges[k] for k,(f,op,a,b) in enumerate(edges) if solver.Value(choose[k])}
    report['objective']=int(round(solver.ObjectiveValue()))
    produced={v:k for k,v in INPUTS.items()}
    gate_list=[]
    def emit(f):
        if f in produced:return produced[f]
        if f not in picked:raise AssertionError(('selected node has no gate',f))
        _,op,a,b=picked[f]
        wa=emit(a);wb=emit(b)
        name='g'+str(len(gate_list))
        if wa==wb:raise AssertionError(('repeated operands',op,wa))
        gate_list.append({'op':op,'a':wa,'b':wb,'out':name})
        produced[f]=name
        return name
    names=[emit(t) for t in outputs]
    c=ras.prune({'gates':gate_list,'outputs':names})
    if not ras.independent_check(c)[0]:raise AssertionError('combined circuit failed all-256 check')
    report['verified_all_256']=True
    report['verified_gates']=len(c['gates'])
    report['gates_by_op']={op:sum(g['op']==op for g in c['gates']) for op in OPS}
    return c,report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--archive-dir',required=True)
    ap.add_argument('--max-parents',type=int,default=28)
    ap.add_argument('--seconds',type=int,default=240)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--rng',type=int,default=1)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    baseline=ras.load_circuit('fs-101')
    assert len(baseline['gates'])==101 and ras.independent_check(baseline)[0]
    found,archive,parents=collect(args.archive_dir,args.max_parents,baseline)
    if not archive:raise AssertionError('No independently verified parent variants found')
    edges,incoming,nodes=union_graph(parents)
    v=trace(baseline);outputs=[v[w] for w in baseline['outputs']]
    c,report=solve(edges,incoming,nodes,outputs,baseline,args.seconds,args.workers,args.rng)
    summary={'status':'found' if len(c['gates'])<=100 else 'no_improvement',
             'archive_files':len(found),'unique_parents':len(archive)+1,
             'selected_parents':len(parents),
             'selected_sources':[p['path'] for p in parents],
             'unique_semantic_nodes':len(nodes),'candidate_gate_hyperedges':len(edges),
             'baseline_gates':len(baseline['gates']),'best_gates':len(c['gates']),
             'verified_all_256':ras.independent_check(c)[0],
             'solver':report,
             'scope':'multi-parent global DAG recombination over exact 256-bit gate-function identities'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    (out/'best.json').write_text(json.dumps(c,indent=2)+'\n')
    if len(c['gates'])<=100:(out/'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
