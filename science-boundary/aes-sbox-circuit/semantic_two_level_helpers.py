#!/usr/bin/env python3
"""Constructive multi-parent AES circuit recombination by semantic hypergraph.

Inputs are verified complete AES circuits from both the 101 frontier and
hundreds of 102-gate affine AND refactor seeds, including an explicit AND shear.
New XOR/XNOR helpers may depend on *other* new helpers, and new AND
factorizations may consume them. Optimize the complete topology jointly.
Optionally force the final circuit to retain a genuinely *new* AND function.
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

MASK=(1<<256)-1

def two_level_expand(parent_edges,parent_nodes,first_width,second_width,include_and):
    """Create missing two-level shared linear helper subgraphs before CP-SAT.

    Source classes are exact 256-bit functions. A first helper h1 is an
    XOR/XNOR of two existing signals; a second helper h2 is an XOR/XNOR of
    h1 and an existing signal. Both can be shared across many AND/linear
    consumers. Every candidate relation is an exact Boolean identity.
    """
    old=set(parent_nodes)
    inputs=set(INPUTS.values())
    parents=set(parent_edges)
    all_edges=set(parent_edges)
    important=collections.Counter()
    for f,op,a,b in parent_edges:
        if op=='AND':
            important[a]+=6;important[b]+=6
            important[f]+=3
    for f in old-inputs:important[f]+=1
    def targets(h):
        found=collections.defaultdict(set)
        for t in old-inputs:
            for mode,p in (('XOR',t^h),('XNOR',t^h^MASK)):
                if p in old and p!=h and p!=t:
                    found[t].add((t,mode,*sorted((p,h))))
        if include_and:
            for q in old:
                t=h&q
                if t in old and t not in inputs and t!=q and t!=h:
                    found[t].add((t,'AND',*sorted((h,q))))
        return found
    def rank(h):
        ts=targets(h)
        utility=sum(min(important[t],20) for t in ts)
        return utility,ts
    originals=sorted(old)
    first_by_function=collections.defaultdict(list)
    direct=0
    for i,a in enumerate(originals):
        for b in originals[i+1:]:
            for op,h in (('XOR',a^b),('XNOR',a^b^MASK)):
                if h in inputs or h in (0,MASK,a,b):continue
                edge=(h,op,a,b)
                if h in old:
                    all_edges.add(edge);direct+=1
                elif len(first_by_function[h])<3:
                    first_by_function[h].append(edge)
    scored=[]
    for h,src in first_by_function.items():
        utility,ts=rank(h)
        if len(ts)>=2 and utility>0:
            scored.append((utility,len(ts),h,src,ts))
    scored.sort(reverse=True,key=lambda z:(z[0],z[1]))
    chosen1=scored[:first_width]
    h1s={x[2] for x in chosen1}
    for _u,_len,h,src,ts in chosen1:
        all_edges.update(src)
        for es in ts.values():all_edges.update(es)
    second_by_function=collections.defaultdict(list)
    for _u,_len,h,src,_ts in chosen1:
        for q in originals:
            for op,v in (('XOR',h^q),('XNOR',h^q^MASK)):
                if v in inputs or v in (0,MASK,h,q):continue
                edge=(v,op,*sorted((h,q)))
                if v in old:
                    all_edges.add(edge)
                elif v not in h1s and len(second_by_function[v])<4:
                    second_by_function[v].append(edge)
    scored2=[]
    for h,src in second_by_function.items():
        utility,ts=rank(h)
        if len(ts)>=2 and utility>0:scored2.append((utility,len(ts),h,src,ts))
    scored2.sort(reverse=True,key=lambda z:(z[0],z[1]))
    chosen2=scored2[:second_width]
    for _u,_len,h,src,ts in chosen2:
        all_edges.update(src)
        for es in ts.values():all_edges.update(es)
    ordered=sorted(all_edges,key=lambda z:(z[0],z[1],z[2],z[3]))
    nodes=set(old);incoming=collections.defaultdict(list)
    for i,(f,op,a,b) in enumerate(ordered):
        nodes.update((f,a,b));incoming[f].append(i)
    stats={'original_nodes':len(old),'original_edges':len(parent_edges),
           'direct_one_gate_alternatives':direct,
           'first_candidate_functions':len(scored),'first_selected':len(chosen1),
           'second_candidate_functions':len(scored2),'second_selected':len(chosen2),
           'expanded_nodes':len(nodes),'expanded_edges':len(ordered),
           'first_top_scores':[z[0] for z in chosen1[:10]],
           'second_top_scores':[z[0] for z in chosen2[:10]]}
    return ordered,incoming,nodes,stats



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

def collect(path,limit,baseline,max_source_gates):
    files=sorted(set(glob.glob(os.path.join(path,'**','archive-*.json'),recursive=True)+
                     glob.glob(os.path.join(path,'**','best.json'),recursive=True)+
                     glob.glob(os.path.join(path,'**','candidate.json'),recursive=True)+
                     glob.glob(os.path.join(path,'**','candidate-*.json'),recursive=True)))
    archive=[];seen={ident(baseline)}
    for file in files:
        c=canonical(json.load(open(file)))
        if len(c['gates'])>max_source_gates:continue
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

def solve(edges,incoming,nodes,outputs,baseline,seconds,workers,rng,force_new_and):
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
    old_ands=describe(baseline)[1]
    newly_realizable=[k for k,(f,op,a,b) in enumerate(edges) if op=='AND' and f not in old_ands]
    if force_new_and:
        if not newly_realizable:raise AssertionError('No new AND basis functions in provided parents')
        model.Add(sum(choose[k] for k in newly_realizable)>=1)
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
    report['new_AND_edges_used']=sum(solver.Value(choose[k]) for k in newly_realizable)
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
    ap.add_argument('--force-new-and',action='store_true')
    ap.add_argument('--first-width',type=int,default=50)
    ap.add_argument('--second-width',type=int,default=140)
    ap.add_argument('--include-and',action='store_true')
    ap.add_argument('--max-source-gates',type=int,default=102)
    ap.add_argument('--max-parents',type=int,default=28)
    ap.add_argument('--seconds',type=int,default=240)
    ap.add_argument('--workers',type=int,default=4)
    ap.add_argument('--rng',type=int,default=1)
    ap.add_argument('--out',required=True)
    args=ap.parse_args();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    baseline=ras.load_circuit('fs-101')
    assert len(baseline['gates'])==101 and ras.independent_check(baseline)[0]
    found,archive,parents=collect(args.archive_dir,args.max_parents,baseline,args.max_source_gates)
    if not archive:raise AssertionError('No independently verified parent variants found')
    edges,incoming,nodes=union_graph(parents)
    edges,incoming,nodes,extension=two_level_expand(edges,nodes,args.first_width,args.second_width,args.include_and)
    v=trace(baseline);outputs=[v[w] for w in baseline['outputs']]
    c,report=solve(edges,incoming,nodes,outputs,baseline,args.seconds,args.workers,args.rng,args.force_new_and)
    oldset=describe(baseline)[1];newset=describe(c)[1]
    changed=len(oldset^newset)
    summary={'status':'found' if len(c['gates'])<=100 else 'new_101_basis' if changed else 'no_improvement',
             'force_new_and':args.force_new_and,'AND_truth_set_symmetric_difference':changed,
             'two_level_extension':extension,
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
    if changed and len(c['gates'])<=101:(out/'novel-101.json').write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
