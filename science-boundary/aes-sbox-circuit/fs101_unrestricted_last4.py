#!/usr/bin/env python3
"""Exact unrestricted 3-gate suffix synthesis after FS101 gate g96.

The merged 101-gate record has exactly four gates after g96: g97, g98, g99,
g100.  Outputs y0..y5 are already available by g96; only y6 and y7 remain.
This experiment fixes the 97-gate prefix through g96 and completely discards the
last-four-gate topology, including the identity/count of the final AND gate.

It asks whether y6 and y7 can be synthesized from *any* prefix wires using at
most three legal two-input gates from {AND,XOR,XNOR}.  Because the verifier
forbids constants and requires distinct operand wires, enumeration obeys those
rules exactly.

Completeness for <=3 new gates:
- enumerate every distinct truth function obtainable by legal gate 1 from two
  prefix wires (keeping one witness; truth-equivalent gate-1 witnesses are
  interchangeable after the gate because only its truth table and distinct new
  wire identity affect future gates);
- after gate 1, with two gates left and two distinct missing target functions,
  gate 2 must either produce one target or, if one target is already present,
  may be an arbitrary helper for the other;
- exhaust both target orders and the latter helper case.

Any hit is spliced onto the original prefix, pruned, checked on all 256 AES
inputs, and written as a complete certificate.  Exhaustion proves only this
fixed-prefix suffix family, but unlike released-AND searches it permits the last
nonlinear function itself to change.
"""
from __future__ import annotations

import itertools
import json
import pathlib
import time

import released_and_skeleton as ras
import search_arch_seed as sas

MASK=(1<<256)-1
OPS=("AND","XOR","XNOR")


def op_eval(op,a,b):
    if op=="AND": return a & b
    if op=="XOR": return a ^ b
    return (a ^ b) ^ MASK


def add_name(by_truth,truth,name):
    xs=by_truth.setdefault(truth,[])
    if name not in xs: xs.append(name)


def base_gate_map(sources):
    """truth -> one legal base/base gate witness using distinct wire names."""
    out={}
    for i,(na,va) in enumerate(sources):
        for nb,vb in sources[i+1:]:
            for op in OPS:
                v=op_eval(op,va,vb)
                out.setdefault(v,(op,na,nb))
    return out


def universe_map(base_by,extras):
    d={v:list(ns) for v,ns in base_by.items()}
    for n,v in extras: add_name(d,v,n)
    return d


def find_one(target,base_sources,base_by,base_expr,extras):
    """Return ('existing',name) or ('gate',(op,a,b)) for <=1 gate from universe."""
    u=universe_map(base_by,extras)
    if target in u:
        return ('existing',u[target][0])
    if target in base_expr:
        return ('gate',base_expr[target])

    # Any new one-gate possibility not already in base_expr must use >=1 extra.
    actual=list(base_sources)+list(extras)
    base_names={n for n,_ in base_sources}
    for ei,(en,ev) in enumerate(extras):
        for on,ov in actual:
            if en==on: continue
            # To avoid duplicate testing of extra/extra pairs, impose name order.
            if on not in base_names and en>on: continue
            for op in OPS:
                if op_eval(op,ev,ov)==target:
                    return ('gate',(op,en,on))
    return None


def candidate_second_helpers(base_sources,base_expr,extras):
    """All distinct truth functions obtainable by one legal gate from current universe."""
    out=dict(base_expr)
    actual=list(base_sources)+list(extras)
    base_names={n for n,_ in base_sources}
    for en,ev in extras:
        for on,ov in actual:
            if en==on: continue
            if on not in base_names and en>on: continue
            for op in OPS:
                v=op_eval(op,ev,ov)
                out.setdefault(v,(op,en,on))
    return out


def append_gate(seq,witness,outname,truth):
    op,a,b=witness
    seq2=list(seq); seq2.append({'op':op,'a':a,'b':b,'out':outname,'truth':truth})
    return seq2


