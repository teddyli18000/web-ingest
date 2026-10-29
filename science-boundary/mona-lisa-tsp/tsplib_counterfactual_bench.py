#!/usr/bin/env python3
"""Hold-out protocol for TSPLIB EUC_2D certified-optimum instances.

Modes are physically separated by workflow jobs:
 PREP produces public reference/parents/LP and private held-out strong tour;
 SEARCH receives ONLY public data, never private or optimum;
 EVAL compares valid search candidates to official TSPLIB optimum and withheld.
All algorithms and random seeds are fixed before eval.
"""
import argparse,hashlib,json,math,random,time
from collections import Counter
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix
from ortools.sat.python import cp_model
def E(u,v):return (u,v) if u<v else (v,u)
def read_tsp(path):
    lines=Path(path).read_text().splitlines()
    dim=int(next(line.split(':')[-1] for line in lines if line.strip().startswith('DIMENSION')))
    wt=next(line.split(':')[-1].strip() for line in lines if line.strip().startswith('EDGE_WEIGHT_TYPE'))
    assert wt=='EUC_2D'
    q=next(i for i,l in enumerate(lines) if l.strip()=='NODE_COORD_SECTION')
    coords=[]
    for l in lines[q+1:]:
        if l.strip()=='EOF':break
        words=l.split()
        if len(words)>=3:coords.append((int(words[0]),float(words[1]),float(words[2])))
    assert len(coords)==dim and sorted(x[0] for x in coords)==list(range(1,dim+1))
    xy=np.asarray([[x,y] for _,x,y in sorted(coords)])
    # TSPLIB nint() is floor(distance+0.5), NOT Python banker rounding.
    dist=np.floor(np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=-1)+0.5).astype(np.int32)
    assert np.diag(dist).sum()==0
    return xy,dist
def score(t,D):return int(sum(D[t[i],t[(i+1)%len(t)]] for i in range(len(t))))
def edge_set(t):return {E(t[i],t[(i+1)%len(t)]) for i in range(len(t))}
def nearest(D,start):
    n=len(D);t=[start];unused=set(range(n))-{start}
    while unused:
        nxt=min(unused,key=lambda v:(int(D[t[-1],v]),v))
        t.append(nxt);unused.remove(nxt)
    return t
def twoopt(t,D,limit=80):
    n=len(t);t=list(t)
    for sweep in range(limit):
        move=False
        for i in range(n-2):
            a,b=t[i],t[i+1]
            for j in range(i+2,n if i else n-1):
                c,d=t[j],t[(j+1)%n]
                if D[a,c]+D[b,d]<D[a,b]+D[c,d]:
                    t[i+1:j+1]=reversed(t[i+1:j+1])
                    move=True;break
            if move:break
        if not move:break
    return t
def shake(t,rng):
    n=len(t);k=sorted(rng.sample(range(2,n-2),3))
    a,b,c=k
    # Four-block relocation, valid Hamiltonian tour.
    return t[:a]+t[b:c]+t[a:b]+t[c:]
