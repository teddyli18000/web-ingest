#!/usr/bin/env python3
"""Exact two-step ODC dependency-release search from the 101-gate AES record.

The known 102->101 breakthrough used a care-equivalent cross-boundary AND operand
reuse that made an older linear computation unnecessary.  Strict one-step resub
can miss the next analogous improvement when a neutral refactor merely *reduces*
a wire's fanout and a second neutral rewrite is needed to kill the wire.

This script exhausts a minimal coordinated family on FS101:

  1. choose an AND root and replace both of its operands by any pair of distinct
     existing earlier wires whose product agrees with the original AND output on
     that root's exact full-circuit observability mask; no helper gates are added;
  2. after the neutral refactor, inspect every non-output wire with exactly one
     remaining gate consumer; exhaust aliasing or replacing that sole consumer by
     any root-independent earlier expression in {AND,XOR,XNOR} that agrees with
     the consumer on its *updated* exact observability mask;
  3. prune.  If the released wire dies, the full circuit loses at least one gate.

Every intermediate and final circuit is independently checked on all 256 inputs.
The search is sharded by the first AND root.  Exhaustion is exact only for this
represented two-step family (existing-wire AND refactor followed by one sole-
consumer ODC retarget); it is not a lower bound for unrestricted circuits.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import time

import released_and_skeleton as ras
import exact_strict_resub as esr
import seed_family_census as census

OPS=('AND','XOR','XNOR')


def sig(c):
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def replace_and(c,idx,a,b):
    nc={'gates':[dict(g) for g in c['gates']],'outputs':list(c['outputs'])}
    nc['gates'][idx]['a']=a;nc['gates'][idx]['b']=b
    return ras.prune(nc)


def gate_consumers(c,wire):
    return [i for i,g in enumerate(c['gates']) if wire in (g['a'],g['b'])]


def root_independent_earlier(c,consumer_idx,victim):
    dep={f'x{i}':False for i in range(8)}
    names=[f'x{i}' for i in range(8)]
    for i,g in enumerate(c['gates'][:consumer_idx]):
        d=(g['out']==victim) or dep.get(g['a'],False) or dep.get(g['b'],False)
        dep[g['out']]=d;names.append(g['out'])
    return [w for w in names if not dep.get(w,False) and w!=victim]


def second_step(c,victim,stats,seen):
    """Exhaust one ODC rewrite of victim's sole gate consumer."""
    users=gate_consumers(c,victim)
    if victim in c['outputs'] or len(users)!=1:return None
    ci=users[0];g=c['gates'][ci]
    vals,outs=esr.eval_all(c);care=esr.care_mask(c,ci,outs);target=vals[g['out']] & care
    earlier=root_independent_earlier(c,ci,victim)

    # Alias the consumer itself to an earlier root-independent wire.
    for w in earlier:
        stats['second_alias_tests']+=1
        if (vals[w]&care)!=target:continue
        nc=esr.alias_gate(c,ci,w)
        h=sig(nc)
        if h in seen:continue
        seen.add(h)
        if not ras.independent_check(nc)[0]:raise AssertionError(('bad second alias',victim,ci,w))
        stats['second_valid']+=1
        if len(nc['gates'])<=100:return nc,{'kind':'alias','victim':victim,'consumer_index':ci,'wire':w,'care_bits':care.bit_count()}

    # Same-count consumer retarget.  Operands are distinct to match verifier.
    for ia,a in enumerate(earlier):
        va=vals[a]
        for b in earlier[ia+1:]:
            vb=vals[b]
            for op in OPS:
                stats['second_gate_tests']+=1
                if (census.op_eval(op,va,vb)&care)!=target:continue
                nc=esr.replace_gate(c,ci,op,a,b)
                h=sig(nc)
                if h in seen:continue
                seen.add(h)
                if not ras.independent_check(nc)[0]:raise AssertionError(('bad second gate',victim,ci,op,a,b))
                stats['second_valid']+=1
                if len(nc['gates'])<=100:
                    return nc,{'kind':'gate','victim':victim,'consumer_index':ci,'op':op,'a':a,'b':b,'care_bits':care.bit_count()}
    return None


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--shard',type=int,default=0);ap.add_argument('--shards',type=int,default=1);ap.add_argument('--out',required=True);args=ap.parse_args()
    outdir=pathlib.Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    base=ras.load_circuit('fs-101');assert len(base['gates'])==101 and ras.independent_check(base)[0]
    vals,outs=esr.eval_all(base);stats=collections.Counter();seen={sig(base)};best=None;best_path=None;t0=time.time()

    for idx,g in enumerate(base['gates']):
        if g['op']!='AND' or (idx%args.shards)!=args.shard:continue
        stats['and_roots']+=1
        care=esr.care_mask(base,idx,outs);target=vals[g['out']]&care
        earlier=[f'x{i}' for i in range(8)]+[q['out'] for q in base['gates'][:idx]]
        original={g['a'],g['b']}
        for ia,a in enumerate(earlier):
            va=vals[a]
            for b in earlier[ia+1:]:
                stats['first_factor_pairs']+=1
                if {a,b}==original:continue
                if ((va&vals[b])&care)!=target:continue
                nc=replace_and(base,idx,a,b)
                if len(nc['gates'])<101:
                    if not ras.independent_check(nc)[0]:raise AssertionError(('bad first direct',idx,a,b))
                    rec={'first':{'and_index':idx,'a':a,'b':b,'care_bits':care.bit_count()},'second':None,'candidate_gates':len(nc['gates'])}
                    if best is None or len(nc['gates'])<len(best['gates']):best=nc;best_path=rec
                    if len(nc['gates'])<=100:break
                if len(nc['gates'])!=101:continue
                h=sig(nc)
                if h in seen:continue
                seen.add(h);stats['neutral_first_states']+=1
                if not ras.independent_check(nc)[0]:raise AssertionError(('bad neutral first',idx,a,b))

                # Only wires whose fanout is now exactly one can be released by
                # the represented single second rewrite.  Scan all gates rather
                # than only the original AND operands because pruning/aliasing of
                # equal signals may expose a different victim.
                fan=collections.Counter()
                for q in nc['gates']:
                    fan[q['a']]+=1;fan[q['b']]+=1
                for q in nc['gates']:
                    w=q['out']
                    if w in nc['outputs'] or fan[w]!=1:continue
                    stats['fanout1_victims']+=1
                    hit=second_step(nc,w,stats,seen)
                    if hit is None:continue
                    cand,move=hit
                    rec={'first':{'and_index':idx,'a':a,'b':b,'care_bits':care.bit_count()},'second':move,'candidate_gates':len(cand['gates'])}
                    if best is None or len(cand['gates'])<len(best['gates']):best=cand;best_path=rec
                    if len(cand['gates'])<=100:break
                if best is not None and len(best['gates'])<=100:break
            if best is not None and len(best['gates'])<=100:break
        if best is not None and len(best['gates'])<=100:break

    summary={'status':'found' if best is not None and len(best['gates'])<=100 else 'exhausted','shard':args.shard,'shards':args.shards,
             'source_gates':101,'best_gates':None if best is None else len(best['gates']),'best_path':best_path,'stats':dict(stats),
             'states_seen':len(seen),'elapsed_s':round(time.time()-t0,3),
             'family_scope':'existing-wire ODC-equivalent AND refactor, then one updated-ODC rewrite of a sole remaining consumer to release a fanout-1 wire'}
    if best is not None:
        (outdir/'best.json').write_text(json.dumps(best,indent=2)+'\n')
        if len(best['gates'])<=100:(outdir/'candidate.json').write_text(json.dumps(best,indent=2)+'\n')
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