def try_finish(base_sources,base_by,base_expr,htruth,hwitness,tA,tB):
    """After fixed gate1=h, exhaust <=2 further gates to obtain both targets."""
    seq=append_gate([],hwitness,'__u1',htruth)
    extras=[('__u1',htruth)]

    rA=find_one(tA,base_sources,base_by,base_expr,extras)
    if rA is None:
        return None
    if rA[0]=='existing':
        a_name=rA[1]
        # A is already available after gate1.  First try B in one more gate.
        rB=find_one(tB,base_sources,base_by,base_expr,extras)
        if rB is not None:
            if rB[0]=='existing': return seq,{'A':a_name,'B':rB[1]}
            seq2=append_gate(seq,rB[1],'__u2',tB)
            return seq2,{'A':a_name,'B':'__u2'}

        # With two gates still available, gate2 may be an arbitrary helper h2,
        # then gate3 must produce B.  Truth-equivalent h2 witnesses are enough.
        for h2,w2 in candidate_second_helpers(base_sources,base_expr,extras).items():
            seq2=append_gate(seq,w2,'__u2',h2)
            extras2=extras+[('__u2',h2)]
            rB=find_one(tB,base_sources,base_by,base_expr,extras2)
            if rB is None: continue
            if rB[0]=='existing': return seq2,{'A':a_name,'B':rB[1]}
            seq3=append_gate(seq2,rB[1],'__u3',tB)
            return seq3,{'A':a_name,'B':'__u3'}
        return None

    # Gate2 produces A.  Then gate3 is the only remaining gate, so B must be
    # present or one gate away from prefix+h1+A.
    seq2=append_gate(seq,rA[1],'__u2',tA)
    extras2=extras+[('__u2',tA)]
    rB=find_one(tB,base_sources,base_by,base_expr,extras2)
    if rB is None: return None
    if rB[0]=='existing': return seq2,{'A':'__u2','B':rB[1]}
    seq3=append_gate(seq2,rB[1],'__u3',tB)
    return seq3,{'A':'__u2','B':'__u3'}


def materialize(c,prefix,seq,target_names):
    gates=[dict(g) for g in c['gates'][:prefix]]
    for g in seq:
        gates.append({k:g[k] for k in ('op','a','b','out')})
    outputs=list(c['outputs'][:6])+[target_names['T6'],target_names['T7']]
    full=ras.prune({'gates':gates,'outputs':outputs})
    ok=ras.independent_check(full)
    if not ok[0]: raise AssertionError(('unrestricted suffix witness failed AES',ok))
    return full


def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); args=ap.parse_args()
    outdir=pathlib.Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    c=ras.load_circuit('fs-101'); assert len(c['gates'])==101 and ras.independent_check(c)[0]
    prefix=next(i for i,g in enumerate(c['gates']) if g['out']=='g96')+1
    assert prefix==97 and len(c['gates'])-prefix==4

    vals=sas.inputs_truth()
    for g in c['gates'][:prefix]: vals[g['out']]=sas.op_eval(g['op'],vals[g['a']],vals[g['b']])
    sources=[(f'x{i}',vals[f'x{i}']) for i in range(8)] + [(g['out'],vals[g['out']]) for g in c['gates'][:prefix]]
    # All wires remain distinct operands even if truth-equivalent.  Keep each
    # source name, and separately index truth -> names for zero-cost aliases.
    base_by={}
    for n,v in sources: add_name(base_by,v,n)
    base_expr=base_gate_map(sources)

    full_vals,outs=sas.eval_circuit(c)
    t6,t7=outs[6],outs[7]
    target_source={'T6':base_by.get(t6,[]),'T7':base_by.get(t7,[])}
    t0=time.time(); tested_h1=0; special_h2=0; found=None

    # If both targets are already prefix functions, pruning itself is a hit.
    if t6 in base_by and t7 in base_by:
        found=([],{'T6':base_by[t6][0],'T7':base_by[t7][0]})

    # Every legal first-gate truth function; one witness per truth is complete.
    if found is None:
        for htruth,hwitness in base_expr.items():
            tested_h1+=1
            for first,second,labA,labB in ((t6,t7,'T6','T7'),(t7,t6,'T7','T6')):
                r=try_finish(sources,base_by,base_expr,htruth,hwitness,first,second)
                if r is None: continue
                seq,namesAB=r
                names={labA:namesAB['A'],labB:namesAB['B']}
                # Remove any redundant generated gates only through full-circuit
                # pruning; the sequence itself always obeys distinct-wire rules.
                full=materialize(c,prefix,seq,names)
                if len(full['gates'])<=100:
                    found=(seq,names,full,htruth,hwitness)
                    break
            if found is not None: break

    elapsed=time.time()-t0
    summary={'status':'found' if found else 'exhausted','prefix_gates':prefix,'old_suffix_gates':4,
             'target_suffix_gates':3,'prefix_source_wires':len(sources),'distinct_prefix_truths':len(base_by),
             'distinct_first_gate_truths':len(base_expr),'tested_first_gate_truths':tested_h1,
             'target6_already_prefix':bool(target_source['T6']),'target7_already_prefix':bool(target_source['T7']),
             'elapsed_s':round(elapsed,3),
             'family_scope':'fixed FS101 prefix through g96; arbitrary <=3 legal AND/XOR/XNOR suffix gates from any prefix wires; only y6/y7 constrained'}
    if found:
        seq,names,full,htruth,hwitness=found
        summary.update(candidate_gates=len(full['gates']),verified_all_256=True,sequence=seq,target_names=names,
                       gate_counts={op:sum(g['op']==op for g in full['gates']) for op in OPS})
        (outdir/'candidate.json').write_text(json.dumps(full,indent=2)+'\n')
    (outdir/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,sort_keys=True),flush=True)

if __name__=='__main__': main()
