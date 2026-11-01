#!/usr/bin/env python3
"""Exact coordinated neutral-consumer retargeting followed by root deletion.

Strict resubstitution only keeps a rewrite when that single move immediately
reduces gate count.  It therefore misses a simple coordinated mechanism:

  1. keep a root temporarily;
  2. retarget each direct consumer to a different two-input gate with exactly
     the same truth table, using wires that no longer depend on the root;
  3. after all consumers are neutral-retargeted, the root becomes dead and is
     pruned, producing a strict one-gate saving.

For every non-output root in FS101 this script exhausts that represented family.
Consumers are processed in topological order.  Once an earlier consumer has
been retargeted, its exact output (and any downstream gates fed only by
root-independent wires) becomes available to later consumers.  Because each
retargeted consumer preserves its *exact* 256-bit truth table, one witness per
consumer is enough and simultaneous rewrites cannot interact semantically.

Candidate gates obey the Few Shots rule of distinct operands and may be AND,
XOR, or XNOR.  Any saving is independently checked on all 256 AES inputs.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import time

import released_and_skeleton as ras
import search_arch_seed as sas

OPS=('AND','XOR','XNOR')


def find_gate(target,earlier,vals):
    tests=0
    for i,a in enumerate(earlier):
        va=vals[a]
        for b in earlier[i+1:]:
            vb=vals[b]
            for op in OPS:
                tests+=1
                if sas.op_eval(op,va,vb)==target:
                    return (op,a,b),tests
    return None,tests


def try_root(c,vals,idx):
    root=c['gates'][idx]['out']
    if root in c['outputs']:
        return None,{'reason':'primary_output','tests':0,'users':0}
    direct=[j for j in range(idx+1,len(c['gates'])) if root in (c['gates'][j]['a'],c['gates'][j]['b'])]
    if not direct:
        return None,{'reason':'no_users','tests':0,'users':0}

    mods=[dict(g) for g in c['gates']]
    independent={f'x{i}':True for i in range(8)}
    for j in range(idx): independent[mods[j]['out']]=True
    independent[root]=False
    direct_set=set(direct); rewrites=[]; tests=0

    for j in range(idx+1,len(mods)):
        q=mods[j]; out=q['out']
        if j in direct_set:
            earlier=[f'x{i}' for i in range(8)] + [mods[k]['out'] for k in range(j) if independent.get(mods[k]['out'],False)]
            wit,n=find_gate(vals[out],earlier,vals);tests+=n
            if wit is None:
                independent[out]=False
                return None,{'reason':'blocked_consumer','blocked_index':j,'tests':tests,'users':len(direct),'rewrites':rewrites}
            op,a,b=wit;mods[j]['op']=op;mods[j]['a']=a;mods[j]['b']=b
            independent[out]=True;rewrites.append({'consumer_index':j,'consumer_out':out,'op':op,'a':a,'b':b})
        else:
            independent[out]=bool(independent.get(q['a'],False) and independent.get(q['b'],False))

    if not all(independent.get(o,False) for o in c['outputs']):
        return None,{'reason':'output_still_depends','tests':tests,'users':len(direct),'rewrites':rewrites}
    nc=ras.prune({'gates':mods,'outputs':list(c['outputs'])})
    if len(nc['gates'])>=len(c['gates']):
        return None,{'reason':'no_prune_saving','tests':tests,'users':len(direct),'rewrites':rewrites}
    ok=ras.independent_check(nc)
    if not ok[0]: raise AssertionError(('neutral fanout retarget produced bad AES',idx,rewrites,ok))
    return nc,{'reason':'found','tests':tests,'users':len(direct),'rewrites':rewrites,'candidate_gates':len(nc['gates'])}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101');assert len(c['gates'])==101 and ras.independent_check(c)[0]
    vals,_outs=sas.eval_circuit(c);rows=[];tot=collections.Counter();t0=time.time();best=None
    for idx,g in enumerate(c['gates']):
        nc,meta=try_root(c,vals,idx);meta={'root_index':idx,'root_out':g['out'],'root_op':g['op'],**meta};rows.append(meta)
        tot['roots']+=1;tot['gate_tests']+=meta.get('tests',0);tot[meta['reason']]+=1
        if nc is not None:
            if best is None or len(nc['gates'])<len(best[0]['gates']): best=(nc,meta)
            p=out/f'candidate-root-{idx}.json';p.write_text(json.dumps(nc,indent=2)+'\n')
            print(json.dumps({'event':'candidate',**meta},sort_keys=True),flush=True)
            if len(nc['gates'])<=100:
                (out/'candidate.json').write_text(json.dumps(nc,indent=2)+'\n')
                break
    summary={'status':'found' if best and len(best[0]['gates'])<=100 else 'exhausted','source_gates':101,
             'best_gates':None if best is None else len(best[0]['gates']),'best_meta':None if best is None else best[1],
             'stats':dict(tot),'rows':rows,'elapsed_s':round(time.time()-t0,3),
             'family_scope':'neutral exact-truth retarget of every direct consumer to root-independent existing wires, followed by root pruning'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__':main()
