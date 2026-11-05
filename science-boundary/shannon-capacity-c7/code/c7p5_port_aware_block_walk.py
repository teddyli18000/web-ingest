#!/usr/bin/env python3
"""Port-aware neutral C7^5 block optimization from a circular 367 code.

A private neighbor z of the incumbent 367-set B has |N[z] ∩ B| = 1.
Count DISTINCT incumbent owners with at least one private neighbor. This is
the exact combinatorial resource exploited by BPZ/Tan fiber-port gadgets.

Rather than optimizing word count alone (already stuck at 367), guide full
adjacent-layer 4D exact MIS moves with a simulated-annealing secondary
objective: maximize distinct private owners while retaining 367 words.
Neighborhood blocker counts and sole-owner XORs update incrementally in
O(243 * changed words), not by recomputing all 367 neighborhoods each move.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
import random
import time
from functools import lru_cache
from pathlib import Path

from c7p5_circular_hall_io import independent, read_circular
from c7p5_two_layer_repair import digits5, enc as enc5, solve_pair, dump_certificate

P=(1,7,49,343,2401)

@lru_cache(maxsize=16807)
def closed_neighborhood(v):
    d=digits5(v)
    return tuple(sum(((d[k]+t[k])%7)*P[k] for k in range(5))
                 for t in itertools.product((-1,0,1),repeat=5))

class PortGeometry:
    def __init__(self,S):
        self.S=set(S)
        self.count=[0]*16807
        self.xor=[0]*16807
        for v in self.S:self._modify(v,+1)
    def _modify(self,v,sign):
        for z in closed_neighborhood(v):
            self.count[z]+=sign
            self.xor[z]^=(v+1)
    def move(self,S):
        rem=self.S-set(S);add=set(S)-self.S
        for v in rem:self._modify(v,-1)
        for v in add:self._modify(v,+1)
        self.S=set(S)
    def counts(self):
        owners=set()
        singletons=0
        for z in range(16807):
            if z not in self.S and self.count[z]==1:
                singletons+=1
                owners.add(self.xor[z]-1)
        return len(owners),singletons

def main():
    p=argparse.ArgumentParser()
    p.add_argument('seed',type=Path)
    p.add_argument('status',type=Path)
    p.add_argument('certificate',type=Path)
    p.add_argument('best_private',type=Path)
    p.add_argument('--random-seed',type=int,default=2026110501)
    p.add_argument('--sweeps',type=int,default=5)
    p.add_argument('--seconds',type=float,default=4.0)
    a=p.parse_args()
    B=set(read_circular(a.seed))
    assert len(B)==367 and independent(sorted(B))
    rng=random.Random(a.random_seed)
    G=PortGeometry(B)
    initial=G.counts()
    assert initial==(6,6),('private owner seed drift',initial)
    cur=initial[0];best_private=cur
    best=B.copy();most_distant=0;seen={frozenset(B)}
    rows=[];t0=time.monotonic()
    for sweep in range(a.sweeps):
        order=list(itertools.product(range(5),range(7)))
        rng.shuffle(order)
        for axis,layer in order:
            before=G.S.copy()
            cand,res=solve_pair(before,axis,layer,rng,a.seconds)
            if len(cand)>=368:
                best=cand.copy()
                dump_certificate(best,a.certificate)
                break
            G.move(cand)
            nowners,nvertices=G.counts()
            # Anneal downward port-count changes so that the combinatorial
            # location, not just the current maximal owner count, can move.
            temp=max(0.18,1.2*(1.0-(sweep/max(a.sweeps,1))))
            accepted=nowners>=cur or rng.random()<math.exp((nowners-cur)/temp)
            if not accepted:
                G.move(before)
                nowners,nvertices=G.counts()
            cur=nowners
            seen.add(frozenset(G.S))
            dist=len(G.S.symmetric_difference(B))
            most_distant=max(most_distant,dist)
            if nowners>best_private:
                best_private=nowners
                best=G.S.copy()
                print('PORT_RECORD',json.dumps({'private_owners':best_private,
                    'private_neighbors':nvertices,'sweep':sweep,
                    'axis':axis,'layer':layer,'changed_points':dist}),flush=True)
            rows.append({'sweep':sweep,'axis':axis,'layer':layer,
                         'ports':nowners,'private_vertices':nvertices,
                         'accepted':accepted,'distance_from_start':dist,
                         'solver_status':res['solver_status']})
        if len(best)>=368:break
    if len(best)==367:
        a.best_private.parent.mkdir(parents=True,exist_ok=True)
        a.best_private.write_text(''.join(f'{v}\n' for v in sorted(best)))
        assert independent(sorted(best))
    out={'method':'port-aware-neutral-C7p5-4D-block-MIS',
         'seed':a.random_seed,'initial_private_owner_count':initial[0],
         'initial_singleton_candidates':initial[1],
         'best_private_owner_count':best_private,
         'best_5d_size':len(best),'candidate_368':len(best)>=368,
         'distinct_states':len(seen),
         'max_symmetric_difference_from_initial':most_distant,
         'solve_count':len(rows),'exact_milps':sum(x['solver_status']==0 for x in rows),
         'time_limit_milps':sum(x['solver_status']==1 for x in rows),
         'elapsed_seconds':time.monotonic()-t0,
         'best_private_points':sorted(best) if len(best)==367 else None,
         'rows':rows}
    a.status.parent.mkdir(parents=True,exist_ok=True)
    a.status.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print('FINAL',json.dumps({k:v for k,v in out.items() if k not in ('best_private_points','rows')},sort_keys=True),flush=True)

if __name__=='__main__':
    main()
