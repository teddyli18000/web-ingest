#!/usr/bin/env python3
"""Exhaustive radius-2 adjacent-transposition search from verified ta41 baseline.

Commuting swaps (disjoint positions or different machines) need one order.
Overlapping swaps on the same machine are noncommuting and require both.
This enumerates exactly C(580,2) + 20*28 = 168470 distinct
two-step transposition expressions, plus the baseline and one-swap radius.
A cyclic intermediate is allowed; only final graph must be feasible.
"""
import argparse
import json
import time
from pathlib import Path
from search import obtain,setup,evaluate

def run(out):
    routes,durations,orders=obtain()
    pos,dur=setup(routes,durations)
    assert evaluate(orders,pos,dur)==2006
    moves=[(m,k) for m in range(20) for k in range(29)]
    best=2006
    winner=None
    examined=0;cyclic=0
    t=time.monotonic()
    def flip(m,k):
        orders[m][k],orders[m][k+1]=orders[m][k+1],orders[m][k]
    for i,(m,k) in enumerate(moves):
        flip(m,k)
        for j in range(i+1,len(moves)):
            n,l=moves[j]
            flip(n,l)
            val=evaluate(orders,pos,dur)
            examined+=1
            if val is None:cyclic+=1
            elif val<best:
                best=val;winner=[row[:] for row in orders]
                print('IMPROVED',best,'moves',i,j,'iteration',examined,flush=True)
            flip(n,l)
            if n==m and l==k+1:
                flip(m,k)
                flip(n,l)
                flip(m,k)
                val=evaluate(orders,pos,dur)
                examined+=1
                if val is None:cyclic+=1
                elif val<best:
                    best=val;winner=[row[:] for row in orders]
                    print('IMPROVED',best,'moves',j,i,'iteration',examined,flush=True)
                flip(m,k)
                flip(n,l)
                flip(m,k)
            if best<=2005:break
        flip(m,k)
        if i%25==0:
            print('PROGRESS',i,len(moves), 'examined',examined,'best',best,flush=True)
        if best<=2005:break
    expected=len(moves)*(len(moves)-1)//2+20*28
    complete=(examined==expected)
    evidence={
        'baseline':2006,'best':best,'total_examined':examined,
        'expected_radius2_expressions':expected,'complete_radius2':complete,
        'cyclic_final_schedules':cyclic,
        'elapsed_seconds':round(time.monotonic()-t,3),
        'exact_scope':'All <=2 adjacent machine-position swaps from this specific baseline; not arbitrary job shop permutations',
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/'radius2-analysis.json').write_text(json.dumps(evidence,indent=2)+'\n')
    if winner is not None:
        (out/'certificate.json').write_text(json.dumps({'machines':winner},separators=(',',':'))+'\n')
    assert complete or best<=2005,(examined,expected,best)
    print('RESULT',json.dumps(evidence),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'results'/'radius2')
    a=p.parse_args();run(a.out)