def degree_lp(D):
    n=len(D)
    pairs=[(i,j) for i in range(n) for j in range(i+1,n)]
    costs=np.array([D[i,j] for i,j in pairs],dtype=float)
    row=[];col=[];dat=[]
    for j,(u,v) in enumerate(pairs):
        row.extend((u,v));col.extend((j,j));dat.extend((1.,1.))
    A=csr_matrix((dat,(row,col)),shape=(n,len(pairs)))
    equal=np.full(n,2.,dtype=float)
    cuts=[];states=[]
    for round_ in range(8):
        if cuts:
            rows=[];cols=[];data=[]
            for i,S in enumerate(cuts):
                for j,(u,v) in enumerate(pairs):
                    if (u in S)!=(v in S):
                        rows.append(i);cols.append(j);data.append(-1.)
            upper=csr_matrix((data,(rows,cols)),shape=(len(cuts),len(pairs)))
            r=linprog(costs,A_eq=A,b_eq=equal,A_ub=upper,b_ub=np.full(len(cuts),-2.),
                    bounds=(0,1),method='highs',options={'time_limit':15})
        else:r=linprog(costs,A_eq=A,b_eq=equal,bounds=(0,1),method='highs',options={'time_limit':15})
        assert r.success,(round_,r.message)
        x=r.x
        # A positive-support connected component identifies a violated SEC.
        p=list(range(n))
        def root(a):
            while p[a]!=a:
                p[a]=p[p[a]];a=p[a]
            return a
        for (u,v),val in zip(pairs,x):
            if val>1e-7:p[root(u)]=root(v)
        groups={}
        for u in range(n):groups.setdefault(root(u),set()).add(u)
        states.append({'round':round_,'support_components':len(groups),
                       'objective':float(r.fun),'fractional_edges':int(((x>1e-5)&(x<1-1e-5)).sum())})
        if len(groups)==1:break
        before=len(cuts)
        for S in groups.values():
            if 1<len(S)<n-1 and S not in cuts:cuts.append(S)
        if len(cuts)==before:break
    return [{'u':int(u),'v':int(v),'x':round(float(val),9)}
            for (u,v),val in zip(pairs,x) if val>1e-6],states
def prepare(name,instance,out):
    xy,D=read_tsp(instance)
    n=len(D);rng=random.Random(20261029+n)
    raw=[]
    for start in range(min(n,25)):
        t=twoopt(nearest(D,start),D)
        raw.append(t)
        for rep in range(2):
            raw.append(twoopt(shake(t,rng),D,limit=rng.randint(6,32)))
    best=min(raw,key=lambda t:score(t,D))
    for i in range(85):
        src=best if i%3 else raw[rng.randrange(len(raw))]
        raw.append(twoopt(shake(src,rng),D,limit=rng.randint(2,14)))
    unique={}
    for t in raw:unique[frozenset(edge_set(t))]=(score(t,D),t)
    arr=sorted(unique.values(),key=lambda x:(x[0],tuple(x[1])))
    assert len(arr)>5
    bestscore,hidden=arr[0]
    refindex=next(i for i in range(2,len(arr)-2) if arr[i][0]>bestscore)
    refscore,ref=arr[refindex]
    parents=[t for val,t in arr[refindex+1:] if val>=refscore][:10]
    assert len(parents)>=4
    lp,rounds=degree_lp(D)
    pub={'instance':name,'n':n,'coordinates':xy.tolist(),'distance':D.tolist(),
         'reference':ref,'reference_score':refscore,'parents':parents,
         'parent_scores':[score(t,D) for t in parents],
         'lp_positive':lp,'lp_rounds':rounds,
         'metric':'TSPLIB EUC_2D, floor(hypot+0.5)'}
    private={'instance':name,'hidden_tour':hidden,'hidden_score':bestscore,
             'reference_score':refscore}
    Path(out).mkdir(parents=True,exist_ok=True)
    (Path(out)/'public.json').write_text(json.dumps(pub,separators=(',',':'))+'\n')
    (Path(out)/'private.json').write_text(json.dumps(private,separators=(',',':'))+'\n')
    print(json.dumps({'stage':'prepare','instance':name,'n':n,'reference':refscore,
           'hidden_better_known':bestscore,'parents':len(parents),
           'lp_rounds':rounds,'LP_positive_edges':len(lp)}),flush=True)
