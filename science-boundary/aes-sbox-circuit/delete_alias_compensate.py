#!/usr/bin/env python3
"""Direct-100 coupled search: delete an earlier gate by alias and retarget a later gate.

The first edit may break AES. A changed later gate is synthesized against
the exact output cofactor care under that broken circuit. Exhaustive for
one earlier-wire alias deletion plus one legal later AND/XOR/XNOR replacement,
with all other gates fixed, modulo equivalent prior signal values.
"""
from __future__ import annotations
import argparse, collections, json, pathlib, time
import released_and_skeleton as ras
import search_arch_seed as sas
MASK=(1<<256)-1
OPS=('AND','XOR','XNOR')

def op_eval(op,a,b):
    if op=='AND':return a&b
    if op=='XOR':return a^b
    return a^b^MASK

def evaluate(c,inputs,drop_i=None,alias=None):
    v=dict(inputs)
    for k,g in enumerate(c['gates']):
        v[g['out']]=v[alias] if k==drop_i else op_eval(g['op'],v[g['a']],v[g['b']])
    return v,[v[w] for w in c['outputs']]

def cofactor_after_j(c,mutvals,j,forced):
    vals=dict(mutvals)
    vals[c['gates'][j]['out']]=forced
    for g in c['gates'][j+1:]:
        vals[g['out']]=op_eval(g['op'],vals[g['a']],vals[g['b']])
    return [vals[w] for w in c['outputs']]

def care_for_repair(target,o0,o1):
    good0=good1=MASK
    for orig,a,b in zip(target,o0,o1):
        good0 &= MASK^(orig^a)
        good1 &= MASK^(orig^b)
    if (good0|good1)!=MASK:return None
    return good1&(MASK^good0),good0^good1

def rebuild(c,i,alias,j=None,replacement=None):
    old=c['gates'][i]['out'];gates=[]
    for k,g in enumerate(c['gates']):
        if k==i:continue
        row=dict(g)
        if k==j:
            op,a,b=replacement
            row.update(op=op,a=a,b=b)
        row['a']=alias if row['a']==old else row['a']
        row['b']=alias if row['b']==old else row['b']
        gates.append(row)
    outs=[alias if w==old else w for w in c['outputs']]
    full=ras.prune({'gates':gates,'outputs':outs})
    if any(g['a']==g['b'] for g in full['gates']):return None
    return full

def candidates_before_j(c,modified,i,j):
    names=[f'x{x}' for x in range(8)]+[g['out'] for k,g in enumerate(c['gates'][:j]) if k!=i]
    by_value={}
    for w in names:by_value.setdefault(modified[w],[]).append(w)
    vals=list(by_value.items())
    for ia,(va,na) in enumerate(vals):
        if len(na)>1:
            for op in OPS:yield op,na[0],na[1],op_eval(op,va,va)
        for vb,nb in vals[ia+1:]:
            for op in OPS:yield op,na[0],nb[0],op_eval(op,va,vb)

def self_test(inputs):
    toy={'gates':[{'op':'AND','a':'x0','b':'x1','out':'a'},
                  {'op':'AND','a':'a','b':'x0','out':'b'}],'outputs':['b']}
    _,goal=evaluate(toy,inputs)
    changed,_=evaluate(toy,inputs,drop_i=0,alias='x0')
    z=cofactor_after_j(toy,changed,1,0)
    o=cofactor_after_j(toy,changed,1,MASK)
    req=care_for_repair(goal,z,o)
    assert req is not None
    must1,care=req
    assert ((inputs['x0']&inputs['x1'])&care)==must1
    full=rebuild(toy,0,'x0',1,('AND','x0','x1'))
    _,result=evaluate(full,inputs)
    assert result==goal and len(full['gates'])==1

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',default='fs-101')
    ap.add_argument('--shard',type=int,default=0)
    ap.add_argument('--shards',type=int,default=8)
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    inputs=sas.inputs_truth();self_test(inputs)
    c=ras.load_circuit(args.source)
    assert len(c['gates'])==101 and ras.independent_check(c)[0]
    base,goal=evaluate(c,inputs)
    stats=collections.Counter();best=None;first=None;t0=time.monotonic()
    for i in range(len(c['gates'])):
        if i%args.shards!=args.shard:continue
        stats['deletion_roots']+=1
        earlier=[f'x{k}' for k in range(8)]+[g['out'] for g in c['gates'][:i]]
        aliases={}
        for w in earlier:aliases.setdefault(base[w],w)
        for alias in aliases.values():
            stats['alias_cases']+=1
            changed,outs=evaluate(c,inputs,drop_i=i,alias=alias)
            if outs==goal:
                full=rebuild(c,i,alias)
                if full and ras.independent_check(full)[0]:
                    best=(full,{'drop':i,'alias':alias,'repair':None});break
            for j in range(i+1,len(c['gates'])):
                stats['repair_positions']+=1
                zero=cofactor_after_j(c,changed,j,0)
                one=cofactor_after_j(c,changed,j,MASK)
                req=care_for_repair(goal,zero,one)
                if req is None:continue
                stats['repairable_positions']+=1
                must1,care=req
                if first is None:first={'drop':i,'alias':alias,'repair_gate':j,'care_bits':care.bit_count()}
                for op,a,b,v in candidates_before_j(c,changed,i,j):
                    stats['gate_candidates']+=1
                    if (v&care)!=must1:continue
                    stats['matched_repair_gates']+=1
                    full=rebuild(c,i,alias,j,(op,a,b))
                    if full is None:stats['same_operand_rejects']+=1;continue
                    if not ras.independent_check(full)[0]:stats['verification_rejects']+=1;continue
                    best=(full,{'drop':i,'alias':alias,'repair':j,'op':op,'a':a,'b':b,'care_bits':care.bit_count()})
                    break
                if best:break
            if best:break
        if best:break
    summary={'status':'found' if best else 'exhausted','source':args.source,'shard':args.shard,'shards':args.shards,
             'stats':dict(stats),'first_repairable':first,'seconds':round(time.monotonic()-t0,3),
             'scope':'delete one gate into earlier alias; simultaneously retarget any later AND/XOR/XNOR gate to two earlier wires, exact joint output care'}
    if best:
        full,wit=best;assert len(full['gates'])<=100
        summary.update(candidate_gates=len(full['gates']),witness=wit,verified_all_256=True)
        (out/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__':main()
