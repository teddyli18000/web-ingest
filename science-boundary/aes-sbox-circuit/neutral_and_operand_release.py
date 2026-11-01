#!/usr/bin/env python3
"""Exact two-step ODC release of an old AND operand in FS101.

Step 1: neutrally refactor an AND root onto any pair of distinct existing earlier
wires whose product matches the original root on its exact full-circuit care
mask.  Step 2: if one of the *old operands* is now a produced non-output wire
with exactly one gate consumer left, exhaust one updated-ODC alias/gate rewrite
of that sole consumer using earlier wires structurally independent of the old
operand.  Pruning then deletes the released old operand gate and yields <=100.

Only the original AND operands can have their fanout decreased by step 1 when no
pruning has yet occurred, so restricting step 2 to them is exact for this stated
two-step dependency-release family and avoids rescanning unrelated fanout-1
wires in every neutral state.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,pathlib,time
import released_and_skeleton as ras
import exact_strict_resub as esr
import seed_family_census as census

OPS=('AND','XOR','XNOR')

def sig(c): return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def replace_and(c,idx,a,b):
    nc={'gates':[dict(g) for g in c['gates']],'outputs':list(c['outputs'])}
    nc['gates'][idx]['a']=a;nc['gates'][idx]['b']=b
    return ras.prune(nc)

def consumers(c,w): return [i for i,g in enumerate(c['gates']) if w in (g['a'],g['b'])]

def independent_earlier(c,ci,victim):
    dep={f'x{i}':False for i in range(8)}; names=[f'x{i}' for i in range(8)]
    for g in c['gates'][:ci]:
        dep[g['out']]=(g['out']==victim) or dep.get(g['a'],False) or dep.get(g['b'],False)
        names.append(g['out'])
    return [w for w in names if w!=victim and not dep.get(w,False)]

def second(c,victim,stats,seen):
    us=consumers(c,victim)
    if victim in c['outputs'] or len(us)!=1:return None
    ci=us[0];g=c['gates'][ci];vals,outs=esr.eval_all(c);care=esr.care_mask(c,ci,outs);target=vals[g['out']]&care
    earlier=independent_earlier(c,ci,victim)
    for w in earlier:
        stats['second_alias_tests']+=1
        if (vals[w]&care)!=target:continue
        nc=esr.alias_gate(c,ci,w);h=sig(nc)
        if h in seen:continue
        seen.add(h)
        if not ras.independent_check(nc)[0]:raise AssertionError(('bad alias',victim,ci,w))
        stats['second_valid']+=1
        if len(nc['gates'])<=100:return nc,{'kind':'alias','victim':victim,'consumer_index':ci,'wire':w,'care_bits':care.bit_count()}
    for ia,a in enumerate(earlier):
        va=vals[a]
        for b in earlier[ia+1:]:
            vb=vals[b]
            for op in OPS:
                stats['second_gate_tests']+=1
                if (census.op_eval(op,va,vb)&care)!=target:continue
                nc=esr.replace_gate(c,ci,op,a,b);h=sig(nc)
                if h in seen:continue
                seen.add(h)
                if not ras.independent_check(nc)[0]:raise AssertionError(('bad gate',victim,ci,op,a,b))
                stats['second_valid']+=1
                if len(nc['gates'])<=100:return nc,{'kind':'gate','victim':victim,'consumer_index':ci,'op':op,'a':a,'b':b,'care_bits':care.bit_count()}
    return None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);ap.add_argument('--out',required=True);args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit('fs-101');assert len(base['gates'])==101 and ras.independent_check(base)[0]
    vals,outs=esr.eval_all(base); produced={g['out'] for g in base['gates']};stats=collections.Counter();seen={sig(base)};best=None;path=None;t0=time.time()
    for idx,g in enumerate(base['gates']):
        if g['op']!='AND' or idx%args.shards!=args.shard:continue
        stats['and_roots']+=1; care=esr.care_mask(base,idx,outs);target=vals[g['out']]&care
        earlier=[f'x{i}' for i in range(8)]+[q['out'] for q in base['gates'][:idx]];old=(g['a'],g['b']);original=set(old)
        for ia,a in enumerate(earlier):
            va=vals[a]
            for b in earlier[ia+1:]:
                stats['first_factor_pairs']+=1
                if {a,b}==original or ((va&vals[b])&care)!=target:continue
                nc=replace_and(base,idx,a,b)
                if len(nc['gates'])<101:
                    if not ras.independent_check(nc)[0]:raise AssertionError(('bad direct',idx,a,b))
                    rec={'first':{'and_index':idx,'a':a,'b':b,'care_bits':care.bit_count()},'second':None,'candidate_gates':len(nc['gates'])}
                    if best is None or len(nc['gates'])<len(best['gates']):best=nc;path=rec
                    if len(nc['gates'])<=100:break
                if len(nc['gates'])!=101:continue
                h=sig(nc)
                if h in seen:continue
                seen.add(h);stats['neutral_first_states']+=1
                if not ras.independent_check(nc)[0]:raise AssertionError(('bad neutral',idx,a,b))
                for victim in dict.fromkeys(old):
                    if victim not in produced or victim in nc['outputs'] or len(consumers(nc,victim))!=1:continue
                    stats['released_operand_candidates']+=1
                    hit=second(nc,victim,stats,seen)
                    if hit is None:continue
                    cand,move=hit;rec={'first':{'and_index':idx,'a':a,'b':b,'care_bits':care.bit_count()},'second':move,'candidate_gates':len(cand['gates'])}
                    if best is None or len(cand['gates'])<len(best['gates']):best=cand;path=rec
                    if len(cand['gates'])<=100:break
                if best is not None and len(best['gates'])<=100:break
            if best is not None and len(best['gates'])<=100:break
        if best is not None and len(best['gates'])<=100:break
    summary={'status':'found' if best is not None and len(best['gates'])<=100 else 'exhausted','shard':args.shard,'shards':args.shards,'source_gates':101,'best_gates':None if best is None else len(best['gates']),'best_path':path,'stats':dict(stats),'states_seen':len(seen),'elapsed_s':round(time.time()-t0,3),'family_scope':'zero-cost existing-wire ODC AND refactor followed by one updated-ODC rewrite releasing an old produced operand whose fanout fell to one'}
    if best is not None:
        (out/'best.json').write_text(json.dumps(best,indent=2)+'\n')
        if len(best['gates'])<=100:(out/'candidate.json').write_text(json.dumps(best,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True),flush=True)
if __name__=='__main__':main()
