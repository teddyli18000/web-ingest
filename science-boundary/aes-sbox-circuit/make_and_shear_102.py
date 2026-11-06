#!/usr/bin/env python3
"""Build a genuinely nonlinear-basis-distinct 102-gate AES circuit from FS101.

In the merged 101-gate circuit:
 p = g41 AND g45  = g46
 q = g45 AND g47  = g48
 g49 = XNOR(p,q)
 g50 = XNOR(g36,g49)

Use (a&b) XOR (a&c) = a&(b XOR c):
 h = XOR(g41,g47)
 qprime = AND(g45,h) = p XOR q
 q = XOR(p,qprime)
 g50 = XOR(g36,qprime).

This costs 102 gates but changes an AND truth function. It supplies a verified
seed outside the frozen 33-AND truth set of archived 101 neutral rotations.
"""
from __future__ import annotations
import argparse,json,pathlib
import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1

def and_values(c):
    values=census.input_tables(False); ands=set()
    for g in c['gates']:
        a,b=values[g['a']],values[g['b']]
        t=census.op_eval(g['op'],a,b);values[g['out']]=t
        if g['op']=='AND':ands.add(t)
    return ands

def build():
    base=ras.load_circuit('fs-101')
    assert len(base['gates'])==101 and ras.independent_check(base)[0]
    G=base['gates']
    assert (G[46]['op'],G[46]['a'],G[46]['b'])==('AND','g41','g45'),G[46]
    assert (G[48]['op'],G[48]['a'],G[48]['b'])==('AND','g45','g47'),G[48]
    assert (G[49]['op'],G[49]['a'],G[49]['b'])==('XNOR','g46','g48'),G[49]
    assert (G[50]['op'],G[50]['a'],G[50]['b'])==('XNOR','g36','g49'),G[50]
    gs=[]
    for i,g in enumerate(G):
        if i==48:
            gs.extend((
                {'op':'XOR','a':'g41','b':'g47','out':'__and_shear_helper'},
                {'op':'AND','a':'g45','b':'__and_shear_helper','out':'__and_shear_qprime'},
                {'op':'XOR','a':'g46','b':'__and_shear_qprime','out':'g48'},
            ))
        elif i==49:continue
        elif i==50:gs.append({'op':'XOR','a':'g36','b':'__and_shear_qprime','out':'g50'})
        else:gs.append(dict(g))
    transformed=ras.prune({'gates':gs,'outputs':list(base['outputs'])})
    assert len(transformed['gates'])==102
    assert ras.independent_check(transformed)[0]
    A,B=and_values(base),and_values(transformed)
    assert len(A)==len(B)==33 and len(A^B)==2
    return base,transformed,{'base_gates':101,'candidate_gates':102,
                             'base_and_count':33,'candidate_and_count':33,
                             'and_truth_set_symmetric_difference':2,
                             'all_256_verified':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    _base,c,summary=build()
    p=pathlib.Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(c,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__':main()
