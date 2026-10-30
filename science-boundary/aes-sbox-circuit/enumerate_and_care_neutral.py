#!/usr/bin/env python3
"""Enumerate exact AND-care neutral/reducing neighbors of a 101 seed.

This is not random ODC. For every AND y=u&v we exhaust replacements whose
operand agrees with u on the care set v=1. We include an existing earlier wire,
or one newly inserted XOR/XNOR helper. Candidates are retained only when pruning
leaves <=101 total gates, then independently checked on all 256 AES inputs.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census
import mine_and_care_aliases as care

MASK=(1<<256)-1


def sig(c): return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def base_seed(which):
    c=ras.load_circuit('fs-101')
    if which=='care53':
        assert c['gates'][53]['op']=='AND' and c['gates'][53]['b']=='g52'
        vals,_=care.eval_all(c)
        assert ((vals['g52']^vals['g50']) & vals[c['gates'][53]['a']])==0
        c['gates'][53]['b']='g50'; c=ras.prune(c)
    assert len(c['gates'])==101 and ras.independent_check(c)[0]
    return c


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed',choices=['original','care53'],required=True)
    ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--out',required=True);args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    base=base_seed(args.seed);vals,_=care.eval_all(base);base_n=len(base['gates']);seen={sig(base)}
    rows=[];matches=0;tested=0
    for idx,g in enumerate(base['gates']):
        if g['op']!='AND' or idx%args.shards!=args.shard:continue
        earlier=[f'x{i}' for i in range(8)]+[q['out'] for q in base['gates'][:idx]]
        truth_to_wire={}
        for w in earlier:truth_to_wire.setdefault(vals[w],w)
        for side,other_side in (('a','b'),('b','a')):
            u=g[side];other=g[other_side];caremask=vals[other];want=vals[u]&caremask
            for w in earlier:
                if w==u or (vals[w]&caremask)!=want:continue
                matches+=1;nc=care.replace_operand(base,idx,side,w);h=sig(nc)
                if h in seen or len(nc['gates'])>base_n:continue
                assert ras.independent_check(nc)[0];seen.add(h)
                rec={'kind':'direct','and_index':idx,'side':side,'old':u,'replacement':w,
                     'care_bits':caremask.bit_count(),'gates':len(nc['gates']),'sha256':h}
                rows.append((rec,nc))
            for p in range(len(earlier)):
                a=earlier[p];va=vals[a]
                for q in range(p+1,len(earlier)):
                    b=earlier[q];x=va^vals[b]
                    for op,tv in (('XOR',x),('XNOR',x^MASK)):
                        tested+=1
                        if (tv&caremask)!=want or tv in truth_to_wire:continue
                        matches+=1;nc=care.insert_helper(base,idx,side,a,b,op)
                        if len(nc['gates'])>base_n:continue
                        h=sig(nc)
                        if h in seen:continue
                        assert ras.independent_check(nc)[0];seen.add(h)
                        rec={'kind':'helper','and_index':idx,'side':side,'old':u,'a':a,'b':b,'op':op,
                             'care_bits':caremask.bit_count(),'gates':len(nc['gates']),'sha256':h}
                        rows.append((rec,nc))
    rows.sort(key=lambda z:(z[0]['gates'],z[0]['kind'],z[0]['and_index'],z[0]['sha256']))
    for j,(rec,c) in enumerate(rows):
        pathlib.Path(out,f'candidate-{j:04d}-{rec["gates"]}.json').write_text(json.dumps(c,indent=2)+'\n')
    summary={'seed':args.seed,'shard':args.shard,'shards':args.shards,'base_gates':base_n,
             'tested_helper_expressions':tested,'care_matches':matches,'kept_neighbors':len(rows),
             'reducing':sum(r['gates']<base_n for r,_ in rows),'neutral':sum(r['gates']==base_n for r,_ in rows),
             'neighbors':[r for r,_ in rows]}
    pathlib.Path(out,'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
