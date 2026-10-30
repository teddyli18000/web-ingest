#!/usr/bin/env python3
"""Exact weak-prize screen for nonperfect 4-owner support graphs x raw k5/k6 defects.

For B=I0\R and C subset B define Y_C={z: empty != N[z] cap B subset C}.
For a core rectangle A x C, the unlocked layer is
    T=(Y_A x Y_C) \ (A x C).
We maximize over independent Z subset T the *weak* prize
    |Z| - (# activated oriented private-pair killer colors) - |A||C|.
Every activated oriented killer color forces at least one peripheral loss under
alpha(C7^5)<=367, so this weak prize is an upper bound on the actual ten-
dimensional gain.  Hence weak_prize<=0 rigorously excludes that rectangle.

The script regenerates all connected four-owner supports, independently checks
that exactly 68 are nonperfect (odd hole/antihole, Strong Perfect Graph Theorem),
and screens their products with the unique k5 and four k6 raw +1 defects.
Weighted MaxSAT is exact; four worker processes are intended on GitHub Actions.
"""
from __future__ import annotations
import argparse, itertools, json, multiprocessing as mp, os, sys
from collections import defaultdict, Counter
from pathlib import Path

K5=("k5",(1644,13347,13600,13692,14040))
K6=(
 ("k6_0",(8888,10960,13347,13600,13692,14040)),
 ("k6_1",(1644,11305,13347,13600,13692,14040)),
 ("k6_2",(1644,13248,13347,13600,13692,14040)),
 ("k6_3",(1644,1741,13347,13600,13692,14040)),
)
G={}

def init_worker(state):
    global G; G=state

def is_cycle_subset(sub, adjmask):
    mask=sum(1<<i for i in sub); n=len(sub)
    # connected + every induced degree exactly 2
    for i in sub:
        if (adjmask[i]&mask).bit_count()!=2: return False
    seen=0; stack=[sub[0]]; seen|=1<<sub[0]
    while stack:
        u=stack.pop(); m=adjmask[u]&mask&~seen
        while m:
            b=m&-m; v=b.bit_length()-1; seen|=b; stack.append(v); m-=b
    return (seen&mask)==mask

def nonperfect(vertices, conf):
    n=len(vertices); adj=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if conf(vertices[i],vertices[j]): adj[i]|=1<<j; adj[j]|=1<<i
    full=(1<<n)-1
    cadj=[(full^(1<<i)^adj[i]) for i in range(n)]
    for k in range(5,n+1,2):
        for sub in itertools.combinations(range(n),k):
            if is_cycle_subset(sub,adj) or is_cycle_subset(sub,cadj): return True
    return False

def alpha_of(vals, conf):
    vals=list(dict.fromkeys(vals)); n=len(vals)
    if n<=1:return n
    compat=[0]*n
    for i in range(n):
        for j in range(i+1,n):
            if not conf(vals[i],vals[j]): compat[i]|=1<<j
    best=0
    def dfs(mask,d):
        nonlocal best
        if d+mask.bit_count()<=best:return
        if not mask:
            best=max(best,d);return
        v=(mask&-mask).bit_length()-1
        dfs(mask&~(1<<v),d)
        dfs(mask&compat[v],d+1)
    dfs((1<<n)-1,0);return best

