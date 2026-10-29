#!/usr/bin/env python3
"""Exact destroy/regrow search around a published 35-vertex R(4,6) graph.

For each old vertex v, fix the other 34 vertices and regrow two arbitrary
vertices: a replacement for v and a genuinely new vertex.  This releases all
69 edges incident with those two vertices, not a small Hamming shell.

In any R(4,6,36) graph every degree is in [11,17].  For a fixed good 34-core,
a new vertex is therefore represented by a core-neighborhood N of size 10..17
such that N contains no core triangle and its complement contains no core
independent 5-set.  For two such domains A,B, their mutual edge is allowed iff
A∩B is independent in the core; their mutual nonedge is allowed iff A∪B hits
every core independent 4-set.  Together with the degree bounds these are all
Ramsey constraints involving one or two new vertices, so the test is exact.
"""
from __future__ import annotations
import argparse,itertools,json
from pathlib import Path
MIN_DEG,MAX_DEG=11,17

def read_exoo(path:Path):
    lines=[''.join(x.split()) for x in path.read_text(encoding='ascii').splitlines()]
    lines=[x for x in lines if x]
    assert len(lines)==35 and all(len(x)==35 and set(x)<={'0','1'} for x in lines)
    for i in range(35):
        assert lines[i][i]=='0'
        for j in range(35):assert lines[i][j]==lines[j][i]
    # Published Exoo files use the opposite color orientation from p003.
    return [''.join('0' if i==j else ('1' if lines[i][j]=='0' else '0') for j in range(35)) for i in range(35)]

def verify(rows):
    n=len(rows)
    for vs in itertools.combinations(range(n),4):
        if all(rows[a][b]=='1' for a,b in itertools.combinations(vs,2)):return False,('K4',vs)
    for vs in itertools.combinations(range(n),6):
        if all(rows[a][b]=='0' for a,b in itertools.combinations(vs,2)):return False,('I6',vs)
    return True,None

def masks(core,rows,k,edge):
    out=[]
    for ids in itertools.combinations(range(len(core)),k):
        if all((rows[core[a]][core[b]]=='1')==edge for a,b in itertools.combinations(ids,2)):
            out.append(sum(1<<i for i in ids))
    return out

def unary_domains(core,rows):
    n=len(core);ALL=(1<<n)-1
    triangles=masks(core,rows,3,True);ind5=masks(core,rows,5,False)
    lo,hi=10,MAX_DEG
    occ=[0]*n
    for m in triangles+ind5:
        for v in range(n):occ[v]+=bool(m>>v&1)
    sols=[];nodes=0
    def prop(one,zero):
        while True:
            if one&zero:return None
            c=one.bit_count();un=n-c-zero.bit_count();changed=0
            if c>hi or c+un<lo:return None
            if c==hi:
                u=ALL&~(one|zero);zero|=u;changed|=u
            if c+un==lo:
                u=ALL&~(one|zero);one|=u;changed|=u
            for m in triangles:
                x=(one&m).bit_count()
                if x>=3:return None
                if x==2:
                    u=m&~(one|zero)
                    if u and not(u&(u-1)):zero|=u;changed|=u
            for m in ind5:
                x=(zero&m).bit_count()
                if x>=5:return None
                if x==4:
                    u=m&~(one|zero)
                    if u and not(u&(u-1)):one|=u;changed|=u
            if not changed:return one,zero
    def dfs(one,zero):
        nonlocal nodes
        nodes+=1;p=prop(one,zero)
        if p is None:return
        one,zero=p
        if one|zero==ALL:
            sols.append(one);return
        U=ALL&~(one|zero)
        v=max((i for i in range(n) if U>>i&1),key=lambda i:occ[i])
        dfs(one|1<<v,zero);dfs(one,zero|1<<v)
    dfs(0,0)
    return sols,{'dfs_nodes':nodes,'triangles':len(triangles),'independent5':len(ind5),
                 'size_hist':{str(k):sum(m.bit_count()==k for m in sols) for k in sorted({m.bit_count() for m in sols})}}

