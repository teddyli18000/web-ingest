#!/usr/bin/env python3
"""Leakage-controlled Mona Lisa counterfactual: 5,757,199 as incumbent.

No Nagata tour is read or imported. Old (>=5,757,199) legal tours and
independent published LP x vectors are the ONLY edge-knowledge inputs.
All selectors share the full old-parent edge union and exactly K new
non-parent chords; the sole objective is a connected tour with lower cost.
A: disagreement and fractional LP support.
B: historical consensus versus LP x~1 conflict.
C: degree-2 subtour defects propose *new* Euclidean bridge pairs.
"""
import argparse, hashlib, importlib.util, json, os, random, sys, time
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from ortools.sat.python import cp_model
sys.path.insert(0,str(Path(__file__).resolve().parent))
from contracted_circuit_search import build_active,reconstruct

N=100000
def edge(a,b):return (min(int(a),int(b)),max(int(a),int(b)))
def key(e):return e[0]*N+e[1]
def pair(k):return (k//N,k%N)
def read_tour(p):
    lines=Path(p).read_text().splitlines()
    i=next(i for i,l in enumerate(lines) if l.strip().upper()=='TOUR_SECTION')
    x=[]
    for l in lines[i+1:]:
        for v in l.split():
            if v in ('-1','EOF'):
                assert len(x)==N and len(set(x))==N,(p,len(x))
                return x
            x.append(int(v)-1)
    raise ValueError('malformed tour')
def tour_edges(t):return {edge(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def read_lp(p):
    out={}
    with open(p) as f:
        n,m=map(int,f.readline().split());assert n==N
        for l in f:
            a,b,x=l.split();a=int(a);b=int(b);x=float(x)
            assert a!=b and 0<=a<N and 0<=b<N and -1e-5<=x<=1+1e-5
            if x>1e-5:out[edge(a,b)]=x
    assert len(out)>N
    return out
def two_factor(t,base,novel,d,seconds,workers):
    active,ordered,macros=build_active(t,base,novel)
    inc={u:[] for u in ordered}
    m=cp_model.CpModel();vars={};obj=[];fixed=0
    for a,b in active:
        q=m.NewBoolVar(f'x{a}_{b}');vars[(a,b)]=q
        inc[a].append(q);inc[b].append(q)
        obj.append(d(a,b)*q)
        if (a,b) in base:fixed+=d(a,b)
    for a,b in macros:
        inc[a].append(1);inc[b].append(1)
    for u in ordered:m.Add(sum(inc[u])==2)
    m.Minimize(sum(obj)-fixed)
    s=cp_model.CpSolver()
    s.parameters.max_time_in_seconds=seconds
    s.parameters.num_search_workers=workers
    s.parameters.random_seed=889
    code=s.Solve(m)
    if code not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return None,{'status':s.StatusName(code)}
    selected={e for e,q in vars.items() if s.Value(q)}
    whole=(base-active)|selected
    assert len(whole)==N
    adj=[[] for _ in range(N)]
    for a,b in whole:adj[a].append(b);adj[b].append(a)
    assert all(len(x)==2 for x in adj)
    seen=bytearray(N);component=[-1]*N;groups=[]
    for start in range(N):
        if seen[start]:continue
        v=start;prev=-1;nodes=[];id=len(groups)
        while not seen[v]:
            seen[v]=1;component[v]=id;nodes.append(v)
            a,b=adj[v];nxt=a if a!=prev else b
            prev,v=v,nxt
        assert v==start
        groups.append(nodes)
    return (adj,component,groups),{'status':s.StatusName(code),
        'components':len(groups),'smallest_component':min(len(z) for z in groups),
        'two_factor_delta':int(round(s.ObjectiveValue()))}
def generate_repair(t,base,parents,d,xy,tree,k,workers,rng,pos):
    # Degree-2 oracle uses only pre-existing parent-union edges.
    oracle,meta=two_factor(t,base,parents-base,d,20,workers)
    proposed={}
    if oracle is not None and meta['components']>1:
        adj,component,groups=oracle
        for g in sorted(groups,key=len):
            samples=g if len(g)<=80 else rng.sample(g,80)
            for u in samples:
                near=tree.query(xy[u],k=96)[1]
                for v in np.atleast_1d(near):
                    v=int(v)
                    if v==u or component[u]==component[v]:continue
                    for pu in adj[u]:
                        for pv in adj[v]:
                            if len({u,v,pu,pv})!=4:continue
                            a,b=edge(u,v),edge(pu,pv)
                            excess=d(*a)+d(*b)-d(u,pu)-d(v,pv)
                            for e in (a,b):
                                if e not in parents and e not in base:
                                    proposed[e]=min(proposed.get(e,float('inf')),excess)
    # Fallback ensures every selector has EXACTLY k genuinely novel chords.
    # It is not guided by hidden optimum or any Nagata-aligned input.
    if len(proposed)<k:
        sites=list(set(t[::97])|set(t[13::101]))
        rng.shuffle(sites)
        for u in sites:
            near=tree.query(xy[u],k=40)[1]
            for v in np.atleast_1d(near):
                v=int(v)
                if v==u:continue
                e=edge(u,v)
                if e in parents or e in base:continue
                penalty=d(*e)-min(d(u,t[(pos[u]-1)%N]),d(u,t[(pos[u]+1)%N]))
                proposed[e]=min(proposed.get(e,float('inf')),10000+penalty)
            if len(proposed)>k*15:break
    assert len(proposed)>=k,(len(proposed),k)
    return [e for e,_ in sorted(proposed.items(),key=lambda x:(x[1],key(x[0])))[:k]],meta

def main():
    p=argparse.ArgumentParser()
    for name in ('reference','parents','lps','out'):p.add_argument('--'+name,required=True)
    p.add_argument('--strategy',choices=['uncertainty','conflict','repair'],required=True)
    p.add_argument('--budget',type=int,default=128)
    p.add_argument('--seconds',type=float,default=100)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--seed',type=int,default=1701)
    a=p.parse_args();started=time.monotonic()
    rng=random.Random(a.seed)
    dest=Path(a.out);dest.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('p010_verify',
         Path(os.environ['FEWSHOTS_ROOT'])/'problems/p010-mona-lisa-tsp/verify/verify.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    xs,ys=v.coordinates()
    xy=np.column_stack((xs,ys))
    def d(i,j):return v.euc_2d(xs[i]-xs[j],ys[i]-ys[j])
    t=read_tour(a.reference)
    base=tour_edges(t)
    assert v.tour_length([x+1 for x in t])==5757199
    pos={u:i for i,u in enumerate(t)}
    hist=Counter();disagreement=np.zeros(N,dtype=np.int8)
    prev=np.empty(N,dtype=np.int32);nxt=np.empty(N,dtype=np.int32)
    prev[t]=np.roll(t,1);nxt[t]=np.roll(t,-1)
    reference_neighbors=np.sort(np.column_stack((prev,nxt)),axis=1)
    source_paths=json.loads(Path(a.parents).read_text())
    assert len(source_paths)>=4
    for name,path in source_paths.items():
        route=read_tour(path)
        score=v.tour_length([x+1 for x in route])
        assert score>=5757199,(name,score) # NO Nagata in the old parents
        es=tour_edges(route);hist.update(es)
        u=np.empty(N,dtype=np.int32);w=np.empty(N,dtype=np.int32)
        u[route]=np.roll(route,1);w[route]=np.roll(route,-1)
        neighbors=np.sort(np.column_stack((u,w)),axis=1)
        disagreement+=np.any(neighbors!=reference_neighbors,axis=1).astype(np.int8)
    parents=set(hist)|base
    all_lp={};snapshot_names=[]
    for name,path in json.loads(Path(a.lps).read_text()).items():
        snapshot_names.append(name)
        for e,x in read_lp(path).items():
            all_lp.setdefault(e,[]).append(x)
    # Select only edges not already provided by any historical parent.
    extra={}
    for e,xx in all_lp.items():
        if e in parents:continue
        u,w=e
        frac=[x*(1-x) for x in xx if 1e-5<x<1-1e-5]
        persistence=len(frac)
        uncertain=int(disagreement[u]>=2)+int(disagreement[w]>=2)
        inconsistent=int(disagreement[u]==0)+int(disagreement[w]==0)
        if a.strategy=='uncertainty':
            if persistence==0:continue
            score=(uncertain,disagreement[u]+disagreement[w],
                   persistence,sum(frac),-key(e))
        elif a.strategy=='conflict':
            # x~1 rejects the historical consensus; also accept strong
            # fractional challenges as a deterministic fallback.
            score=(int(max(xx)>=.99999),inconsistent,
                   int(disagreement[u]+disagreement[w]==0),
                   len(xx),max(xx),-key(e))
        else:continue
        extra[e]=score
    initial_meta={}
    if a.strategy=='repair':
        new,initial_meta=generate_repair(t,base,parents,d,xy,cKDTree(xy),
                    a.budget,a.workers,rng,pos)
    else:
        assert len(extra)>=a.budget,(a.strategy,len(extra))
        new=[e for e,_ in sorted(extra.items(),key=lambda z:z[1],reverse=True)[:a.budget]]
    assert len(set(new))==a.budget and all(e not in parents for e in new)
    active,ordered,macros=build_active(t,base,(parents-base)|set(new))
    idx={z:i for i,z in enumerate(ordered)}
    m=cp_model.CpModel();arcs=[];var={};weighted=[];oldcost=0
    for u,w in sorted(active):
        q=m.NewBoolVar(f'x{u}_{w}')
        f=m.NewBoolVar(f'f{u}_{w}');r=m.NewBoolVar(f'r{u}_{w}')
        m.Add(f+r==q)
        arcs.extend(((idx[u],idx[w],f),(idx[w],idx[u],r)))
        var[(u,w)]=q
        weighted.append(d(u,w)*q)
        if (u,w) in base:oldcost+=d(u,w)
    for u,w in macros:
        f=m.NewBoolVar(f'MF{u}_{w}');r=m.NewBoolVar(f'MR{u}_{w}')
        m.Add(f+r==1);arcs.extend(((idx[u],idx[w],f),(idx[w],idx[u],r)))
    m.AddCircuit(arcs)
    delta=sum(weighted)-oldcost
    m.Add(delta<=-1);m.Minimize(delta)
    solver=cp_model.CpSolver()
    remaining=max(1,a.seconds-(time.monotonic()-started))
    solver.parameters.max_time_in_seconds=remaining
    solver.parameters.num_search_workers=a.workers
    solver.parameters.random_seed=a.seed
    report={'protocol':'hidden-nagata-199','strategy':a.strategy,
      'score_reference':5757199,'parents':len(source_paths)+1,
      'LP_snapshots':snapshot_names,'parent_union':len(parents),
      'new_chord_budget':a.budget,'selected_chords':[list(e) for e in new],
      'selector_oracle':initial_meta,'active_edges':len(active),
      'contracted_vertices':len(ordered),'time_limit':a.seconds,
      'pre_solve_seconds':round(time.monotonic()-started,3),
      'reference_sha256':hashlib.sha256(Path(a.reference).read_bytes()).hexdigest(),
      'parent_sha256':{name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in source_paths.items()},
      'LP_sha256':{name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in json.loads(Path(a.lps).read_text()).items()}}
    print(json.dumps({'stage':'model',**{k:v for k,v in report.items() if k not in ('selected_chords','parent_sha256','LP_sha256')}}),flush=True)
    status=solver.Solve(m)
    report.update({'status':solver.StatusName(status),
      'branches':solver.NumBranches(),'conflicts':solver.NumConflicts(),
      'best_bound':solver.BestObjectiveBound(),
      'wall_seconds':round(time.monotonic()-started,3)})
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        chosen={e for e,q in var.items() if solver.Value(q)}
        route=reconstruct(t,base,active,chosen)
        score=v.tour_length(route)
        assert score<5757199
        blob=json.dumps({'tour':route},separators=(',',':')).encode()
        verdict=v.verify_bytes(blob,v.load_config())
        assert verdict['valid'] and verdict['score']==score
        (dest/'certificate.json').write_bytes(blob)
        report.update({'score':score,'improvement':5757199-score,'valid':True,
                       'official_hash':verdict['canonical_hash']})
    (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'stage':'result',**{k:v for k,v in report.items() if k not in ('selected_chords','parent_sha256','LP_sha256')}}),flush=True)
if __name__=='__main__':main()