def select_repair(ref,D,parents,k,seed):
    n=len(D);parent_union=set().union(*(edge_set(t) for t in parents),edge_set(ref))
    # Cheapest degree-2 solution built only from permitted parent edges.
    model=cp_model.CpModel()
    q={e:model.NewBoolVar(f'{e[0]}_{e[1]}') for e in parent_union}
    for u in range(n):model.Add(sum(x for e,x in q.items() if u in e)==2)
    model.Minimize(sum(int(D[u,v])*x for (u,v),x in q.items()))
    s=cp_model.CpSolver();s.parameters.num_search_workers=1;s.parameters.max_time_in_seconds=2
    status=s.Solve(model)
    candidates={}
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        eds={e for e,x in q.items() if s.Value(x)}
        adj=[[] for _ in range(n)]
        for u,v in eds:adj[u].append(v);adj[v].append(u)
        seen=set();groups=[];cid={}
        for start in range(n):
            if start in seen:continue
            stack=[start];group=[];i=len(groups)
            while stack:
                u=stack.pop()
                if u in seen:continue
                seen.add(u);cid[u]=i;group.append(u)
                stack.extend(adj[u])
            groups.append(group)
        for g in groups:
            for u in g:
                for v in range(n):
                    if cid[v]==cid[u]:continue
                    for a in adj[u]:
                        for b in adj[v]:
                            if len({a,b,u,v})<4:continue
                            repair=int(D[u,v]+D[a,b]-D[u,a]-D[v,b])
                            for e in (E(u,v),E(a,b)):
                                if e not in parent_union:candidates[e]=min(candidates.get(e,999999),repair)
        meta={'oracle_status':s.StatusName(status),'oracle_components':len(groups),
              'oracle_score':int(round(s.ObjectiveValue()))}
    else:meta={'oracle_status':s.StatusName(status)}
    # Geometrical fallback never accesses any held-out tour.
    rng=random.Random(seed)
    for u in range(n):
        for v in range(u+1,n):
            e=E(u,v)
            if e in parent_union or e in candidates:continue
            candidates[e]=100000+int(D[u,v])
    ranked=sorted(candidates,key=lambda e:(candidates[e],e))
    return ranked[:k],meta
def search(inp,strategy,budget,out,seconds=12):
    t0=time.monotonic();pub=json.loads(Path(inp).read_text())
    D=np.asarray(pub['distance'],dtype=np.int32)
    n=len(D);ref=pub['reference'];parents=pub['parents']
    base=edge_set(ref);parent=set().union(*(edge_set(t) for t in parents),base)
    disagree=np.zeros(n,dtype=np.int16)
    orig=[set((ref[(i-1)%n],ref[(i+1)%n])) for i in range(n)]
    for t in parents:
        pos={u:i for i,u in enumerate(t)}
        for u in range(n):
            j=pos[u]
            if {t[(j-1)%n],t[(j+1)%n]}!=orig[ref.index(u)]:
                disagree[u]+=1
    lp={E(r['u'],r['v']):r['x'] for r in pub['lp_positive']}
    eligible={e:x for e,x in lp.items() if e not in parent}
    meta={}
    if strategy=='repair':
        selected,meta=select_repair(ref,D,parents,budget,20261029)
    else:
        def keyscore(pair):
            (u,v),x=pair
            if strategy=='uncertainty':
                return (int(1e-5<x<1-1e-5),int(disagree[u]>0)+int(disagree[v]>0),
                        disagree[u]+disagree[v],x*(1-x),-u*n-v)
            if strategy=='conflict':
                return (int(x>=1-1e-5),int(disagree[u]==0)+int(disagree[v]==0),
                        x, -u*n-v)
            raise ValueError(strategy)
        ranked=[e for e,x in sorted(eligible.items(),key=keyscore,reverse=True)]
        if len(ranked)<budget:
            fallback=sorted((e for e in
                 (E(u,v) for u in range(n) for v in range(u+1,n))
                 if e not in parent and e not in eligible),key=lambda e:(D[e],e))
            ranked+=fallback
        selected=ranked[:budget]
        meta={'novel_lp_supported':sum(e in eligible for e in selected),
              'fractional_lp_supported':sum(1e-5<lp.get(e,0)<1-1e-5 for e in selected)}
    assert len(selected)==budget and not(set(selected)&parent)
    edges=parent|set(selected)
    model=cp_model.CpModel();arcs=[];var={}
    for u,v in sorted(edges):
        q=model.NewBoolVar(f'q{u}_{v}')
        f=model.NewBoolVar(f'f{u}_{v}');r=model.NewBoolVar(f'r{u}_{v}')
        model.Add(f+r==q)
        arcs.extend(((u,v,f),(v,u,r)));var[(u,v)]=q
    model.AddCircuit(arcs)
    model.Minimize(sum(int(D[u,v])*q for (u,v),q in var.items()))
    s=cp_model.CpSolver()
    s.parameters.num_search_workers=1
    s.parameters.random_seed=1701
    s.parameters.max_time_in_seconds=max(.1,seconds-(time.monotonic()-t0))
    result=s.Solve(model)
    output={'instance':pub['instance'],'strategy':strategy,'budget':budget,
      'reference_score':pub['reference_score'],'LP_rounds':pub['lp_rounds'],
      'method_meta':meta,'selected_chords':selected,
      'status':s.StatusName(result),'seconds':round(time.monotonic()-t0,3)}
    if result in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        eds={e for e,q in var.items() if s.Value(q)}
        assert len(eds)==n
        adj=[[] for _ in range(n)]
        for u,v in eds:adj[u].append(v);adj[v].append(u)
        route=[0];seen={0};prev=-1;cur=0
        while True:
            a,b=adj[cur];nxt=a if a!=prev else b
            if nxt==0:break
            assert nxt not in seen
            seen.add(nxt);route.append(nxt);prev,cur=cur,nxt
        assert len(route)==n and len(seen)==n
        cost=score(route,D)
        assert cost==round(s.ObjectiveValue())
        output.update({'score':cost,'gain':pub['reference_score']-cost,'tour':route})
    dest=Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('selected_chords','tour')}),flush=True)
