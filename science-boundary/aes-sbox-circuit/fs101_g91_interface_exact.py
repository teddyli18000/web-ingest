#!/usr/bin/env python3
"""Exact direct-100 synthesis of the g91/g93/y4/y5 interface in FS101.

Old non-contiguous four-gate subnetwork after g90:
  g91 = XNOR(g37,g89)
  g93 = XOR(g44,g91)     # feeds later g96
  g94 = XOR(g43,g93)     # AES output y4
  g95 = XOR(g24,g91)     # AES output y5
(g92, producing y3, is independent of this cone and remains untouched.)

A 100-gate circuit exists immediately if the three externally required truth
functions {g93,y4,y5} can be generated with <=3 arbitrary legal two-input gates
from any wire available through g90.  Gate operations are AND/XOR/XNOR and
operands must be distinct, exactly matching the Few Shots verifier.

If none of the three targets is already available at the g90 cut, every gate in
a <=3-gate realization must itself produce one target.  In that common case it
is therefore complete to enumerate all six target topological orders and test
whether each next target is one legal gate from prefix wires plus previously
created targets.  If a target is already free, the script falls back to an
exhaustive one-helper enumeration for the remaining budget.

Any hit is spliced into the full 101-gate record, pruned, independently checked
on all 256 AES inputs, and emitted as a candidate.
"""
from __future__ import annotations

import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import search_arch_seed as sas

MASK=(1<<256)-1
OPS=('AND','XOR','XNOR')
REMOVE={'g91','g93','g94','g95'}
TARGET_OLD=('g93','g94','g95')


def op_eval(op,a,b):
    if op=='AND': return a & b
    if op=='XOR': return a ^ b
    return (a ^ b) ^ MASK


def find_one(target,avail,vals):
    for i,a in enumerate(avail):
        va=vals[a]
        for b in avail[i+1:]:
            vb=vals[b]
            for op in OPS:
                if op_eval(op,va,vb)==target:
                    return (op,a,b)
    return None


def all_one_gate(avail,vals):
    out={}
    for i,a in enumerate(avail):
        va=vals[a]
        for b in avail[i+1:]:
            vb=vals[b]
            for op in OPS:
                v=op_eval(op,va,vb)
                out.setdefault(v,(op,a,b))
    return out


def materialize(c,seq,target_names):
    gates=[]
    inserted=False
    for g in c['gates']:
        if g['out']=='g91' and not inserted:
            for q in seq:
                gates.append({k:q[k] for k in ('op','a','b','out')})
            inserted=True
        if g['out'] in REMOVE:
            continue
        ng=dict(g)
        ng['a']=target_names.get(ng['a'],ng['a'])
        ng['b']=target_names.get(ng['b'],ng['b'])
        gates.append(ng)
    outs=[target_names.get(w,w) for w in c['outputs']]
    full=ras.prune({'gates':gates,'outputs':outs})
    ok=ras.independent_check(full)
    if not ok[0]: raise AssertionError(('g91 interface witness failed AES',ok,seq,target_names))
    return full


def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); args=ap.parse_args()
    outdir=pathlib.Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101'); assert len(c['gates'])==101 and ras.independent_check(c)[0]
    vals,outs=sas.eval_circuit(c)
    cut=next(i for i,g in enumerate(c['gates']) if g['out']=='g90')+1
    prefix_names=[f'x{i}' for i in range(8)]+[g['out'] for g in c['gates'][:cut]]
    prefix_vals={n:vals[n] for n in prefix_names}
    target_truth={w:vals[w] for w in TARGET_OLD}
    free={w:next((n for n in prefix_names if vals[n]==t),None) for w,t in target_truth.items()}
    missing=[w for w in TARGET_OLD if free[w] is None]
    t0=time.time(); tested_orders=0; tested_helpers=0; found=None

    # Case 1: all missing targets can consume the entire gate budget, so every
    # new gate must be one target. Enumerating target orders is complete.
    if len(missing)==3:
        for order in itertools.permutations(missing):
            tested_orders+=1; av=list(prefix_names); vmap=dict(prefix_vals); seq=[]; names={}
            ok=True
            for k,w in enumerate(order):
                hit=find_one(target_truth[w],av,vmap)
                if hit is None:
                    ok=False; break
                op,a,b=hit; nn=f'__gi{k}'; seq.append({'op':op,'a':a,'b':b,'out':nn})
                vmap[nn]=target_truth[w]; av.append(nn); names[w]=nn
            if ok:
                full=materialize(c,seq,names)
                if len(full['gates'])<=100:
                    found=(seq,names,full); break
    else:
        # General <=3-gate fallback.  At most two targets are missing.  Enumerate
        # every possible first helper truth once, then test target orders for the
        # remaining two slots.  Also include the no-helper path.
        base_expr=all_one_gate(prefix_names,prefix_vals)
        helper_options=[(None,None)]+list(base_expr.items())
        for hv,hwit in helper_options:
            if hwit is not None: tested_helpers+=1
            av=list(prefix_names); vmap=dict(prefix_vals); seq=[]; names={w:n for w,n in free.items() if n is not None}
            if hwit is not None:
                op,a,b=hwit; nn='__gi0'; seq.append({'op':op,'a':a,'b':b,'out':nn});vmap[nn]=hv;av.append(nn)
            budget=3-len(seq)
            rem=[w for w in TARGET_OLD if w not in names]
            if len(rem)>budget: continue
            for order in itertools.permutations(rem):
                tested_orders+=1; av2=list(av);v2=dict(vmap);seq2=list(seq);names2=dict(names);ok=True
                for w in order:
                    hit=find_one(target_truth[w],av2,v2)
                    if hit is None: ok=False;break
                    op,a,b=hit;nn=f'__gi{len(seq2)}';seq2.append({'op':op,'a':a,'b':b,'out':nn});v2[nn]=target_truth[w];av2.append(nn);names2[w]=nn
                if not ok: continue
                full=materialize(c,seq2,names2)
                if len(full['gates'])<=100:
                    found=(seq2,names2,full);break
            if found:break

    summary={'status':'found' if found else 'exhausted','cut_gate':cut,'prefix_sources':len(prefix_names),
             'old_removed_gates':4,'target_new_gates':3,'targets':list(TARGET_OLD),'free_targets':free,
             'tested_orders':tested_orders,'tested_helpers':tested_helpers,'elapsed_s':round(time.time()-t0,3),
             'family_scope':'fixed FS101 through g90; replace non-contiguous {g91,g93,g94,g95} by <=3 arbitrary AND/XOR/XNOR gates realizing exact {g93,y4,y5} interface'}
    if found:
        seq,names,full=found;summary.update(candidate_gates=len(full['gates']),verified_all_256=True,sequence=seq,target_names=names,
                                             gate_counts={op:sum(g['op']==op for g in full['gates']) for op in OPS})
        (outdir/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
