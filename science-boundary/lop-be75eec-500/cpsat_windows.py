#!/usr/bin/env python3
"""CP-SAT large contiguous LOP windows: jointly optimize 36–78 vertices.
The model enforces transitive precedence using the two triangle inequalities.
All winning candidates are independently rescored against the full matrix.
"""
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
import json
from pathlib import Path
import random
import sys
import time
from ortools.sat.python import cp_model

N=500
def objective(p,M):
    return sum(M[p[i]][p[j]] for i in range(N) for j in range(i+1,N))
def window_score(p,M):
    return sum(M[p[i]][p[j]] for i in range(len(p)) for j in range(i+1,len(p)))

def optimize(task):
    p,M,start,k,seed,seconds=task
    block=p[start:start+k]
    model=cp_model.CpModel()
    x={(i,j):model.NewBoolVar(f'x{i}_{j}') for i in range(k) for j in range(i+1,k)}
    for t in x.values():model.AddHint(t,1)
    for i in range(k):
        for j in range(i+1,k):
            for m in range(j+1,k):
                e=x[i,j]+x[j,m]-x[i,m]
                model.Add(e>=0)
                model.Add(e<=1)
    model.Maximize(sum((M[block[i]][block[j]]-M[block[j]][block[i]])*x[i,j]
                       for i in range(k) for j in range(i+1,k)))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=seconds
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=seed
    status=solver.Solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return start,k,0,None
    indegree=[0]*k
    for i in range(k):
        for j in range(i+1,k):
            if solver.Value(x[i,j]):indegree[j]+=1
            else:indegree[i]+=1
    chosen=[block[v] for v in sorted(range(k),key=indegree.__getitem__)]
    gain=window_score(chosen,M)-window_score(block,M)
    return start,k,gain,chosen

def rank_windows(p,M):
    ranked=[]
    for k in (36,44,54,66,78):
        for begin in range(0,N-k+1,11):
            v=p[begin:begin+k]
            conflict=sum(max(0,M[v[j]][v[i]]-M[v[i]][v[j]])
                         for i in range(k) for j in range(i+1,k))
            ranked.append((conflict/(k**1.4),begin,k))
    return sorted(ranked,reverse=True)

def main():
    data=list(map(int,Path(sys.argv[1]).read_text().split()))
    assert data[0]==N and len(data)==N*N+1
    M=[data[1+i*N:1+(i+1)*N] for i in range(N)]
    p=list(map(int,Path(sys.argv[2]).read_text().split()))
    assert sorted(p)==list(range(N))
    output=Path(sys.argv[3])
    budget=float(sys.argv[4])
    threads=int(sys.argv[5])
    rng=random.Random(20261112)
    best=objective(p,M)
    ranked=rank_windows(p,M)
    visited=set()
    deadline=time.monotonic()+budget
    done=0
    records=0
    inflight={}
    print('INITIAL',best,flush=True)
    with ProcessPoolExecutor(max_workers=threads) as pool:
        while time.monotonic()<deadline or inflight:
            while len(inflight)<threads and time.monotonic()<deadline:
                for _ in range(100):
                    if rng.random()<0.7:
                        _,start,k=ranked[rng.randrange(min(125,len(ranked)))]
                    else:
                        k=rng.choice((36,44,54,66,78))
                        start=rng.randrange(N-k+1)
                    if (start,k) not in visited:break
                visited.add((start,k))
                base=p.copy()
                val=best
                task=(base,M,start,k,rng.randrange(1,10000000),4.0)
                inflight[pool.submit(optimize,task)]=(base,val)
            if not inflight:break
            finished,_=wait(inflight,return_when=FIRST_COMPLETED,timeout=1.0)
            for f in finished:
                original,val=inflight.pop(f)
                start,k,gain,block=f.result()
                done+=1
                if gain>0:
                    candidate=original.copy()
                    candidate[start:start+k]=block
                    v=objective(candidate,M)
                    assert v==val+gain
                    if v>best:
                        p=candidate
                        best=v
                        records+=1
                        visited.clear()
                        ranked=rank_windows(p,M)
                        output.write_text(json.dumps({'order':p},separators=(',',':')))
                        print('RECORD',best,'window',start,k,'tested',done,flush=True)
                if done%15==0:print('PROGRESS',done,'best',best,flush=True)
    print('FINAL',best,'windows',done,'records',records,flush=True)

if __name__=='__main__':main()
