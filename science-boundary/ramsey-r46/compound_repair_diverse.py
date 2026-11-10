#!/usr/bin/env python3
"""Conflict cascade and delayed-acceptance compound repair for R(4,6,36)."""
import argparse
import json
import math
import random
import time
from pathlib import Path

N = 36
FULL = (1 << N) - 1
PAIRS = [(i,j) for i in range(N) for j in range(i+1,N)]

class Graph:
    def __init__(self, adj):
        self.a = adj[:]
        self.c4, self.c6 = self.totals()
    def copy(self):
        obj = Graph.__new__(Graph)
        obj.a = self.a[:]
        obj.c4, obj.c6 = self.c4, self.c6
        return obj
    def comps(self):
        return [FULL & ~self.a[i] & ~(1<<i) for i in range(N)]
    @staticmethod
    def count_cliques(adj, cand, k):
        if k == 0: return 1
        count = 0
        while cand.bit_count() >= k:
            b = cand & -cand
            v = b.bit_length()-1
            cand ^= b
            count += Graph.count_cliques(adj, cand & adj[v], k-1)
        return count
    def totals(self):
        return self.count_cliques(self.a,FULL,4),self.count_cliques(self.comps(),FULL,6)
    def witnesses(self, independent=False):
        adj = self.comps() if independent else self.a
        k = 6 if independent else 4
        ans = []
        def rec(cand, chosen):
            if len(chosen)==k:
                ans.append(chosen)
                return
            left = k-len(chosen)
            while cand.bit_count()>=left:
                b=cand&-cand
                v=b.bit_length()-1
                cand^=b
                rec(cand&adj[v],chosen+(v,))
        rec(FULL,())
        return ans
    def delta(self,u,v,comps=None):
        common = self.a[u]&self.a[v]
        k4 = 0
        m = common
        while m:
            b=m&-m
            x=b.bit_length()-1
            m^=b
            k4 += (self.a[x]&m).bit_count()
        if comps is None:comps=self.comps()
        others = FULL & ~self.a[u] & ~self.a[v] & ~(1<<u) & ~(1<<v)
        i6 = self.count_cliques(comps,others,4)
        return (-k4,i6) if self.a[u]>>v&1 else (k4,-i6)
    def flip(self,u,v,delta=None):
        if delta is None:delta=self.delta(u,v)
        self.a[u] ^= 1<<v
        self.a[v] ^= 1<<u
        self.c4 += delta[0]
        self.c6 += delta[1]
    def objective(self):return self.c4+self.c6
    def encode(self):
        return [''.join('1' if self.a[i]>>j&1 else '0' for j in range(N)) for i in range(N)]

