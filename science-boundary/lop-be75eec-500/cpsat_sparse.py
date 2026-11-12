#!/usr/bin/env python3
"""Jointly optimize 28–56 arbitrary rank holes with CP-SAT precedence/rank variables.

Unlike exact subset DP, this model can couple many far-apart vertex slots.
Each chosen vertex receives a rank among chosen slots, with an AllDifferent
constraint and reified pairwise precedence; fixed vertices contribute a
position-dependent unary score.
"""
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from pathlib import Path
import json,random,sys,time
from ortools.sat.python import cp_model

N=500
def full_score(p,W):
    return sum(W[p[i]][p[j]] for i in range(N) for j in range(i+1,N))

def solve(args):
    order,W,positions,seconds,seed=args
    k=len(positions)
    vertices=[order[t] for t in positions]
    occupied=set(positions)
    unary=[]
    for a in range(k):
        v=vertices[a]
        gain=sum(W[v][order[t]] for t in range(N) if t not in occupied)
        u=[]
        t=0
        for target in positions:
            while t<target:
                if t not in occupied:
                    gain+=W[order[t]][v]-W[v][order[t]]
                t+=1
            u.append(gain)
        unary.append(u)
    model=cp_model.CpModel()
    rank=[model.NewIntVar(0,k-1,f'r{i}') for i in range(k)]
    model.AddAllDifferent(rank)
    ext=[]
    for i in range(k):
        a=model.NewIntVar(min(unary[i]),max(unary[i]),f'u{i}')
        model.AddElement(rank[i],unary[i],a)
        ext.append(a)
        model.AddHint(rank[i],i)
    binary=[]
    for i in range(k):
        for j in range(i+1,k):
            x=model.NewBoolVar(f'x{i}_{j}')
            model.Add(rank[i]<rank[j]).OnlyEnforceIf(x)
            model.Add(rank[i]>rank[j]).OnlyEnforceIf(x.Not())
            model.AddHint(x,1)
            binary.append((W[vertices[i]][vertices[j]]-W[vertices[j]][vertices[i]])*x)
    model.Maximize(sum(ext)+sum(binary))
    solver=cp_model.CpSolver()
    solver.parameters.num_search_workers=1
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.random_seed=seed
    status=solver.Solve(model)
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        return positions,0,None,0
    ranked=[None]*k
    for i in range(k):
        ranked[solver.Value(rank[i])]=vertices[i]
    candidate=order.copy()
    for t,pos in enumerate(positions):
        candidate[pos]=ranked[t]
    gain=full_score(candidate,W)-full_score(order,W)
    return positions,gain,candidate,float(solver.WallTime())

def choose(order,W,mode,rng):
    k=rng.choice((28,32,36,40,44,48,52,56))
    if mode==0:
        a=rng.randrange(N-k+1)
        return list(range(a,a+k))
    if mode in (1,2):
        clusters=mode+1
        positions=set()
        for c in range(clusters):
            size=k//clusters+(c<k%clusters)
            start=rng.randrange(N-size+1)
            positions.update(range(start,start+size))
        while len(positions)<k:positions.add(rng.randrange(N))
        return sorted(positions)[:k]
    if mode==3:
        length=rng.randrange(k,min(200,N)+1)
        start=rng.randrange(N-length+1)
        return sorted(rng.sample(range(start,start+length),k))
    if mode==4:
        seed=rng.randrange(N)
        primary=order[seed]
        weights=[]
        for pos,v in enumerate(order):
            if pos==seed:continue
            regret=max(0,W[v][primary]-W[primary][v]) if pos>seed else max(0,W[primary][v]-W[v][primary])
            weight=regret/(1+abs(pos-seed)/20)+rng.randrange(100)
            weights.append((weight,pos))
        weights.sort(reverse=True)
        positions={seed}
        positions.update(t for _,t in weights[:k-1])
        return sorted(positions)
    return sorted(rng.sample(range(N),k))

def main():
    data=list(map(int,Path(sys.argv[1]).read_text().split()))
    assert data[0]==N and len(data)==N*N+1
    W=[data[1+i*N:1+(i+1)*N] for i in range(N)]
    order=list(map(int,Path(sys.argv[2]).read_text().split()))
    assert sorted(order)==list(range(N))
    out=Path(sys.argv[3])
    expires=time.monotonic()+int(sys.argv[4])
    cores=int(sys.argv[5])
    score=full_score(order,W)
    rng=random.Random(922019)
    running={}
    tasks=0
    improvements=0
    uniq=set()
    print('INITIAL',score,flush=True)
    with ProcessPoolExecutor(max_workers=cores) as pool:
        while time.monotonic()<expires or running:
            while time.monotonic()<expires and len(running)<cores:
                mode=(tasks//3)%6
                positions=choose(order,W,mode,rng)
                key=tuple(positions)
                if key in uniq:continue
                uniq.add(key)
                parent=order.copy()
                s=score
                future=pool.submit(solve,(parent,W,positions,5.0,rng.randrange(1,10000000)))
                running[future]=(parent,s)
                tasks+=1
            if not running:break
            finished,_=wait(running,timeout=1,return_when=FIRST_COMPLETED)
            for future in finished:
                parent,parent_score=running.pop(future)
                positions,gain,candidate,seconds=future.result()
                if gain>0:
                    assert full_score(candidate,W)==parent_score+gain
                    if parent_score+gain>score:
                        order=candidate
                        score=parent_score+gain
                        improvements+=1
                        uniq.clear()
                        out.write_text(json.dumps({'order':order},separators=(',',':')))
                        print('RECORD',score,'holes',len(positions),'tasks',tasks,flush=True)
                if tasks%20==0:print('PROGRESS',tasks,'best',score,flush=True)
    print('FINAL',score,'tasks',tasks,'records',improvements,flush=True)
if __name__=='__main__':
    main()