def solve_case(task):
    ai,name,C=task; A=G['nonperfect'][ai]; YC=G['pool'][tuple(C)]; YA=G['pool'][tuple(A)]
    core={(x,y) for x in A for y in C}
    cand=[(x,y) for x in YA for y in YC if (x,y) not in core]
    m=len(cand); from pysat.formula import WCNF
    from pysat.examples.rc2 import RC2
    w=WCNF(); acts={}
    def av(side,color):
        key=(side,color)
        if key not in acts: acts[key]=m+len(acts)+1
        return acts[key]
    # hard conflicts and killer activation
    for i in range(m):
        x,y=cand[i]; kx=G['killer'][x]; ky=G['killer'][y]
        if kx is not None:w.append([-(i+1),av(0,kx)])
        if ky is not None:w.append([-(i+1),av(1,ky)])
    for i in range(m):
        x,y=cand[i]
        for j in range(i+1,m):
            u,v=cand[j]
            if G['conf5'](x,u) and G['conf5'](y,v): w.append([-(i+1),-(j+1)])
    for i in range(m): w.append([i+1],weight=1)
    # all 16 potential oriented colors must contribute the constant correctly
    for side in (0,1):
        for c in range(8): w.append([-av(side,c)],weight=1)
    with RC2(w,solver='g4',adapt=True,exhaust=True,incr=False) as rc2:
        model=rc2.compute(); cost=rc2.cost
    pos=set(z for z in model if z>0); sel=[cand[i] for i in range(m) if i+1 in pos]
    active=[k for k,v in acts.items() if v in pos]
    weak_value=m-cost # = selected - activated
    core_cost=len(A)*len(C); weak_gain=weak_value-core_cost
    # stronger projection-alpha penalty on this exact weak-optimum witness.
    strong_pen=0; detail={}
    for side in (0,1):
        for c in range(8):
            if side==0: vals={y for x,y in sel if G['killer'][x]==c}
            else: vals={x for x,y in sel if G['killer'][y]==c}
            if vals:
                a=alpha_of(sorted(vals),G['conf5']); strong_pen+=a; detail[f'{side}:{c}']={'n':len(vals),'alpha':a}
    strong_witness_gain=len(sel)-core_cost-strong_pen
    return {'A':list(A),'defect':name,'C':list(C),'YA':len(YA),'YC':len(YC),'T':m,
            'selected':len(sel),'active_oriented_killers':len(active),'weak_gain':weak_gain,
            'strong_witness_gain':strong_witness_gain,'strong_penalty':strong_pen,
            'projection_penalties':detail,
            'selected_vertices':[list(z) for z in sel] if weak_gain>0 else []}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('tan_root',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--workers',type=int,default=max(1,min(4,os.cpu_count() or 1)));a=ap.parse_args()
    root=a.tan_root.resolve();sys.path.insert(0,str(root));from shannon.certificates import load_base  # type: ignore
    p=root/'data'/'base_c7.json';raw=json.loads(p.read_text());base,_t,_e,ax=load_base(p)
    if not all(ax.values()):raise RuntimeError({k:v for k,v in ax.items() if not v})
    ring=base.ring; I=set(map(int,raw['I0']));pairs=[tuple(map(int,q)) for q in raw['private_pairs']];R={x for x,_ in pairs};B=I-R
    if len(B)!=359 or len(pairs)!=8:raise RuntimeError(('base drift',len(B),len(pairs)))
    def conf5(x,y):return y in ring.NB[x]
    support={}; groups=defaultdict(list); killer={}
    for z in range(ring.n):
        S=tuple(sorted(ring.NB[z]&B));support[z]=S
        if S:groups[S].append(z)
        ks=[i for i,(u,v) in enumerate(pairs) if u in ring.NB[z] and v in ring.NB[z]]
        if len(ks)>1:raise RuntimeError(('multi-killer',z,ks))
        killer[z]=ks[0] if ks else None
    edges=[frozenset(s) for s in groups if 2<=len(s)<=4]
    inc=defaultdict(list)
    for e in edges:
        for u in e:inc[u].append(e)
    states={e for e in edges if len(e)<=4}
    changed=True
    while changed:
        changed=False
        for S in list(states):
            if len(S)>=4:continue
            cand_edges=set()
            for u in S:cand_edges.update(inc[u])
            for e in cand_edges:
                U=S|e
                if len(U)<=4 and U not in states:states.add(U);changed=True
    fours=sorted(tuple(sorted(s)) for s in states if len(s)==4)
    if len(fours)!=16166:raise RuntimeError(('connected-four count drift',len(fours)))
    def pool(C):
        C=set(C);out=[]
        for S,vs in groups.items():
            if set(S)<=C:out.extend(vs)
        return sorted(set(out))
    pool_cache={C:pool(C) for C in fours}
    defects=[K5,*K6]
    for _,C in defects:pool_cache[tuple(C)]=pool(C)
    nonp=[]
    for C in fours:
        if nonperfect(pool_cache[C],conf5):nonp.append(C)
    if len(nonp)!=68:raise RuntimeError(('nonperfect-four count drift',len(nonp)))
    state={'nonperfect':nonp,'pool':pool_cache,'killer':killer,'conf5':conf5}
    tasks=[(i,name,C) for i in range(len(nonp)) for name,C in defects]
    # ring closures are not pickleable under spawn; Actions/Linux fork keeps state cheaply.
    ctx=mp.get_context('fork')
    with ctx.Pool(a.workers,initializer=init_worker,initargs=(state,)) as P:
        results=list(P.imap_unordered(solve_case,tasks,chunksize=1))
    results.sort(key=lambda r:(-r['weak_gain'],-r['strong_witness_gain'],r['defect'],r['A']))
    hist=Counter(r['weak_gain'] for r in results)
    out={'method':'exact-weak-prize-nonperfect4-x-raw-k5k6','connected_four_sets':len(fours),'nonperfect_four_sets':len(nonp),'rectangles':len(results),
         'weak_gain_histogram':{str(k):v for k,v in sorted(hist.items())},'max_weak_gain':max(r['weak_gain'] for r in results),
         'max_strong_witness_gain':max(r['strong_witness_gain'] for r in results),'positive_weak':[r for r in results if r['weak_gain']>0]}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='positive_weak'},sort_keys=True));print('positive_weak',len(out['positive_weak']))
if __name__=='__main__':main()
