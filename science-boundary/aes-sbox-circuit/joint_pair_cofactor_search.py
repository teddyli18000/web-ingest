#!/usr/bin/env python3
"""Direct-100 coupled two-root substitution via joint observability.

For roots i<j, force both to 0 and both to 1, evaluate the entire
AES circuit on all 256 inputs, and derive the exact care constraints on
a shared replacement h. Search aliases and all single AND/XOR/XNOR
helpers available before root i. Individual-root ODC is NOT assumed.
Exhaustion is restricted to this one-shared-signal family, with no
remaining degenerate same-operand gates.
"""
from __future__ import annotations
import argparse
import collections
import json
import pathlib
import time
import released_and_skeleton as ras
import search_arch_seed as sas

MASK=(1<<256)-1
OPS=('AND','XOR','XNOR')

def op_eval(op,a,b):
    if op=='AND': return a&b
    if op=='XOR': return a^b
    return (a^b)^MASK

def evaluate(c,inputs,i=None,j=None,forced=0):
    vals=dict(inputs)
    for k,g in enumerate(c['gates']):
        vals[g['out']]=forced if k==i or k==j else op_eval(g['op'],vals[g['a']],vals[g['b']])
    return vals,[vals[w] for w in c['outputs']]

def joint_care(target,out0,out1):
    good0=MASK; good1=MASK
    for orig,zero,one in zip(target,out0,out1):
        good0 &= MASK^(orig^zero)
        good1 &= MASK^(orig^one)
    if (good0|good1)!=MASK: return None
    return good1 & (MASK^good0), good0^good1

def helpers(names,vals):
    known={vals[w] for w in names}
    out={}; tests=0
    for ia,a in enumerate(names):
        for b in names[ia+1:]:
            for op in OPS:
                tests+=1; v=op_eval(op,vals[a],vals[b])
                if v not in known: out.setdefault(v,(op,a,b))
    return out,tests

def rebuild(c,i,j,witness):
    op,a,b=witness
    old={c['gates'][i]['out'],c['gates'][j]['out']}
    h=a if op=='ALIAS' else '__joint_pair_shared'
    gates=[]
    for k,g in enumerate(c['gates']):
        if k==i and op!='ALIAS': gates.append({'op':op,'a':a,'b':b,'out':h})
        if k in (i,j): continue
        row=dict(g)
        row['a']=h if row['a'] in old else row['a']
        row['b']=h if row['b'] in old else row['b']
        gates.append(row)
    outs=[h if w in old else w for w in c['outputs']]
    full=ras.prune({'gates':gates,'outputs':outs})
    if any(g['a']==g['b'] for g in full['gates']): return None
    return full

def self_check(c,inputs):
    """Algebraic cofactor-vs-direct-intervention calibration."""
    for i,j in [(2,13),(11,35),(30,90)]:
        _,out0=evaluate(c,inputs,i,j,0)
        _,out1=evaluate(c,inputs,i,j,MASK)
        vals=dict(inputs)
        h=inputs['x0']
        for k,g in enumerate(c['gates']):
            vals[g['out']]=h if k in (i,j) else op_eval(g['op'],vals[g['a']],vals[g['b']])
        direct=[vals[w] for w in c['outputs']]
        predicted=[(a&(MASK^h))|(b&h) for a,b in zip(out0,out1)]
        assert predicted==direct,('cofactor calibration',i,j)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',default='fs-101')
    ap.add_argument('--shard',type=int,default=0)
    ap.add_argument('--shards',type=int,default=8)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit(args.source)
    assert len(c['gates'])==101 and ras.independent_check(c)[0]
    inputs=sas.inputs_truth()
    base,target=evaluate(c,inputs)
    self_check(c,inputs)
    stats=collections.Counter();best=None;first=None;t0=time.monotonic()
    for i in range(len(c['gates'])-1):
        if i%args.shards!=args.shard: continue
        stats['first_roots']+=1
        earlier=[f'x{k}' for k in range(8)]+[g['out'] for g in c['gates'][:i]]
        cand,nexp=helpers(earlier,base)
        stats['helper_expressions']+=nexp
        stats['distinct_helpers']+=len(cand)
        for j in range(i+1,len(c['gates'])):
            stats['root_pairs']+=1
            _,o0=evaluate(c,inputs,i,j,0)
            _,o1=evaluate(c,inputs,i,j,MASK)
            res=joint_care(target,o0,o1)
            if res is None: continue
            stats['jointly_admissible_pairs']+=1
            must1,care=res
            if first is None: first={'i':i,'j':j,'care_bits':care.bit_count()}
            for wire in earlier:
                stats['alias_checks']+=1
                if (base[wire]&care)!=must1: continue
                stats['matching_aliases']+=1
                full=rebuild(c,i,j,('ALIAS',wire,''))
                if full is None: stats['same_operand_rejects']+=1;continue
                if not ras.independent_check(full)[0]: stats['verification_rejects']+=1;continue
                best=(full,{'i':i,'j':j,'alias':wire,'care_bits':care.bit_count()});break
            if best:break
            for h,wit in cand.items():
                stats['helper_checks']+=1
                if (h&care)!=must1:continue
                stats['matching_helpers']+=1
                full=rebuild(c,i,j,wit)
                if full is None:stats['same_operand_rejects']+=1;continue
                if not ras.independent_check(full)[0]:stats['verification_rejects']+=1;continue
                best=(full,{'i':i,'j':j,'helper':wit,'care_bits':care.bit_count()});break
            if best:break
        if best:break
    result={'source':args.source,'shard':args.shard,'shards':args.shards,
            'status':'found' if best else 'exhausted',
            'first_jointly_admissible':first,'stats':dict(stats),
            'elapsed_s':round(time.monotonic()-t0,3),
            'scope':'joint two-root replace by one earlier existing wire or new AND/XOR/XNOR helper, with no surviving repeated-operand gates'}
    if best:
        full,witness=best
        assert len(full['gates'])<=100
        result.update(candidate_gates=len(full['gates']),witness=witness,verified_all_256=True)
        (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True),flush=True)

if __name__=='__main__':main()
