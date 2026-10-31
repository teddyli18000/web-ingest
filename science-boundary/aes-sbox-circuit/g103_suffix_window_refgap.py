#!/usr/bin/env python3
"""Exact local SAT shaving of contiguous windows in the 22-gate G103 suffix.

For each contiguous window of the pure-linear suffix, compute its exact live-in
interface and the subset of window outputs that remain live after the window.
Express those live-outs as linear forms over the live-ins, then call the pinned
2026 `refutation-gap` CaDiCaL shortest-SLP encoder asking whether the same local
map can be realised with one fewer XOR gate.

Unlike retained-guide deletion, the replacement helpers are completely new and
unconstrained.  A SAT model is replayed, converted to XOR/XNOR with exact affine
polarities, spliced back into the complete G103 circuit, pruned, and independently
checked on all 256 AES inputs.  UNSAT/timeout is recorded only at its actual
strength; this script is primarily a constructive local superoptimizer.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import released_and_skeleton as ras
import g103_suffix_linear_rnbp as suf


def affine_suffix_values(c, suffix, boundary):
    m=len(boundary); C=1<<m
    vals={w:(1<<i) for i,w in enumerate(boundary)}
    for g in suffix:
        vals[g['out']]=vals[g['a']]^vals[g['b']]^(C if g['op']=='XNOR' else 0)
    return m,C,vals


def window_problem(suffix, outputs, vals, m, C, i, j):
    win=suffix[i:j]
    produced={g['out'] for g in win}
    liveins=[]; seen=set()
    for g in win:
        for w in (g['a'],g['b']):
            if w not in produced and w not in seen:
                seen.add(w); liveins.append(w)
    # Anything produced in the window and consumed later or exposed as final output.
    later=suffix[j:]
    used_after={w for g in later for w in (g['a'],g['b'])}
    liveouts=[]
    for g in win:
        w=g['out']
        if (w in used_after or w in outputs) and w not in liveouts:
            liveouts.append(w)
    if not liveouts:
        return None

    # Re-express exact affine values relative to the live-in signals themselves.
    lm=len(liveins); LC=1<<lm
    loc={w:1<<k for k,w in enumerate(liveins)}
    exact_const={w:(vals[w]>>m)&1 for w in liveins}
    for g in win:
        a,b=loc[g['a']],loc[g['b']]
        ca,cb=exact_const[g['a']],exact_const[g['b']]
        loc[g['out']]=a^b
        exact_const[g['out']]=ca^cb^(1 if g['op']=='XNOR' else 0)
    targets=[loc[w] for w in liveouts]
    consts=[exact_const[w] for w in liveouts]
    if len(set(targets))!=len(targets):
        return None
    # The external minimum-SLP encoding treats input basis vectors as free targets.
    # A complemented input is not free in XOR/XNOR cost, so skip that rare shape
    # rather than accept a false local shaving witness.
    for q,cbit in zip(targets,consts):
        if q and q&(q-1)==0:
            k=q.bit_length()-1
            if cbit!=exact_const[liveins[k]]:
                return None
    return {'i':i,'j':j,'old_gates':j-i,'liveins':liveins,'liveouts':liveouts,
            'n_inputs':lm,'targets':targets,'target_consts':consts,
            'input_consts':[exact_const[w] for w in liveins]}


def splice(c, prefix, suffix, vals, m, wp, program):
    i,j=wp['i'],wp['j']; liveins=wp['liveins']; liveouts=wp['liveouts']
    sig=[1<<k for k in range(len(liveins))]
    names=list(liveins); const=list(wp['input_consts'])
    wanted={q:c for q,c in zip(wp['targets'],wp['target_consts'])}
    repl=[]
    for gi,(a,b) in enumerate(program):
        v=sig[a]^sig[b]
        desired=wanted.get(v,0)
        neg=desired^const[a]^const[b]
        out=f'__wref_{gi}'
        repl.append({'op':'XNOR' if neg else 'XOR','a':names[a],'b':names[b],'out':out})
        sig.append(v); names.append(out); const.append(desired)
    by={}
    for si,v in enumerate(sig):
        exact=(v,const[si])
        by.setdefault(exact,names[si])
    mp={}
    for w,q,cbit in zip(liveouts,wp['targets'],wp['target_consts']):
        n=by.get((q,cbit))
        if n is None:
            return None
        mp[w]=n

    gates=[dict(g) for g in prefix]
    # Keep suffix gates before window, append replacement, then rewrite later refs.
    gates.extend(dict(g) for g in suffix[:i])
    gates.extend(repl)
    for g in suffix[j:]:
        ng=dict(g); ng['a']=mp.get(ng['a'],ng['a']); ng['b']=mp.get(ng['b'],ng['b'])
        mp[ng['out']]=ng['out']; gates.append(ng)
    outs=[mp.get(o,o) for o in c['outputs']]
    full=ras.prune({'gates':gates,'outputs':outs})
    if not ras.independent_check(full)[0]:
        return None
    return full


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--refgap',required=True)
    ap.add_argument('--min-len',type=int,default=3)
    ap.add_argument('--max-len',type=int,default=10)
    ap.add_argument('--shard',type=int,default=0)
    ap.add_argument('--shards',type=int,default=1)
    ap.add_argument('--conf-budget',type=int,default=300000)
    ap.add_argument('--out',required=True)
    args=ap.parse_args(); out=pathlib.Path(args.out); out.mkdir(parents=True,exist_ok=True)
    root=str(pathlib.Path(args.refgap).resolve()); sys.path.insert(0,root)
    from slp.instance import SLPInstance,verify
    from slp.optimal import exists_program

    c=ras.load_circuit('nist-g103'); assert ras.independent_check(c)[0]
    last,prefix,suffix,boundary=suf.split(c)
    m,C,vals=affine_suffix_values(c,suffix,boundary)
    windows=[]
    serial=0
    for L in range(args.min_len,args.max_len+1):
        for i in range(0,len(suffix)-L+1):
            j=i+L
            wp=window_problem(suffix,c['outputs'],vals,m,C,i,j)
            if wp is None: continue
            if serial%args.shards==args.shard: windows.append(wp)
            serial+=1

    rows=[]; best=None
    t0=time.time()
    for wi,wp in enumerate(windows):
        k=wp['old_gates']-1
        inst=SLPInstance(name=f'g103-suffix-window-{wp["i"]}-{wp["j"]}',
                         n_inputs=wp['n_inputs'],targets=tuple(wp['targets']))
        r=exists_program(inst,k,conf_budget=args.conf_budget)
        rec={'i':wp['i'],'j':wp['j'],'old':wp['old_gates'],'target_k':k,
             'liveins':wp['n_inputs'],'liveouts':len(wp['liveouts']),
             'sat':r.sat,'timed_out':r.timed_out,'seconds':round(r.seconds,3),
             'vars':r.n_vars,'clauses':r.n_clauses}
        if r.sat:
            verify(inst,r.program)
            full=splice(c,prefix,suffix,vals,m,wp,r.program)
            rec['splice_ok']=full is not None
            if full is not None:
                rec['full_gates']=len(full['gates'])
                p=out/f'candidate-{wp["i"]}-{wp["j"]}.json'
                p.write_text(json.dumps(full,indent=2)+'\n')
                if best is None or len(full['gates'])<best[0]: best=(len(full['gates']),p.name,rec)
        rows.append(rec)
        print(json.dumps(rec,sort_keys=True),flush=True)
        if best is not None and best[0]<=102:
            # One verified shave is enough for this pass; subsequent passes should
            # optimize the new seed rather than spend the same compute elsewhere.
            break
    summary={'shard':args.shard,'shards':args.shards,'windows_considered':len(windows),
             'rows':rows,'best':best,'elapsed_s':round(time.time()-t0,3),
             'interpretation':'SAT candidates replayed and all-256 checked; timeout inconclusive; UNSAT family-local'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},sort_keys=True),flush=True)

if __name__=='__main__': main()
