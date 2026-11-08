#!/usr/bin/env python3
"""Constructive C7^10 rectangular core-release search from any verified record.

Search coupled 5D owner sets A,C (size 6) rich in overlapping support-three
outside vertices. Release all necessary old 10D points jointly while placing
outside×outside, row, column and periphery replacements in one MILP. Optimize
the ACTUAL 10D gain; any positive result materializes a complete certificate.
"""
import argparse,collections,itertools,json,random,time
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

P=(1,7,49,343,2401)
U=7**5
D=tuple(tuple(v//p%7 for p in P) for v in range(U))
OFF=tuple(itertools.product((-1,0,1),repeat=5))

def code(d):return sum(x*P[i] for i,x in enumerate(d))
@lru_cache(maxsize=U)
def nb(v):return tuple(code(tuple((D[v][k]+e[k])%7 for k in range(5))) for e in OFF)
def conflict(a,b):return all((x-y)%7 in (0,1,6) for x,y in zip(D[a],D[b]))
def word(a,b):return ''.join(map(str,D[a]+D[b]))

def run(parent,source,output,shard,shards,trials,limit,seed):
    t0=time.monotonic()
    W=set(json.loads(source.read_text())['points'])
    assert len(W)==134753
    B={code(tuple(map(int,line.split()))) for line in parent.read_text().splitlines() if line.strip()}
    R=((1,3,4,4,6),(3,4,0,3,5),(5,3,1,3,4),(4,4,6,1,6),
       (6,0,6,4,5),(0,3,5,6,5),(6,4,3,4,0),(6,4,5,3,2))
    B-=set(map(code,R))
    assert len(B)==359
    groups=collections.defaultdict(set)
    for s in W:
        groups[code(tuple(map(int,s[:5])))].add(code(tuple(map(int,s[5:]))))
    mask={p:sum(1<<v for v in s) for p,s in groups.items()}
    su={};owner=collections.defaultdict(list)
    for v in range(U):
        if v in B:continue
        S=frozenset(B.intersection(nb(v)))
        if len(S)<=6:
            su[v]=S
            if len(S)==3:
                for o in S:owner[o].append(S)
    rng=random.Random(seed)
    trip=list({x for x in su.values() if len(x)==3})
    clusters=set()
    for s in trip:
        for _ in range(3):
            A=set(s)
            while len(A)<6:
                nearby=set().union(*(owner[v] for v in A))
                pool=set().union(*nearby)-A
                if not pool:break
                scores=[(sum(x <= (A|{q}) for x in nearby),rng.random(),q) for q in pool]
                A.add(max(scores)[2])
            if len(A)==6:clusters.add(tuple(sorted(A)))
    scored=sorted(((sum(set(t)<=set(A) for t in trip),A) for A in clusters),reverse=True)
    core_sets=[A for _,A in scored[:1000]]
    assert len(core_sets)>=50
    output.mkdir(parents=True,exist_ok=True)
    scorebest=134753;best_gain=0;best_move_count=0;completed=0;timed_out=0
    @lru_cache(maxsize=U)
    def nbmask(v):return sum(1<<x for x in nb(v))
    @lru_cache(maxsize=U)
    def nearrows(v):return tuple((p,mask[p]) for p in nb(v) if p in mask)
    for trial in range(shard,trials,shards):
        A=set(rng.choice(core_sets));C=set(rng.choice(core_sets))
        US=set(A)|{v for v,S in su.items() if S<=A}
        VS=set(C)|{v for v,S in su.items() if S<=C}
        cand=[];blockers=set()
        for u in sorted(US):
            Q=nearrows(u)
            for v in sorted(VS):
                if v in groups.get(u,()):continue
                q=nbmask(v);bl=[]
                for p,z in Q:
                    hits=z&q
                    while hits:
                        bit=hits&-hits
                        bl.append((p,bit.bit_length()-1))
                        hits-=bit
                if not bl: # already a direct positive witness
                    words=W|{word(u,v)}
                    assert len(words)==134754
                    (output/'certificate.json').write_text(json.dumps({'points':sorted(words)},separators=(',',':'))+'\n')
                    return {'score':134754,'trial':trial,'gain':1,'direct_add':[u,v],
                            'elapsed_seconds':time.monotonic()-t0}
                cand.append((u,v,bl));blockers.update(bl)
        n=len(cand);Blist=sorted(blockers);bidx={q:i for i,q in enumerate(Blist)}
        rows=[];cols=[];vals=[];hi=[]
        def addrow(terms,bound):
            k=len(hi);hi.append(bound)
            for j,v in terms:rows.append(k);cols.append(j);vals.append(v)
        for i,(u,v,block) in enumerate(cand):
            for p in block:addrow(((i,1),(n+bidx[p],-1)),0)
        for i,(u,v,_) in enumerate(cand):
            for j in range(i+1,n):
                x,y,_=cand[j]
                if conflict(u,x) and conflict(v,y):addrow(((i,1),(j,1)),1)
        M=coo_matrix((np.asarray(vals,float),(rows,cols)),shape=(len(hi),n+len(Blist))).tocsr()
        obj=np.r_[-np.ones(n),np.ones(len(Blist))]
        sol=milp(obj,integrality=np.ones(n+len(Blist)),
                 bounds=Bounds(np.zeros(n+len(Blist)),np.ones(n+len(Blist))),
                 constraints=LinearConstraint(M,-np.inf,hi),
                 options={'time_limit':limit,'mip_rel_gap':0})
        completed+=1
        if sol.status!=0:timed_out+=1
        if sol.x is None:continue
        added=[(u,v) for i,(u,v,_) in enumerate(cand) if sol.x[i]>.5]
        removed={b for i,(_,_,bl) in enumerate(cand) if sol.x[i]>.5 for b in bl}
        gain=len(added)-len(removed)
        if gain>best_gain or (gain==best_gain and len(added)>best_move_count):
            best_gain=gain;best_move_count=len(added)
            print('BEST',json.dumps({'shard':shard,'trial':trial,'gain':gain,
                'added':len(added),'removed':len(removed)}),flush=True)
        if gain>0:
            words=(W-{word(u,v) for u,v in removed})|{word(u,v) for u,v in added}
            assert len(words)==134753+gain
            (output/'certificate.json').write_text(json.dumps({'points':sorted(words)},separators=(',',':'))+'\n')
            scorebest=len(words)
            break
    return {'method':'core-rectangle-and-periphery-joint-construction',
            'shard':shard,'trials_requested':trials,'cases_solved':completed,
            'incomplete_cases':timed_out,'best_gain':best_gain,
            'best_neutral_move_count':best_move_count,
            'score':scorebest,'elapsed_seconds':round(time.monotonic()-t0,2)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('r367',type=Path);p.add_argument('record',type=Path)
    p.add_argument('output',type=Path)
    p.add_argument('--shard',type=int,required=True)
    p.add_argument('--shards',type=int,default=4)
    p.add_argument('--trials',type=int,default=400)
    p.add_argument('--limit',type=float,default=3)
    p.add_argument('--seed',type=int,default=20261108)
    a=p.parse_args()
    out=run(a.r367,a.record,a.output,a.shard,a.shards,a.trials,a.limit,a.seed+a.shard)
    (a.output/'status.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps(out,sort_keys=True),flush=True)

if __name__=='__main__':main()
