#!/usr/bin/env python3
"""Exhaust exact cross-boundary substitutions at every AND input.

For y=u&v, replacing u by w is exact iff (u XOR w)&v == 0.  This is the
algebraic pattern behind the final 102->101 saving in PR #31.  We enumerate it
for complete circuits rather than respecting any named decomposition boundary.

We also enumerate a newly inserted one-gate affine helper op(a,b) when replacing
an AND operand.  Such a rewrite is retained only if pruning removes at least two
old gates, so the total circuit strictly shrinks despite the new helper.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, pathlib
import released_and_skeleton as ras
import seed_family_census as census

MASK=(1<<256)-1
OPS=('XOR','XNOR')

def eval_all(c):
    vals=census.input_tables(False); order=[f'x{i}' for i in range(8)]
    for g in c['gates']:
        vals[g['out']]=census.op_eval(g['op'],vals[g['a']],vals[g['b']]);order.append(g['out'])
    return vals,order

def replace_operand(c,idx,side,w):
    nc={'gates':[dict(g) for g in c['gates']],'outputs':list(c['outputs'])}
    nc['gates'][idx][side]=w
    return ras.prune(nc)

def insert_helper(c,idx,side,a,b,op):
    nc={'gates':[dict(g) for g in c['gates']],'outputs':list(c['outputs'])}
    h='__care_helper__'; assert h not in {g['out'] for g in nc['gates']}
    nc['gates'].insert(idx,{'op':op,'a':a,'b':b,'out':h})
    nc['gates'][idx+1][side]=h
    return ras.prune(nc)

def sig(c):return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seed-family',choices=sorted(ras.SOURCES),required=True)
    ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--out',required=True);ap.add_argument('--neutral-limit',type=int,default=20)
    args=ap.parse_args();outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit(args.seed_family);assert ras.independent_check(base)[0]
    vals,_=eval_all(base);base_n=len(base['gates']);best=base;seen={sig(base)}
    direct_matches=0;helper_matches=0;reductions=[];neutral=[];tested_helpers=0
    for idx,g in enumerate(base['gates']):
        if g['op']!='AND' or (idx%args.shards)!=args.shard:continue
        earlier=[f'x{i}' for i in range(8)]+[q['out'] for q in base['gates'][:idx]]
        truth_to_wire={}
        for w in earlier:truth_to_wire.setdefault(vals[w],w)
        for side,other_side in (('a','b'),('b','a')):
            u=g[side];other=g[other_side];care=vals[other];want=vals[u]&care
            # Exact existing-wire aliases on the other AND input's care set.
            for w in earlier:
                if w==u:continue
                if (vals[w]&care)!=want:continue
                direct_matches+=1;nc=replace_operand(base,idx,side,w);h=sig(nc)
                if h in seen:continue
                seen.add(h);assert ras.independent_check(nc)[0]
                rec={'kind':'direct','and_index':idx,'side':side,'old':u,'replacement':w,'care_bits':care.bit_count(),'gates':len(nc['gates'])}
                if len(nc['gates'])<base_n:
                    reductions.append(rec)
                    if len(nc['gates'])<len(best['gates']):best=nc
                elif len(nc['gates'])==base_n and len(neutral)<args.neutral_limit:neutral.append(rec)
            # One newly synthesized affine helper.  Enumerate each unordered pair once.
            for p in range(len(earlier)):
                a=earlier[p];va=vals[a]
                for q in range(p+1,len(earlier)):
                    b=earlier[q];vb=vals[b]
                    x=va^vb
                    for op,tv in (('XOR',x),('XNOR',x^MASK)):
                        tested_helpers+=1
                        if (tv&care)!=want:continue
                        # Existing function is already covered by direct alias enumeration.
                        if tv in truth_to_wire:continue
                        helper_matches+=1
                        nc=insert_helper(base,idx,side,a,b,op)
                        # Adding one helper must kill >=2 old gates for a strict reduction.
                        if len(nc['gates'])>=base_n:continue
                        h=sig(nc)
                        if h in seen:continue
                        seen.add(h);assert ras.independent_check(nc)[0]
                        rec={'kind':'one_helper','and_index':idx,'side':side,'old':u,'a':a,'b':b,'op':op,'care_bits':care.bit_count(),'gates':len(nc['gates'])}
                        reductions.append(rec)
                        if len(nc['gates'])<len(best['gates']):best=nc
    json.dump(best,open(outdir/'best.json','w'),indent=2)
    summary={'seed_family':args.seed_family,'shard':args.shard,'shards':args.shards,'base_gates':base_n,'best_gates':len(best['gates']),
             'direct_matches':direct_matches,'one_helper_care_matches':helper_matches,'tested_helper_expressions':tested_helpers,
             'strict_reductions':sorted(reductions,key=lambda x:x['gates']),'neutral_examples':neutral,'verified_best':ras.independent_check(best)[0]}
    json.dump(summary,open(outdir/'summary.json','w'),indent=2);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
