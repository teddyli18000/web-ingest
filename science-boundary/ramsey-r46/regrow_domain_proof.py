#!/usr/bin/env python3
from __future__ import annotations
import argparse,itertools,json,time
from pathlib import Path
import networkx as nx
MIN_DEG,MAX_DEG=11,17

def load(path):
    r=json.load(open(path))['adjacency']; n=len(r)
    assert n==36 and all(len(x)==n for x in r)
    assert all(r[i][i]=='0' and all(r[i][j]==r[j][i] for j in range(n)) for i in range(n))
    return r

def badsets(r):
    k4=[];i6=[]
    for vs in itertools.combinations(range(36),4):
        if all(r[a][b]=='1' for a,b in itertools.combinations(vs,2)):k4.append(vs)
    for vs in itertools.combinations(range(36),6):
        if all(r[a][b]=='0' for a,b in itertools.combinations(vs,2)):i6.append(vs)
    return k4,i6

def masks_of_sets(core,r,k,edge):
    out=[]
    for ids in itertools.combinations(range(len(core)),k):
        if all((r[core[a]][core[b]]=='1')==edge for a,b in itertools.combinations(ids,2)):
            m=0
            for i in ids:m|=1<<i
            out.append(m)
    return out

def unary_domains(r,removed):
    core=[v for v in range(36) if v not in removed]; n=len(core); ALL=(1<<n)-1
    tri=masks_of_sets(core,r,3,True); ind5=masks_of_sets(core,r,5,False)
    lo=max(0,MIN_DEG-(len(removed)-1)); hi=MAX_DEG
    sols=[]; nodes=0
    def prop(one,zero):
        nonlocal nodes
        while True:
            if one&zero:return None
            c1=one.bit_count(); un=n-c1-zero.bit_count()
            if c1>hi or c1+un<lo:return None
            changed=0
            if c1==hi: changed|=ALL&~(one|zero); zero|=changed
            if c1+un==lo:
                u=ALL&~(one|zero); one|=u; changed|=u
            for m in tri:
                a=(one&m).bit_count()
                if a>=3:return None
                if a==2:
                    u=m&~(one|zero)
                    if u and u&(u-1)==0: zero|=u; changed|=u
            for m in ind5:
                z=(zero&m).bit_count()
                if z>=5:return None
                if z==4:
                    u=m&~(one|zero)
                    if u and u&(u-1)==0: one|=u; changed|=u
            if not changed:return one,zero
    occ=[0]*n
    for m in tri+ind5:
        for v in range(n):occ[v]+=bool(m>>v&1)
    def dfs(one,zero):
        nonlocal nodes
        nodes+=1;p=prop(one,zero)
        if p is None:return
        one,zero=p
        if one|zero==ALL:
            if lo<=one.bit_count()<=hi:sols.append(one)
            return
        U=ALL&~(one|zero); v=max((i for i in range(n) if U>>i&1),key=lambda i:occ[i])
        dfs(one|1<<v,zero);dfs(one,zero|1<<v)
    dfs(0,0)
    return core,sols,{'triangles':len(tri),'independent5':len(ind5),'dfs_nodes':nodes,'size_hist':{str(k):sum(x.bit_count()==k for x in sols) for k in sorted({x.bit_count() for x in sols})}}

def core_structures(core,r):
    edges=masks_of_sets(core,r,2,True); I2=masks_of_sets(core,r,2,False);I3=masks_of_sets(core,r,3,False);I4=masks_of_sets(core,r,4,False)
    cdeg=[sum(r[u][v]=='1' for v in core) for u in core]
    return edges,I2,I3,I4,cdeg

def pair_states(dom,edges,I4):
    M=len(dom)
    n=max((e.bit_length() for e in edges),default=0)
    adj=[0]*n
    for e in edges:
        a=(e & -e).bit_length()-1; rest=e & (e-1); b=(rest & -rest).bit_length()-1
        adj[a]|=1<<b;adj[b]|=1<<a
    def independent_mask(m):
        z=m
        while z:
            lb=z&-z;v=lb.bit_length()-1;z-=lb
            if adj[v]&z:return False
        return True
    all4=(1<<len(I4))-1
    cov=[]
    for a in dom:
        c=0
        for q,s4 in enumerate(I4):
            if a&s4:c|=1<<q
        cov.append(c)
    st=[[0]*M for _ in range(M)]
    for i,a in enumerate(dom):
        for j,b in enumerate(dom):
            eok=independent_mask(a&b)
            nok=(cov[i]|cov[j])==all4
            st[i][j]=(1 if nok else 0)|(2 if eok else 0)
    return st

def core_degree_ok(tup,dom,cdeg):
    for v,d in enumerate(cdeg):
        if not MIN_DEG<=d+sum((dom[i]>>v)&1 for i in tup)<=MAX_DEG:return False
    return True

