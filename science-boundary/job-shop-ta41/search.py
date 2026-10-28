#!/usr/bin/env python3
"""Reproducible ta41 critical-path tabu search; standard library only."""
import argparse, ast, hashlib, json, random, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RAW="https://raw.githubusercontent.com/few-shots/few-shots/main/problems/p009-job-shop-ta41/"
def obtain():
    def read(path):
        with urllib.request.urlopen(RAW+path,timeout=40) as r: return r.read().decode()
    src=read("verify/verify.py")
    import re
    instance=ast.literal_eval(re.search(r'^INSTANCE = ("""[\s\S]*?""")',src,re.M).group(1))
    assert hashlib.sha256(instance.encode("ascii")).hexdigest()=="fec53111ca4624c4095e10cd92a4f3f3201414705c6ffff18a20c0a9ec1f5789"
    rows=[[int(x) for x in line.split()] for line in instance.splitlines()[1:]]
    routes=[x[::2] for x in rows]; durations=[x[1::2] for x in rows]
    orders=json.loads(read("baseline/certificate.json"))["machines"]
    return routes,durations,orders

def setup(routes,durs):
    pos=[[0]*20 for _ in range(30)]
    duration=[0]*600
    for j in range(30):
        for k,m in enumerate(routes[j]):
            pos[j][m]=k;duration[j*20+k]=durs[j][k]
    return pos,duration

def evaluate(orders,pos,duration,trace=False):
    pred=[-1]*600; succ=[-1]*600
    for m,order in enumerate(orders):
        for a,b in zip(order,order[1:]):
            u=a*20+pos[a][m];v=b*20+pos[b][m]
            succ[u]=v;pred[v]=u
    deg=[int(i%20!=0)+int(pred[i]>=0) for i in range(600)]
    ready=[i for i in range(600) if deg[i]==0]
    starts=[0]*600;parent=[-1]*600;done=0;end=0;tail=-1
    while ready:
        u=ready.pop();done+=1
        finish=starts[u]+duration[u]
        if finish>end: end=finish;tail=u
        for v in ((u+1) if u%20!=19 else -1,succ[u]):
            if v<0:continue
            if finish>starts[v]:starts[v]=finish;parent[v]=u
            deg[v]-=1
            if deg[v]==0:ready.append(v)
    if done<600:return None
    if not trace:return end
    critical=[]
    while tail>=0:
        critical.append(tail);tail=parent[tail]
    critical.reverse()
    return end,critical

def critical_moves(orders,pos,critical):
    index={}
    for m,order in enumerate(orders):
        for k,j in enumerate(order):index[j*20+pos[j][m]]=(m,k)
    moves=set()
    for u,v in zip(critical,critical[1:]):
        m,k=index[u]; mm,kk=index[v]
        if m==mm and kk==k+1:moves.add((m,k))
    return list(moves)

def solve(routes,durs,baseline,seconds,seed,out):
    rng=random.Random(seed);pos,duration=setup(routes,durs)
    base=evaluate(baseline,pos,duration)
    assert base==2006, f"baseline mismatch {base}"
    current=[x[:] for x in baseline];current_score=base
    best=[x[:] for x in current];best_score=base
    tabu={};step=0;stagnation=0;start=time.monotonic()
    last_report=start
    while time.monotonic()-start<seconds:
        state=evaluate(current,pos,duration,True)
        if state is None:raise AssertionError("current state is cyclic")
        score,critical=state
        moves=critical_moves(current,pos,critical)
        rng.shuffle(moves)
        candidates=[]
        for m,k in moves:
            a,b=current[m][k:k+2]
            current[m][k:k+2]=[b,a]
            val=evaluate(current,pos,duration)
            current[m][k:k+2]=[a,b]
            if val is not None and (tabu.get((m,b,a),0)<=step or val<best_score):
                candidates.append((val,rng.random(),m,k,a,b))
        if candidates:
            val,_,m,k,a,b=min(candidates)
            current[m][k:k+2]=[b,a]
            current_score=val;step+=1
            tabu[(m,a,b)]=step+rng.randint(8,24)
        else:
            stagnation+=1
        if current_score<best_score:
            best_score=current_score;best=[x[:] for x in current];stagnation=0
            save(out,best,best_score,seed,step,base)
            print(f"best {best_score} step {step} elapsed {time.monotonic()-start:.1f}",flush=True)
        else:stagnation+=1
        if stagnation>max(200,6*len(moves)):
            if rng.random()<0.65: current=[x[:] for x in best]
            else:current=[x[:] for x in baseline]
            # Random noncritical swaps also enable jumps across critical-path basins
            for _ in range(rng.randrange(2,18)):
                m=rng.randrange(20);k=rng.randrange(29)
                current[m][k],current[m][k+1]=current[m][k+1],current[m][k]
                if evaluate(current,pos,duration) is None:
                    current[m][k],current[m][k+1]=current[m][k+1],current[m][k]
            current_score=evaluate(current,pos,duration)
            tabu.clear();stagnation=0
        if time.monotonic()-last_report>=60:
            print(f"heartbeat best={best_score} current={current_score} steps={step}",flush=True)
            last_report=time.monotonic()
    if best_score==base:save(out,best,best_score,seed,step,base)
    assert evaluate(best,pos,duration)==best_score
    print(f"RESULT best={best_score} baseline={base} steps={step}",flush=True)

def save(out,orders,score,seed,steps,baseline):
    out.mkdir(parents=True,exist_ok=True)
    (out/"certificate.json").write_text(json.dumps({"machines":orders},separators=(",",":"))+"\n")
    (out/"search-result.json").write_text(json.dumps(dict(score=score,seed=seed,steps=steps,baseline=baseline),indent=2)+"\n")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=int,default=300)
    p.add_argument("--seed",type=int,default=41)
    p.add_argument("--output",type=Path,default=ROOT/"results"/"run")
    a=p.parse_args()
    solve(*obtain(),a.seconds,a.seed,a.output)