def solve_core(rows,deleted):
    core=[v for v in range(35) if v!=deleted];n=34
    dom,meta=unary_domains(core,rows)
    core_edges=masks(core,rows,2,True);I4=masks(core,rows,4,False)
    coredeg=[sum(rows[u][v]=='1' for v in core) for u in core]
    adj=[0]*n
    for e in core_edges:
        vs=[i for i in range(n) if e>>i&1];adj[vs[0]]|=1<<vs[1];adj[vs[1]]|=1<<vs[0]
    def independent(m):
        z=m
        while z:
            lb=z&-z;v=lb.bit_length()-1;z-=lb
            if adj[v]&z:return False
        return True
    all4=(1<<len(I4))-1
    coverage=[]
    for m in dom:
        z=0
        for q,s in enumerate(I4):
            if m&s:z|=1<<q
        coverage.append(z)
    checked=0
    for i,a in enumerate(dom):
        for j,b in enumerate(dom):
            for edge in (0,1):
                checked+=1
                if edge and not independent(a&b):continue
                if not edge and (coverage[i]|coverage[j])!=all4:continue
                if not MIN_DEG<=a.bit_count()+edge<=MAX_DEG:continue
                if not MIN_DEG<=b.bit_count()+edge<=MAX_DEG:continue
                if any(not MIN_DEG<=coredeg[v]+((a>>v)&1)+((b>>v)&1)<=MAX_DEG for v in range(n)):continue
                return {'status':'SAT','domain_count':len(dom),'unary':meta,'checked_pair_states':checked,
                        'domain_ordinals':[i,j],'new_edge':edge,'domain_masks':[a,b],'core':core}
    return {'status':'UNSAT','domain_count':len(dom),'unary':meta,'checked_pair_states':checked}

def reconstruct(rows,hit):
    core=hit['core'];masks2=hit['domain_masks'];edge=hit['new_edge']
    out=[['0']*36 for _ in range(36)]
    for i,u in enumerate(core):
        for j,v in enumerate(core):out[i][j]=rows[u][v]
    for q,m in enumerate(masks2):
        v=34+q
        for i in range(34):
            if m>>i&1:out[v][i]=out[i][v]='1'
    if edge:out[34][35]=out[35][34]='1'
    rr=[''.join(x) for x in out];ok,bad=verify(rr);assert ok,bad
    deg=[x.count('1') for x in rr];assert min(deg)>=MIN_DEG and max(deg)<=MAX_DEG
    return rr

def main():
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--summary',type=Path,required=True);ap.add_argument('--candidate',type=Path)
    a=ap.parse_args();rows=read_exoo(a.input);ok,bad=verify(rows);assert ok,bad
    results=[];candidate=None
    for deleted in range(35):
        d=solve_core(rows,deleted);d['deleted_vertex']=deleted;results.append(d)
        print(json.dumps({k:d[k] for k in ('deleted_vertex','status','domain_count','checked_pair_states')},sort_keys=True),flush=True)
        if d['status']=='SAT':
            candidate=reconstruct(rows,d);break
    out={'campaign':'exact-two-vertex-regrow-of-one-published-35-core','source':str(a.input),'deleted_cores_completed':len(results),
         'all_unsat':len(results)==35 and all(x['status']=='UNSAT' for x in results),'found':candidate is not None,'results':results}
    a.summary.parent.mkdir(parents=True,exist_ok=True);a.summary.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    if candidate is not None:
        assert a.candidate is not None
        a.candidate.write_text(json.dumps({'adjacency':candidate},indent=2)+'\n')
        print(json.dumps({'FOUND':True,'deleted_vertex':results[-1]['deleted_vertex'],'edges':sum(x.count('1') for x in candidate)//2},sort_keys=True))
    else:print(json.dumps({'FOUND':False,'deleted_cores_completed':len(results),'domain_counts':[x['domain_count'] for x in results]},sort_keys=True))
if __name__=='__main__':main()