def select_actions(g, kind, forbidden, rng, avoid=()):
    choices = {}
    for w in forbidden:
        for i,x in enumerate(w):
            for y in w[i+1:]:
                u,v = (x,y) if x<y else (y,x)
                if (u,v) in avoid:continue
                edge = bool(g.a[u]>>v&1)
                if edge == (kind == 4):
                    choices[(u,v)] = choices.get((u,v),0)+1
    if not choices:return []
    comps=g.comps()
    ranked=[]
    for e,covered in choices.items():
        dk4,di6=g.delta(*e,comps)
        score=g.objective()+dk4+di6
        ranked.append((score,-covered,e,(dk4,di6)))
    ranked.sort(key=lambda x:(x[0],x[1],rng.random()))
    return ranked

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--steps',type=int,default=4000)
    p.add_argument('--depth',type=int,default=6)
    p.add_argument('--seconds',type=float,default=25)
    p.add_argument('--novel-out',type=Path)
    p.add_argument('--min-distance',type=int,default=12)
    p.add_argument('--depth-jitter',type=int,default=10)
    p.add_argument('--cross-rate',type=float,default=0.12)
    p.add_argument('--initial',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    rng=random.Random(args.seed)
    rows=json.loads(args.initial.read_text())['adjacency']
    a=[sum(1<<j for j,c in enumerate(row) if c=='1') for row in rows]
    seed=Graph(a);assert seed.objective()<=14
    global_best=seed.objective()
    elites=[seed.copy()]
    current=seed.copy()
    initial=seed.a[:]
    maxdiv=0
    start=time.monotonic()
    accepted=0;sum_d=0
    for it in range(args.steps):
        if time.monotonic()-start>args.seconds:break
        if it%450==0 and it:
            current=rng.choice(elites[:min(8,len(elites))]).copy()
        before=current.objective()
        state=current.copy()
        if len(elites)>=2 and rng.random()<args.cross_rate:
            other=rng.choice(elites[1:])
            differing=[(u,v) for u,v in PAIRS
                       if ((state.a[u]>>v)&1)!=((other.a[u]>>v)&1)]
            for u,v in rng.sample(differing,min(len(differing),rng.randint(3,12))):
                state.flip(u,v)
        witness4=state.witnesses(False)
        witness6=state.witnesses(True)
        kind=4 if rng.random()<(.5 if not witness4 or not witness6 else len(witness4)/(len(witness4)+len(witness6))) else 6
        if kind==4 and not witness4:kind=6
        if kind==6 and not witness6:kind=4
        actions=select_actions(state,kind,witness4 if kind==4 else witness6,rng)
        if not actions:continue
        selected=actions[rng.randrange(min(len(actions),min(4,1+it%3)))]
        state.flip(*selected[2],selected[3])
        tabu=[selected[2]]
        for depth in range(args.depth+rng.randrange(args.depth_jitter+1)):
            if state.objective()<global_best:
                global_best=state.objective()
                k4,i6=state.totals()
                assert (k4,i6)==(state.c4,state.c6)
                args.out.write_text(json.dumps({'adjacency':state.encode()},indent=1))
                print('BREAK',it,depth,global_best,state.c4,state.c6,'elapsed',round(time.monotonic()-start,2),flush=True)
                elites.insert(0,state.copy());elites=elites[:12]
                if global_best==0:return
            candidates=[]
            for k,ws in ((4,state.witnesses(False)),(6,state.witnesses(True))):
                if not ws:continue
                # Repair the type of violation created by the previous move,
                # but permit switching priority as the bottleneck migrates.
                candidates += select_actions(state,k,ws,rng,tabu[-2:])[:12]
            if not candidates:break
            candidates.sort(key=lambda z:(z[0],z[1],rng.random()))
            chosen=candidates[rng.randrange(min(6,1+(depth%4)))]
            state.flip(*chosen[2],chosen[3]);tabu.append(chosen[2])
        new=state.objective()
        if new<=global_best and args.novel_out:
            distance=sum((state.a[i]^initial[i]).bit_count() for i in range(N))//2
            if distance>=args.min_distance and distance>maxdiv:
                k4,i6=state.totals()
                assert (k4,i6)==(state.c4,state.c6)
                maxdiv=distance
                args.novel_out.write_text(json.dumps({'adjacency':state.encode()},indent=1))
                print('DIVERSE',it,'score',new,'K4',k4,'I6',i6,'distance',distance,
                      'elapsed',round(time.monotonic()-start,2),flush=True)
        if new<global_best:
            global_best=new
            k4,i6=state.totals()
            assert (k4,i6)==(state.c4,state.c6)
            args.out.write_text(json.dumps({'adjacency':state.encode()},indent=1))
            print('BREAK_END',it,global_best,k4,i6,flush=True)
        temperature=0.6+2.0*(1-(it%500)/500)
        if new<=before or rng.random()<math.exp(min(0,(before-new)/temperature)):
            current=state;accepted+=1
            if new <= global_best+1 and all(
                sum((g.a[i]^state.a[i]).bit_count() for i in range(N))//2
                >= max(4,args.min_distance//2) for g in elites):
                elites.append(state.copy())
                elites.sort(key=lambda x:x.objective())
                elites=elites[:12]
        if it%200==0:
            print('PROGRESS',it,'best',global_best,'current',current.objective(),'accepted',accepted,flush=True)
        if it%100==0:
            assert current.totals()==(current.c4,current.c6)
    print('SUMMARY',json.dumps({'iterations':it+1,'best':global_best,'accepted':accepted,'seconds':round(time.monotonic()-start,2),'max_diverse_distance':maxdiv}))
if __name__=='__main__':main()