def evaluate(public,private,results,out,official_opt):
    pub=json.loads(Path(public).read_text());hid=json.loads(Path(private).read_text())
    D=np.asarray(pub['distance'],dtype=np.int32)
    assert score(hid['hidden_tour'],D)==hid['hidden_score']
    assert score(pub['reference'],D)==pub['reference_score']
    assert official_opt<=hid['hidden_score']<pub['reference_score']
    target=edge_set(hid['hidden_tour'])-edge_set(pub['reference'])
    cases=[]
    for f in Path(results).rglob('result.json'):
        r=json.loads(f.read_text())
        if r['instance']!=pub['instance']:continue
        row={k:r.get(k) for k in ('strategy','budget','status','seconds','score','gain','method_meta')}
        row['target_edges_in_added_chords']=len(set(map(tuple,r['selected_chords']))&target)
        if 'tour' in r:
            assert score(r['tour'],D)==r['score']
            row['hidden_structure_recall']=round(len((edge_set(r['tour'])-edge_set(pub['reference']))&target)/len(target),5)
            row['reached_certified_optimum']=(r['score']==official_opt)
            assert r['score']>=official_opt,('suboptimality/metric bug',r['score'],official_opt)
        cases.append(row)
    summary={'instance':pub['instance'],'n':pub['n'],'certified_optimum':official_opt,
      'blind_reference_score':pub['reference_score'],'hidden_generator_best':hid['hidden_score'],
      'hidden_missing_edges':len(target),'cases':cases,
      'note':'Official TSPLIB optimum withheld from search. LP is degree+separated-support-cut relaxation; incomplete SEC family, not full TSP polytope.'}
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','search','evaluate'])
    for name in ('instance','name','out','public','private','results','strategy','budget','optimum'):
        p.add_argument('--'+name)
    p.add_argument('--seconds',type=float,default=12)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.name,a.instance,a.out)
    if a.mode=='search':search(a.public,a.strategy,int(a.budget),a.out,a.seconds)
    if a.mode=='evaluate':evaluate(a.public,a.private,a.results,a.out,int(a.optimum))