def exact_small(k,dom,st,core,I2,I3,I4,cdeg):
    pairs=list(itertools.combinations(range(k),2)); checked=0
    for tup in itertools.product(range(len(dom)),repeat=k):
        if not core_degree_ok(tup,dom,cdeg):continue
        M=[dom[i] for i in tup]
        for h in range(1<<len(pairs)):
            checked+=1; deg=[0]*k;ok=True
            for p,(a,b) in enumerate(pairs):
                e=(h>>p)&1
                if not (st[tup[a]][tup[b]] & (2 if e else 1)):ok=False;break
                if e:deg[a]+=1;deg[b]+=1
            if not ok:continue
            if any(not MIN_DEG<=M[i].bit_count()+deg[i]<=MAX_DEG for i in range(k)):continue
            if k>=4:
                for q in itertools.combinations(range(k),4):
                    if all((h>>pairs.index(tuple(sorted((a,b)))))&1 for a,b in itertools.combinations(q,2)):ok=False;break
            if not ok:continue
            for q in itertools.combinations(range(k),3):
                e3=[(h>>pairs.index(tuple(sorted((a,b)))))&1 for a,b in itertools.combinations(q,2)]
                union=0;inter=(1<<len(core))-1
                for a in q:union|=M[a];inter&=M[a]
                if all(e3) and inter:ok=False;break
                if not any(e3) and any(not (union&s) for s in I3):ok=False;break
            if not ok:continue
            if k>=4:
                for q in itertools.combinations(range(k),4):
                    if any((h>>pairs.index(tuple(sorted((a,b)))))&1 for a,b in itertools.combinations(q,2)):continue
                    union=0
                    for a in q:union|=M[a]
                    if any(not (union&s) for s in I2):ok=False;break
            if ok:return {'status':'SAT','checked_h_states':checked,'tuple':tup,'h':h}
    return {'status':'UNSAT','checked_h_states':checked}

def pair_tuple_search(k,dom,st,cdeg):
    n=len(cdeg); add=[0]*n;sel=[];nodes=0;leaves=0
    def dfs(dep):
        nonlocal nodes,leaves
        nodes+=1;rem=k-dep
        for v,d in enumerate(cdeg):
            cur=d+add[v]
            if cur>MAX_DEG or cur+rem<MIN_DEG:return
        if dep==k:leaves+=1;return
        for j in range(len(dom)):
            if any(st[i][j]==0 for i in sel):continue
            sel.append(j)
            m=dom[j]
            for v in range(n):add[v]+=(m>>v)&1
            dfs(dep+1)
            for v in range(n):add[v]-=(m>>v)&1
            sel.pop()
    dfs(0);return {'status':'UNSAT' if leaves==0 else 'UNKNOWN','dfs_nodes':nodes,'pair_degree_feasible_tuples':leaves}

def clique_bound(k,st):
    G=nx.Graph();M=len(st);G.add_nodes_from(range(M));loops=0
    for i in range(M):
        loops+=st[i][i]!=0
        for j in range(i+1,M):
            if st[i][j]:G.add_edge(i,j)
    omega=max((len(c) for c in nx.find_cliques(G)),default=0)
    return {'compat_edges':G.number_of_edges(),'compat_loops':loops,'omega':omega,'status':'UNSAT' if loops==0 and omega<k else 'UNKNOWN'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('source',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();r=load(a.source)
    K,I=badsets(r);assert (len(K),len(I))==(10,4)
    trans=[p for p in itertools.combinations(range(36),2) if all(set(p)&set(s) for s in K+I)]
    assert trans==[(2,35),(5,35),(10,35),(13,35)],trans
    out={'source':str(a.source),'source_edges':sum(x.count('1') for x in r)//2,'defects':{'K4':len(K),'I6':len(I)},'minimum_two_vertex_transversals':[list(x) for x in trans],'k2':[],'nested':[]}
    for rem in trans:
        core,dom,meta=unary_domains(r,rem);edges,I2,I3,I4,cdeg=core_structures(core,r);st=pair_states(dom,edges,I4);res=exact_small(2,dom,st,core,I2,I3,I4,cdeg)
        out['k2'].append({'removed':list(rem),'core_size':len(core),'domain_count':len(dom),'unary':meta,'exact':res})
        assert res['status']=='UNSAT'
    nested=[[2,35,13],[2,35,13,5],[2,35,13,5,9],[2,35,13,5,9,10],[2,35,13,5,9,10,34],[2,35,13,5,9,10,34,25]]
    expect_domains=[5,11,17,25,449,1109]
    for rem,ed in zip(nested,expect_domains):
        t=time.time();core,dom,meta=unary_domains(r,rem);assert len(dom)==ed,(rem,len(dom),ed)
        edges,I2,I3,I4,cdeg=core_structures(core,r);st=pair_states(dom,edges,I4);k=len(rem)
        if k<=4: proof=exact_small(k,dom,st,core,I2,I3,I4,cdeg)
        elif k<=6: proof=pair_tuple_search(k,dom,st,cdeg)
        else: proof=clique_bound(k,st)
        assert proof['status']=='UNSAT',(rem,proof)
        elapsed=time.time()-t
        out['nested'].append({'removed':rem,'k':k,'core_size':len(core),'domain_count':len(dom),'unary':meta,'proof':proof})
        print(json.dumps({'k':k,'domain_count':len(dom),'proof':proof,'seconds':elapsed},sort_keys=True),flush=True)
    out['conclusion']='all four k2 defect-transversal regrows and the nested k3..k8 hierarchy around the best 14-defect graph are exactly UNSAT'
    if a.output:a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'k2_domains':[x['domain_count'] for x in out['k2']],'nested_domains':[x['domain_count'] for x in out['nested']],'conclusion':out['conclusion']},sort_keys=True))
if __name__=='__main__':main()
